import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const CBRN_BASE_URL = import.meta.env.VITE_CBRN_API_URL ?? 'http://localhost:8087/api/v1'

export const cbrnClient = axios.create({
  baseURL: CBRN_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

cbrnClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
