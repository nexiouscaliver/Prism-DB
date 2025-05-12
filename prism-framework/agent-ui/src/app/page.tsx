'use client'

import React, { useEffect, useState } from "react";
import { useRouter } from 'next/navigation';
import { motion } from "framer-motion";
import Link from "next/link";
import { useAuthStore } from '@/store/auth-store';
import dynamic from 'next/dynamic';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Importing UI components
import { Button } from "@/components/ui/button";

// Import the workflow diagram with dynamic import to avoid SSR issues with Mermaid.js
const AgentWorkflowDiagram = dynamic(
  () => import('@/components/diagrams/agent-workflow'),
  { 
    ssr: false, 
    loading: () => (
      <div className="h-full w-full flex items-center justify-center">
        <div className="animate-pulse text-primary text-lg">Loading workflow diagram...</div>
      </div>
    )
  }
);

// TypeScript interfaces for data
interface QueryData {
  type: "bar" | "pie" | "table" | "scatter";
  labels?: string[];
  values?: number[];
  rows?: string[][];
  title: string;
  unit?: string;
  dataType?: string;
  sqlQuery: string;
  executionTime: string;
  insight: string;
  recommendation: string;
}

interface DemoQuery {
  id: number;
  query: string;
  data: QueryData;
}

export default function Home() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  
  // State for interactive demo section
  const [selectedQuery, setSelectedQuery] = useState(1);
  const [customQuery, setCustomQuery] = useState("");
  const [executingQuery, setExecutingQuery] = useState(false);
  
  // Get current query data and ensure it has defined properties
  const currentQueryData = demoQueries.find(q => q.id === selectedQuery)?.data || demoQueries[0].data;
  
  // Ensure values are defined with fallbacks
  const currentValues = currentQueryData.values || [];
  const currentLabels = currentQueryData.labels || [];
  const currentRows = currentQueryData.rows || [];
  
  // Function to handle selecting a query
  const handleQuerySelect = (id: number) => {
    setSelectedQuery(id);
  };
  
  // Function to handle custom query submission
  const handleCustomQuerySubmit = () => {
    if (customQuery.trim() === "") return;
    
    setExecutingQuery(true);
    
    // Simulate query execution delay and redirect to login
    setTimeout(() => {
      setExecutingQuery(false);
      router.push('/auth/login');
    }, 800);
  };
  
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/playground');
    }
  }, [isAuthenticated, router]);
  
  return (
    <div className="min-h-screen">
      {/* Navigation Bar */}
      <nav className="fixed top-0 w-full py-4 bg-black/30 backdrop-blur-lg z-50 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-8 w-8 text-primary"
            >
              <path d="M12 3v19" />
              <path d="M5 8h14" />
              <path d="M4 5v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2Z" />
            </svg>
            <span className="text-2xl font-bold bg-gradient-to-r from-violet-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              PrismDB
            </span>
          </div>
          <div className="hidden md:flex space-x-8">
            <a href="#features" className="text-white/70 hover:text-white transition-colors">Features</a>
            <a href="#agents" className="text-white/70 hover:text-white transition-colors">Agents</a>
            <a href="#architecture" className="text-white/70 hover:text-white transition-colors">Architecture</a>
            <a href="#demo" className="text-white/70 hover:text-white transition-colors">Demo</a>
          </div>
          <div>
            <Link href="/auth/login">
              <Button variant="outline" size="sm" className="mr-2">
                Log In
              </Button>
            </Link>
            <Link href="/auth/register">
              <Button variant="outline" size="sm">
                Sign Up
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-28 pb-16 md:pt-36 md:pb-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-black/90 via-purple-950/10 to-black z-0"></div>
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]"></div>
        </div>
        
        <motion.div 
          className="container relative z-10 mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-center">
            <motion.h1 
              className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white mb-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <span className="block">Transform Natural Language</span>
              <span className="block bg-gradient-to-r from-purple-400 via-pink-500 to-indigo-400 bg-clip-text text-transparent">
                Into Powerful Database Insights
              </span>
            </motion.h1>
            <motion.p 
              className="mt-6 text-lg md:text-xl text-zinc-300 max-w-3xl mx-auto"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              Prism Framework is a sophisticated multi-agent system that acts as a contextual prism for databases,
              transforming raw natural language queries into structured insights, visual reports,
              and actionable diagrams through advanced AI techniques.
            </motion.p>
            <motion.div 
              className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <Link href="/auth/login">
                <Button variant="outline" size="lg" className="text-base px-8 py-6">
                  Get Started
                </Button>
              </Link>
              <Link href="https://github.com/nexiouscaliver/Prism-DB" target="_blank" rel="noopener">
                <Button variant="outline" size="lg" className="text-base px-8 py-6">
                  View on GitHub
                </Button>
              </Link>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-black/70 relative">
        <div className="absolute inset-0 bg-grid-white/5 [mask-image:linear-gradient(to_bottom,transparent,black)]"></div>
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10 max-w-6xl">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-12">
            Powerful Features
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                className="bg-black/40 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:border-primary/50 transition-all duration-300"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="flex items-center space-x-2 mb-4">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
                </div>
                <p className="text-zinc-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Agent Architecture Section */}
      <section id="agents" className="py-20 bg-gradient-to-b from-black/70 to-purple-950/20 relative">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-12">
            Multi-Agent Architecture
          </h2>
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <h3 className="text-2xl font-semibold text-white mb-4">Collaborative AI Agents</h3>
              <p className="text-zinc-300 mb-6">
                Prism Framework leverages a sophisticated multi-agent system where specialized AI agents collaborate to 
                understand and process your natural language queries.
              </p>
              <ul className="space-y-3">
                {agents.map((agent, idx) => (
                  <li key={idx} className="flex items-start">
                    <div className="flex-shrink-0 h-6 w-6 rounded-full bg-primary/30 flex items-center justify-center mt-1 mr-3">
                      <span className="text-xs font-semibold text-primary">{idx+1}</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-white">{agent.name}</h4>
                      <p className="text-sm text-zinc-400">{agent.description}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </motion.div>
            <motion.div
              className="relative h-[450px] rounded-xl overflow-hidden border border-white/10"
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <AgentWorkflowDiagram />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section id="architecture" className="py-20 bg-black/80 relative">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-12">
            System Architecture
          </h2>
          <div className="bg-gradient-to-r from-purple-900/40 via-blue-900/40 to-indigo-900/40 p-8 rounded-xl backdrop-blur-sm border border-white/10">
            <div className="grid md:grid-cols-3 gap-6">
              {architecture.map((component, idx) => (
                <motion.div
                  key={idx}
                  className="p-4 rounded-lg bg-black/50 border border-white/5"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: idx * 0.1 }}
                  viewport={{ once: true }}
                >
                  <h4 className="text-lg font-semibold text-white mb-2">{component.name}</h4>
                  <p className="text-sm text-zinc-400">{component.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" className="py-20 bg-gradient-to-b from-purple-950/20 to-black relative">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6 text-center">
            Experience PrismDB In Action
          </h2>
          <p className="text-zinc-300 mb-12 max-w-3xl mx-auto text-center">
            See how our AI-powered agents transform natural language into powerful database insights, visualizations, and automated analysis.
          </p>

          <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
            {/* Left side: Interactive query demonstration */}
            <motion.div 
              className="bg-black/40 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <div className="p-5 border-b border-white/10 flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  </div>
                  <span className="text-sm text-zinc-400">PrismDB Query Interface</span>
                </div>
              </div>
              <div className="p-5 space-y-4">
                {/* Example queries */}
                <div>
                  <h4 className="text-sm text-zinc-400 mb-2">Example Queries:</h4>
                  <div className="space-y-2">
                    {demoQueries.map((item) => (
                      <div 
                        key={item.id} 
                        className={`text-sm p-2 rounded-lg cursor-pointer transition-colors border ${
                          selectedQuery === item.id 
                            ? "bg-primary/20 border-primary/50 text-white" 
                            : "bg-white/5 border-white/5 hover:bg-primary/10 hover:border-primary/40"
                        }`}
                        onClick={() => handleQuerySelect(item.id)}
                      >
                        {item.query}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Interactive query box */}
                <div className="relative mt-6">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input 
                    type="text" 
                    placeholder="Ask a question about your data..." 
                    className="block w-full pl-10 pr-12 py-3 border border-white/10 rounded-lg bg-black/30 text-white text-sm focus:ring-2 focus:ring-primary/50 focus:border-transparent focus:outline-none"
                    value={customQuery}
                    onChange={(e) => setCustomQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleCustomQuerySubmit();
                      }
                    }}
                  />
                  <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                    <button 
                      className="p-1 rounded-md bg-primary/20 hover:bg-primary/30 text-primary transition-colors"
                      onClick={handleCustomQuerySubmit}
                      disabled={executingQuery}
                    >
                      {executingQuery ? (
                        <svg className="animate-spin h-5 w-5 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Right side: Results visualization */}
            <motion.div 
              className="bg-black/40 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden"
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <div className="p-5 border-b border-white/10">
                <h3 className="text-white text-sm">Query Results & Visualizations</h3>
              </div>
              <div className="p-5 space-y-6">
                {/* Visualization result */}
                <div className="aspect-[4/3] rounded-lg bg-gradient-to-tr from-indigo-950/40 to-purple-900/40 border border-white/5 flex items-center justify-center p-6">
                  <div className="flex flex-col space-y-5 w-full">
                    {/* Conditional chart rendering based on data type */}
                    {currentQueryData.type === "bar" && currentValues ? (
                      <div className="w-full">
                        <ResponsiveContainer width="100%" height={200}>
                          <ScatterChart
                            margin={{
                              top: 10,
                              right: 30,
                              left: 0,
                              bottom: 30,
                            }}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="x" 
                              type="category" 
                              name="Category" 
                              allowDuplicatedCategory={false}
                              tick={{fill: '#9ca3af', fontSize: 10}}
                            />
                            <YAxis 
                              dataKey="y" 
                              name="Value" 
                              tick={{fill: '#9ca3af', fontSize: 10}}
                            />
                            <Tooltip 
                              cursor={{ strokeDasharray: '3 3' }} 
                              contentStyle={{
                                backgroundColor: '#111',
                                borderColor: 'rgba(255, 255, 255, 0.1)',
                                color: '#fff',
                                fontSize: '12px'
                              }}
                            />
                            <Scatter 
                              name="Values" 
                              data={currentLabels.map((label, i) => ({ x: label, y: currentValues[i] }))} 
                              fill="#8884d8" 
                              shape="circle"
                            />
                          </ScatterChart>
                        </ResponsiveContainer>
                        <div className="text-xs text-center text-zinc-500">{currentQueryData.title}</div>
                      </div>
                    ) : null}

                    {currentQueryData.type === "pie" && currentValues ? (
                      <div className="flex flex-col items-center justify-center h-full">
                        <div className="relative w-40 h-40 mb-4">
                          <svg viewBox="0 0 100 100" className="w-full h-full">
                            {currentValues.map((value, i, arr) => {
                              // Calculate the slice
                              const total = arr.reduce((a, b) => a + b, 0);
                              const startPercent = arr.slice(0, i).reduce((a, b) => a + b, 0) / total;
                              const endPercent = startPercent + value / total;
                              
                              const startX = 50 + 40 * Math.cos(2 * Math.PI * startPercent);
                              const startY = 50 + 40 * Math.sin(2 * Math.PI * startPercent);
                              const endX = 50 + 40 * Math.cos(2 * Math.PI * endPercent);
                              const endY = 50 + 40 * Math.sin(2 * Math.PI * endPercent);
                              
                              // Large arc flag is 1 if slice is > 50%
                              const largeArcFlag = endPercent - startPercent > 0.5 ? 1 : 0;
                              
                              // Colors for pie slices
                              const colors = [
                                "rgb(124, 58, 237)", // purple-600
                                "rgb(79, 70, 229)",  // indigo-600
                                "rgb(37, 99, 235)",  // blue-600
                                "rgb(16, 185, 129)", // emerald-600
                                "rgb(245, 158, 11)", // amber-600
                                "rgb(239, 68, 68)"   // red-600
                              ];
                              
                              // SVG path for the slice
                              return (
                                <path
                                  key={i}
                                  d={`M 50 50 L ${startX} ${startY} A 40 40 0 ${largeArcFlag} 1 ${endX} ${endY} Z`}
                                  fill={colors[i % colors.length]}
                                  stroke="#000"
                                  strokeWidth="0.5"
                                  opacity={0.8 + (i * 0.03)}
                                />
                              );
                            })}
                          </svg>
                        </div>
                        
                        {/* Legend */}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                          {currentLabels.map((label, i) => (
                            <div key={i} className="flex items-center text-xs space-x-1">
                              <div className={`w-2 h-2 rounded-full`} style={{
                                backgroundColor: ["rgb(124, 58, 237)", "rgb(79, 70, 229)", "rgb(37, 99, 235)", 
                                "rgb(16, 185, 129)", "rgb(245, 158, 11)", "rgb(239, 68, 68)"][i % 6]
                              }}></div>
                              <span className="text-zinc-400">
                                {label} {currentValues && `(${currentValues[i]}${currentQueryData.unit || ''})`}
                              </span>
                            </div>
                          ))}
                        </div>
                        
                        <div className="text-xs text-center text-zinc-500 mt-2">{currentQueryData.title}</div>
                      </div>
                    ) : null}

                    {currentQueryData.type === "table" && currentRows ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left text-zinc-400">
                          <thead className="text-xs text-zinc-300 border-b border-white/10">
                            <tr>
                              {currentLabels.map((label, i) => (
                                <th key={i} className="px-2 py-2">{label}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {currentRows.map((row, i) => (
                              <tr key={i} className="border-b border-white/5">
                                {row.map((cell, j) => (
                                  <td key={j} className="px-2 py-2">{cell}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <div className="text-xs text-center text-zinc-500 mt-4">{currentQueryData.title}</div>
                      </div>
                    ) : null}
                  </div>
                </div>

                {/* AI explanation */}
                <div className="p-4 bg-black/30 rounded-lg border border-white/5">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/30 flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white mb-1">AI Analysis</h4>
                      <p className="text-xs text-zinc-400 leading-relaxed">
                        {currentQueryData.insight}
                        <span className="block mt-1 text-primary">{currentQueryData.recommendation}</span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* SQL query info */}
                <div className="mt-4 pt-4 border-t border-white/5">
                  <div className="flex justify-between text-xs text-zinc-500">
                    <span>Generated SQL:</span>
                    <button 
                      className="text-primary hover:text-primary/80 transition-colors"
                      onClick={() => alert(`SQL Query:\n\n${currentQueryData.sqlQuery}`)}
                    >
                      View
                    </button>
                  </div>
                  <div className="flex justify-between text-xs text-zinc-500 mt-2">
                    <span>Execution time:</span>
                    <span>{currentQueryData.executionTime}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Try it yourself CTA */}
          <div className="mt-12 text-center">
            <Link href="/auth/register">
              <Button variant="outline" size="lg" className="bg-primary/10 hover:bg-primary/20 text-white border-primary/30">
                Try It Yourself
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <div className="rounded-2xl bg-gradient-to-r from-purple-900/40 via-blue-900/40 to-indigo-900/40 p-10 backdrop-blur-sm border border-white/10">
            <div className="text-center">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                Ready to Transform Your Data Experience?
              </h2>
              <p className="text-lg text-zinc-300 max-w-3xl mx-auto mb-10">
                Get started with Prism Framework today and see how our multi-agent system can unlock the full potential of your databases.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/auth/register">
                  <Button variant="outline" size="lg" className="px-8 py-6 text-base">
                    Sign Up Now
                  </Button>
                </Link>
                <Link href="/auth/login">
                  <Button variant="outline" size="lg" className="px-8 py-6 text-base">
                    Log In
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/10 bg-black/80">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-6 w-6 text-primary"
                >
                  <path d="M12 3v19" />
                  <path d="M5 8h14" />
                  <path d="M4 5v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2Z" />
                </svg>
                <span className="text-xl font-bold bg-gradient-to-r from-violet-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  PrismDB
                </span>
              </div>
              <p className="text-sm text-zinc-400">
                A multi-agent framework for transforming natural language into database insights.
              </p>
            </div>
            
            <div>
              <h4 className="text-white font-medium mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="text-zinc-400 hover:text-white transition-colors">Features</a></li>
                <li><a href="#agents" className="text-zinc-400 hover:text-white transition-colors">Agents</a></li>
                <li><a href="#architecture" className="text-zinc-400 hover:text-white transition-colors">Architecture</a></li>
                <li><a href="#demo" className="text-zinc-400 hover:text-white transition-colors">Demo</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-medium mb-4">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="text-zinc-400 hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white transition-colors">API Reference</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white transition-colors">GitHub</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-medium mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="text-zinc-400 hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-zinc-500">
              &copy; {new Date().getFullYear()} PrismDB. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a href="#" className="text-zinc-400 hover:text-white transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="text-zinc-400 hover:text-white transition-colors">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Data for features section
const features = [
  {
    title: "Natural Language Interface",
    description: "Transform plain English into SQL queries without writing a single line of code. Our advanced NLP engine understands complex queries and context.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-primary"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
        />
      </svg>
    ),
  },
  {
    title: "Multi-Database Support",
    description: "Connect to PostgreSQL, MySQL, MongoDB, and other databases with a unified interface. Query across different data sources seamlessly.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-primary"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125"
        />
      </svg>
    ),
  },
  {
    title: "Visualization Engine",
    description: "Automatically generates charts, graphs, and visualizations from query results with intelligent formatting based on data types and relationships.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-primary"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
        />
      </svg>
    ),
  },
  {
    title: "Context-Aware Agents",
    description: "Our specialized AI agents understand database schemas, user behavior, and domain semantics to deliver highly relevant results and insights.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-primary"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z"
        />
      </svg>
    ),
  },
  {
    title: "Real-time Analysis",
    description: "Get immediate insights from your data with real-time query processing and analysis. Perfect for dashboards and live monitoring.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-primary"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    title: "Enterprise Security",
    description: "Bank-grade security with role-based access control, audit logs, and encryption at rest and in transit to protect your sensitive data.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-primary"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
        />
      </svg>
    ),
  },
];

// Data for agent architecture section
const agents = [
  {
    name: "Query Understanding Agent",
    description: "Parses natural language queries, identifies intent, and extracts key data points for processing."
  },
  {
    name: "Schema Analysis Agent",
    description: "Maps query requirements to database schema and identifies relevant tables and relationships."
  },
  {
    name: "SQL Generation Agent",
    description: "Creates optimized SQL queries based on the identified schema and user intent."
  },
  {
    name: "Visualization Agent",
    description: "Selects and generates the most appropriate visualizations based on query results and data patterns."
  },
  {
    name: "Explanation Agent",
    description: "Provides human-readable explanations of complex query results and insights."
  }
];

// Data for architecture section
const architecture = [
  {
    name: "Frontend Layer",
    description: "Modern, responsive UI built with Next.js and React for a seamless user experience."
  },
  {
    name: "API Gateway",
    description: "Secure entry point handling authentication, request routing, and rate limiting."
  },
  {
    name: "Agent Orchestration Engine",
    description: "Coordinates the multi-agent workflow and manages communication between agents."
  },
  {
    name: "Natural Language Processing",
    description: "Advanced NLP models that understand context, domain-specific terminology, and query intent."
  },
  {
    name: "Database Connectors",
    description: "Secure connectors for various database systems with connection pooling and query optimization."
  },
  {
    name: "Query Execution Engine",
    description: "High-performance execution layer with caching and optimization for fast results."
  },
  {
    name: "Visualization Service",
    description: "Generates interactive charts, graphs, and dashboards from query results."
  },
  {
    name: "Security Layer",
    description: "End-to-end encryption, role-based access control, and comprehensive audit logging."
  },
  {
    name: "Analytics & Monitoring",
    description: "Performance monitoring, usage analytics, and system health dashboards."
  }
];

// Mock data for demonstration
const demoQueries: DemoQuery[] = [
  {
    id: 1,
    query: "Show me sales by region for last quarter",
    data: {
      type: "bar",
      labels: ["North", "South", "East", "West", "Central"],
      values: [45, 52, 38, 59, 47],
      title: "Sales by Region (Last Quarter)",
      unit: "K",
      dataType: "currency",
      sqlQuery: "SELECT region, SUM(sales) AS total_sales FROM sales WHERE quarter = 'Q4' GROUP BY region ORDER BY region",
      executionTime: "0.45s",
      insight: "The Western region shows the highest sales performance at $59K, while the Eastern region is underperforming at $38K compared to other regions.",
      recommendation: "Consider investigating the sales strategy in the Eastern region to identify improvement opportunities."
    }
  },
  {
    id: 2,
    query: "Find customers who haven't ordered in 6 months",
    data: {
      type: "table",
      labels: ["Customer", "Last Order", "Total Orders", "Lifetime Value"],
      rows: [
        ["Acme Corp", "May 10, 2023", "32", "$28,450"],
        ["XYZ Industries", "Apr 22, 2023", "17", "$15,720"],
        ["Global Solutions", "Apr 15, 2023", "23", "$34,125"],
        ["Tech Innovations", "Mar 30, 2023", "8", "$12,340"],
        ["Quantum Enterprises", "Mar 28, 2023", "15", "$20,150"]
      ],
      title: "Inactive Customers (6+ Months)",
      sqlQuery: "SELECT c.name, MAX(o.order_date) as last_order, COUNT(o.id) as total_orders, SUM(o.total) as lifetime_value FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id HAVING MAX(o.order_date) < DATE_SUB(NOW(), INTERVAL 6 MONTH) ORDER BY last_order DESC LIMIT 5",
      executionTime: "207ms",
      insight: "5 high-value customers haven't placed orders in over 6 months. Acme Corp, with 32 previous orders and a lifetime value of $28,450, has been inactive since May 10, 2023.",
      recommendation: "Initiate a targeted re-engagement campaign for these 5 customers with personalized offers based on their purchase history."
    }
  },
  {
    id: 3,
    query: "Create a visualization of website traffic by source",
    data: {
      type: "pie",
      labels: ["Organic Search", "Direct", "Social Media", "Referral", "Email", "Paid Search"],
      values: [38, 22, 15, 12, 8, 5],
      title: "Website Traffic by Source",
      unit: "%",
      dataType: "percentage",
      sqlQuery: "SELECT source, COUNT(*) as visits, (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM visits WHERE visit_date >= DATE_SUB(NOW(), INTERVAL 30 DAY))) as percentage FROM visits WHERE visit_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY source ORDER BY visits DESC",
      executionTime: "156ms",
      insight: "Organic search drives 38% of your website traffic, followed by direct visits at 22%. Social media contributes 15%, but paid search only accounts for 5% of total traffic.",
      recommendation: "Consider reallocating some of your paid search budget to social media campaigns which show better engagement and conversion rates."
    }
  },
  {
    id: 4,
    query: "Which products have the highest profit margin?",
    data: {
      type: "bar",
      labels: ["Premium Software", "Enterprise Security", "Cloud Storage", "Analytics Dashboard", "Developer API"],
      values: [72, 68, 55, 48, 43],
      title: "Top 5 Products by Profit Margin",
      unit: "%",
      dataType: "percentage",
      sqlQuery: "SELECT p.name, ((p.price - p.cost) / p.price * 100) as margin FROM products p ORDER BY margin DESC LIMIT 5",
      executionTime: "98ms",
      insight: "Premium Software has the highest profit margin at 72%, followed by Enterprise Security at 68%. All top 5 products have margins above 40%.",
      recommendation: "Focus sales efforts on Premium Software and Enterprise Security to maximize profitability. Consider bundle offers that include these high-margin products."
    }
  },
  {
    id: 5,
    query: "Compare performance across all stores",
    data: {
      type: "bar",
      labels: ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"],
      values: [87, 65, 92, 78, 63, 71],
      title: "Store Performance Index",
      unit: "",
      dataType: "score",
      sqlQuery: "SELECT store_name, (sales_score * 0.4 + customer_satisfaction * 0.3 + efficiency * 0.3) as performance_score FROM store_metrics ORDER BY performance_score DESC",
      executionTime: "183ms",
      insight: "Chicago has the highest performance score at 92, followed by New York at 87. Phoenix is underperforming with a score of 63, primarily due to lower customer satisfaction ratings.",
      recommendation: "Implement the successful customer service practices from the Chicago store in Phoenix to improve its performance metrics."
    }
  }
];
