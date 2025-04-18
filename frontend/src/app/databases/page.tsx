"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/navbar";
import { Button } from "@/components/ui/button";
import { CardSpotlight } from "@/components/ui/card-spotlight";
import { listDatabases } from "@/lib/api";
import { getAuthToken } from "@/lib/utils";

export default function DatabasesPage() {
  const [databases, setDatabases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();
  
  useEffect(() => {
    // Check if user is logged in
    const token = getAuthToken();
    if (!token) {
      router.push("/login");
      return;
    }
    
    // Load available databases
    const fetchDatabases = async () => {
      try {
        setLoading(true);
        setError("");
        
        const response = await listDatabases();
        
        if (response && response.data && response.data.databases) {
          setDatabases(response.data.databases);
        } else {
          setError("Failed to load databases");
        }
      } catch (err: any) {
        console.error("Error loading databases:", err);
        setError(err.response?.data?.error?.message || "Failed to load databases");
      } finally {
        setLoading(false);
      }
    };
    
    fetchDatabases();
  }, [router]);
  
  // Function to determine database status badge color
  const getStatusColor = (status?: string) => {
    if (!status) return "bg-blue-500/20 text-blue-400 border-blue-500/30"; // Default for undefined
    
    switch (status.toLowerCase()) {
      case "connected":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "disconnected":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      case "error":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    }
  };
  
  return (
    <div className="min-h-screen flex flex-col dark">
      <Navbar />
      
      <main className="flex-1 py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-white">Connected Databases</h1>
            <Button
              variant="gradient"
              onClick={() => router.push("/dashboard")}
            >
              Run a Query
            </Button>
          </div>
          
          {/* Error Display */}
          {error && (
            <div className="mb-8 rounded-md bg-red-500/10 p-4 text-sm text-red-400">
              {error}
            </div>
          )}
          
          {/* Loading State */}
          {loading ? (
            <div className="flex items-center justify-center p-12">
              <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-purple-500"></div>
              <span className="ml-3 text-zinc-400">Loading databases...</span>
            </div>
          ) : (
            <>
              {/* Database Grid */}
              {databases.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {databases.map((db) => (
                    <CardSpotlight key={db.id} containerClassName="h-full">
                      <div className="p-6">
                        <div className="flex items-start justify-between">
                          <div>
                            <h2 className="text-xl font-semibold text-white mb-1">{db.name}</h2>
                            <p className="text-sm text-zinc-400 mb-4">{db.type}</p>
                          </div>
                          <span 
                            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${getStatusColor(db.connection_status)}`}
                          >
                            {db.connection_status || (db.readonly ? "Read-only" : "Available")}
                          </span>
                        </div>
                        
                        {db.tables && (
                          <div>
                            <h3 className="text-sm font-medium text-zinc-300 mb-2">Available Tables</h3>
                            <div className="max-h-32 overflow-y-auto rounded-md bg-zinc-900/50 p-3">
                              {db.tables.length > 0 ? (
                                <ul className="space-y-1 text-xs text-zinc-400">
                                  {db.tables.map((table: string) => (
                                    <li key={table} className="flex items-center">
                                      <svg 
                                        xmlns="http://www.w3.org/2000/svg" 
                                        className="h-3 w-3 mr-1.5 text-indigo-400" 
                                        fill="none" 
                                        viewBox="0 0 24 24" 
                                        stroke="currentColor"
                                      >
                                        <path 
                                          strokeLinecap="round" 
                                          strokeLinejoin="round" 
                                          strokeWidth={2} 
                                          d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" 
                                        />
                                      </svg>
                                      {table}
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-xs text-zinc-500">No tables available</p>
                              )}
                            </div>
                          </div>
                        )}
                        
                        <div className="mt-6 flex justify-end">
                          <Button 
                            variant="glossy"
                            onClick={() => router.push(`/dashboard?db=${db.id}`)}
                            className="text-xs"
                          >
                            Query this Database
                          </Button>
                        </div>
                      </div>
                    </CardSpotlight>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-white/10 p-12 text-center">
                  <h3 className="text-lg font-medium text-white mb-2">No Databases Connected</h3>
                  <p className="text-zinc-400 mb-6">There are no databases configured or connected at the moment.</p>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
} 