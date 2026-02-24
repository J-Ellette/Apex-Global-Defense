import { apiClient } from './client'
import { oobClient } from './oobClient'
import { simClient } from './simClient'
import { cyberClient } from './cyberClient'
import { cbrnClient } from './cbrnClient'
import { asymClient } from './asymClient'
import type {
  LoginRequest,
  LoginResponse,
  User,
  Country,
  MilitaryUnit,
  CreateUnitRequest,
  UpdateUnitRequest,
  CompareRequest,
  CompareResponse,
  EquipmentCatalogItem,
  Scenario,
  CreateScenarioRequest,
  UpdateScenarioRequest,
  BranchScenarioRequest,
  SimulationRun,
  SimEvent,
  AfterActionReport,
  StartRunRequest,
  LogisticsState,
  ATTACKTactic,
  ATTACKTechnique,
  InfraGraph,
  InfraNode,
  InfraEdge,
  CreateInfraNodeRequest,
  CreateInfraEdgeRequest,
  CyberAttack,
  CreateAttackRequest,
  SimulateAttackRequest,
  SimulateAttackResult,
  CBRNCategory,
  CBRNAgent,
  CBRNRelease,
  CreateReleaseRequest,
  DispersionSimulation,
  IEDCategory,
  IEDTypeEntry,
  InsurgentCell,
  CreateCellRequest,
  UpdateCellRequest,
  CellLink,
  CreateCellLinkRequest,
  CellNetwork,
  IEDIncident,
  CreateIncidentRequest,
  UpdateIncidentRequest,
  NetworkAnalysis,
} from './types'

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<LoginResponse>('/auth/login', data).then((r) => r.data),

  refresh: (refreshToken: string) =>
    apiClient
      .post<LoginResponse>('/auth/refresh', { refresh_token: refreshToken })
      .then((r) => r.data),

  logout: (refreshToken: string) =>
    apiClient.post('/auth/logout', { refresh_token: refreshToken }),

  me: () => apiClient.get<User>('/auth/me').then((r) => r.data),
}

export const oobApi = {
  listCountries: () =>
    oobClient.get<Country[]>('/oob/countries').then((r) => r.data),

  getCountry: (code: string) =>
    oobClient.get<Country>(`/oob/countries/${code}`).then((r) => r.data),

  listForces: (code: string) =>
    oobClient.get<MilitaryUnit[]>(`/oob/countries/${code}/forces`).then((r) => r.data),

  getUnit: (id: string) =>
    oobClient.get<MilitaryUnit>(`/oob/units/${id}`).then((r) => r.data),

  createUnit: (data: CreateUnitRequest) =>
    oobClient.post<MilitaryUnit>('/oob/units', data).then((r) => r.data),

  updateUnit: (id: string, data: UpdateUnitRequest) =>
    oobClient.put<MilitaryUnit>(`/oob/units/${id}`, data).then((r) => r.data),

  deleteUnit: (id: string) => oobClient.delete(`/oob/units/${id}`),

  compareCountries: (data: CompareRequest) =>
    oobClient.post<CompareResponse>('/oob/compare', data).then((r) => r.data),

  listEquipmentCatalog: () =>
    oobClient.get<EquipmentCatalogItem[]>('/oob/equipment/catalog').then((r) => r.data),
}

export const scenarioApi = {
  listScenarios: () =>
    oobClient.get<Scenario[]>('/scenarios').then((r) => r.data),

  getScenario: (id: string) =>
    oobClient.get<Scenario>(`/scenarios/${id}`).then((r) => r.data),

  createScenario: (data: CreateScenarioRequest) =>
    oobClient.post<Scenario>('/scenarios', data).then((r) => r.data),

  updateScenario: (id: string, data: UpdateScenarioRequest) =>
    oobClient.put<Scenario>(`/scenarios/${id}`, data).then((r) => r.data),

  deleteScenario: (id: string) => oobClient.delete(`/scenarios/${id}`),

  branchScenario: (id: string, data: BranchScenarioRequest) =>
    oobClient.post<Scenario>(`/scenarios/${id}/branch`, data).then((r) => r.data),
}

export const simApi = {
  listRuns: (scenarioId: string) =>
    simClient.get<SimulationRun[]>(`/scenarios/${scenarioId}/runs`).then((r) => r.data),

  startRun: (scenarioId: string, data: StartRunRequest) =>
    simClient.post<SimulationRun>(`/scenarios/${scenarioId}/runs`, data).then((r) => r.data),

  getRun: (runId: string) =>
    simClient.get<SimulationRun>(`/runs/${runId}`).then((r) => r.data),

  pauseRun: (runId: string) =>
    simClient.post<SimulationRun>(`/runs/${runId}/pause`).then((r) => r.data),

  resumeRun: (runId: string) =>
    simClient.post<SimulationRun>(`/runs/${runId}/resume`).then((r) => r.data),

  stepRun: (runId: string) =>
    simClient.post<SimEvent>(`/runs/${runId}/step`).then((r) => r.data),

  getEvents: (runId: string, since?: string) =>
    simClient
      .get<SimEvent[]>(`/runs/${runId}/events`, { params: since ? { since } : undefined })
      .then((r) => r.data),

  getReport: (runId: string) =>
    simClient.get<AfterActionReport>(`/runs/${runId}/report`).then((r) => r.data),

  getLogistics: (runId: string) =>
    simClient.get<LogisticsState>(`/runs/${runId}/logistics`).then((r) => r.data),
}

export const cyberApi = {
  // ATT&CK Techniques
  listTechniques: (params?: { tactic?: ATTACKTactic; platform?: string; severity?: string; q?: string }) =>
    cyberClient.get<ATTACKTechnique[]>('/cyber/techniques', { params }).then((r) => r.data),

  getTechnique: (id: string) =>
    cyberClient.get<ATTACKTechnique>(`/cyber/techniques/${id}`).then((r) => r.data),

  // Infrastructure Graph
  getGraph: (scenarioId?: string) =>
    cyberClient
      .get<InfraGraph>('/cyber/infrastructure', { params: scenarioId ? { scenario_id: scenarioId } : undefined })
      .then((r) => r.data),

  createNode: (data: CreateInfraNodeRequest) =>
    cyberClient.post<InfraNode>('/cyber/infrastructure/nodes', data).then((r) => r.data),

  deleteNode: (nodeId: string) => cyberClient.delete(`/cyber/infrastructure/nodes/${nodeId}`),

  createEdge: (data: CreateInfraEdgeRequest) =>
    cyberClient.post<InfraEdge>('/cyber/infrastructure/edges', data).then((r) => r.data),

  deleteEdge: (edgeId: string) => cyberClient.delete(`/cyber/infrastructure/edges/${edgeId}`),

  // Cyber Attacks
  listAttacks: (params?: { scenario_id?: string; status?: string }) =>
    cyberClient.get<CyberAttack[]>('/cyber/attacks', { params }).then((r) => r.data),

  createAttack: (data: CreateAttackRequest) =>
    cyberClient.post<CyberAttack>('/cyber/attacks', data).then((r) => r.data),

  getAttack: (attackId: string) =>
    cyberClient.get<CyberAttack>(`/cyber/attacks/${attackId}`).then((r) => r.data),

  simulateAttack: (attackId: string, data: SimulateAttackRequest) =>
    cyberClient.post<SimulateAttackResult>(`/cyber/attacks/${attackId}/simulate`, data).then((r) => r.data),
}

export const cbrnApi = {
  // Agent catalog
  listAgents: (params?: { category?: CBRNCategory; q?: string }) =>
    cbrnClient.get<CBRNAgent[]>('/cbrn/agents', { params }).then((r) => r.data),

  getAgent: (agentId: string) =>
    cbrnClient.get<CBRNAgent>(`/cbrn/agents/${agentId}`).then((r) => r.data),

  // Release events
  listReleases: (scenarioId?: string) =>
    cbrnClient
      .get<CBRNRelease[]>('/cbrn/releases', { params: scenarioId ? { scenario_id: scenarioId } : undefined })
      .then((r) => r.data),

  createRelease: (data: CreateReleaseRequest) =>
    cbrnClient.post<CBRNRelease>('/cbrn/releases', data).then((r) => r.data),

  getRelease: (releaseId: string) =>
    cbrnClient.get<CBRNRelease>(`/cbrn/releases/${releaseId}`).then((r) => r.data),

  deleteRelease: (releaseId: string) => cbrnClient.delete(`/cbrn/releases/${releaseId}`),

  // Dispersion simulation
  simulate: (releaseId: string) =>
    cbrnClient.post<DispersionSimulation>(`/cbrn/releases/${releaseId}/simulate`).then((r) => r.data),

  getSimulation: (releaseId: string) =>
    cbrnClient.get<DispersionSimulation>(`/cbrn/releases/${releaseId}/simulation`).then((r) => r.data),
}

export const asymApi = {
  // Cell function catalog (static)
  listCellTypes: () =>
    asymClient.get('/asym/cell-types').then((r) => r.data),

  // IED type catalog (static)
  listIEDTypes: (params?: { category?: IEDCategory }) =>
    asymClient.get<IEDTypeEntry[]>('/asym/ied-types', { params }).then((r) => r.data),

  getIEDType: (typeId: string) =>
    asymClient.get<IEDTypeEntry>(`/asym/ied-types/${typeId}`).then((r) => r.data),

  // Insurgent cells
  listCells: (params?: { scenario_id?: string; status?: string }) =>
    asymClient.get<InsurgentCell[]>('/asym/cells', { params }).then((r) => r.data),

  createCell: (data: CreateCellRequest) =>
    asymClient.post<InsurgentCell>('/asym/cells', data).then((r) => r.data),

  getCell: (cellId: string) =>
    asymClient.get<InsurgentCell>(`/asym/cells/${cellId}`).then((r) => r.data),

  updateCell: (cellId: string, data: UpdateCellRequest) =>
    asymClient.put<InsurgentCell>(`/asym/cells/${cellId}`, data).then((r) => r.data),

  deleteCell: (cellId: string) => asymClient.delete(`/asym/cells/${cellId}`),

  // Cell links
  createCellLink: (data: CreateCellLinkRequest) =>
    asymClient.post<CellLink>('/asym/cell-links', data).then((r) => r.data),

  deleteCellLink: (linkId: string) => asymClient.delete(`/asym/cell-links/${linkId}`),

  // Cell network
  getNetwork: (scenarioId?: string) =>
    asymClient
      .get<CellNetwork>('/asym/network', { params: scenarioId ? { scenario_id: scenarioId } : undefined })
      .then((r) => r.data),

  // Network analysis
  analyzeNetwork: (scenarioId?: string) =>
    asymClient
      .get<NetworkAnalysis>('/asym/network/analysis', {
        params: scenarioId ? { scenario_id: scenarioId } : undefined,
      })
      .then((r) => r.data),

  // IED incidents
  listIncidents: (params?: { scenario_id?: string; status?: string }) =>
    asymClient.get<IEDIncident[]>('/asym/incidents', { params }).then((r) => r.data),

  createIncident: (data: CreateIncidentRequest) =>
    asymClient.post<IEDIncident>('/asym/incidents', data).then((r) => r.data),

  getIncident: (incidentId: string) =>
    asymClient.get<IEDIncident>(`/asym/incidents/${incidentId}`).then((r) => r.data),

  updateIncident: (incidentId: string, data: UpdateIncidentRequest) =>
    asymClient.put<IEDIncident>(`/asym/incidents/${incidentId}`, data).then((r) => r.data),

  deleteIncident: (incidentId: string) => asymClient.delete(`/asym/incidents/${incidentId}`),
}
