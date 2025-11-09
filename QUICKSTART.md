# 🚀 Quick Start Guide

## Installation

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

Or using `uv`:

```bash
uv sync
```

2. **Set up environment:**

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=your_api_key_here
OUTPUT_DIR=./generated_code
```

3. **Run the code generator:**

```bash
python main.py
```

## First Steps

When you start the application, you'll see a welcome screen with example options. You can:

1. **Type a number (1-5)** to select a quick example
2. **Describe what you want** in natural language
3. **Type `help`** for more information
4. **Type `tools`** to see available tools

## Example Queries

### Simple Code Generation

```
💬 What code would you like to generate?
> Create a Python function that calculates the factorial of a number
```

### Complete Project

```
💬 What code would you like to generate?
> Generate a FastAPI REST API with user authentication, database models, and CRUD operations
```

### Multiple Files

```
💬 What code would you like to generate?
> Create a Python package with a main module, utils module, and unit tests
```

## Output Location

Generated code is saved to `./generated_code/` by default (or the directory specified in `OUTPUT_DIR` environment variable).

## Tips

- Be specific about what you want to generate
- You can request entire projects or single files
- The generator remembers context within a session
- All conversations are saved in `code_generator_checkpoints.db`

## Troubleshooting

### API Key Error

If you see "ANTHROPIC_API_KEY not found":
1. Make sure you created a `.env` file
2. Check that the API key is correctly set
3. Restart the application

### Import Errors

If you see import errors:
```bash
pip install -r requirements.txt
```

### Model Not Found

If you see model errors, check that you're using a valid Anthropic API key with access to Claude Sonnet 4.5.

