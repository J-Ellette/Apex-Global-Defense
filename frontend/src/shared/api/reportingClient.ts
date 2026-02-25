import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const REPORTING_BASE_URL = import.meta.env.VITE_REPORTING_API_URL ?? 'http://localhost:8092/api/v1'

export const reportingClient = axios.create({
  baseURL: REPORTING_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

reportingClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
