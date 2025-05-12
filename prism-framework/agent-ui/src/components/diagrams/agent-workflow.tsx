'use client';

import React from 'react';
import { MermaidDiagram } from '../ui/mermaid-diagram';

export function AgentWorkflowDiagram() {
  // Mermaid diagram definition for PrismDB agent workflow
  const diagram = `
  flowchart TD
    classDef userInteraction fill:#7c3aed,stroke:#7c3aed,color:white,stroke-width:1px
    classDef agentNode fill:#2563eb,stroke:#2563eb,color:white,stroke-width:1px
    classDef dataNode fill:#475569,stroke:#475569,color:white,stroke-width:1px
    classDef resultNode fill:#10b981,stroke:#10b981,color:white,stroke-width:1px

    User[User Query] --> |"Natural Language Input"| QUA
    subgraph Agents
      QUA[Query Understanding Agent] --> |"Extracts Intent"| SAA
      SAA[Schema Analysis Agent] --> |"Maps Schema"| SQA
      SQA[SQL Generation Agent] --> |"Optimized SQL"| QEE
      QEE[Query Execution Engine] --> |"Query Results"| VA
      VA[Visualization Agent] --> |"Charts & Graphs"| EA
      EA[Explanation Agent] --> |"Human-Readable Insights"| Results
    end
    
    subgraph Databases
      DB1[(PostgreSQL)]
      DB2[(MySQL)]
      DB3[(MongoDB)]
      DB4[(Other DBs...)]
    end
    
    QEE --> |"Executes Queries"| DB1
    QEE --> |"Executes Queries"| DB2
    QEE --> |"Executes Queries"| DB3
    QEE --> |"Executes Queries"| DB4
    
    Results[Results & Insights] --> |"Returned to"| User
    
    class User,Results userInteraction
    class QUA,SAA,SQA,VA,EA,QEE agentNode
    class DB1,DB2,DB3,DB4 dataNode
    class Results resultNode
  `;

  return (
    <MermaidDiagram 
      chart={diagram} 
      className="w-full h-full bg-black/30 backdrop-blur-sm border border-white/10"
      config={{
        theme: 'dark',
        fontFamily: 'system-ui, sans-serif',
        themeVariables: {
          nodeBorder: '#1e293b',
          mainBkg: '#0f172a',
          nodeTextColor: '#ffffff',
          textColor: '#e2e8f0',
          lineColor: '#64748b',
          fontSize: '14px',
        }
      }}
    />
  );
}

// Export as default for dynamic import
export default AgentWorkflowDiagram; 