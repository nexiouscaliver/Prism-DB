'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'sonner'
import { useAuthStore } from '@/store/auth-store'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuthStore()
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    
    try {
      const success = await login(formData)
      
      if (success) {
        toast.success('Logged in successfully')
        router.push('/')
      } else {
        setError('Invalid username or password')
        toast.error('Login failed')
      }
    } catch (err) {
      setError('An error occurred during login')
      toast.error('Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-background relative">
      <Link 
        href="/" 
        className="absolute top-6 left-6 flex items-center justify-center w-8 h-8 rounded-full bg-background border border-input shadow-sm hover:shadow-md transition-all duration-200 text-muted-foreground hover:text-foreground group"
      >
        <ArrowLeft size={16} className="transition-transform group-hover:-translate-x-0.5" />
        <span className="sr-only">Back to home</span>
      </Link>
      
      <div className="m-auto w-full max-w-md p-8 space-y-8 bg-background rounded-lg border shadow-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground">PrismDB</h1>
          <p className="text-muted-foreground mt-2">Log in to your account</p>
        </div>
        
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-600 rounded-md text-sm">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium text-foreground">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              value={formData.username}
              onChange={handleChange}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Enter your username"
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="password" className="text-sm font-medium text-foreground">
                Password
              </label>
            </div>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Enter your password"
            />
          </div>
          
          <Button
            type="submit"
            className="w-full bg-primary text-black hover:bg-primary/90"
            disabled={isLoading}
          >
            {isLoading ? 'Logging in...' : 'Log in'}
          </Button>
        </form>
        
        <div className="text-center text-sm mt-6">
          <p className="text-muted-foreground">
            Don't have an account?{' '}
            <Link href="/auth/register" className="text-primary hover:underline">
              Sign up
            </Link>
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            
          </p>
        </div>
      </div>
    </div>
  )
} 