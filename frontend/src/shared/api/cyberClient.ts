import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const CYBER_BASE_URL = import.meta.env.VITE_CYBER_API_URL ?? 'http://localhost:8086/api/v1'

export const cyberClient = axios.create({
  baseURL: CYBER_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

cyberClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
