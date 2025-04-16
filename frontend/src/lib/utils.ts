import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api/v1"

export const setAuthToken = (token: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("token", token)
  }
}

export const getAuthToken = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("token")
  }
  return null
}

export const removeAuthToken = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("token")
  }
} 