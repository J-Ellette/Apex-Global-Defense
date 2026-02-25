import axios, { type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../../../app/providers/AuthProvider'

const TRAINING_BASE_URL = import.meta.env.VITE_TRAINING_API_URL ?? 'http://localhost:8096/api/v1'

export const trainingClient = axios.create({
  baseURL: TRAINING_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

trainingClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
