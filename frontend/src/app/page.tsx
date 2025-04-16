"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar";
import { HoverEffect } from "@/components/ui/card-hover-effect";
// import { GradientBackground } from "@/components/ui/gradient-background";
// import { InfiniteMovingCards } from "@/components/ui/infinite-moving-cards";
// import { Button } from "@/components/ui/button";
// import { CardSpotlight } from "@/components/ui/card-spotlight";

export default function Home() {
  return (    
  <div className="header-container">
      <img src="logo.2.jpg" alt="Overlay image" className="nav-overlay-image" />
      <div className="fixed top-0 left-0 right-0 z-10 w-full">
        <Navbar />
      </div>
      
      {/* Section 1: Hero */}
      <section id="home" className="min-h-screen flex items-center">
        <motion.div 
          className="container mx-auto mt-16 px-6 text-white max-w-5xl"
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >          <h1 className="text-5xl font-bold mb-2 text-center">PrismDB</h1>
          <h2 className="text-3xl font-semibold mb-4 text-center">Transform Natural Language</h2>
          <p className="text-lg">
            PrismDB is a multi-agent framework that acts as a contextual prism for databases, 
            transforming raw natural language queries into structured insights, visual reports, 
            and actionable diagrams.
          </p>
        </motion.div>
      </section>

      {/* Section 2: Features */}
      <section id="features" className="py-20 bg-gray-900 text-white">
        <div className="max-w-5xl mx-auto px-8">
          <h2 className="text-3xl font-semibold mb-8 text-center">Features</h2>
          <HoverEffect items={projects.slice(0, 3)} />
        </div>
      </section>

      {/* Section 3: Why Us */}
      <section id="why-us" className="py-20 bg-black text-white">
        <div className="max-w-5xl mx-auto px-8">
          <h2 className="text-3xl font-semibold mb-8 text-center">Why Choose PrismDB</h2>
          <div className="grid md:grid-cols-2 gap-10">
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3">Powerful Insights</h3>
              <p>Extract meaningful insights from your data with our advanced contextual understanding engines that go beyond simple keyword matching.</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3">Enterprise Ready</h3>
              <p>Built for scale with enterprise-grade security and performance that can handle your most demanding database workloads.</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3">Intuitive Interface</h3>
              <p>Natural language interface means your entire team can work with complex data without specialized SQL knowledge.</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-3">Multi-Agent Collaboration</h3>
              <p>Our agents work together to provide comprehensive answers by combining database knowledge with contextual understanding.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 4: Demo Section */}
      <section id="demo" className="py-20 bg-gradient-to-b from-purple-900 to-black text-white">
        <div className="max-w-5xl mx-auto px-8 text-center">
          <h2 className="text-3xl font-semibold mb-8">See PrismDB In Action</h2>
          <p className="text-lg mb-8">Watch how PrismDB transforms natural language into powerful database insights.</p>
          <div className="bg-black/50 p-8 rounded-lg mx-auto max-w-3xl aspect-video flex items-center justify-center">
            <p className="text-xl">Demo Video Player Would Go Here</p>
          </div>
        </div>
      </section>

      {/* Section 5: Get Started */}
      <section id="auth" className="py-20 bg-gray-900 text-white">
        <div className="max-w-5xl mx-auto px-8 text-center">
          <h2 className="text-3xl font-semibold mb-8">Ready to Get Started?</h2>
          <p className="text-lg mb-8">Transform how you interact with your databases today.</p>
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-3 rounded-md text-lg font-medium transition-colors">
            Sign Up Now
          </button>
        </div>
      </section>
    </div>
  );
}

export const projects = [
  {
    title: "Natural Language Interface",
    description:
      "Transform plain English into SQL queries without writing a single line of code",
    link: "https://stripe.com",
  },
  {
    title: "Multi-Database Support",
    description:
      "Connect to PostgreSQL, MySQL, and other SQL databases with a unified interface.",
    link: "https://netflix.com",
  },
  {
    title: "Visualization Engine",
    description:
      "Automatically generates charts and visualizations from query results with no extra work.",
    link: "https://google.com",
  },
  {
    title: "Context-Aware Agents",
    description:
      "Leverage multiple agents to provide context-aware responses and insights.",
    link: "https://meta.com",
  },
  {
    title: "Advanced Analytics",
    description:
      "Powerful analytics capabilities to extract meaningful insights from your data.",
    link: "https://amazon.com",
  },
  {
    title: "Enterprise Security",
    description:
      "Enterprise-grade security features to protect your sensitive data.",
    link: "https://microsoft.com",
  },
];

  /* <main className="min-h-screen overflow--hidden">
    
      
      {/* Hero Section }
      <section className="relative overflow-hidden pb-20 pt-24">
        <GradientBackground />
        <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-6 text-4xl font-bold tracking-tight text-white sm:text-5xl md:text-6xl">
              <span className="block">Transform Natural Language</span>
              <span className="block bg-gradient-to-r from-purple-400 via-pink-500 to-indigo-400 bg-clip-text text-transparent">
                Into Data Insights
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-zinc-300">
              PrismDB is a multi-agent framework that acts as a contextual prism for 
              databases, transforming raw natural language queries into structured insights, 
              visual reports, and actionable diagrams.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link href="/login">
                <Button className="text-lg">
                  Get Started
                </Button>
              </Link>
              <Link href="https://github.com/your-org/prismdb" target="_blank" rel="noopener">
                <Button className="border-white/20 bg-white/5 backdrop-blur-sm">
                  View on GitHub
                </Button>
              </Link>
            </div>
          </div>
        </div> */
        
        
      
      {/* Features Section }
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="mb-6 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Powerful Features
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-zinc-400">
              PrismDB offers a suite of features to make database interactions simpler, faster, and more powerful.
            </p>
          </div>
        
          
          <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <CardSpotlight key={index} containerClassName="h-full">
                <div className="flex h-full flex-col p-2">
                  <div className="mb-5 rounded-full bg-indigo-900/30 p-2 w-fit">
                    {feature.icon}
                  </div>
                  <h3 className="mb-2 text-xl font-bold text-white">{feature.title}</h3>
                  <p className="flex-1 text-sm text-zinc-400">{feature.description}</p>
                </div>
              </CardSpotlight>
            ))}
          </div>
        </div>
      </section>
      
      {/* Testimonials }
      <section className="py-20 bg-black/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="mb-6 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              What Our Users Say
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-zinc-400">
              Organizations around the world are using PrismDB to transform their data workflows.
            </p>
          </div>
          
          <div className="mt-16">
            <InfiniteMovingCards items={testimonials} direction="right" speed="slow" />
          </div>
        </div>
      </section>
      
      {/* CTA Section }
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl bg-gradient-to-r from-purple-900/40 via-blue-900/40 to-indigo-900/40 p-10 backdrop-blur-sm border border-white/10">
            <div className="text-center">
              <h2 className="mb-6 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Ready to Transform Your Data Experience?
              </h2>
              <p className="mx-auto max-w-2xl text-lg text-zinc-300">
                Get started with PrismDB today and see how natural language can unlock the power of your databases.
              </p>
              
              <div className="mt-10 flex items-center justify-center gap-x-6">
                <Link href="/login">
                  <Button>
                    Get Started
                  </Button>
                </Link>
                <Link href="/dashboard">
                  <Button className="border-white/20 bg-white/5 backdrop-blur-sm">
                    View Demo
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Footer }
      <footer className="border-t border-white/10 bg-black/80 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex items-center space-x-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                // viewBox="0 0 24 24"
                height="1200px"
                width="1200px"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-6 w-6 text-purple-500"
              >
                <path d="M12 3v19" />
                <path d="M5 8h14" />
                <path d="M15 5V2" />
                <path d="M9 5V2" />
                <path d="M15 22v-3" />
                <path d="M9 22v-3" />
                <path d="M4 5v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2Z" />
              </svg>
              <span className="text-xl font-bold bg-gradient-to-r from-violet-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
                PrismDB
              </span>
            </div>
            
            <div className="mt-8 md:mt-0">
              <p className="text-sm text-zinc-400">
                &copy; {new Date().getFullYear()} PrismDB. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </main>
</>
  );
}


{/* // Made by shahil:

const testimonials = [
  {
    quote: "PrismDB transformed how we analyze our customer data. The natural language interface saves us hours of writing SQL queries.",
    name: "Sarah Johnson",
    title: "Data Analyst at TechCorp",
  },
  {
    quote: "Our team loves using PrismDB for quick data insights. The visualization engine produces beautiful charts without any manual work.",
    name: "Michael Chen",
    title: "VP of Engineering at DataFlow",
  },
  {
    quote: "The multi-database support is a game-changer. We can query across all our data sources with a single natural language prompt.",
    name: "Jessica Martinez",
    title: "CTO at Analytics Inc",
  },
  {
    quote: "Setting up PrismDB was incredibly easy. Within an hour, our team was generating complex reports that used to take days.",
    name: "David Wilson",
    title: "Lead Data Scientist at Quantum Systems",
  },
  {
    quote: "The agent system in PrismDB is remarkably intelligent. It understands context and produces accurate SQL queries even for complex business questions.",
    name: "Emily Zhang",
    title: "Business Intelligence Manager at Global Retail",
  },
];

const features = [
  {
    title: "Natural Language Interface",
    description: "Transform plain English into SQL queries without writing a single line of code.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        // height="20 px"
        // width="20 px"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-indigo-400"
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
    description: "Connect to PostgreSQL, MySQL, and other SQL databases with a unified interface.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-indigo-400"
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
    description: "Automatically generates charts and visualizations from query results with no extra work.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-indigo-400"
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
    description: "AI agents that understand schemas, user behavior, and domain semantics for better results.",
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        className="h-6 w-6 text-indigo-400"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
        />
      </svg>
    ),
  },
];

All this was before return()

{/* Floating Mockup }
<div className="relative mx-auto mt-20 max-w-5xl">
<div className="overflow-hidden rounded-xl border border-white/10 bg-black/30 shadow-2xl backdrop-blur-sm">
  <div className="border-b border-white/10 px-6 py-3">
    <div className="flex items-center space-x-2">
      <div className="h-3 w-3 rounded-full bg-red-500"></div>
      <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
      <div className="h-3 w-3 rounded-full bg-green-500"></div>
      <div className="ml-4 text-sm text-gray-400">Query Editor - PrismDB</div>
    </div>
  </div>
  <div className="p-6">
    <div className="mb-4 rounded-lg bg-zinc-800/70 p-4">
      <div className="text-sm text-gray-300">
        {">"} Show me the top 5 customers by total spend in the last quarter.
      </div>
    </div>
    <div className="mb-4 rounded-lg bg-zinc-900/70 p-4">
      <div className="text-xs text-purple-400">GENERATED SQL</div>
      <div className="mt-2 font-mono text-xs text-gray-300">
        {`SELECT
c.customer_id, 
c.first_name,
c.last_name,
c.email,
SUM(p.amount) AS total_spend
FROM customers c
JOIN payments p ON c.customer_id = p.customer_id
WHERE p.payment_date > CURRENT_DATE - INTERVAL '3 month'
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY total_spend DESC
LIMIT 5;`}
      </div>
    </div>
    <div className="rounded-lg bg-zinc-800/70 p-4">
      <div className="text-xs text-indigo-400">RESULT</div>
      <div className="mt-2 overflow-x-auto">
        <table className="min-w-full divide-y divide-white/10">
          <thead>
            <tr>
              <th className="py-2 text-left text-xs font-medium text-gray-400">ID</th>
              <th className="py-2 text-left text-xs font-medium text-gray-400">First Name</th>
              <th className="py-2 text-left text-xs font-medium text-gray-400">Last Name</th>
              <th className="py-2 text-left text-xs font-medium text-gray-400">Email</th>
              <th className="py-2 text-left text-xs font-medium text-gray-400">Total Spend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            <tr>
              <td className="py-2 text-xs text-gray-300">148</td>
              <td className="py-2 text-xs text-gray-300">Eleanor</td>
              <td className="py-2 text-xs text-gray-300">Hunt</td>
              <td className="py-2 text-xs text-gray-300">eleanor.hunt@example.com</td>
              <td className="py-2 text-xs text-gray-300">$211.55</td>
            </tr>
            <tr>
              <td className="py-2 text-xs text-gray-300">526</td>
              <td className="py-2 text-xs text-gray-300">Karl</td>
              <td className="py-2 text-xs text-gray-300">Seal</td>
              <td className="py-2 text-xs text-gray-300">karl.seal@example.com</td>
              <td className="py-2 text-xs text-gray-300">$208.58</td>
            </tr>
            <tr>
              <td className="py-2 text-xs text-gray-300">178</td>
              <td className="py-2 text-xs text-gray-300">Marion</td>
              <td className="py-2 text-xs text-gray-300">Snyder</td>
              <td className="py-2 text-xs text-gray-300">marion.snyder@example.com</td>
              <td className="py-2 text-xs text-gray-300">$194.61</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
</div>
</section>

{/* Features Section }
<section className="py-20">
<div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
  <div className="text-center">
    <h2 className="mb-6 text-3xl font-bold tracking-tight text-white sm:text-4xl">
      Powerful Features
    </h2>
    <p className="mx-auto max-w-2xl text-lg text-zinc-400">
      PrismDB offers a suite of features to make database interactions simpler, faster, and more powerful.
    </p>
  </div>

  
  <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
    {features.map((feature, index) => (
      <CardSpotlight key={index} containerClassName="h-full">
        <div className="flex h-full flex-col p-2">
          <div className="mb-5 rounded-full bg-indigo-900/30 p-2 w-fit">
            {feature.icon}
          </div>
          <h3 className="mb-2 text-xl font-bold text-white">{feature.title}</h3>
          <p className="flex-1 text-sm text-zinc-400">{feature.description}</p>
        </div>
      </CardSpotlight>
    ))}
  </div>
</div>
</section>

{/* Testimonials }
<section className="py-20 bg-black/50">
<div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
  <div className="text-center">
    <h2 className="mb-6 text-3xl font-bold tracking-tight text-white sm:text-4xl">
      What Our Users Say
    </h2>
    <p className="mx-auto max-w-2xl text-lg text-zinc-400">
      Organizations around the world are using PrismDB to transform their data workflows.
    </p>
  </div>
  
  <div className="mt-16">
    <InfiniteMovingCards items={testimonials} direction="right" speed="slow" />
  </div>
</div>
</section> */}