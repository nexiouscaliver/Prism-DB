import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export type User = {
  id: string
  username: string
  email: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  login: (credentials: { username: string; password: string }) => Promise<boolean>
  register: (userData: { username: string; email: string; password: string }) => Promise<boolean>
  logout: () => void
}

// Hard-coded users for demo purposes
const DEMO_USERS = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@prismdb.io',
    password: 'admin123'
  },
  {
    id: '2',
    username: 'Shahil',
    email: 'shahil@prismdb.io',
    password: 'shahil123'
  }
]

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      
      login: async (credentials) => {
        // Find user with matching credentials
        const user = DEMO_USERS.find(
          (u) => 
            u.username === credentials.username && 
            u.password === credentials.password
        )
        
        if (user) {
          // Set auth state
          set({ 
            isAuthenticated: true, 
            user: {
              id: user.id,
              username: user.username,
              email: user.email
            }
          })
          return true
        }
        
        return false
      },
      
      register: async (userData) => {
        // Check if username or email already exists
        const existingUser = DEMO_USERS.find(
          (u) => u.username === userData.username || u.email === userData.email
        )
        
        if (existingUser) {
          return false
        }
        
        // In a real app, we would add the user to the database
        // For this demo, we'll just simulate a successful registration
        const newUser = {
          id: String(DEMO_USERS.length + 1),
          username: userData.username,
          email: userData.email
        }
        
        set({ isAuthenticated: true, user: newUser })
        return true
      },
      
      logout: () => {
        set({ isAuthenticated: false, user: null })
      }
    }),
    {
      name: 'prismdb-auth-storage',
      storage: createJSONStorage(() => localStorage)
    }
  )
) 