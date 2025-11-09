"""
Core Code Generator Agent Implementation using LangGraph
"""
import os
from typing import Annotated, Sequence, Literal
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.tree import Tree
from rich.prompt import Prompt
from tools.code_tools import get_code_tools
from tools.file_tools import get_file_tools

console = Console()


class AgentState(BaseModel):
    """State management for the code generator workflow"""
    messages: Annotated[Sequence[BaseMessage], add_messages]


class CodeGeneratorAgent:
    """
    AI Code Generator using LangGraph and Claude Sonnet 4.5
    
    Architecture:
    - StateGraph with 3 nodes: model_response, tool_use
    - Persistent state using SQLite checkpointing
    - Tool integration: code generation tools + file operations
    """
    
    def __init__(self):
        self.console = console
        self._checkpointer_ctx = None
        self.checkpointer = None
        self.agent = None
        self.thread_id = "code_generator_session"
        self.last_options = {}  # Store numbered options from bullet points
        
        # Display welcome banner
        self._display_welcome()
        
        # Initialize LLM - Claude Sonnet 4.5
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5",  # Claude Sonnet 4.5
            temperature=0.7,  # Slightly higher for creative code generation
            max_tokens=8192,  # Higher token limit for code generation
        )
        
        # Initialize tools
        self.console.print("[cyan]🔧 Loading tools...[/cyan]")
        self.tools = []
        
        # Load code generation tools
        code_tools = get_code_tools()
        self.tools.extend(code_tools)
        self.console.print(f"[green]✓ Loaded {len(code_tools)} code generation tools[/green]")
        
        # Load file operation tools
        file_tools = get_file_tools()
        self.tools.extend(file_tools)
        self.console.print(f"[green]✓ Loaded {len(file_tools)} file operation tools[/green]")
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build workflow
        self.workflow = StateGraph(AgentState)
        self._setup_workflow()
    
    def _display_welcome(self):
        """Display a welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🚀  AI CODE GENERATOR  🚀                              ║
║                                                           ║
║   ▸ Powered by Claude Sonnet 4.5 + LangGraph            ║
║   ▸ Generate code from natural language                 ║
║   ▸ Type 'exit' or 'quit' to terminate                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
    
    def _setup_workflow(self):
        """Setup the StateGraph workflow"""
        # Register nodes
        self.workflow.add_node("model_response", self.model_response)
        self.workflow.add_node("tool_use", self.tool_use)
        
        # Define edges
        self.workflow.set_entry_point("model_response")
        self.workflow.add_edge("tool_use", "model_response")
        
        # Conditional routing
        self.workflow.add_conditional_edges(
            "model_response",
            self.check_tool_use,
            {
                "tool_use": "tool_use",
                END: END,
            },
        )
    
    async def initialize(self):
        """Async initialization for checkpointer"""
        # Initialize SQLite checkpointer
        db_path = os.path.join(os.getcwd(), "code_generator_checkpoints.db")
        self.console.print(f"[cyan]💾 Initializing checkpoint database: {db_path}[/cyan]")
        
        self._checkpointer_ctx = AsyncSqliteSaver.from_conn_string(db_path)
        self.checkpointer = await self._checkpointer_ctx.__aenter__()
        
        # Compile the workflow with checkpointer
        self.agent = self.workflow.compile(
            checkpointer=self.checkpointer
        )
        self.console.print("[green]✓ Agent initialized successfully![/green]\n")
        
        # Show quick start guide
        self._display_quick_start()
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self._checkpointer_ctx:
                await self._checkpointer_ctx.__aexit__(None, None, None)
        except Exception:
            pass  # Ignore cleanup errors on exit
    
    def _format_with_numbers(self, text) -> str:
        """Convert bullet points to numbered list and store mapping"""
        import re
        
        # Handle if text is a list of content blocks
        if isinstance(text, list):
            # Extract text from content blocks
            text_parts = []
            for block in text:
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])
                elif isinstance(block, str):
                    text_parts.append(block)
            text = '\n'.join(text_parts)
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        
        # Reset options
        self.last_options = {}
        
        # Find bullet points (• or -)
        lines = text.split('\n')
        option_num = 1
        formatted_lines = []
        
        for line in lines:
            # Match bullet points with various formats
            bullet_match = re.match(r'^(\s*)[•\-\*]\s+(.+)$', line)
            if bullet_match:
                indent = bullet_match.group(1)
                content = bullet_match.group(2)
                
                # Store the mapping
                self.last_options[str(option_num)] = content
                
                # Replace with number
                formatted_lines.append(f"{indent}**{option_num}.** {content}")
                option_num += 1
            else:
                formatted_lines.append(line)
        
        result = '\n'.join(formatted_lines)
        
        # Add helper text if options were found
        if self.last_options:
            result += f"\n\n*💡 Tip: Type a number (1-{len(self.last_options)}) to select an option*"
        
        return result
    
    def _clean_messages_for_anthropic(self, messages):
        """
        Clean messages to ensure Anthropic API requirements:
        - Every AIMessage with tool_calls must be immediately followed by ToolMessages
        - Remove orphaned tool_calls that don't have corresponding ToolMessages
        """
        cleaned = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            
            # Always preserve SystemMessage
            if isinstance(msg, SystemMessage):
                cleaned.append(msg)
                i += 1
                continue
            
            # If this is an AIMessage with tool_calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                # Check if the next messages are ToolMessages for these tool_calls
                tool_call_ids = {tc.get("id") for tc in msg.tool_calls}
                found_tool_results = set()
                
                # Look ahead for ToolMessages
                j = i + 1
                while j < len(messages):
                    next_msg = messages[j]
                    if isinstance(next_msg, ToolMessage):
                        if next_msg.tool_call_id in tool_call_ids:
                            found_tool_results.add(next_msg.tool_call_id)
                        j += 1
                    else:
                        # Not a ToolMessage, stop looking
                        break
                
                # If all tool_calls have corresponding ToolMessages, include them all
                if tool_call_ids == found_tool_results:
                    # Include the AIMessage
                    cleaned.append(msg)
                    # Include all ToolMessages
                    for k in range(i + 1, j):
                        cleaned.append(messages[k])
                    i = j
                    continue
                else:
                    # Missing tool results - create a new AIMessage without tool_calls
                    # This prevents the API error
                    from langchain_core.messages import AIMessage
                    cleaned_msg = AIMessage(content=msg.content)
                    cleaned.append(cleaned_msg)
                    i += 1
                    continue
            
            # Regular message, include it
            cleaned.append(msg)
            i += 1
        
        return cleaned
    
    def _generate_basic_readme(self, project_name: str, file_path: str, response_content: str) -> str:
        """Generate a basic README when content is missing"""
        try:
            # Extract project info from response
            project_info = {
                "name": project_name.replace("_", " ").replace("-", " ").title(),
                "description": "A project generated by AI Code Generator"
            }
            
            # Try to extract description from response
            if response_content:
                import re
                # Look for project descriptions
                desc_patterns = [
                    r'(?:I\'ll create|This will|This is).*?([A-Z][^.!?]*(?:\.|!|\?))',
                    r'comprehensive\s+([^.!?]+)',
                ]
                for pattern in desc_patterns:
                    match = re.search(pattern, response_content, re.IGNORECASE)
                    if match:
                        project_info["description"] = match.group(1).strip()
                        break
            
            # Check what files exist in the project directory
            project_dir = os.path.dirname(file_path) if os.path.dirname(file_path) != '.' else os.path.dirname(os.path.abspath(file_path))
            files_list = []
            if os.path.exists(project_dir):
                for item in os.listdir(project_dir):
                    if os.path.isfile(os.path.join(project_dir, item)) and item != "README.md":
                        files_list.append(f"- `{item}`")
            
            # Generate basic README
            readme_content = f"""# {project_info['name']}

{project_info['description']}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Project Structure

{chr(10).join(files_list) if files_list else "- See project files for structure"}

## Features

- Generated by AI Code Generator
- Ready to use and customize

## License

This project is provided as-is for educational and development purposes.
"""
            return readme_content
        except Exception as e:
            # Fallback to minimal README
            return f"""# {project_name.replace('_', ' ').replace('-', ' ').title()}

A project generated by AI Code Generator.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## License

This project is provided as-is for educational and development purposes.
"""
    
    def model_response(self, state: AgentState) -> dict:
        """Node: Generate model response"""
        original_messages = state.messages
        
        # Clean messages to ensure Anthropic API compliance
        messages = self._clean_messages_for_anthropic(list(original_messages))
        
        # Add system message if this is the first message (check original count)
        if len(original_messages) == 1:
            system_message = SystemMessage(content="""You are an expert AI code generator powered by Claude Sonnet 4.5.

Your primary capabilities:
- Generate complete, production-ready code from natural language descriptions
- Create entire project structures with multiple files
- Write code in multiple programming languages (Python, JavaScript, TypeScript, Java, etc.)
- Generate unit tests for code
- Analyze and improve existing code
- Create proper project structures with best practices

CRITICAL RULES:
1. When generating code, ALWAYS write it to files using the write_file tool
2. **CRITICAL**: When calling write_file, you MUST provide BOTH parameters:
   - file_path: The path where the file should be written
   - content: The complete file content as a string
   - **NEVER call write_file without the content parameter - this will cause an error**
   - **For README.md files, you MUST write the complete markdown content in the content parameter**
3. For multi-file projects, use create_project_structure or multiple write_file calls
4. Generate complete, runnable code - not just snippets
5. Include proper error handling, documentation, and best practices
6. Use appropriate file paths - default to ./generated_code/ directory
7. When creating projects, organize files in proper directory structures
8. **When creating README.md files, you MUST include the complete README content in the content parameter, not just mention that you'll create it**
9. Generate code that follows language-specific conventions and best practices
10. **ALWAYS provide ALL required parameters when calling any tool** - check tool descriptions carefully
11. **Before calling write_file for README.md, write out the complete markdown content first in your response, then include it in the tool call**

WORKFLOW:
1. Understand the user's requirements
2. Plan the code structure (files, directories, dependencies)
3. **GENERATE THE COMPLETE CODE CONTENT FIRST** (in your response)
4. **THEN** call write_file with BOTH file_path AND content parameters
5. Do NOT call write_file until you have the complete content ready
6. Write files using tools
7. Confirm completion with a summary

IMPORTANT TOOL USAGE PATTERN:
- Step 1: Generate the code content in your response
- Step 2: Call write_file with file_path="path/to/file" AND content="<the complete code you generated>"
- NEVER call write_file without the content parameter - you must have the content ready first

Be helpful, thorough, and generate high-quality, production-ready code.""")
            messages = [system_message] + list(messages)
        
        # Display thinking indicator
        with self.console.status("[bold cyan]🤔 Generating code...", spinner="dots"):
            response = self.llm_with_tools.invoke(messages)
        
        # Display AI response
        if response.content:
            # Convert bullet points to numbered list
            formatted_content = self._format_with_numbers(response.content)
            
            self.console.print(Panel(
                Markdown(formatted_content),
                title="[bold cyan]🤖 Code Generator[/bold cyan]",
                border_style="cyan"
            ))
        
        return {"messages": [response]}
    
    def tool_use(self, state: AgentState) -> dict:
        """Node: Execute tool calls"""
        messages = state.messages
        last_message = messages[-1]
        
        tool_calls = last_message.tool_calls
        tool_messages = []
        
        # Find the last AI response with content (before tool calls)
        last_response_content = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                last_response_content = str(msg.content)
                break
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"].copy() if tool_call.get("args") else {}
            
            # Auto-fix: If write_file is missing content, try to extract it from the response
            if tool_name == "write_file" and ("content" not in tool_args or not tool_args.get("content")):
                file_path = tool_args.get("file_path", "")
                content = ""
                
                if last_response_content and file_path:
                    import re
                    filename = os.path.basename(file_path)
                    is_readme = "README" in filename.upper() or "readme" in filename.lower()
                    
                    # Try to find code blocks in the response
                    code_block_pattern = r'```(?:\w+)?\n(.*?)```'
                    code_blocks = re.findall(code_block_pattern, last_response_content, re.DOTALL)
                    
                    if code_blocks:
                        # Use the last code block (most likely the one for this file)
                        content = code_blocks[-1].strip()
                        self.console.print(f"[yellow]🔧 Auto-extracted content for {filename} from code block[/yellow]")
                    
                    # For README files, try to extract markdown content from the response
                    if not content and is_readme:
                        # Look for markdown content after mentioning the filename or README
                        lines = last_response_content.split('\n')
                        collecting = False
                        collected_lines = []
                        readme_mentions = ['readme', 'documentation', '##', '# ']
                        
                        for i, line in enumerate(lines):
                            # Start collecting if we see README-related keywords or markdown headers
                            if any(mention in line.lower() for mention in readme_mentions) or filename.lower() in line.lower():
                                collecting = True
                            
                            if collecting:
                                # Stop if we hit another code block or tool call mention
                                if '```' in line and collected_lines:
                                    break
                                if 'tool_use' in line or 'write_file' in line:
                                    break
                                collected_lines.append(line)
                        
                        if collected_lines:
                            # Clean up the collected lines
                            content = '\n'.join(collected_lines).strip()
                            # Remove any tool call references
                            content = re.sub(r'tool_use.*?write_file.*?\n', '', content, flags=re.DOTALL)
                            if content:
                                self.console.print(f"[yellow]🔧 Auto-extracted README content for {filename} from response text[/yellow]")
                    
                    # If still no content, try to find content after the filename is mentioned
                    if not content:
                        lines = last_response_content.split('\n')
                        collecting = False
                        collected_lines = []
                        
                        for i, line in enumerate(lines):
                            # Look for filename or code block markers
                            if filename in line or '```' in line:
                                if '```' in line:
                                    collecting = True
                                    continue
                            
                            if collecting:
                                if '```' in line:
                                    break
                                collected_lines.append(line)
                        
                        if collected_lines:
                            content = '\n'.join(collected_lines).strip()
                    
                    # If we found content, add it to tool_args
                    if content:
                        tool_args["content"] = content
                        self.console.print(f"[green]✓ Auto-fixed write_file call for {file_path}[/green]")
                    elif is_readme:
                        # Generate a basic README if content still missing
                        # Extract project info from other files or response
                        project_name = os.path.basename(os.path.dirname(file_path)) if os.path.dirname(file_path) != '.' else "Project"
                        basic_readme = self._generate_basic_readme(project_name, file_path, last_response_content)
                        if basic_readme:
                            tool_args["content"] = basic_readme
                            self.console.print(f"[yellow]🔧 Generated basic README for {filename} (content was missing)[/yellow]")
            
            # Display tool execution
            self.console.print(f"\n[bold yellow]🔧 Executing tool:[/bold yellow] [magenta]{tool_name}[/magenta]")
            self.console.print(f"[dim]Arguments: {list(tool_args.keys())}[/dim]\n")
            
            # Find and execute the tool
            tool = next((t for t in self.tools if t.name == tool_name), None)
            
            if tool:
                try:
                    # Final validation - if still missing content, return error
                    if tool_name == "write_file":
                        if "content" not in tool_args or not tool_args.get("content"):
                            file_path = tool_args.get("file_path", "unknown")
                            error_msg = f"""ERROR: The write_file tool call is missing the required 'content' parameter.

You attempted to call write_file with only: {list(tool_args.keys())}
But write_file REQUIRES both parameters:
1. file_path: "{file_path}" (you provided this ✓)
2. content: <the actual file content as a string> (MISSING ✗)

ACTION REQUIRED: You must call write_file again with BOTH parameters. 
First, generate the file content in your response, then call write_file with:
- file_path: "{file_path}"
- content: "<the complete file content as a string>"

Do not call write_file until you have the complete content ready to write."""
                            self.console.print(f"[bold red]✗ {error_msg}[/bold red]")
                            tool_messages.append(
                                ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_call["id"]
                                )
                            )
                            continue
                    
                    result = tool.invoke(tool_args)
                    
                    # Display tool result
                    self.console.print(Panel(
                        str(result),
                        title=f"[bold green]✓ Tool Result: {tool_name}[/bold green]",
                        border_style="green"
                    ))
                    
                    tool_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call["id"]
                        )
                    )
                except Exception as e:
                    # Provide more helpful error messages
                    error_str = str(e)
                    if "validation error" in error_str.lower() and "required" in error_str.lower():
                        # Extract missing field from Pydantic error
                        if "content" in error_str.lower():
                            error_msg = f"Error: The '{tool_name}' tool requires a 'content' parameter. Please provide the content to write to the file. You called the tool with: {list(tool_args.keys())}. Please try again with all required parameters."
                        else:
                            error_msg = f"Error: The '{tool_name}' tool is missing required parameters. Error: {error_str}. Please provide all required parameters and try again."
                    else:
                        error_msg = f"Tool error in {tool_name}: {error_str}"
                    
                    self.console.print(f"[bold red]✗ {error_msg}[/bold red]")
                    
                    tool_messages.append(
                        ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call["id"]
                        )
                    )
            else:
                error_msg = f"Tool {tool_name} not found"
                self.console.print(f"[bold red]✗ {error_msg}[/bold red]")
                
                tool_messages.append(
                    ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call["id"]
                    )
                )
        
        return {"messages": tool_messages}
    
    def check_tool_use(self, state: AgentState) -> Literal["tool_use", END]:
        """Conditional edge: Check if tools should be used"""
        messages = state.messages
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tool_use"
        return END
    
    async def run(self):
        """Main interactive loop"""
        config = {"configurable": {"thread_id": self.thread_id}}
        
        while True:
            try:
                # Get user input with rich prompt
                self.console.print()
                try:
                    user_input = Prompt.ask(
                        "[bold green]💬 What code would you like to generate?[/bold green] [dim](or type 'help')[/dim]",
                        default=""
                    )
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n[bold cyan]👋 Goodbye![/bold cyan]\n")
                    break
                
                # Skip empty input
                if not user_input or not user_input.strip():
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.console.print("\n[bold cyan]👋 Goodbye![/bold cyan]\n")
                    break
                
                # Special commands
                if user_input.lower() == 'help':
                    self._display_help()
                    continue
                
                if user_input.lower() == 'tools':
                    self._display_tools()
                    continue
                
                # Check if user typed a number to select an option
                if user_input.strip().isdigit() and user_input.strip() in self.last_options:
                    selected_option = self.last_options[user_input.strip()]
                    self.console.print(f"[green]✓ Selected:[/green] {selected_option}\n")
                    user_input = selected_option
                
                # Create human message
                human_message = HumanMessage(content=user_input)
                
                # Invoke the workflow (it will run until END)
                await self.agent.ainvoke(
                    {"messages": [human_message]},
                    config=config
                )
                
            except KeyboardInterrupt:
                self.console.print("\n[bold cyan]👋 Goodbye![/bold cyan]\n")
                break
            except Exception as e:
                import traceback
                self.console.print(f"[bold red]❌ Error: {e}[/bold red]")
                self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
                self.console.print("[yellow]Continuing... Type 'exit' to quit[/yellow]")
    
    def _display_quick_start(self):
        """Display quick start guide on startup"""
        # Set up initial numbered options
        self.last_options = {
            "1": "Generate a Python REST API with FastAPI",
            "2": "Create a React component for a todo list",
            "3": "Build a Python class for database connections",
            "4": "Generate a FastAPI web application with authentication",
            "5": "Create a Python script for data processing"
        }
        
        quick_start = """
[bold cyan]🚀 What would you like to generate?[/bold cyan]

**1.** Generate a Python REST API with FastAPI
**2.** Create a React component for a todo list
**3.** Build a Python class for database connections
**4.** Generate a FastAPI web application with authentication
**5.** Create a Python script for data processing

[dim]Commands: [green]help[/green] | [green]tools[/green] | [green]exit[/green][/dim]
[dim]💡 Type a number (1-5) or describe what you want to generate[/dim]
"""
        self.console.print(Panel(quick_start, border_style="cyan", padding=(1, 2)))
    
    def _display_help(self):
        """Display help information"""
        help_text = """
# 🆘 Help

## Available Commands:
- **help**: Display this help message
- **tools**: List all available tools
- **exit/quit/q**: Exit the generator

## Example Queries:
- "Generate a Python REST API with FastAPI"
- "Create a React component for a todo list"
- "Build a Python class for handling database connections"
- "Generate a complete FastAPI web application with authentication"
- "Create a Python script that processes CSV files"
- "Generate a Node.js Express server with MongoDB integration"

## Tips:
- Be specific about what you want to generate
- You can request entire projects or single files
- Generated code is saved to ./generated_code/ by default
- All interactions are saved in checkpoints.db for debugging
        """
        self.console.print(Panel(
            Markdown(help_text),
            title="[bold cyan]Help[/bold cyan]",
            border_style="cyan"
        ))
    
    def _display_tools(self):
        """Display available tools in a tree structure"""
        tree = Tree("🔧 [bold cyan]Available Tools[/bold cyan]")
        
        # Group tools by type
        code_branch = tree.add("💻 [yellow]Code Generation Tools[/yellow]")
        file_branch = tree.add("📁 [magenta]File Operation Tools[/magenta]")
        
        code_tools = get_code_tools()
        file_tools = get_file_tools()
        
        for tool in self.tools:
            if tool in code_tools:
                code_branch.add(f"[yellow]• {tool.name}[/yellow]: {tool.description}")
            elif tool in file_tools:
                file_branch.add(f"[magenta]• {tool.name}[/magenta]: {tool.description}")
        
        self.console.print(tree)

