'use client'

import React from "react";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from "framer-motion";
import Link from "next/link";
import { useAuthStore } from '@/store/auth-store';
import dynamic from 'next/dynamic';

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

export default function Home() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  
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
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            See Prism Framework In Action
          </h2>
          <p className="text-zinc-300 mb-12 max-w-3xl mx-auto">
            Watch how our AI-powered agents transform natural language into powerful database insights, visualizations, and automated analysis.
          </p>
          <div className="mx-auto max-w-4xl aspect-video rounded-xl overflow-hidden border border-white/10">
            <div className="h-full w-full bg-black/70 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">▶️</div>
                <p className="text-white/70">Demo video coming soon</p>
              </div>
            </div>
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
