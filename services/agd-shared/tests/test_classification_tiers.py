"""Tests for agd_shared.auth classification helpers.

These tests exercise:
  - get_user_classification() — JWT claim → clearance string
  - classification_allowed_levels() — clearance ceiling → visible levels
  - enforce_classification_ceiling() — HTTP-403 guard per tier

They serve as regression tests for Priority D (RLS classification tier
validation): the application-layer enforcement must match the DB-layer
agd_visible_classifications() PL/pgSQL function defined in
db/init/011_classification_hardening.sql.

No database connection is required — application-layer logic only.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from agd_shared.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_user_classification,
)

# ---------------------------------------------------------------------------
# Classification order (must match 011_classification_hardening.sql)
# ---------------------------------------------------------------------------

_ORDERED_LEVELS = ["UNCLASS", "FOUO", "SECRET", "TOP_SECRET", "TS_SCI"]


# ---------------------------------------------------------------------------
# get_user_classification
# ---------------------------------------------------------------------------

class TestGetUserClassification:
    """get_user_classification maps JWT 'cls' claim → clearance string."""

    @pytest.mark.parametrize("cls_int,expected", [
        (0, "UNCLASS"),
        (1, "FOUO"),
        (2, "SECRET"),
        (3, "TOP_SECRET"),
        (4, "TS_SCI"),
    ])
    def test_integer_claim(self, cls_int: int, expected: str):
        assert get_user_classification({"cls": cls_int}) == expected

    @pytest.mark.parametrize("cls_str", _ORDERED_LEVELS)
    def test_string_claim(self, cls_str: str):
        assert get_user_classification({"cls": cls_str}) == cls_str

    def test_missing_claim_defaults_to_unclass(self):
        assert get_user_classification({}) == "UNCLASS"

    def test_unknown_integer_defaults_to_unclass(self):
        assert get_user_classification({"cls": 99}) == "UNCLASS"

    def test_unknown_string_defaults_to_unclass(self):
        assert get_user_classification({"cls": "COSMIC_TOP_SECRET"}) == "UNCLASS"


# ---------------------------------------------------------------------------
# classification_allowed_levels
# ---------------------------------------------------------------------------

class TestClassificationAllowedLevels:
    """Cumulative clearance: level X allows all levels at X and below.

    This mirrors the agd_visible_classifications() DB function:
      UNCLASS    → ['UNCLASS']
      FOUO       → ['UNCLASS', 'FOUO']
      SECRET     → ['UNCLASS', 'FOUO', 'SECRET']
      TOP_SECRET → ['UNCLASS', 'FOUO', 'SECRET', 'TOP_SECRET']
      TS_SCI     → ['UNCLASS', 'FOUO', 'SECRET', 'TOP_SECRET', 'TS_SCI']
    """

    def test_unclass_sees_only_unclass(self):
        assert classification_allowed_levels("UNCLASS") == ["UNCLASS"]

    def test_fouo_sees_unclass_and_fouo(self):
        assert classification_allowed_levels("FOUO") == ["UNCLASS", "FOUO"]

    def test_secret_sees_up_to_secret(self):
        assert classification_allowed_levels("SECRET") == ["UNCLASS", "FOUO", "SECRET"]

    def test_top_secret_sees_up_to_top_secret(self):
        assert classification_allowed_levels("TOP_SECRET") == [
            "UNCLASS", "FOUO", "SECRET", "TOP_SECRET"
        ]

    def test_ts_sci_sees_all_levels(self):
        assert classification_allowed_levels("TS_SCI") == [
            "UNCLASS", "FOUO", "SECRET", "TOP_SECRET", "TS_SCI"
        ]

    def test_each_tier_includes_all_lower_tiers(self):
        """Every tier must be a superset of the tier below it."""
        for i in range(1, len(_ORDERED_LEVELS)):
            current = _ORDERED_LEVELS[i]
            previous = _ORDERED_LEVELS[i - 1]
            current_levels = classification_allowed_levels(current)
            previous_levels = classification_allowed_levels(previous)
            assert set(previous_levels).issubset(set(current_levels)), (
                f"{current} allowed levels should include all {previous} levels"
            )

    def test_each_tier_contains_its_own_level(self):
        for level in _ORDERED_LEVELS:
            assert level in classification_allowed_levels(level)

    def test_unknown_clearance_defaults_to_unclass_visibility(self):
        assert classification_allowed_levels("UNKNOWN") == ["UNCLASS"]


# ---------------------------------------------------------------------------
# enforce_classification_ceiling
# ---------------------------------------------------------------------------

class TestEnforceClassificationCeiling:
    """enforce_classification_ceiling raises HTTP 403 when record exceeds user
    clearance; passes silently when clearance is sufficient.

    Tests cover the full cross-product of user_cls × record_cls tiers.
    """

    @pytest.mark.parametrize("user_cls,record_cls", [
        # Same tier — always allowed
        ("UNCLASS", "UNCLASS"),
        ("FOUO", "FOUO"),
        ("SECRET", "SECRET"),
        ("TOP_SECRET", "TOP_SECRET"),
        ("TS_SCI", "TS_SCI"),
        # Higher clearance — allowed
        ("FOUO", "UNCLASS"),
        ("SECRET", "UNCLASS"),
        ("SECRET", "FOUO"),
        ("TOP_SECRET", "UNCLASS"),
        ("TOP_SECRET", "FOUO"),
        ("TOP_SECRET", "SECRET"),
        ("TS_SCI", "UNCLASS"),
        ("TS_SCI", "FOUO"),
        ("TS_SCI", "SECRET"),
        ("TS_SCI", "TOP_SECRET"),
    ])
    def test_allowed_combinations(self, user_cls: str, record_cls: str):
        """Should not raise when user clearance >= record classification."""
        user = {"cls": user_cls}
        enforce_classification_ceiling(user, record_cls)  # must not raise

    @pytest.mark.parametrize("user_cls,record_cls", [
        # Lower clearance — must be rejected
        ("UNCLASS", "FOUO"),
        ("UNCLASS", "SECRET"),
        ("UNCLASS", "TOP_SECRET"),
        ("UNCLASS", "TS_SCI"),
        ("FOUO", "SECRET"),
        ("FOUO", "TOP_SECRET"),
        ("FOUO", "TS_SCI"),
        ("SECRET", "TOP_SECRET"),
        ("SECRET", "TS_SCI"),
        ("TOP_SECRET", "TS_SCI"),
    ])
    def test_forbidden_combinations(self, user_cls: str, record_cls: str):
        """Should raise HTTP 403 when user clearance < record classification."""
        user = {"cls": user_cls}
        with pytest.raises(HTTPException) as exc_info:
            enforce_classification_ceiling(user, record_cls)
        assert exc_info.value.status_code == 403
        assert user_cls in exc_info.value.detail
        assert record_cls in exc_info.value.detail

    def test_403_detail_includes_both_levels(self):
        """Error detail must name both the record level and user ceiling."""
        user = {"cls": "UNCLASS"}
        with pytest.raises(HTTPException) as exc_info:
            enforce_classification_ceiling(user, "TOP_SECRET")
        detail = exc_info.value.detail
        assert "TOP_SECRET" in detail
        assert "UNCLASS" in detail

    def test_rls_tier_visibility_matches_app_layer(self):
        """Application layer and DB RLS function must enforce identical rules.

        The DB function agd_visible_classifications() returns the same level
        sets as classification_allowed_levels().  This test confirms the
        application layer is consistent so that RLS and app-layer checks are
        never out of sync.
        """
        db_rls_expected = {
            "UNCLASS":    ["UNCLASS"],
            "FOUO":       ["UNCLASS", "FOUO"],
            "SECRET":     ["UNCLASS", "FOUO", "SECRET"],
            "TOP_SECRET": ["UNCLASS", "FOUO", "SECRET", "TOP_SECRET"],
            "TS_SCI":     ["UNCLASS", "FOUO", "SECRET", "TOP_SECRET", "TS_SCI"],
        }
        for clearance, expected_visible in db_rls_expected.items():
            assert classification_allowed_levels(clearance) == expected_visible, (
                f"App-layer visible levels for {clearance!r} "
                f"do not match DB RLS function output"
            )
