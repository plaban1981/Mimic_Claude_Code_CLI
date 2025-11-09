# 📊 Visual Architecture Summary

## Mermaid Flow Diagrams

### 1. Overall System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        UI[Rich Terminal UI / Web UI]
    end
    
    subgraph "Entry Point"
        MAIN[main.py / app.py]
    end
    
    subgraph "Core Agent"
        AGENT[CodeGeneratorAgent]
        SG[StateGraph Workflow]
        LLM[Claude Sonnet 4.5]
    end
    
    subgraph "Workflow Nodes"
        MR[model_response]
        TU[tool_use]
        CT[check_tool_use]
    end
    
    subgraph "Tools Layer"
        CT_TOOLS[Code Generation Tools]
        FT_TOOLS[File Operation Tools]
    end
    
    subgraph "Persistence"
        CP[SQLite Checkpointer]
        DB[(code_generator_checkpoints.db)]
    end
    
    subgraph "Output"
        FS[File System]
        GEN[./generated_code/]
    end
    
    UI --> MAIN
    MAIN --> AGENT
    AGENT --> SG
    SG --> MR
    SG --> TU
    SG --> CT
    MR --> LLM
    LLM --> CT
    CT -->|has tools| TU
    CT -->|no tools| END[END]
    TU --> CT_TOOLS
    TU --> FT_TOOLS
    CT_TOOLS --> FS
    FT_TOOLS --> FS
    FS --> GEN
    SG --> CP
    CP --> DB
    TU --> MR
    
    style UI fill:#e1f5ff
    style AGENT fill:#fff4e1
    style LLM fill:#ffe1f5
    style CP fill:#e1ffe1
    style GEN fill:#f5e1ff
```

### 2. StateGraph Workflow Flow

```mermaid
stateDiagram-v2
    [*] --> model_response: User Input
    
    model_response: Model Response Node
    model_response: - Clean messages
    model_response: - Add system message
    model_response: - Invoke LLM
    model_response: - Format response
    
    model_response --> check_tool_use: Response Generated
    
    check_tool_use: Check Tool Use
    check_tool_use: - Check for tool_calls
    check_tool_use: - Route decision
    
    check_tool_use --> tool_use: Has tool_calls
    check_tool_use --> END: No tool_calls
    
    tool_use: Tool Use Node
    tool_use: - Extract tool calls
    tool_use: - Auto-fix missing content
    tool_use: - Execute tools
    tool_use: - Create ToolMessages
    
    tool_use --> model_response: Tools Executed
    
    END: End State
    END --> [*]: Complete
    
    note right of model_response
        Cleans messages for
        Anthropic API compliance
    end note
    
    note right of tool_use
        Auto-extracts content
        if missing from response
    end note
```

### 3. Message Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Main
    participant Agent
    participant StateGraph
    participant LLM
    participant Tools
    participant Checkpointer
    participant FileSystem
    
    User->>Main: Natural Language Request
    Main->>Agent: Initialize & Run
    Agent->>StateGraph: Invoke with HumanMessage
    
    StateGraph->>Checkpointer: Load State
    Checkpointer-->>StateGraph: Previous Messages
    
    StateGraph->>StateGraph: Clean Messages
    StateGraph->>LLM: Process with Context
    
    LLM->>LLM: Generate Response
    LLM->>LLM: Decide on Tool Usage
    LLM-->>StateGraph: AIMessage (with/without tool_calls)
    
    alt Has Tool Calls
        StateGraph->>Tools: Execute Tools
        Tools->>FileSystem: Read/Write Files
        FileSystem-->>Tools: Results
        Tools-->>StateGraph: ToolMessages
        StateGraph->>LLM: Continue with Results
        LLM-->>StateGraph: Final Response
    else No Tool Calls
        StateGraph->>Checkpointer: Save State
        StateGraph-->>User: Display Response
    end
    
    StateGraph->>Checkpointer: Save State
    Checkpointer-->>StateGraph: State Saved
```

### 4. Tool Execution Flow

```mermaid
flowchart TD
    START[LLM Generates Tool Calls] --> EXTRACT[Extract tool_calls from AIMessage]
    
    EXTRACT --> LOOP{For each tool_call}
    
    LOOP --> CHECK_TYPE{Tool Type?}
    
    CHECK_TYPE -->|write_file| VALIDATE[Validate Parameters]
    CHECK_TYPE -->|Other Tools| EXECUTE[Execute Tool]
    
    VALIDATE --> HAS_CONTENT{Has content?}
    
    HAS_CONTENT -->|No| AUTO_FIX[Auto-Extract Content]
    HAS_CONTENT -->|Yes| EXECUTE
    
    AUTO_FIX --> EXTRACT_CODE[Try Code Blocks]
    EXTRACT_CODE --> FOUND_CODE{Found?}
    
    FOUND_CODE -->|Yes| EXECUTE
    FOUND_CODE -->|No| EXTRACT_TEXT[Try Response Text]
    
    EXTRACT_TEXT --> FOUND_TEXT{Found?}
    
    FOUND_TEXT -->|Yes| EXECUTE
    FOUND_TEXT -->|No| IS_README{Is README?}
    
    IS_README -->|Yes| GEN_README[Generate Basic README]
    IS_README -->|No| ERROR[Return Error Message]
    
    GEN_README --> EXECUTE
    
    EXECUTE --> SUCCESS{Success?}
    SUCCESS -->|Yes| TOOL_MSG[Create ToolMessage]
    SUCCESS -->|No| ERROR_MSG[Create Error ToolMessage]
    
    TOOL_MSG --> NEXT{More tools?}
    ERROR_MSG --> NEXT
    
    NEXT -->|Yes| LOOP
    NEXT -->|No| RETURN[Return All ToolMessages]
    
    RETURN --> CONTINUE[Continue to model_response]
    
    style AUTO_FIX fill:#fff4e1
    style GEN_README fill:#e1ffe1
    style ERROR fill:#ffe1e1
    style SUCCESS fill:#e1ffe1
```

### 5. State Persistence Flow

```mermaid
flowchart LR
    subgraph "Agent State"
        STATE[AgentState<br/>messages: Sequence[BaseMessage]]
    end
    
    subgraph "Checkpointer"
        CP[AsyncSqliteSaver]
        THREAD[Thread ID<br/>code_generator_session]
    end
    
    subgraph "Database"
        DB[(SQLite DB<br/>code_generator_checkpoints.db)]
        TABLES[Tables:<br/>• checkpoints<br/>• writes]
    end
    
    STATE -->|Save State| CP
    CP -->|Store| THREAD
    THREAD -->|Persist| DB
    DB --> TABLES
    
    DB -->|Load State| CP
    CP -->|Restore| STATE
    
    style STATE fill:#e1f5ff
    style CP fill:#fff4e1
    style DB fill:#e1ffe1
```

### 6. Error Handling & Recovery Flow

```mermaid
flowchart TD
    TOOL_CALL[Tool Call Received] --> VALIDATE{Validate Parameters}
    
    VALIDATE -->|Valid| EXECUTE[Execute Tool]
    VALIDATE -->|Invalid| AUTO_FIX[Auto-Fix Attempt]
    
    AUTO_FIX --> FIXED{Fixed?}
    FIXED -->|Yes| EXECUTE
    FIXED -->|No| ERROR_MSG[Create Error Message]
    
    EXECUTE --> SUCCESS{Success?}
    
    SUCCESS -->|Yes| RESULT[Return Success Result]
    SUCCESS -->|No| CATCH[Capture Exception]
    
    CATCH --> FORMAT[Format Error Message]
    FORMAT --> ERROR_MSG
    
    ERROR_MSG --> TOOL_MSG[Create ToolMessage with Error]
    RESULT --> TOOL_MSG_SUCCESS[Create ToolMessage with Result]
    
    TOOL_MSG --> LOOP_BACK[Return to model_response]
    TOOL_MSG_SUCCESS --> LOOP_BACK
    
    LOOP_BACK --> LLM_RETRY[LLM Sees Error/Result]
    LLM_RETRY --> DECIDE{LLM Decision}
    
    DECIDE -->|Retry| TOOL_CALL
    DECIDE -->|Continue| NEXT[NEXT]
    DECIDE -->|Abort| END[END]
    
    style AUTO_FIX fill:#fff4e1
    style ERROR_MSG fill:#ffe1e1
    style RESULT fill:#e1ffe1
    style LLM_RETRY fill:#e1f5ff
```

### 7. Web Application Architecture (app.py)

```mermaid
graph TB
    subgraph "Client"
        BROWSER[Web Browser]
        WS[WebSocket Connection]
    end
    
    subgraph "FastAPI Application"
        APP[app.py]
        ROUTES[REST API Routes]
        WS_ENDPOINT[WebSocket Endpoint]
    end
    
    subgraph "Agent Manager"
        AM[AgentManager]
        AGENTS[Agent Instances<br/>Per Session]
    end
    
    subgraph "Core Agent"
        AGENT[CodeGeneratorAgent]
        SG[StateGraph]
    end
    
    subgraph "Tools & LLM"
        TOOLS[Tools]
        LLM[Claude Sonnet 4.5]
    end
    
    BROWSER -->|HTTP| ROUTES
    BROWSER -->|WS| WS_ENDPOINT
    
    ROUTES --> APP
    WS_ENDPOINT --> APP
    
    APP --> AM
    AM --> AGENTS
    AGENTS --> AGENT
    AGENT --> SG
    SG --> TOOLS
    SG --> LLM
    
    AGENT -->|Stream Events| WS_ENDPOINT
    WS_ENDPOINT -->|Real-time Updates| WS
    WS --> BROWSER
    
    style BROWSER fill:#e1f5ff
    style APP fill:#fff4e1
    style AM fill:#ffe1f5
    style AGENT fill:#e1ffe1
```

### 8. Complete Request Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant UI as UI Layer
    participant A as Agent
    participant SG as StateGraph
    participant L as LLM
    participant T as Tools
    participant C as Checkpointer
    participant F as FileSystem
    
    U->>UI: "Generate FastAPI API"
    UI->>A: Create HumanMessage
    A->>SG: Invoke workflow
    SG->>C: Load state
    C-->>SG: Previous messages
    
    SG->>SG: Clean messages
    SG->>L: Invoke with messages
    L->>L: Process & Generate
    L-->>SG: AIMessage + tool_calls
    
    SG->>SG: check_tool_use
    SG->>T: Execute tools
    
    loop For each tool
        T->>T: Validate & Auto-fix
        T->>F: Execute operation
        F-->>T: Result
        T-->>SG: ToolMessage
    end
    
    SG->>L: Continue with results
    L->>L: Process results
    L-->>SG: Final AIMessage
    
    SG->>C: Save state
    C-->>SG: Saved
    SG-->>A: Complete
    A-->>UI: Format response
    UI-->>U: Display result
```

## Quick Reference Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Rich Terminal)               │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MAIN.PY (Entry Point)                      │
│  • Load .env                                                    │
│  • Create output directory                                      │
│  • Initialize agent                                             │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              CODEGENERATORAGENT (Core Agent)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  StateGraph Workflow                                      │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │  │
│  │  │ model_       │───▶│ check_      │───▶│ tool_       │ │  │
│  │  │ response     │    │ tool_use    │    │ use         │ │  │
│  │  └──────┬───────┘    └─────────────┘    └──────┬───────┘ │  │
│  │         │                                        │          │  │
│  │         └──────────────────────────────────────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Claude Sonnet 4.5 (LLM)                                  │  │
│  │  • Temperature: 0.7                                        │  │
│  │  • Max Tokens: 8192                                        │  │
│  │  • Tools Bound: Yes                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         TOOL LAYER                               │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │  Code Generation      │  │  File Operations     │           │
│  │  • generate_code      │  │  • read_file        │           │
│  │  • create_project_   │  │  • write_file       │           │
│  │    structure          │  │  • list_files       │           │
│  │  • generate_file      │  │  • create_directory│           │
│  │  • analyze_code       │  │  • search_files    │           │
│  │  • generate_tests     │  │                     │           │
│  └──────────────────────┘  └──────────────────────┘           │
│                                                                   │
│  ┌──────────────────────┐                                      │
│  │  MCP Tools (Optional)│                                      │
│  │  • FileSystem MCP     │                                      │
│  │  • DuckDuckGo MCP     │                                      │
│  │  • GitHub MCP         │                                      │
│  └──────────────────────┘                                      │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLite Checkpointer                                      │  │
│  │  • Thread ID: code_generator_session                      │  │
│  │  • Saves: All messages, state, metadata                   │  │
│  │  • File: code_generator_checkpoints.db                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Generated Code Files                                      │  │
│  │  • Location: ./generated_code/                            │  │
│  │  • Format: Python, JavaScript, etc.                        │  │
│  │  • Structure: Organized by project                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Message Flow Visualization

```
┌─────────┐
│  USER   │
└────┬────┘
     │ "Generate FastAPI API"
     ▼
┌─────────────────────────────────────┐
│  HumanMessage                       │
│  content: "Generate FastAPI API"   │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  StateGraph: model_response         │
│  ┌───────────────────────────────┐ │
│  │ Add SystemMessage (if first)  │ │
│  │ Invoke LLM with messages      │ │
│  └───────────────────────────────┘ │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  AIMessage                          │
│  content: "I'll generate..."        │
│  tool_calls: [                      │
│    {name: "generate_code", ...},    │
│    {name: "write_file", ...}        │
│  ]                                  │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  StateGraph: tool_use               │
│  ┌───────────────────────────────┐ │
│  │ Execute generate_code         │ │
│  │ Execute write_file            │ │
│  └───────────────────────────────┘ │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  ToolMessage(s)                     │
│  content: "Code generated..."       │
│  tool_call_id: "..."                │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  StateGraph: model_response         │
│  ┌───────────────────────────────┐ │
│  │ LLM processes tool results     │ │
│  │ Generates final response      │ │
│  └───────────────────────────────┘ │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  AIMessage                          │
│  content: "I've created..."         │
│  tool_calls: [] (none)              │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  Checkpointer: Save State           │
│  ┌───────────────────────────────┐ │
│  │ Save all messages to DB       │ │
│  │ Update checkpoint             │ │
│  └───────────────────────────────┘ │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────┐
│  USER   │
│  (sees formatted response)          │
└─────────┘
```

## Tool Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│  LLM Decides: Need Tools                                │
└────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Extract tool_calls from AIMessage                      │
│  [                                                       │
│    {name: "generate_code", args: {...}},                │
│    {name: "write_file", args: {...}}                    │
│  ]                                                       │
└────────────────────┬────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐         ┌───────────────┐
│ Code Tool     │         │ File Tool     │
│ generate_code │         │ write_file    │
└───────┬───────┘         └───────┬───────┘
        │                         │
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│ LLM Generates │         │ File System   │
│ Code          │         │ Write File    │
└───────┬───────┘         └───────┬───────┘
        │                         │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ ToolMessage Results  │
        │ [                    │
        │   "Code: def api..."  │
        │   "File written: ✓"   │
        │ ]                    │
        └─────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Return to LLM       │
        │ (Continue workflow)  │
        └─────────────────────┘
```

## State Persistence Flow

```
┌─────────────────────────────────────────────────────────┐
│  AgentState                                             │
│  ┌───────────────────────────────────────────────────┐ │
│  │ messages: [                                        │ │
│  │   SystemMessage("You are..."),                    │ │
│  │   HumanMessage("Generate API"),                   │ │
│  │   AIMessage("I'll generate..."),                 │ │
│  │   ToolMessage("Code generated..."),                │ │
│  │   AIMessage("Done!")                               │ │
│  │ ]                                                  │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  AsyncSqliteSaver                                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Thread ID: "code_generator_session"                │ │
│  │ Checkpoint ID: "abc123..."                         │ │
│  │ Save: messages, metadata, timestamps              │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  SQLite Database                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ code_generator_checkpoints.db                      │ │
│  │                                                    │ │
│  │ Tables:                                           │ │
│  │  • checkpoints                                    │ │
│  │  • writes                                         │ │
│  │                                                    │ │
│  │ Enables:                                          │ │
│  │  • Conversation resume                           │ │
│  │  • Debugging                                     │ │
│  │  • State inspection                              │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Component Interaction Matrix

```
┌─────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ Component   │ Interacts    │ Interaction  │ Data Flow    │ Purpose      │
│             │ With         │ Type         │              │              │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ User        │ Agent        │ I/O          │ Text         │ Requests     │
│ Agent       │ StateGraph   │ Control      │ State        │ Orchestrate  │
│ StateGraph  │ LLM          │ Invoke       │ Messages     │ Process      │
│ StateGraph  │ Tools        │ Execute      │ Args/Results │ Execute      │
│ StateGraph  │ Checkpointer │ Persist      │ State        │ Save/Load    │
│ LLM         │ Tools        │ Bind         │ Functions    │ Tool Calling │
│ Tools       │ FileSystem   │ I/O          │ Files        │ Operations   │
│ Tools       │ MCP Servers  │ RPC          │ Requests     │ External     │
│ Checkpointer│ SQLite       │ Storage      │ State        │ Persistence  │
└─────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│  Tool Execution                                         │
└────────────────────┬────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐         ┌───────────────┐
│ Success       │         │ Error         │
│ Return Result │         │ Catch Exception│
└───────┬───────┘         └───────┬───────┘
        │                         │
        │                         ▼
        │              ┌─────────────────┐
        │              │ Create Error     │
        │              │ ToolMessage      │
        │              └────────┬────────┘
        │                         │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Add to State        │
        │ Continue Workflow   │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ LLM Processes       │
        │ (Error or Success)  │
        └─────────────────────┘
```

## Key Design Patterns

### 1. StateGraph Pattern
- **Purpose**: Manage workflow state
- **Implementation**: Three-node graph with conditional routing
- **Benefits**: Clear flow, easy to extend

### 2. Tool Binding Pattern
- **Purpose**: Enable LLM function calling
- **Implementation**: Tools bound to LLM via `bind_tools()`
- **Benefits**: LLM can intelligently choose tools

### 3. Checkpointing Pattern
- **Purpose**: Persist conversation state
- **Implementation**: SQLite-based async checkpointing
- **Benefits**: Resume conversations, debugging

### 4. Message Pattern
- **Purpose**: Standardize communication
- **Implementation**: LangChain message types
- **Benefits**: Type safety, consistency

### 5. Tool Registry Pattern
- **Purpose**: Manage available tools
- **Implementation**: Tool lists in separate modules
- **Benefits**: Modularity, easy to extend

## Performance Metrics

```
┌─────────────────────────────────────────────────────────┐
│  Typical Request Flow Timing                             │
├─────────────────────────────────────────────────────────┤
│  User Input Processing:        < 0.1s                    │
│  State Load:                   < 0.1s                   │
│  LLM Processing:               2-10s                    │
│  Tool Execution:               < 1s (local)              │
│  Tool Execution (MCP):         1-5s                     │
│  State Save:                   < 0.1s                   │
│  Response Formatting:          < 0.1s                   │
├─────────────────────────────────────────────────────────┤
│  Total (typical):              5-30s                    │
│  Total (complex):              30-60s                    │
└─────────────────────────────────────────────────────────┘
```

## Scalability Considerations

```
┌─────────────────────────────────────────────────────────┐
│  Current Architecture: Single-threaded, async           │
│  • One user per process                                 │
│  • Thread-based state isolation                         │
│  • SQLite for persistence                               │
├─────────────────────────────────────────────────────────┤
│  Scaling Options:                                       │
│  • Multiple processes (process pool)                    │
│  • Distributed state (Redis/PostgreSQL)                  │
│  • Load balancing (multiple agents)                      │
│  • Caching (frequently used code patterns)              │
└─────────────────────────────────────────────────────────┘
```

