'use client';

import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
  config?: any;
  className?: string;
}

export function MermaidDiagram({ chart, config, className = '' }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const init = async () => {
      try {
        // Configure mermaid
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose', // Required for interactive features
          ...config,
        });

        // Render the diagram
        const { svg: renderedSvg } = await mermaid.render('diagram', chart);
        setSvg(renderedSvg);
        setError(null);
      } catch (err) {
        console.error('Error rendering mermaid diagram:', err);
        setError('Failed to render diagram');
      }
    };

    init();
  }, [chart, config]);

  // Handle zooming with mouse wheel
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY * -0.01;
    const newZoom = Math.min(Math.max(zoom + delta, 0.5), 3); // Limit zoom between 0.5x and 3x
    setZoom(newZoom);
  };

  // Handle dragging to pan the diagram
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Reset zoom and position
  const handleReset = () => {
    setZoom(1);
    setPosition({ x: 0, y: 0 });
  };

  useEffect(() => {
    // Cleanup event listeners
    const currentRef = containerRef.current;
    
    return () => {
      if (currentRef) {
        currentRef.removeEventListener('mouseup', handleMouseUp as any);
        currentRef.removeEventListener('mouseleave', handleMouseUp as any);
      }
    };
  }, []);

  return (
    <div className={`relative overflow-hidden rounded-lg ${className}`} ref={containerRef}>
      {/* Zoom controls */}
      <div className="absolute top-3 right-3 flex gap-2 z-20">
        <button 
          onClick={() => setZoom(Math.min(zoom + 0.1, 3))}
          className="bg-black/40 hover:bg-black/60 text-white p-2 rounded"
          aria-label="Zoom in"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="11" y1="8" x2="11" y2="14"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
          </svg>
        </button>
        <button 
          onClick={() => setZoom(Math.max(zoom - 0.1, 0.5))}
          className="bg-black/40 hover:bg-black/60 text-white p-2 rounded"
          aria-label="Zoom out"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
          </svg>
        </button>
        <button 
          onClick={handleReset}
          className="bg-black/40 hover:bg-black/60 text-white p-2 rounded"
          aria-label="Reset view"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 2v6h6"></path>
            <path d="M21 12A9 9 0 0 0 6 5.3L3 8"></path>
            <path d="M21 22v-6h-6"></path>
            <path d="M3 12a9 9 0 0 0 15 6.7l3-2.7"></path>
          </svg>
        </button>
      </div>

      {/* Instructions prompt */}
      <div className="absolute bottom-3 left-3 z-20 text-xs text-white/70 bg-black/40 p-2 rounded">
        <p>Use mouse wheel to zoom, drag to pan</p>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-600/20 text-red-400 rounded-lg">
          <p>{error}</p>
        </div>
      )}

      {/* Diagram container */}
      <div
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ 
          transform: `scale(${zoom}) translate(${position.x}px, ${position.y}px)`,
          transformOrigin: 'center',
          cursor: isDragging ? 'grabbing' : 'grab',
          transition: isDragging ? 'none' : 'transform 0.1s ease-out'
        }}
        className="min-h-[300px] flex items-center justify-center"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
} 