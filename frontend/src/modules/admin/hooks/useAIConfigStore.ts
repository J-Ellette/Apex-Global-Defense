import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type AIProvider = 'ollama' | 'openai' | 'anthropic' | 'azure_openai'

export interface AIConfig {
  provider: AIProvider
  ollamaUrl: string
  ollamaModel: string
  apiKey: string
  azureEndpoint: string
  azureDeployment: string
  azureApiKey: string
  fallbackEnabled: boolean
  showConfidenceScores: boolean
}

const DEFAULT_CONFIG: AIConfig = {
  provider: 'ollama',
  ollamaUrl: 'http://localhost:11434',
  ollamaModel: 'llama3.1:8b',
  apiKey: '',
  azureEndpoint: '',
  azureDeployment: '',
  azureApiKey: '',
  fallbackEnabled: true,
  showConfidenceScores: true,
}

interface AIConfigStore {
  config: AIConfig
  setConfig: (config: AIConfig) => void
}

export const useAIConfigStore = create<AIConfigStore>()(
  persist(
    (set) => ({
      config: DEFAULT_CONFIG,
      setConfig: (config) => set({ config }),
    }),
    {
      name: 'agd-ai-config',
      // Never persist API keys to localStorage
      partialize: (state) => ({
        config: {
          ...state.config,
          apiKey: '',
          azureApiKey: '',
        },
      }),
    },
  ),
)
