"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/navbar";
import { Button } from "@/components/ui/button";
import { CardSpotlight } from "@/components/ui/card-spotlight";
import { generateQuery, executeQuery, listDatabases } from "@/lib/api";
import { getAuthToken } from "@/lib/utils";

export default function Dashboard() {
  const [naturalLanguageQuery, setNaturalLanguageQuery] = useState("");
  const [generatedSQL, setGeneratedSQL] = useState("");
  const [queryResult, setQueryResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [databases, setDatabases] = useState<any[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState("");
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
        const response = await listDatabases();
        if (response && response.databases) {
          setDatabases(response.databases);
          if (response.databases.length > 0) {
            setSelectedDatabase(response.databases[0].id);
          }
        }
      } catch (err) {
        console.error("Error fetching databases:", err);
        setError("Failed to load databases. Please try again later.");
      }
    };
    
    fetchDatabases();
  }, [router]);
  
  const handleGenerateQuery = async () => {
    if (!naturalLanguageQuery.trim()) {
      setError("Please enter a query");
      return;
    }
    
    try {
      setLoading(true);
      setError("");
      setGeneratedSQL("");
      setQueryResult(null);
      
      const response = await generateQuery(naturalLanguageQuery, selectedDatabase);
      
      if (response && response.sql_info && response.sql_info.generated_sql) {
        setGeneratedSQL(response.sql_info.generated_sql);
      } else {
        setError("Failed to generate SQL query");
      }
    } catch (err: any) {
      console.error("Error generating query:", err);
      setError(err.response?.data?.error?.message || "Failed to generate query");
    } finally {
      setLoading(false);
    }
  };
  
  const handleExecuteQuery = async () => {
    if (!generatedSQL.trim()) {
      setError("No SQL query to execute");
      return;
    }
    
    try {
      setLoading(true);
      setError("");
      setQueryResult(null);
      
      const response = await executeQuery(generatedSQL, {}, selectedDatabase);
      
      if (response && response.result) {
        setQueryResult(response.result);
      } else {
        setError("Failed to execute query");
      }
    } catch (err: any) {
      console.error("Error executing query:", err);
      setError(err.response?.data?.error?.message || "Failed to execute query");
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen flex flex-col dark">
      <Navbar />
      
      <main className="flex-1 py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-white mb-8">Database Query Dashboard</h1>
          
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            {/* Natural Language Query Input */}
            <div className="lg:col-span-2">
              <CardSpotlight containerClassName="h-full">
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-white mb-4">Natural Language Query</h2>
                  
                  <div className="mb-4">
                    <label htmlFor="database" className="block text-sm font-medium text-zinc-300 mb-1">
                      Select Database
                    </label>
                    <select
                      id="database"
                      value={selectedDatabase}
                      onChange={(e) => setSelectedDatabase(e.target.value)}
                      className="block w-full rounded-md border border-white/10 bg-zinc-900/50 px-3 py-2 text-white shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                    >
                      {databases.map((db) => (
                        <option key={db.id} value={db.id}>
                          {db.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="mb-4">
                    <textarea
                      className="w-full h-32 rounded-md border border-white/10 bg-zinc-900/50 px-3 py-2 text-white placeholder-zinc-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
                      placeholder="Enter your query in natural language, e.g. 'Show me the top 5 customers by total spend'"
                      value={naturalLanguageQuery}
                      onChange={(e) => setNaturalLanguageQuery(e.target.value)}
                    />
                  </div>
                  
                  <Button
                    variant="gradient"
                    onClick={handleGenerateQuery}
                    disabled={loading || !naturalLanguageQuery.trim()}
                  >
                    {loading ? "Generating..." : "Generate SQL"}
                  </Button>
                </div>
              </CardSpotlight>
            </div>
            
            {/* Quick Tips */}
            <div>
              <CardSpotlight containerClassName="h-full">
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-white mb-4">Query Tips</h2>
                  <ul className="space-y-2 text-sm text-zinc-300">
                    <li className="flex items-start gap-2">
                      <span className="text-purple-400">•</span>
                      <span>Be specific about what data you want to see</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-purple-400">•</span>
                      <span>Mention time periods if relevant (e.g., "last month", "Q1 2023")</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-purple-400">•</span>
                      <span>Specify sorting (e.g., "ordered by amount", "top 10")</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-purple-400">•</span>
                      <span>Include grouping information if needed (e.g., "grouped by category")</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-purple-400">•</span>
                      <span>For complex queries, break them down into simpler steps</span>
                    </li>
                  </ul>
                  
                  <h3 className="text-md font-semibold text-white mt-6 mb-2">Example Queries</h3>
                  <ul className="space-y-2 text-sm text-zinc-300">
                    <li className="flex items-start gap-2">
                      <span className="text-indigo-400">→</span>
                      <span>"Show total sales by country in the last quarter"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-indigo-400">→</span>
                      <span>"List customers who haven't made a purchase in 6 months"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-indigo-400">→</span>
                      <span>"What's the average order value by product category?"</span>
                    </li>
                  </ul>
                </div>
              </CardSpotlight>
            </div>
          </div>
          
          {/* Error Display */}
          {error && (
            <div className="mt-8 rounded-md bg-red-500/10 p-4 text-sm text-red-400">
              {error}
            </div>
          )}
          
          {/* Generated SQL */}
          {generatedSQL && (
            <div className="mt-8">
              <CardSpotlight>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-white">Generated SQL</h2>
                    <Button variant="outline" onClick={handleExecuteQuery} disabled={loading}>
                      {loading ? "Executing..." : "Execute Query"}
                    </Button>
                  </div>
                  
                  <div className="rounded-md bg-zinc-900/70 p-4 font-mono text-sm text-zinc-300 overflow-x-auto">
                    {generatedSQL.split("\n").map((line, i) => (
                      <div key={i}>{line || " "}</div>
                    ))}
                  </div>
                </div>
              </CardSpotlight>
            </div>
          )}
          
          {/* Query Results */}
          {queryResult && (
            <div className="mt-8">
              <CardSpotlight>
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-white mb-4">Query Results</h2>
                  
                  <div className="rounded-md bg-zinc-900/70 p-4 overflow-x-auto">
                    <p className="text-xs text-zinc-500 mb-2">
                      {queryResult.row_count} row{queryResult.row_count !== 1 ? "s" : ""} returned in {queryResult.execution_time.toFixed(3)}s
                    </p>
                    
                    {queryResult.rows.length > 0 ? (
                      <table className="min-w-full divide-y divide-white/10">
                        <thead>
                          <tr>
                            {queryResult.columns.map((column: any) => (
                              <th 
                                key={column.name} 
                                className="py-3.5 px-4 text-left text-sm font-semibold text-zinc-300"
                              >
                                {column.display_name || column.name}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {queryResult.rows.map((row: any, rowIndex: number) => (
                            <tr key={rowIndex}>
                              {queryResult.columns.map((column: any) => (
                                <td 
                                  key={`${rowIndex}-${column.name}`} 
                                  className="whitespace-nowrap py-2 px-4 text-sm text-zinc-400"
                                >
                                  {row[column.name] != null ? String(row[column.name]) : "NULL"}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p className="text-zinc-400">No results found</p>
                    )}
                  </div>
                </div>
              </CardSpotlight>
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 