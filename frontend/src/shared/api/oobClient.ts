import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/app/providers/AuthProvider'

const OOB_BASE_URL = import.meta.env.VITE_OOB_API_URL ?? '/api/v1'

export const oobClient = axios.create({
  baseURL: OOB_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

oobClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
