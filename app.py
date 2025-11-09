#!/usr/bin/env python3
"""
FastAPI Web Application for AI Code Generator

A beautiful full-stack web application that provides the same functionality
as main.py but with a modern web interface.
"""
import asyncio
import os
import sys
import uuid
from typing import Optional, Dict, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agent import CodeGeneratorAgent
from langchain_core.messages import HumanMessage
from rich.console import Console

# Load environment variables
load_dotenv()

# Create a silent console for web version
class SilentConsole:
    """A console that suppresses all output for web use"""
    def print(self, *args, **kwargs):
        pass
    
    def status(self, *args, **kwargs):
        class Status:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return Status()

# Global agent manager
class AgentManager:
    """Manages multiple agent instances for concurrent users"""
    def __init__(self):
        self.agents: Dict[str, CodeGeneratorAgent] = {}
        self.agent_configs: Dict[str, dict] = {}
    
    async def get_or_create_agent(self, session_id: str) -> CodeGeneratorAgent:
        """Get existing agent or create new one for session"""
        if session_id not in self.agents:
            agent = CodeGeneratorAgent()
            # Suppress console output for web version
            agent.console = SilentConsole()
            await agent.initialize()
            self.agents[session_id] = agent
            self.agent_configs[session_id] = {
                "configurable": {"thread_id": f"web_session_{session_id}"}
            }
        return self.agents[session_id]
    
    async def cleanup_agent(self, session_id: str):
        """Cleanup agent for a session"""
        if session_id in self.agents:
            await self.agents[session_id].cleanup()
            del self.agents[session_id]
            if session_id in self.agent_configs:
                del self.agent_configs[session_id]

agent_manager = AgentManager()

# Pydantic models
class GenerateRequest(BaseModel):
    """Request model for code generation"""
    prompt: str = Field(..., min_length=1, description="Natural language description of code to generate")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    language: Optional[str] = Field("python", description="Target programming language")

class GenerateResponse(BaseModel):
    """Response model for code generation"""
    session_id: str
    response: str
    tool_calls: List[Dict] = []
    files_created: List[str] = []
    timestamp: datetime

class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    created_at: datetime
    message_count: int

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    print("🚀 Starting AI Code Generator Web Application...")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  WARNING: ANTHROPIC_API_KEY not found!")
        print("   Please set your Anthropic API key in .env file")
    
    # Create output directory
    output_dir = os.getenv("OUTPUT_DIR", "./generated_code")
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {os.path.abspath(output_dir)}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    # Cleanup all agents
    for session_id in list(agent_manager.agents.keys()):
        await agent_manager.cleanup_agent(session_id)

# Initialize FastAPI app
app = FastAPI(
    title="AI Code Generator",
    description="A powerful AI-powered code generator with web interface",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for the UI)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Helper function to format agent response for web
def format_agent_response(response_text: str, tool_results: List[Dict] = None) -> Dict:
    """Format agent response for web display"""
    files_created = []
    tool_calls = []
    
    if tool_results:
        for result in tool_results:
            if isinstance(result, dict):
                tool_name = result.get("tool_name", "")
                tool_result = result.get("result", "")
                
                # Extract file paths from write_file results
                if "write_file" in tool_name.lower() or "Successfully wrote" in str(tool_result):
                    # Try to extract file path
                    if "to " in str(tool_result):
                        file_path = str(tool_result).split("to ")[-1].strip()
                        files_created.append(file_path)
                
                tool_calls.append({
                    "name": tool_name,
                    "result": str(tool_result)
                })
    
    return {
        "response": response_text,
        "tool_calls": tool_calls,
        "files_created": files_created
    }

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI"""
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        # Return a simple HTML if file doesn't exist
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Code Generator</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>AI Code Generator</h1>
            <p>Please create the UI files in the static directory.</p>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "active_sessions": len(agent_manager.agents),
        "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY"))
    }

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate code from a natural language prompt
    
    This endpoint processes code generation requests synchronously.
    For real-time updates, use the WebSocket endpoint.
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Get or create agent for this session
        agent = await agent_manager.get_or_create_agent(session_id)
        config = agent_manager.agent_configs[session_id]
        
        # Create human message
        human_message = HumanMessage(content=request.prompt)
        
        # Invoke the workflow
        result = await agent.agent.ainvoke(
            {"messages": [human_message]},
            config=config
        )
        
        # Extract response
        messages = result.get("messages", [])
        response_text = ""
        tool_results = []
        
        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                response_text += str(msg.content) + "\n\n"
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_results.append({
                        "tool_name": tool_call.get("name", ""),
                        "args": tool_call.get("args", {})
                    })
        
        # Format response
        formatted = format_agent_response(response_text, tool_results)
        
        return GenerateResponse(
            session_id=session_id,
            response=formatted["response"],
            tool_calls=formatted["tool_calls"],
            files_created=formatted["files_created"],
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating code: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time code generation
    
    Provides streaming updates during code generation process.
    """
    await manager.connect(websocket)
    
    try:
        # Get or create agent for this session
        agent = await agent_manager.get_or_create_agent(session_id)
        config = agent_manager.agent_configs[session_id]
        
        # Send welcome message
        await manager.send_personal_message({
            "type": "status",
            "message": "Connected to AI Code Generator",
            "session_id": session_id
        }, websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "generate":
                prompt = data.get("prompt", "")
                
                if not prompt:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Prompt cannot be empty"
                    }, websocket)
                    continue
                
                # Send thinking indicator
                await manager.send_personal_message({
                    "type": "thinking",
                    "message": "🤔 Generating code..."
                }, websocket)
                
                # Create human message
                human_message = HumanMessage(content=prompt)
                
                # Invoke workflow and stream updates
                try:
                    # Stream the workflow execution
                    async for event in agent.agent.astream(
                        {"messages": [human_message]},
                        config=config
                    ):
                        # Process events
                        for node_name, node_output in event.items():
                            if node_name == "model_response":
                                messages = node_output.get("messages", [])
                                for msg in messages:
                                    if hasattr(msg, "content") and msg.content:
                                        await manager.send_personal_message({
                                            "type": "response",
                                            "content": str(msg.content),
                                            "node": node_name
                                        }, websocket)
                            
                            elif node_name == "tool_use":
                                messages = node_output.get("messages", [])
                                for msg in messages:
                                    if hasattr(msg, "content"):
                                        await manager.send_personal_message({
                                            "type": "tool_result",
                                            "tool_name": "tool_execution",
                                            "result": str(msg.content),
                                            "node": node_name
                                        }, websocket)
                    
                    # Send completion message - ensure this is always sent
                    await manager.send_personal_message({
                        "type": "complete",
                        "message": "Code generation completed"
                    }, websocket)
                
                except Exception as e:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Error: {str(e)}"
                    }, websocket)
            
            elif data.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong"
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Optionally cleanup agent after disconnect (or keep for session reuse)
        # await agent_manager.cleanup_agent(session_id)
    except Exception as e:
        manager.disconnect(websocket)
        print(f"WebSocket error: {e}")

@app.get("/api/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a session"""
    if session_id not in agent_manager.agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": "active"
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and cleanup its agent"""
    if session_id not in agent_manager.agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await agent_manager.cleanup_agent(session_id)
    return {"message": "Session deleted", "session_id": session_id}

@app.get("/api/tools")
async def list_tools():
    """List all available tools"""
    from tools.code_tools import get_code_tools
    from tools.file_tools import get_file_tools
    
    code_tools = get_code_tools()
    file_tools = get_file_tools()
    
    return {
        "code_tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in code_tools
        ],
        "file_tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in file_tools
        ]
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

