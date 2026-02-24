import { apiClient } from './client'
import { oobClient } from './oobClient'
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
