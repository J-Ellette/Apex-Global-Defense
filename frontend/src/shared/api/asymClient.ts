import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/app/providers/AuthProvider'

const ASYM_BASE_URL = import.meta.env.VITE_ASYM_API_URL ?? 'http://localhost:8088/api/v1'

export const asymClient = axios.create({
  baseURL: ASYM_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

asymClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
