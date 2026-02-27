import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/app/providers/AuthProvider'

const ECON_BASE_URL = import.meta.env.VITE_ECON_API_URL ?? 'http://localhost:8093/api/v1'

export const econClient = axios.create({
  baseURL: ECON_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

econClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
