"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/navbar";
import { Button } from "@/components/ui/button";
import { CardSpotlight } from "@/components/ui/card-spotlight";
import { listAgents, getAgent, configureAgent } from "@/lib/api";
import { getAuthToken } from "@/lib/utils";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [configuring, setConfiguring] = useState(false);
  const [error, setError] = useState("");
  const [configureError, setConfigureError] = useState("");
  const router = useRouter();
  
  useEffect(() => {
    // Check if user is logged in
    const token = getAuthToken();
    if (!token) {
      router.push("/login");
      return;
    }
    
    // Load available agents
    const fetchAgents = async () => {
      try {
        setLoading(true);
        setError("");
        
        const response = await listAgents();
        
        if (response && response.agents) {
          setAgents(response.agents);
        } else {
          setError("Failed to load agents");
        }
      } catch (err: any) {
        console.error("Error loading agents:", err);
        setError(err.response?.data?.error?.message || "Failed to load agents");
      } finally {
        setLoading(false);
      }
    };
    
    fetchAgents();
  }, [router]);
  
  const handleAgentSelect = async (agentId: string) => {
    try {
      setLoading(true);
      setError("");
      
      const response = await getAgent(agentId);
      
      if (response && response.agent) {
        setSelectedAgent(response.agent);
      } else {
        setError(`Failed to load agent ${agentId}`);
      }
    } catch (err: any) {
      console.error(`Error loading agent ${agentId}:`, err);
      setError(err.response?.data?.error?.message || `Failed to load agent ${agentId}`);
    } finally {
      setLoading(false);
    }
  };
  
  const handleConfigureSave = async () => {
    if (!selectedAgent) return;
    
    try {
      setConfiguring(true);
      setConfigureError("");
      
      await configureAgent(selectedAgent.id, selectedAgent.config);
      
      // Refresh agent list
      const response = await listAgents();
      if (response && response.agents) {
        setAgents(response.agents);
      }
      
      setSelectedAgent(null);
    } catch (err: any) {
      console.error("Error configuring agent:", err);
      setConfigureError(err.response?.data?.error?.message || "Failed to configure agent");
    } finally {
      setConfiguring(false);
    }
  };
  
  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "inactive":
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
          <h1 className="text-3xl font-bold text-white mb-8">AI Agents</h1>
          
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
              <span className="ml-3 text-zinc-400">Loading agents...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
              {/* Agent List */}
              <div className="lg:col-span-1">
                <CardSpotlight containerClassName="h-full">
                  <div className="p-6">
                    <h2 className="text-xl font-semibold text-white mb-4">Available Agents</h2>
                    
                    {agents.length > 0 ? (
                      <ul className="space-y-3">
                        {agents.map((agent) => (
                          <li key={agent.id}>
                            <button
                              onClick={() => handleAgentSelect(agent.id)}
                              className={`w-full rounded-lg border border-white/10 p-3 text-left transition-colors hover:bg-white/5 ${
                                selectedAgent?.id === agent.id ? "bg-white/10" : ""
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <h3 className="text-sm font-medium text-white">{agent.name}</h3>
                                  <p className="text-xs text-zinc-400">ID: {agent.id}</p>
                                </div>
                                <span 
                                  className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${getStatusColor(agent.status)}`}
                                >
                                  {agent.status}
                                </span>
                              </div>
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="rounded-lg border border-dashed border-white/10 p-6 text-center">
                        <p className="text-sm text-zinc-400">No agents available</p>
                      </div>
                    )}
                  </div>
                </CardSpotlight>
              </div>
              
              {/* Agent Details */}
              <div className="lg:col-span-2">
                {selectedAgent ? (
                  <CardSpotlight>
                    <div className="p-6">
                      <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-semibold text-white">{selectedAgent.name} Configuration</h2>
                        <span 
                          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${getStatusColor(selectedAgent.status)}`}
                        >
                          {selectedAgent.status}
                        </span>
                      </div>
                      
                      {/* Configuration Error */}
                      {configureError && (
                        <div className="mb-4 rounded-md bg-red-500/10 p-3 text-sm text-red-400">
                          {configureError}
                        </div>
                      )}
                      
                      {/* Agent Configuration Form */}
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-zinc-300 mb-1">
                            Agent ID
                          </label>
                          <input
                            type="text"
                            value={selectedAgent.id}
                            readOnly
                            className="block w-full rounded-md border border-white/10 bg-zinc-900/50 px-3 py-2 text-white shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                          />
                        </div>
                        
                        {/* Sample configuration fields - these would be based on the actual agent config schema */}
                        <div>
                          <label className="block text-sm font-medium text-zinc-300 mb-1">
                            Configuration
                          </label>
                          <textarea
                            rows={8}
                            className="w-full rounded-md border border-white/10 bg-zinc-900/50 px-3 py-2 text-white placeholder-zinc-500 font-mono shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                            value={JSON.stringify(selectedAgent.config || {}, null, 2)}
                            onChange={(e) => {
                              try {
                                const newConfig = JSON.parse(e.target.value);
                                setSelectedAgent({
                                  ...selectedAgent,
                                  config: newConfig
                                });
                                setConfigureError("");
                              } catch (err) {
                                setConfigureError("Invalid JSON configuration");
                              }
                            }}
                          />
                          <p className="mt-1 text-xs text-zinc-500">
                            Edit the JSON configuration above to modify agent behavior
                          </p>
                        </div>
                        
                        <div className="flex justify-end space-x-3 pt-4">
                          <Button
                            variant="outline"
                            className="border-white/20"
                            onClick={() => setSelectedAgent(null)}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="gradient"
                            onClick={handleConfigureSave}
                            disabled={configuring}
                          >
                            {configuring ? "Saving..." : "Save Configuration"}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardSpotlight>
                ) : (
                  <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-white/10 p-12 text-center">
                    <div>
                      <h3 className="text-lg font-medium text-white mb-2">Select an Agent</h3>
                      <p className="text-zinc-400">
                        Choose an agent from the list to view and configure its settings.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 