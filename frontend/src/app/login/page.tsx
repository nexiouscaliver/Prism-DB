"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/ui/navbar";
import { login } from "@/lib/api";
import { setAuthToken } from "@/lib/utils";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError("Please enter both username and password");
      return;
    }
    
    try {
      setLoading(true);
      setError("");
      
      const response = await login(username, password);
      
      if (response && response.access_token) {
        setAuthToken(response.access_token);
        router.push("/dashboard");
      } else {
        setError("Invalid response from server");
      }
    } catch (err: any) {
      console.error("Login error:", err);
      setError(err.response?.data?.error?.message || "Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col">
      <Navbar />
      
      <div className="flex flex-1 items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8">
          <div>
            <div className="flex justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-12 w-12 text-purple-500"
              >
                <path d="M12 3v19" />
                <path d="M5 8h14" />
                <path d="M15 5V2" />
                <path d="M9 5V2" />
                <path d="M15 22v-3" />
                <path d="M9 22v-3" />
                <path d="M4 5v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2Z" />
              </svg>
            </div>
            <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-white">
              Sign in to PrismDB
            </h2>
            <p className="mt-2 text-center text-sm text-zinc-400">
              Enter your credentials to access your account
            </p>
          </div>
          
          <div className="mt-8 rounded-xl border border-white/10 bg-black/30 p-8 backdrop-blur-sm">
            {error && (
              <div className="mb-4 rounded-md bg-red-500/10 p-3 text-sm text-red-400">
                {error}
              </div>
            )}
            
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-zinc-300">
                  Username
                </label>
                <div className="mt-1">
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="block w-full appearance-none rounded-md border border-white/10 bg-zinc-900/50 px-3 py-2 text-white placeholder-zinc-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-zinc-300">
                  Password
                </label>
                <div className="mt-1">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full appearance-none rounded-md border border-white/10 bg-zinc-900/50 px-3 py-2 text-white placeholder-zinc-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <Button
                  type="submit"
                  variant="gradient"
                  className="w-full"
                  disabled={loading}
                >
                  {loading ? "Signing in..." : "Sign in"}
                </Button>
              </div>
            </form>
            
            {/* For demo purposes, we'll add a note about credentials */}
            <div className="mt-6">
              <p className="text-center text-xs text-zinc-500">
                For demo purposes, use:
                <br />
                Username: <span className="font-mono text-zinc-400">demo</span>
                <br />
                Password: <span className="font-mono text-zinc-400">password</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
} 