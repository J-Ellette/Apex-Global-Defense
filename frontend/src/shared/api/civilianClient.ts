import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const CIVILIAN_BASE_URL = import.meta.env.VITE_CIVILIAN_API_URL ?? 'http://localhost:8091/api/v1'

export const civilianClient = axios.create({
  baseURL: CIVILIAN_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

civilianClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
