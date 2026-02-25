import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const INFOOPS_BASE_URL = import.meta.env.VITE_INFOOPS_API_URL ?? 'http://localhost:8094/api/v1'

export const infoopsClient = axios.create({
  baseURL: INFOOPS_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

infoopsClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
