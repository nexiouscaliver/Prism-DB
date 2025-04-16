'use client';

import { animate as framerAnimate } from "framer-motion";
import { useEffect, useRef } from "react";

export default function AnimatedContent() {
  const contentRef = useRef(null);

  useEffect(() => {
    if (contentRef.current) {
      framerAnimate(contentRef.current, { 
        y: [50, 0], 
        opacity: [0, 1] 
      }, { 
        duration: 0.8,
        ease: 'easeOut' 
      });
    }
  }, []);

  return (
    <div ref={contentRef} className="container mx-auto mt-16 px-4 text-white max-w-3xl">
      <h1 className="text-5xl font-bold mb-2 text-center">PrismDB</h1>
      <h2 className="text-3xl font-semibold mb-4">Transform Natural Language</h2>
      <p className="text-lg">
        PrismDB is a multi-agent framework that acts as a contextual prism for databases, 
        transforming raw natural language queries into structured insights, visual reports, 
        and actionable diagrams.
      </p>
    </div>
  );
}
