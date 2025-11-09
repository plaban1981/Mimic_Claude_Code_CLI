"""
Code generation tools for the code generator
"""
import os
import json
from typing import List, Dict, Any
from langchain_core.tools import tool


@tool
def generate_code(description: str, language: str = "python", file_path: str = None) -> str:
    """
    Generate code from a natural language description.
    
    Args:
        description: Natural language description of what code to generate
        language: Programming language (default: "python")
        file_path: Optional file path where the code should be saved
    
    Returns:
        Generated code as a string
    """
    # This tool is primarily used to signal the LLM to generate code
    # The actual generation happens in the model_response node
    # This tool provides structure for the LLM to understand code generation requests
    
    return f"Code generation requested for: {description}\nLanguage: {language}\nFile: {file_path or 'Not specified'}"


@tool
def create_project_structure(project_name: str, structure: str) -> str:
    """
    Create a complete project structure with multiple files and directories.
    
    Args:
        project_name: Name of the project
        structure: JSON string describing the project structure with files and their content
    
    Returns:
        Success message with created files
    """
    try:
        # Parse structure JSON
        if isinstance(structure, str):
            structure_data = json.loads(structure)
        else:
            structure_data = structure
        
        # Get output directory
        output_dir = os.getenv("OUTPUT_DIR", "./generated_code")
        project_path = os.path.join(output_dir, project_name)
        
        # Create project directory
        os.makedirs(project_path, exist_ok=True)
        
        created_files = []
        
        # Create files and directories
        def create_item(path: str, item: Dict[str, Any]):
            full_path = os.path.join(project_path, path)
            
            if item.get("type") == "directory":
                os.makedirs(full_path, exist_ok=True)
                created_files.append(f"📁 {path}/")
                
                # Create sub-items
                for sub_name, sub_item in item.get("items", {}).items():
                    create_item(os.path.join(path, sub_name), sub_item)
            else:
                # It's a file
                content = item.get("content", "")
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created_files.append(f"📄 {path}")
        
        # Process structure
        for item_name, item_data in structure_data.items():
            create_item(item_name, item_data)
        
        return f"✓ Created project '{project_name}' with {len(created_files)} items:\n\n" + "\n".join(created_files)
    
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON structure - {str(e)}"
    except Exception as e:
        return f"Error creating project structure: {str(e)}"


@tool
def generate_file(file_path: str, description: str, language: str = "python") -> str:
    """
    Generate a single file with code based on a description.
    
    Args:
        file_path: Path where the file should be created
        description: Description of what the file should contain
        language: Programming language (default: "python")
    
    Returns:
        Success message
    """
    # This tool signals the LLM to generate code for a specific file
    # The actual code generation happens in the model_response node
    
    return f"File generation requested:\nPath: {file_path}\nDescription: {description}\nLanguage: {language}"


@tool
def analyze_code(file_path: str) -> str:
    """
    Analyze existing code and provide suggestions for improvement.
    
    Args:
        file_path: Path to the code file to analyze
    
    Returns:
        Analysis and suggestions
    """
    try:
        # Read the file
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Return the code for analysis by the LLM
        return f"Code from {file_path}:\n\n{content}\n\nPlease analyze this code and provide suggestions."
    
    except Exception as e:
        return f"Error analyzing code: {str(e)}"


@tool
def generate_tests(file_path: str, test_framework: str = "pytest") -> str:
    """
    Generate unit tests for an existing code file.
    
    Args:
        file_path: Path to the code file to generate tests for
        test_framework: Testing framework to use (default: "pytest")
    
    Returns:
        Success message or code content for test generation
    """
    try:
        # Read the file
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Return the code for test generation by the LLM
        return f"Generate {test_framework} tests for this code:\n\n{content}"
    
    except Exception as e:
        return f"Error generating tests: {str(e)}"


def get_code_tools() -> List:
    """Return list of all code generation tools"""
    return [
        generate_code,
        create_project_structure,
        generate_file,
        analyze_code,
        generate_tests,
    ]

