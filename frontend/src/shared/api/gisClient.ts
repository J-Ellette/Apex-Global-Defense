import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const GIS_BASE_URL = import.meta.env.VITE_GIS_API_URL ?? 'http://localhost:8095/api/v1'

export const gisClient = axios.create({
  baseURL: GIS_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60_000,
})

gisClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
