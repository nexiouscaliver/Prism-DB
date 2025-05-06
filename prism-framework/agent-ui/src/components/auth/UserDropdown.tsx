'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth-store'
import { toast } from 'sonner'

export default function UserDropdown() {
  const { user, logout } = useAuthStore()
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])
  
  const handleLogout = () => {
    logout()
    toast.success('Logged out successfully')
    router.push('/auth/login')
  }
  
  if (!user) {
    return null
  }
  
  return (
    <div className="relative" ref={dropdownRef}>
      <button
        className="flex items-center space-x-2 rounded-full p-1 text-sm text-foreground hover:bg-accent hover:text-accent-foreground focus:outline-none"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
          {user.username.charAt(0).toUpperCase()}
        </div>
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-md border bg-background shadow-md z-50">
          <div className="p-2 border-b">
            <p className="text-sm font-medium">{user.username}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
          <div className="p-1">
            <button 
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 text-sm rounded-md hover:bg-accent hover:text-accent-foreground"
            >
              Log out
            </button>
          </div>
        </div>
      )}
    </div>
  )
} 