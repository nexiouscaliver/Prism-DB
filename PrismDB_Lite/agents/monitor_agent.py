import logging
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from queue import Queue
from threading import Lock

from .base import BaseAgent

logger = logging.getLogger("prismdb.agent.monitor")

class MonitorAgent(BaseAgent):
    """
    Monitor Agent tracks the thought processes of other agents and provides
    real-time streaming of agent activities and state.
    """
    
    def __init__(self, name="monitor_agent", config=None):
        """
        Initialize the monitor agent.
        
        Args:
            name (str): Name of the agent
            config (dict, optional): Configuration for the agent
        """
        super().__init__(name, config)
        self.events = []
        self.event_queue = Queue()
        self.listeners = []
        self.lock = Lock()
        self.max_events = config.get("max_events", 1000) if config else 1000
    
    async def process(self, message, context=None):
        """
        Process a message and track agent activity.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: Current monitoring state
        """
        context = context or {}
        
        # Check if this is a command message
        command = message.get("command", "")
        
        if command == "clear":
            # Clear all events
            with self.lock:
                self.events = []
            self.log_thought("Cleared event history")
            return {"status": "success", "message": "Event history cleared"}
        
        elif command == "get_events":
            # Return all events or a specified range
            start = message.get("start", 0)
            limit = message.get("limit", 100)
            
            with self.lock:
                requested_events = self.events[start:start+limit]
            
            return {
                "status": "success",
                "events": requested_events,
                "total": len(self.events),
                "start": start,
                "limit": limit
            }
        
        elif command == "get_agent_events":
            # Get events for a specific agent
            agent_name = message.get("agent_name", "")
            if not agent_name:
                return {"status": "error", "message": "No agent name provided"}
            
            with self.lock:
                agent_events = [e for e in self.events if e.get("agent") == agent_name]
            
            return {
                "status": "success",
                "agent": agent_name,
                "events": agent_events,
                "count": len(agent_events)
            }
        
        elif command == "register_listener":
            # Register a callback function to be notified of new events
            callback = message.get("callback")
            if callback and callable(callback):
                self.listeners.append(callback)
                self.log_thought(f"Registered new event listener (total: {len(self.listeners)})")
                return {"status": "success", "message": "Listener registered"}
            else:
                return {"status": "error", "message": "Invalid callback function"}
        
        elif command == "unregister_listener":
            # Unregister a callback function
            callback = message.get("callback")
            if callback and callback in self.listeners:
                self.listeners.remove(callback)
                self.log_thought(f"Unregistered event listener (remaining: {len(self.listeners)})")
                return {"status": "success", "message": "Listener unregistered"}
            else:
                return {"status": "error", "message": "Listener not found"}
        
        # If no command, record an event
        event_type = message.get("type", "info")
        agent = message.get("agent", "unknown")
        message_content = message.get("message", "")
        
        self.record_event(event_type, agent, message_content, context)
        
        return {"status": "success", "message": "Event recorded"}
    
    def record_event(self, event_type: str, agent: str, message: str, metadata: Dict[str, Any] = None):
        """
        Record a new event.
        
        Args:
            event_type (str): Type of event (info, thought, error, etc.)
            agent (str): Name of the agent
            message (str): Event message
            metadata (dict, optional): Additional metadata
        """
        event = {
            "timestamp": time.time(),
            "formatted_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "agent": agent,
            "message": message,
            "metadata": metadata or {}
        }
        
        with self.lock:
            self.events.append(event)
            
            # Trim events if we exceed the maximum
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
        
        # Add to the event queue for streaming
        self.event_queue.put(event)
        
        # Notify listeners
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                self.logger.error(f"Error notifying listener: {str(e)}")
    
    def record_agent_thought(self, agent_name: str, thought: str, context: Dict[str, Any] = None):
        """
        Record an agent's thought process.
        
        Args:
            agent_name (str): Name of the agent
            thought (str): The thought content
            context (dict, optional): Additional context
        """
        self.record_event("thought", agent_name, thought, context)
    
    def record_agent_error(self, agent_name: str, error: str, context: Dict[str, Any] = None):
        """
        Record an agent error.
        
        Args:
            agent_name (str): Name of the agent
            error (str): The error message
            context (dict, optional): Additional context
        """
        self.record_event("error", agent_name, error, context)
    
    def record_agent_action(self, agent_name: str, action: str, context: Dict[str, Any] = None):
        """
        Record an agent action.
        
        Args:
            agent_name (str): Name of the agent
            action (str): The action taken
            context (dict, optional): Additional context
        """
        self.record_event("action", agent_name, action, context)
    
    def record_agent_result(self, agent_name: str, result: Dict[str, Any], context: Dict[str, Any] = None):
        """
        Record an agent's result.
        
        Args:
            agent_name (str): Name of the agent
            result (dict): The result data
            context (dict, optional): Additional context
        """
        # Convert result to string if it's not already
        if isinstance(result, dict):
            message = json.dumps(result, indent=2)
        else:
            message = str(result)
        
        self.record_event("result", agent_name, message, context)
    
    def get_event_stream(self):
        """
        Get a generator that yields events as they occur.
        
        Returns:
            generator: Event stream generator
        """
        last_id = 0
        
        with self.lock:
            # First yield all existing events
            for i, event in enumerate(self.events):
                event_copy = event.copy()
                event_copy["id"] = i
                last_id = i
                yield event_copy
        
        # Then yield new events as they arrive
        while True:
            try:
                event = self.event_queue.get(timeout=1)
                last_id += 1
                event_copy = event.copy()
                event_copy["id"] = last_id
                yield event_copy
            except Exception:
                # If no event is available, yield a keepalive
                yield {"type": "keepalive", "timestamp": time.time()}
    
    async def stream_events(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Stream events to a callback function.
        
        Args:
            callback (callable): Function to call with each event
        """
        last_id = 0
        
        with self.lock:
            # First yield all existing events
            for i, event in enumerate(self.events):
                event_copy = event.copy()
                event_copy["id"] = i
                last_id = i
                await callback(event_copy)
        
        # Register as a listener for new events
        async def async_listener(event):
            nonlocal last_id
            last_id += 1
            event_copy = event.copy()
            event_copy["id"] = last_id
            await callback(event_copy)
        
        self.listeners.append(async_listener)
        
        try:
            # Keep the connection alive
            while True:
                await asyncio.sleep(30)  # Send keepalive every 30 seconds
                await callback({"type": "keepalive", "timestamp": time.time()})
        finally:
            # Clean up when done
            if async_listener in self.listeners:
                self.listeners.remove(async_listener)
    
    def get_execution_graph(self):
        """
        Generate a graph representation of agent execution flow.
        
        Returns:
            dict: Graph structure with nodes and edges
        """
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Track unique agents and their last event
        agent_nodes = {}
        last_event = {}
        
        with self.lock:
            for event in self.events:
                agent = event.get("agent")
                event_type = event.get("type")
                
                # Add node if it doesn't exist
                if agent not in agent_nodes:
                    node_id = f"agent-{len(agent_nodes)}"
                    agent_nodes[agent] = node_id
                    graph["nodes"].append({
                        "id": node_id,
                        "label": agent,
                        "type": "agent"
                    })
                
                # Add event node
                event_id = f"event-{len(graph['nodes'])}"
                graph["nodes"].append({
                    "id": event_id,
                    "label": event.get("message", "")[:30] + "..." if len(event.get("message", "")) > 30 else event.get("message", ""),
                    "type": event_type,
                    "timestamp": event.get("timestamp")
                })
                
                # Add edge from agent to event
                graph["edges"].append({
                    "from": agent_nodes[agent],
                    "to": event_id,
                    "label": event_type
                })
                
                # If agent is responding to another agent, add edge
                if "source_agent" in event.get("metadata", {}):
                    source_agent = event["metadata"]["source_agent"]
                    if source_agent in agent_nodes and source_agent in last_event:
                        graph["edges"].append({
                            "from": last_event[source_agent],
                            "to": event_id,
                            "label": "response"
                        })
                
                # Update last event for this agent
                last_event[agent] = event_id
        
        return graph
    
    def get_agent_statistics(self):
        """
        Calculate statistics for each agent.
        
        Returns:
            dict: Agent statistics
        """
        stats = {}
        
        with self.lock:
            for event in self.events:
                agent = event.get("agent")
                event_type = event.get("type")
                
                if agent not in stats:
                    stats[agent] = {
                        "total_events": 0,
                        "thought_count": 0,
                        "error_count": 0,
                        "action_count": 0,
                        "result_count": 0,
                        "avg_response_time": 0,
                        "first_event": event.get("timestamp"),
                        "last_event": event.get("timestamp")
                    }
                
                # Update counts
                stats[agent]["total_events"] += 1
                
                if event_type == "thought":
                    stats[agent]["thought_count"] += 1
                elif event_type == "error":
                    stats[agent]["error_count"] += 1
                elif event_type == "action":
                    stats[agent]["action_count"] += 1
                elif event_type == "result":
                    stats[agent]["result_count"] += 1
                
                # Update timestamps
                stats[agent]["last_event"] = event.get("timestamp")
                
                # Calculate average response time if applicable
                if "response_time" in event.get("metadata", {}):
                    current_avg = stats[agent]["avg_response_time"]
                    current_count = stats[agent]["total_events"] - 1
                    new_time = event["metadata"]["response_time"]
                    
                    if current_count > 0:
                        stats[agent]["avg_response_time"] = (current_avg * current_count + new_time) / (current_count + 1)
                    else:
                        stats[agent]["avg_response_time"] = new_time
        
        return stats 