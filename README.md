# 🤖 AI Code Generator

A powerful AI-powered code generator built with **LangGraph** and **Claude Sonnet 4.5**. This application uses the same architectural principles as the Claude Code Assistant, but specialized for generating code from natural language descriptions.

![Code Generator](https://img.shields.io/badge/LangGraph-0.2.0-blue) ![Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-orange)

## ✨ Features

- **StateGraph Workflow**: Clean three-node architecture (user_input → model_response → tool_use)
- **Persistent State**: SQLite-based checkpointing for conversation history
- **Code Generation**: Generate complete projects, files, and code snippets
- **Project Structure**: Create entire project structures with multiple files
- **Rich Terminal UI**: Beautiful, colorful interface with emojis
- **Multi-file Support**: Generate multiple files in a single request
- **Code Analysis**: Analyze and improve existing code

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key
- pip or uv package manager

### Installation

1. **Clone or navigate to the project:**

```bash
cd Code_editor
```

2. **Set up environment variables:**

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Install dependencies:**

```bash
pip install -e .
# or with uv
uv sync
```

4. **Run the code generator:**

```bash
python main.py
# or with uv
uv run main.py
```

## 💻 Usage

Once started, you'll see a colorful terminal interface. Try these commands:

### Basic Commands

```
help          - Display help information
tools         - List all available tools
exit/quit/q   - Exit the generator
```

### Example Queries

```
"Generate a Python REST API with FastAPI"
"Create a React component for a todo list"
"Build a Python class for handling database connections"
"Generate a complete FastAPI web application with authentication"
"Create a Python script that processes CSV files"
"Generate a Node.js Express server with MongoDB integration"
```

## 🛠️ Available Tools

### Code Generation Tools

- **generate_code**: Generate code from natural language description
- **create_project_structure**: Create complete project structures
- **generate_file**: Generate a single file with code
- **analyze_code**: Analyze and suggest improvements for code
- **generate_tests**: Generate unit tests for existing code

### File Operations

- **read_file**: Read file contents
- **write_file**: Write content to a file
- **list_files**: List directory contents
- **create_directory**: Create directory structure
- **search_files**: Search for files by pattern

## 📁 Project Structure

```
code-generator/
├── main.py                 # Entry point
├── agent.py                # Core agent implementation
├── tools/
│   ├── __init__.py
│   ├── code_tools.py       # Code generation tools
│   └── file_tools.py       # File operation tools
├── pyproject.toml          # Dependencies
├── .env.example            # Environment template
└── README.md
```

## 🏗️ Architecture

### StateGraph Flow

1. **User Input**: Collects user requirements/description
2. **Model Response**: Claude Sonnet 4.5 processes the input and decides whether to use tools
3. **Tool Use** (conditional): Executes code generation or file operations
4. **Loop**: Returns to model response with tool results, or back to user input

### Checkpointing

LangGraph's SQLite checkpointer saves the entire conversation state after each step:
- Enables conversation resume after crashes
- Facilitates debugging and analysis
- Supports multi-turn context retention

## 🎨 Customization

### Environment Variables

Create a `.env` file with:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional
OUTPUT_DIR=./generated_code
```

### Adding Custom Tools

To add custom code generation tools, edit `tools/code_tools.py`:

```python
from langchain_core.tools import tool

@tool
def my_custom_generator(description: str) -> str:
    """Generate code based on description"""
    # Your implementation
    return generated_code

# Add to get_code_tools()
```

## 🔒 Security Considerations

- **File Access**: Generated files are saved to the specified output directory
- **API Keys**: Never commit `.env` files. Use environment variables.
- **Code Execution**: Generated code is not automatically executed
- **Review**: Always review generated code before use

## 📚 Examples

### Generate a Simple Python Script

```
User: "Create a Python script that reads a JSON file and prints all keys"

Assistant: [Generates the script and saves it]
```

### Generate a Complete Project

```
User: "Generate a FastAPI application with user authentication, database models, and CRUD operations"

Assistant: [Creates project structure with multiple files]
```

### Multi-file Generation

```
User: "Create a Python package with a main module, utils module, and tests"

Assistant: [Generates all files in proper structure]
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add support for more programming languages
- [ ] Implement code templates and patterns
- [ ] Add code quality checks
- [ ] Support for project scaffolding
- [ ] Integration with version control
- [ ] Web UI interface

## 📖 Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Anthropic Claude API](https://www.anthropic.com/api)
- [Rich Terminal Library](https://github.com/Textualize/rich)

---

**Happy Coding! 🚀**

