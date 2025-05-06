'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/store/auth-store'

interface ProtectedRouteProps {
  children: React.ReactNode
}

const publicRoutes = ['/auth/login', '/auth/register']

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()
  
  useEffect(() => {
    // If not authenticated and not on a public route, redirect to login
    if (!isAuthenticated && !publicRoutes.includes(pathname)) {
      router.push('/auth/login')
    }
    
    // If authenticated and on a public route (login/register), redirect to home
    if (isAuthenticated && publicRoutes.includes(pathname)) {
      router.push('/')
    }
  }, [isAuthenticated, pathname, router])
  
  // If on a protected route and not authenticated, show nothing (will redirect)
  if (!isAuthenticated && !publicRoutes.includes(pathname)) {
    return null
  }
  
  return <>{children}</>
} 