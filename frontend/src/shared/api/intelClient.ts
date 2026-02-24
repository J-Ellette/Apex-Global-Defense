import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const INTEL_BASE_URL = import.meta.env.VITE_INTEL_API_URL ?? 'http://localhost:8090/api/v1'

export const intelClient = axios.create({
  baseURL: INTEL_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

intelClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
