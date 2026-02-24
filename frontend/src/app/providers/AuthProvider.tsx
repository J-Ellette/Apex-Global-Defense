import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Permission, Role, ClassificationLevel } from '../../shared/api/types'
import { authApi } from '../../shared/api/endpoints'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean

  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setTokens: (accessToken: string, refreshToken: string) => void

  // Derived helpers
  hasRole: (role: Role) => boolean
  hasPermission: (permission: Permission) => boolean
  classificationLevel: ClassificationLevel
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        const response = await authApi.login({ email, password })
        set({
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token,
          isAuthenticated: true,
        })
      },

      logout: async () => {
        const { refreshToken } = get()
        if (refreshToken) {
          try {
            await authApi.logout(refreshToken)
          } catch {
            // Best-effort logout — clear local state regardless
          }
        }
        set({ user: null, token: null, refreshToken: null, isAuthenticated: false })
      },

      setTokens: (accessToken: string, newRefreshToken: string) => {
        set({ token: accessToken, refreshToken: newRefreshToken })
      },

      hasRole: (role: Role) => {
        return get().user?.roles.includes(role) ?? false
      },

      hasPermission: (permission: Permission) => {
        // Derive permissions from roles client-side (mirrors backend RolePermissions map)
        const user = get().user
        if (!user) return false
        return ROLE_PERMISSIONS[permission]?.some((r) => user.roles.includes(r)) ?? false
      },

      get classificationLevel(): ClassificationLevel {
        return get().user?.classification ?? 'UNCLASS'
      },
    }),
    {
      name: 'agd-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)

// Permission → roles that grant it (mirrors backend RolePermissions in models/models.go).
// Keep in sync with the backend when roles or permissions change.
const ROLE_PERMISSIONS: Record<Permission, Role[]> = {
  'scenario:read':        ['viewer', 'analyst', 'planner', 'commander', 'sim_operator', 'admin'],
  'scenario:write':       ['planner', 'commander', 'admin'],
  'oob:read':             ['viewer', 'analyst', 'planner', 'commander', 'sim_operator', 'admin'],
  'oob:write':            ['planner', 'commander', 'admin'],
  'intel:read':           ['analyst', 'planner', 'commander', 'admin'],
  'intel:write':          ['analyst', 'commander', 'admin'],
  'simulation:run':       ['sim_operator', 'admin'],
  'simulation:control':   ['sim_operator', 'admin'],
  'users:manage':         ['admin'],
  'classification:manage':['classification_officer'],
}
