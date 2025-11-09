# 🧪 Testing Guide

## Prerequisites Check

Before testing, ensure you have:

1. ✅ Python 3.11+ installed
2. ✅ Dependencies installed
3. ✅ `.env` file with `ANTHROPIC_API_KEY` set

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or if using `uv`:

```bash
uv sync
```

## Step 2: Verify Environment

Check that your `.env` file exists and has the API key:

```bash
# On Windows PowerShell
Get-Content .env

# On Linux/Mac
cat .env
```

You should see:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
OUTPUT_DIR=./generated_code
```

## Step 3: Run the Application

```bash
python main.py
```

You should see:
- Welcome banner
- Tool loading messages
- Checkpoint database initialization
- Quick start menu

## Step 4: Basic Test Commands

### Test 1: Simple Code Generation

When prompted, type:
```
Create a Python function that calculates the factorial of a number
```

Expected: The agent should generate code and save it to a file.

### Test 2: Quick Start Option

Type `1` to select the first quick start option:
```
1
```

Expected: Should generate a FastAPI REST API.

### Test 3: Help Command

Type:
```
help
```

Expected: Should display help information.

### Test 4: Tools Command

Type:
```
tools
```

Expected: Should list all available tools.

### Test 5: Exit

Type:
```
exit
```

Expected: Should gracefully exit the application.

## Step 5: Verify Generated Code

After generating code, check the output directory:

```bash
# On Windows PowerShell
Get-ChildItem generated_code -Recurse

# On Linux/Mac
ls -la generated_code/
```

You should see generated files in the `generated_code/` directory.

## Step 6: Check Checkpoint Database

The application creates a checkpoint database:

```bash
# On Windows PowerShell
Test-Path code_generator_checkpoints.db

# On Linux/Mac
ls code_generator_checkpoints.db
```

This database stores conversation history.

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"
- Check that `.env` file exists in the project root
- Verify the API key is correctly set
- Restart the application

### Error: "ModuleNotFoundError"
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.11+)

### Error: "Model not found"
- Verify your API key has access to Claude Sonnet 4.5
- Check your Anthropic account status

### Application hangs
- Check your internet connection
- Verify API key is valid
- Check Anthropic API status

## Advanced Testing

### Test Multi-file Project Generation

```
Generate a FastAPI application with user authentication, database models, and CRUD operations
```

### Test Code Analysis

First, create a test file, then:
```
Analyze the code in test_file.py and suggest improvements
```

### Test Test Generation

First, create a Python file, then:
```
Generate pytest unit tests for my_file.py
```

## Expected Behavior

✅ Application starts without errors
✅ Welcome banner displays
✅ Tools load successfully
✅ Can generate code from natural language
✅ Files are saved to `generated_code/` directory
✅ Checkpoint database is created
✅ Can exit gracefully with `exit` or `quit`

## Performance Notes

- First API call may take a few seconds
- Code generation typically takes 5-15 seconds depending on complexity
- Multi-file projects may take longer

