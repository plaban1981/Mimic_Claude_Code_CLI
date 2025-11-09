# 🏗️ Complete Architecture Diagram

## System Overview

This document provides a comprehensive architecture diagram explaining the workflow between agents, tools, and MCP servers in the Code Generator application.

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface"
        UI[Rich Terminal UI]
    end
    
    subgraph "Code Generator Agent"
        MAIN[main.py]
        AGENT[CodeGeneratorAgent]
        STATE[AgentState]
        WORKFLOW[StateGraph Workflow]
    end
    
    subgraph "LLM Layer"
        LLM[Claude Sonnet 4.5]
        TOOLS_BOUND[LLM with Tools Bound]
    end
    
    subgraph "Tool Layer"
        CODE_TOOLS[Code Generation Tools]
        FILE_TOOLS[File Operation Tools]
        MCP_TOOLS[MCP Tools - Optional]
    end
    
    subgraph "MCP Servers - Optional"
        MCP_FS[FileSystem MCP]
        MCP_DDG[DuckDuckGo MCP]
        MCP_GH[GitHub MCP]
    end
    
    subgraph "Persistence Layer"
        CHECKPOINT[SQLite Checkpointer]
        DB[(checkpoints.db)]
    end
    
    subgraph "Output"
        FILES[Generated Code Files]
        DIR[generated_code/]
    end
    
    UI --> MAIN
    MAIN --> AGENT
    AGENT --> WORKFLOW
    WORKFLOW --> STATE
    WORKFLOW --> TOOLS_BOUND
    TOOLS_BOUND --> LLM
    WORKFLOW --> CODE_TOOLS
    WORKFLOW --> FILE_TOOLS
    WORKFLOW --> MCP_TOOLS
    MCP_TOOLS --> MCP_FS
    MCP_TOOLS --> MCP_DDG
    MCP_TOOLS --> MCP_GH
    WORKFLOW --> CHECKPOINT
    CHECKPOINT --> DB
    FILE_TOOLS --> FILES
    FILES --> DIR
    
    style AGENT fill:#4169E1
    style LLM fill:#20B2AA
    style WORKFLOW fill:#FFD700
    style CODE_TOOLS fill:#FF6347
    style FILE_TOOLS fill:#9370DB
    style MCP_TOOLS fill:#FFA500
    style CHECKPOINT fill:#32CD32
```

## StateGraph Workflow Detail

```mermaid
stateDiagram-v2
    [*] --> EntryPoint
    
    EntryPoint --> ModelResponse: User Input
    
    ModelResponse: Claude Sonnet 4.5 processes
    ModelResponse: Generates response
    ModelResponse: May request tools
    
    ModelResponse --> CheckToolUse: Response ready
    
    CheckToolUse: Check for tool_calls
    CheckToolUse --> ToolUse: Has tool calls
    CheckToolUse --> END: No tool calls
    
    ToolUse: Execute tools
    ToolUse: Code generation tools
    ToolUse: File operation tools
    ToolUse: MCP tools (optional)
    
    ToolUse --> ModelResponse: Tool results
    
    ModelResponse --> CheckToolUse: Continue workflow
    
    END --> [*]
    
    note right of ModelResponse
        System message added
        on first interaction
    end note
    
    note right of ToolUse
        Tools execute and
        return results
    end note
    
    note right of CheckToolUse
        Conditional routing
        based on tool needs
    end note
```

## Message Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant StateGraph
    participant LLM
    participant Tools
    participant MCP
    participant Checkpointer
    participant FileSystem
    
    User->>Agent: Natural Language Request
    Agent->>StateGraph: Invoke with message
    StateGraph->>Checkpointer: Load state
    
    StateGraph->>LLM: Process with context
    LLM->>LLM: Generate response
    LLM->>LLM: Decide on tool usage
    
    alt Tool Calls Needed
        LLM->>StateGraph: Response with tool_calls
        StateGraph->>Tools: Execute tools
        
        alt Local Tools
            Tools->>FileSystem: Read/Write files
            FileSystem->>Tools: File operations result
        else MCP Tools
            Tools->>MCP: MCP server request
            MCP->>Tools: MCP response
        end
        
        Tools->>StateGraph: Tool results
        StateGraph->>LLM: Continue with results
        LLM->>LLM: Process tool results
        LLM->>StateGraph: Final response
    else No Tools Needed
        LLM->>StateGraph: Direct response
    end
    
    StateGraph->>Checkpointer: Save state
    Checkpointer->>StateGraph: State saved
    StateGraph->>Agent: Response ready
    Agent->>User: Display formatted response
```

## Tool Architecture

```mermaid
graph LR
    subgraph "Tool Categories"
        CT[Code Generation Tools]
        FT[File Operation Tools]
        MT[MCP Tools]
    end
    
    subgraph "Code Generation Tools"
        CG[generate_code]
        CPS[create_project_structure]
        GF[generate_file]
        AC[analyze_code]
        GT[generate_tests]
    end
    
    subgraph "File Operation Tools"
        RF[read_file]
        WF[write_file]
        LF[list_files]
        CD[create_directory]
        SF[search_files]
    end
    
    subgraph "MCP Tools - Optional"
        MCP_FS[MCP FileSystem]
        MCP_DDG[MCP DuckDuckGo]
        MCP_GH[MCP GitHub]
    end
    
    CT --> CG
    CT --> CPS
    CT --> GF
    CT --> AC
    CT --> GT
    
    FT --> RF
    FT --> WF
    FT --> LF
    FT --> CD
    FT --> SF
    
    MT --> MCP_FS
    MT --> MCP_DDG
    MT --> MCP_GH
    
    CG --> LLM[LLM Generates Code]
    WF --> FS[File System]
    CPS --> FS
    GF --> FS
    
    style CT fill:#FF6347
    style FT fill:#9370DB
    style MT fill:#FFA500
```

## Complete Data Flow

```mermaid
flowchart TD
    START([User Input]) --> LOAD[Load State from DB]
    LOAD --> ADD_MSG[Add HumanMessage to State]
    ADD_MSG --> CHECK_FIRST{First Message?}
    
    CHECK_FIRST -->|Yes| ADD_SYS[Add SystemMessage]
    CHECK_FIRST -->|No| INVOKE_LLM
    ADD_SYS --> INVOKE_LLM[Invoke LLM with Tools]
    
    INVOKE_LLM --> LLM_PROCESS[Claude Sonnet 4.5 Processing]
    LLM_PROCESS --> HAS_TOOLS{Has tool_calls?}
    
    HAS_TOOLS -->|Yes| EXEC_TOOLS[Execute Tools]
    HAS_TOOLS -->|No| FORMAT_RESPONSE[Format Response]
    
    EXEC_TOOLS --> TOOL_TYPE{Tool Type?}
    
    TOOL_TYPE -->|Code Gen| CODE_TOOL[Code Generation Tool]
    TOOL_TYPE -->|File Op| FILE_TOOL[File Operation Tool]
    TOOL_TYPE -->|MCP| MCP_TOOL[MCP Tool]
    
    CODE_TOOL --> LLM_GEN[LLM Generates Code]
    LLM_GEN --> WRITE_FILE[write_file Tool]
    
    FILE_TOOL --> FILE_OP[File System Operation]
    MCP_TOOL --> MCP_SERVER[MCP Server Request]
    
    WRITE_FILE --> FILE_OP
    FILE_OP --> TOOL_RESULT[Tool Result]
    MCP_SERVER --> TOOL_RESULT
    
    TOOL_RESULT --> ADD_TOOL_MSG[Add ToolMessage to State]
    ADD_TOOL_MSG --> INVOKE_LLM
    
    FORMAT_RESPONSE --> DISPLAY[Display to User]
    DISPLAY --> SAVE_STATE[Save State to DB]
    SAVE_STATE --> WAIT_INPUT[Wait for Next Input]
    WAIT_INPUT --> START
    
    style START fill:#90EE90
    style LLM_PROCESS fill:#20B2AA
    style EXEC_TOOLS fill:#FFD700
    style SAVE_STATE fill:#32CD32
```

## Agent Class Structure

```mermaid
classDiagram
    class CodeGeneratorAgent {
        -Console console
        -AsyncSqliteSaver checkpointer
        -ChatAnthropic llm
        -List tools
        -StateGraph workflow
        -str thread_id
        +__init__()
        +initialize() async
        +run() async
        +cleanup() async
        -model_response(state)
        -tool_use(state)
        -check_tool_use(state)
        -_setup_workflow()
        -_display_welcome()
    }
    
    class AgentState {
        +Sequence[BaseMessage] messages
    }
    
    class StateGraph {
        +add_node(name, func)
        +add_edge(from, to)
        +add_conditional_edges(node, condition, mapping)
        +compile(checkpointer)
    }
    
    class ChatAnthropic {
        +model: str
        +temperature: float
        +max_tokens: int
        +bind_tools(tools)
        +invoke(messages)
    }
    
    class Tool {
        <<interface>>
        +name: str
        +description: str
        +invoke(args)
    }
    
    class CodeTools {
        +generate_code()
        +create_project_structure()
        +generate_file()
        +analyze_code()
        +generate_tests()
    }
    
    class FileTools {
        +read_file()
        +write_file()
        +list_files()
        +create_directory()
        +search_files()
    }
    
    class MCPTools {
        +get_mcp_tools() async
    }
    
    CodeGeneratorAgent --> AgentState
    CodeGeneratorAgent --> StateGraph
    CodeGeneratorAgent --> ChatAnthropic
    CodeGeneratorAgent --> Tool
    Tool <|.. CodeTools
    Tool <|.. FileTools
    Tool <|.. MCPTools
    StateGraph --> AgentState
```

## Checkpointing System

```mermaid
graph TB
    subgraph "State Management"
        STATE[AgentState]
        MSGS[Messages Array]
    end
    
    subgraph "Checkpointing"
        CHECKPOINT[AsyncSqliteSaver]
        DB[(SQLite Database)]
        THREAD[Thread ID]
    end
    
    subgraph "State Persistence"
        SAVE[Save State]
        LOAD[Load State]
        HISTORY[Conversation History]
    end
    
    STATE --> MSGS
    MSGS --> CHECKPOINT
    CHECKPOINT --> DB
    CHECKPOINT --> THREAD
    DB --> SAVE
    DB --> LOAD
    SAVE --> HISTORY
    LOAD --> HISTORY
    
    note1[After each node execution]
    note2[Before workflow starts]
    
    note1 --> SAVE
    note2 --> LOAD
    
    style CHECKPOINT fill:#32CD32
    style DB fill:#FFD700
    style HISTORY fill:#9370DB
```

## Tool Execution Flow

```mermaid
sequenceDiagram
    participant SG as StateGraph
    participant LLM as Claude Sonnet 4.5
    participant Tool as Tool Registry
    participant CT as Code Tool
    participant FT as File Tool
    participant FS as File System
    participant MCP as MCP Server
    
    SG->>LLM: Invoke with messages
    LLM->>LLM: Analyze request
    LLM->>SG: Response with tool_calls
    
    SG->>Tool: Find tool by name
    Tool->>CT: Code generation tool?
    Tool->>FT: File operation tool?
    Tool->>MCP: MCP tool?
    
    alt Code Generation
        CT->>LLM: Request code generation
        LLM->>CT: Generated code
        CT->>FT: write_file(code)
    end
    
    alt File Operation
        FT->>FS: Execute operation
        FS->>FT: Operation result
    end
    
    alt MCP Tool
        MCP->>MCP: Process request
        MCP->>Tool: MCP response
    end
    
    CT->>SG: Tool result
    FT->>SG: Tool result
    MCP->>SG: Tool result
    
    SG->>LLM: Continue with tool results
    LLM->>SG: Final response
```

## Component Interaction Matrix

| Component | Interacts With | Interaction Type | Purpose |
|-----------|----------------|------------------|---------|
| **User** | Agent | Input/Output | Natural language requests |
| **Agent** | StateGraph | Control | Orchestrates workflow |
| **StateGraph** | LLM | Invocation | Processes messages |
| **StateGraph** | Tools | Execution | Executes tool calls |
| **StateGraph** | Checkpointer | Persistence | Saves/loads state |
| **LLM** | Tools | Binding | Tool function calling |
| **Tools** | File System | I/O | File operations |
| **Tools** | MCP Servers | RPC | External services |
| **Checkpointer** | SQLite DB | Storage | State persistence |

## Error Handling Flow

```mermaid
graph TD
    START[Tool Execution] --> TRY{Try Execute}
    TRY -->|Success| RESULT[Return Result]
    TRY -->|Error| CATCH[Catch Exception]
    
    CATCH --> ERROR_MSG[Create Error Message]
    ERROR_MSG --> TOOL_MSG[Create ToolMessage]
    TOOL_MSG --> ADD_STATE[Add to State]
    ADD_STATE --> CONTINUE[Continue Workflow]
    
    RESULT --> ADD_STATE
    
    CONTINUE --> LLM[LLM Processes Error]
    LLM --> RETRY{Retry?}
    RETRY -->|Yes| START
    RETRY -->|No| USER_NOTIFY[Notify User]
    
    style CATCH fill:#FF6347
    style ERROR_MSG fill:#FFA500
    style USER_NOTIFY fill:#FFD700
```

## Summary

This architecture demonstrates:

1. **Three-Node Workflow**: Model Response → Tool Use → Model Response (conditional)
2. **Tool Integration**: Local tools and optional MCP tools
3. **State Persistence**: SQLite checkpointing for conversation history
4. **LLM Integration**: Claude Sonnet 4.5 with tool binding
5. **Error Handling**: Graceful error handling and recovery
6. **Extensibility**: Easy to add new tools or MCP servers

The system is designed to be:
- **Modular**: Clear separation of concerns
- **Extensible**: Easy to add new tools
- **Persistent**: State saved across sessions
- **Robust**: Error handling at every level
- **Interactive**: Rich terminal UI for user experience

