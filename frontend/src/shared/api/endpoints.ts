import { apiClient } from './client'
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

const OOB_BASE = import.meta.env.VITE_OOB_API_URL ?? '/api/v1'

// Dedicated axios instance pointing at oob-svc (shares interceptors via import of apiClient base).
// For simplicity in dev we route through the same base; in production Kong proxies both.
import axios from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const oobClient = axios.create({
  baseURL: OOB_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})

oobClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

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
