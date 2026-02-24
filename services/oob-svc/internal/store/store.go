package store

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/lib/pq"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/models"
)

// OOBStore manages Order of Battle data in PostgreSQL.
type OOBStore struct {
	db *sqlx.DB
}

// NewOOBStore creates a new OOBStore.
func NewOOBStore(db *sqlx.DB) *OOBStore {
	return &OOBStore{db: db}
}

// ListCountries returns all countries ordered by name.
func (s *OOBStore) ListCountries(ctx context.Context) ([]models.Country, error) {
	const q = `
		SELECT code, name, region, alliance_codes, gdp_usd, defense_budget_usd,
		       population, area_km2, iso2, flag_emoji, updated_at
		FROM countries
		ORDER BY name`

	rows, err := s.db.QueryContext(ctx, q)
	if err != nil {
		return nil, fmt.Errorf("list countries: %w", err)
	}
	defer rows.Close()

	var countries []models.Country
	for rows.Next() {
		c, err := scanCountry(rows)
		if err != nil {
			return nil, err
		}
		countries = append(countries, *c)
	}
	return countries, rows.Err()
}

// GetCountry retrieves a single country by ISO 3166-1 alpha-3 code.
func (s *OOBStore) GetCountry(ctx context.Context, code string) (*models.Country, error) {
	const q = `
		SELECT code, name, region, alliance_codes, gdp_usd, defense_budget_usd,
		       population, area_km2, iso2, flag_emoji, updated_at
		FROM countries
		WHERE code = $1`

	rows, err := s.db.QueryContext(ctx, q, strings.ToUpper(code))
	if err != nil {
		return nil, fmt.Errorf("get country: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, ErrNotFound
	}
	return scanCountry(rows)
}

// ListUnitsByCountry returns military units for a given country.
func (s *OOBStore) ListUnitsByCountry(ctx context.Context, code string) ([]models.MilitaryUnit, error) {
	const q = `
		SELECT id, country_code, branch, echelon, name, short_name, nato_symbol,
		       parent_id,
		       ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
		       classification::text, confidence, data_sources, as_of, created_at, updated_at
		FROM military_units
		WHERE country_code = $1
		ORDER BY branch, name`

	rows, err := s.db.QueryContext(ctx, q, strings.ToUpper(code))
	if err != nil {
		return nil, fmt.Errorf("list units by country: %w", err)
	}
	defer rows.Close()

	var units []models.MilitaryUnit
	for rows.Next() {
		u, err := scanUnit(rows)
		if err != nil {
			return nil, err
		}
		units = append(units, *u)
	}
	return units, rows.Err()
}

// GetUnit retrieves a single military unit by ID.
func (s *OOBStore) GetUnit(ctx context.Context, id uuid.UUID) (*models.MilitaryUnit, error) {
	const q = `
		SELECT id, country_code, branch, echelon, name, short_name, nato_symbol,
		       parent_id,
		       ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
		       classification::text, confidence, data_sources, as_of, created_at, updated_at
		FROM military_units
		WHERE id = $1`

	rows, err := s.db.QueryContext(ctx, q, id)
	if err != nil {
		return nil, fmt.Errorf("get unit: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, ErrNotFound
	}
	return scanUnit(rows)
}

// CreateUnit inserts a new military unit.
func (s *OOBStore) CreateUnit(ctx context.Context, req models.CreateUnitRequest) (*models.MilitaryUnit, error) {
	classification := req.Classification
	if classification == "" {
		classification = "UNCLASS"
	}

	var dataSources *string
	if len(req.DataSources) > 0 {
		b, err := json.Marshal(req.DataSources)
		if err != nil {
			return nil, fmt.Errorf("marshal data_sources: %w", err)
		}
		s := string(b)
		dataSources = &s
	}

	var locationExpr string
	var args []interface{}

	// Base args: country_code, branch, echelon, name, short_name, nato_symbol, parent_id,
	//            classification, confidence, data_sources, as_of
	args = append(args,
		strings.ToUpper(req.CountryCode),
		req.Branch,
		req.Echelon,
		req.Name,
		req.ShortName,
		req.NATOSymbol,
		req.ParentID,
		classification,
		req.Confidence,
		dataSources,
		req.AsOf,
	)

	if req.Latitude != nil && req.Longitude != nil {
		args = append(args, *req.Longitude, *req.Latitude)
		locationExpr = fmt.Sprintf("ST_SetSRID(ST_MakePoint($%d, $%d), 4326)::geography", len(args)-1, len(args))
	} else {
		locationExpr = "NULL"
	}

	q := fmt.Sprintf(`
		INSERT INTO military_units
		    (country_code, branch, echelon, name, short_name, nato_symbol, parent_id,
		     location, classification, confidence, data_sources, as_of)
		VALUES ($1, $2, $3, $4, $5, $6, $7, %s, $8, $9, $10::jsonb::text[], $11)
		RETURNING id, country_code, branch, echelon, name, short_name, nato_symbol,
		          parent_id,
		          ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
		          classification::text, confidence, data_sources, as_of, created_at, updated_at`,
		locationExpr)

	rows, err := s.db.QueryContext(ctx, q, args...)
	if err != nil {
		return nil, fmt.Errorf("create unit: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, fmt.Errorf("create unit: no row returned")
	}
	return scanUnit(rows)
}

// UpdateUnit applies a partial update to a military unit.
func (s *OOBStore) UpdateUnit(ctx context.Context, id uuid.UUID, req models.UpdateUnitRequest) (*models.MilitaryUnit, error) {
	setClauses := []string{}
	args := []interface{}{}
	argIdx := 1

	addField := func(col string, val interface{}) {
		setClauses = append(setClauses, fmt.Sprintf("%s = $%d", col, argIdx))
		args = append(args, val)
		argIdx++
	}

	if req.Branch != nil {
		addField("branch", *req.Branch)
	}
	if req.Echelon != nil {
		addField("echelon", *req.Echelon)
	}
	if req.Name != nil {
		addField("name", *req.Name)
	}
	if req.ShortName != nil {
		addField("short_name", *req.ShortName)
	}
	if req.NATOSymbol != nil {
		addField("nato_symbol", *req.NATOSymbol)
	}
	if req.ParentID != nil {
		addField("parent_id", *req.ParentID)
	}
	if req.Classification != nil {
		addField("classification", *req.Classification)
	}
	if req.Confidence != nil {
		addField("confidence", *req.Confidence)
	}
	if len(req.DataSources) > 0 {
		b, err := json.Marshal(req.DataSources)
		if err != nil {
			return nil, fmt.Errorf("marshal data_sources: %w", err)
		}
		addField("data_sources", string(b)+"::jsonb::text[]")
	}
	if req.AsOf != nil {
		addField("as_of", *req.AsOf)
	}
	if req.Latitude != nil && req.Longitude != nil {
		setClauses = append(setClauses, fmt.Sprintf(
			"location = ST_SetSRID(ST_MakePoint($%d, $%d), 4326)::geography", argIdx, argIdx+1,
		))
		args = append(args, *req.Longitude, *req.Latitude)
		argIdx += 2
	}

	if len(setClauses) == 0 {
		return s.GetUnit(ctx, id)
	}

	setClauses = append(setClauses, "updated_at = NOW()")

	args = append(args, id)
	q := fmt.Sprintf(`
		UPDATE military_units
		SET %s
		WHERE id = $%d
		RETURNING id, country_code, branch, echelon, name, short_name, nato_symbol,
		          parent_id,
		          ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
		          classification::text, confidence, data_sources, as_of, created_at, updated_at`,
		strings.Join(setClauses, ", "), argIdx)

	rows, err := s.db.QueryContext(ctx, q, args...)
	if err != nil {
		return nil, fmt.Errorf("update unit: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, ErrNotFound
	}
	return scanUnit(rows)
}

// DeleteUnit removes a military unit by ID.
func (s *OOBStore) DeleteUnit(ctx context.Context, id uuid.UUID) error {
	result, err := s.db.ExecContext(ctx, `DELETE FROM military_units WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("delete unit: %w", err)
	}
	n, _ := result.RowsAffected()
	if n == 0 {
		return ErrNotFound
	}
	return nil
}

// CountryStrength aggregates unit and personnel data for a country.
func (s *OOBStore) CountryStrength(ctx context.Context, code string, asOf *time.Time) (*models.CountryStrength, error) {
	country, err := s.GetCountry(ctx, code)
	if err != nil {
		return nil, err
	}

	var asOfFilter string
	var asOfArg interface{}
	if asOf != nil {
		asOfFilter = "AND as_of <= $2"
		asOfArg = *asOf
	}

	q := fmt.Sprintf(`
		SELECT branch, COUNT(*) AS cnt
		FROM military_units
		WHERE country_code = $1 %s
		GROUP BY branch`, asOfFilter)

	var rows *sql.Rows
	var rowErr error
	if asOf != nil {
		rows, rowErr = s.db.QueryContext(ctx, q, strings.ToUpper(code), asOfArg)
	} else {
		rows, rowErr = s.db.QueryContext(ctx, q, strings.ToUpper(code))
	}
	if rowErr != nil {
		return nil, fmt.Errorf("country strength query: %w", rowErr)
	}
	defer rows.Close()

	byBranch := make(map[string]int)
	total := 0
	for rows.Next() {
		var branch string
		var cnt int
		if err := rows.Scan(&branch, &cnt); err != nil {
			return nil, err
		}
		byBranch[branch] = cnt
		total += cnt
	}

	// Aggregate personnel
	pq := `
		SELECT
		    SUM(pc.total)        AS total,
		    SUM(pc.active_duty)  AS active_duty,
		    SUM(pc.reserve)      AS reserve,
		    SUM(pc.paramilitary) AS paramilitary
		FROM personnel_counts pc
		JOIN military_units mu ON mu.id = pc.unit_id
		WHERE mu.country_code = $1`

	var ps models.PersonnelSummary
	err = s.db.QueryRowContext(ctx, pq, strings.ToUpper(code)).Scan(
		&ps.Total, &ps.ActiveDuty, &ps.Reserve, &ps.Paramilitary,
	)
	if err != nil && err != sql.ErrNoRows {
		return nil, fmt.Errorf("personnel query: %w", err)
	}

	return &models.CountryStrength{
		Country:    *country,
		TotalUnits: total,
		ByBranch:   byBranch,
		Personnel:  &ps,
	}, nil
}

// ListEquipmentCatalog returns all equipment catalog entries.
func (s *OOBStore) ListEquipmentCatalog(ctx context.Context) ([]models.EquipmentCatalogItem, error) {
	const q = `
		SELECT type_code, category, name, origin_country, specs, threat_score, in_service_year, updated_at
		FROM equipment_catalog
		ORDER BY category, name`

	rows, err := s.db.QueryContext(ctx, q)
	if err != nil {
		return nil, fmt.Errorf("list equipment catalog: %w", err)
	}
	defer rows.Close()

	var items []models.EquipmentCatalogItem
	for rows.Next() {
		var item models.EquipmentCatalogItem
		var specsJSON []byte
		err := rows.Scan(
			&item.TypeCode, &item.Category, &item.Name, &item.OriginCountry,
			&specsJSON, &item.ThreatScore, &item.InServiceYear, &item.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("scan equipment catalog: %w", err)
		}
		if specsJSON != nil {
			item.Specs = &specsJSON
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

// ── helpers ───────────────────────────────────────────────────────────────────

// ErrNotFound is returned when a requested record does not exist.
var ErrNotFound = fmt.Errorf("not found")

// scanner is a common interface for *sql.Row and *sql.Rows.
type scanner interface {
	Scan(dest ...interface{}) error
}

func scanCountry(row scanner) (*models.Country, error) {
	c := &models.Country{}
	var allianceJSON []byte

	err := row.Scan(
		&c.Code, &c.Name, &c.Region, &allianceJSON,
		&c.GDPUsd, &c.DefenseBudgetUsd, &c.Population, &c.AreaKm2,
		&c.ISO2, &c.FlagEmoji, &c.UpdatedAt,
	)
	if err != nil {
		return nil, fmt.Errorf("scan country: %w", err)
	}

	// alliance_codes is stored as a TEXT[] in Postgres; driver returns it as "{X,Y}"
	if len(allianceJSON) > 0 {
		c.AllianceCodes = parsePGTextArray(string(allianceJSON))
	}
	if c.AllianceCodes == nil {
		c.AllianceCodes = []string{}
	}

	return c, nil
}

func scanUnit(row scanner) (*models.MilitaryUnit, error) {
	u := &models.MilitaryUnit{}
	var sourcesJSON []byte

	err := row.Scan(
		&u.ID, &u.CountryCode, &u.Branch, &u.Echelon, &u.Name, &u.ShortName, &u.NATOSymbol,
		&u.ParentID,
		&u.Latitude, &u.Longitude,
		&u.Classification, &u.Confidence, &sourcesJSON,
		&u.AsOf, &u.CreatedAt, &u.UpdatedAt,
	)
	if err != nil {
		return nil, fmt.Errorf("scan unit: %w", err)
	}

	if len(sourcesJSON) > 0 {
		u.DataSources = parsePGTextArray(string(sourcesJSON))
	}
	if u.DataSources == nil {
		u.DataSources = []string{}
	}

	return u, nil
}

// parsePGTextArray parses a PostgreSQL TEXT[] literal like {"A","B","C"} or {A,B,C}.
func parsePGTextArray(s string) []string {
	s = strings.TrimPrefix(s, "{")
	s = strings.TrimSuffix(s, "}")
	if s == "" {
		return []string{}
	}
	parts := strings.Split(s, ",")
	result := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		p = strings.Trim(p, `"`)
		if p != "" {
			result = append(result, p)
		}
	}
	return result
}

// ── Scenario CRUD ─────────────────────────────────────────────────────────────

// ListScenarios returns all scenarios for the given org, newest first.
func (s *OOBStore) ListScenarios(ctx context.Context, orgID string) ([]models.Scenario, error) {
	const q = `
		SELECT id, name, description, classification::text, created_by, org_id,
		       parent_id, tags, created_at, updated_at
		FROM scenarios
		WHERE org_id = $1
		ORDER BY updated_at DESC`

	rows, err := s.db.QueryContext(ctx, q, orgID)
	if err != nil {
		return nil, fmt.Errorf("list scenarios: %w", err)
	}
	defer rows.Close()

	var scenarios []models.Scenario
	for rows.Next() {
		sc, err := scanScenario(rows)
		if err != nil {
			return nil, err
		}
		scenarios = append(scenarios, *sc)
	}
	if scenarios == nil {
		scenarios = []models.Scenario{}
	}
	return scenarios, rows.Err()
}

// GetScenario retrieves a single scenario by ID.
func (s *OOBStore) GetScenario(ctx context.Context, id uuid.UUID) (*models.Scenario, error) {
	const q = `
		SELECT id, name, description, classification::text, created_by, org_id,
		       parent_id, tags, created_at, updated_at
		FROM scenarios
		WHERE id = $1`

	rows, err := s.db.QueryContext(ctx, q, id)
	if err != nil {
		return nil, fmt.Errorf("get scenario: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, ErrNotFound
	}
	return scanScenario(rows)
}

// CreateScenario inserts a new scenario row.
func (s *OOBStore) CreateScenario(ctx context.Context, req models.CreateScenarioRequest, userID, orgID uuid.UUID) (*models.Scenario, error) {
	cls := req.Classification
	if cls == "" {
		cls = "UNCLASS"
	}
	tags := req.Tags
	if tags == nil {
		tags = []string{}
	}

	const q = `
		INSERT INTO scenarios (name, description, classification, created_by, org_id, tags)
		VALUES ($1, $2, $3::classification_level, $4, $5, $6)
		RETURNING id, name, description, classification::text, created_by, org_id,
		          parent_id, tags, created_at, updated_at`

	rows, err := s.db.QueryContext(ctx, q,
		req.Name, req.Description, cls, userID, orgID,
		pq.Array(tags),
	)
	if err != nil {
		return nil, fmt.Errorf("create scenario: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, fmt.Errorf("create scenario: no row returned")
	}
	return scanScenario(rows)
}

// UpdateScenario applies a partial update to a scenario.
func (s *OOBStore) UpdateScenario(ctx context.Context, id uuid.UUID, req models.UpdateScenarioRequest) (*models.Scenario, error) {
	sc, err := s.GetScenario(ctx, id)
	if err != nil {
		return nil, err
	}

	if req.Name != nil {
		sc.Name = *req.Name
	}
	sc.Description = req.Description
	if req.Classification != nil {
		sc.Classification = *req.Classification
	}
	if req.Tags != nil {
		sc.Tags = req.Tags
	} else if sc.Tags == nil {
		sc.Tags = []string{}
	}

	const q = `
		UPDATE scenarios
		SET name = $1, description = $2, classification = $3::classification_level,
		    tags = $4, updated_at = NOW()
		WHERE id = $5
		RETURNING id, name, description, classification::text, created_by, org_id,
		          parent_id, tags, created_at, updated_at`

	rows, err := s.db.QueryContext(ctx, q,
		sc.Name, sc.Description, sc.Classification,
		pq.Array(sc.Tags), id,
	)
	if err != nil {
		return nil, fmt.Errorf("update scenario: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, ErrNotFound
	}
	return scanScenario(rows)
}

// DeleteScenario removes a scenario by ID.
func (s *OOBStore) DeleteScenario(ctx context.Context, id uuid.UUID) error {
	res, err := s.db.ExecContext(ctx, `DELETE FROM scenarios WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("delete scenario: %w", err)
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return ErrNotFound
	}
	return nil
}

// BranchScenario creates a copy of an existing scenario with a new name and
// sets the parent_id to the source scenario ID.
func (s *OOBStore) BranchScenario(ctx context.Context, sourceID uuid.UUID, branchName string, userID uuid.UUID) (*models.Scenario, error) {
	src, err := s.GetScenario(ctx, sourceID)
	if err != nil {
		return nil, err
	}

	tags := src.Tags
	if tags == nil {
		tags = []string{}
	}

	const q = `
		INSERT INTO scenarios (name, description, classification, created_by, org_id, parent_id, tags)
		VALUES ($1, $2, $3::classification_level, $4, $5, $6, $7)
		RETURNING id, name, description, classification::text, created_by, org_id,
		          parent_id, tags, created_at, updated_at`

	rows, err := s.db.QueryContext(ctx, q,
		branchName, src.Description, src.Classification,
		userID, src.OrgID, src.ID, pq.Array(tags),
	)
	if err != nil {
		return nil, fmt.Errorf("branch scenario: %w", err)
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, fmt.Errorf("branch scenario: no row returned")
	}
	return scanScenario(rows)
}

func scanScenario(row scanner) (*models.Scenario, error) {
	sc := &models.Scenario{}
	var tags pq.StringArray

	if err := row.Scan(
		&sc.ID, &sc.Name, &sc.Description, &sc.Classification,
		&sc.CreatedBy, &sc.OrgID, &sc.ParentID, &tags,
		&sc.CreatedAt, &sc.UpdatedAt,
	); err != nil {
		return nil, fmt.Errorf("scan scenario: %w", err)
	}

	if tags != nil {
		sc.Tags = []string(tags)
	} else {
		sc.Tags = []string{}
	}
	return sc, nil
}

// ── Audit Log ─────────────────────────────────────────────────────────────────

// AuditEntry holds a single audit event to write.
type AuditEntry struct {
	UserID       uuid.UUID
	SessionID    *uuid.UUID
	Action       string
	ResourceType string
	ResourceID   *uuid.UUID
	Classification string
	IPAddress    string
	UserAgent    string
	Payload      interface{}
}

// WriteAuditLog appends a row to the audit_log partitioned table.
// It is best-effort: errors are returned but must not fail the primary request.
func (s *OOBStore) WriteAuditLog(ctx context.Context, e AuditEntry) error {
	payloadJSON, _ := json.Marshal(e.Payload)

	var ip *net.IP
	if e.IPAddress != "" {
		parsed := net.ParseIP(e.IPAddress)
		ip = &parsed
	}

	cls := e.Classification
	if cls == "" {
		cls = "UNCLASS"
	}

	_, err := s.db.ExecContext(ctx, `
		INSERT INTO audit_log
		    (user_id, session_id, action, resource_type, resource_id,
		     classification, ip_address, user_agent, payload)
		VALUES ($1, $2, $3, $4, $5, $6::classification_level, $7::inet, $8, $9)`,
		e.UserID, e.SessionID, e.Action, e.ResourceType, e.ResourceID,
		cls, ipToString(ip), e.UserAgent, payloadJSON,
	)
	if err != nil {
		return fmt.Errorf("write audit log: %w", err)
	}
	return nil
}

func ipToString(ip *net.IP) *string {
	if ip == nil {
		return nil
	}
	s := ip.String()
	return &s
}

// WriteAuditLogAsync fires the audit write in a goroutine so it never blocks
// the HTTP response path.  Log errors are swallowed — add a zap.Logger if you
// need them surfaced.
func (s *OOBStore) WriteAuditLogAsync(e AuditEntry) {
	go func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = s.WriteAuditLog(ctx, e) //nolint:errcheck
	}()
}
