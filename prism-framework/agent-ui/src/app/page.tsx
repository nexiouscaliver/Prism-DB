'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/playground/Sidebar/Sidebar'
import { ChatArea } from '@/components/playground/ChatArea'
import { Suspense } from 'react'
import { useAuthStore } from '@/store/auth-store'

export default function Home() {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()
  
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, router])
  
  if (!isAuthenticated) {
    return null
  }
  
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <div className="flex h-screen bg-background/80">
        <Sidebar />
        <ChatArea />
      </div>
    </Suspense>
  )
}
