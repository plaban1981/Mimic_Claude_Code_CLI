#!/usr/bin/env python3
"""
Main entry point for the AI Code Generator

A powerful code generator using LangGraph and Claude Sonnet 4.5
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from agent import CodeGeneratorAgent
from rich.console import Console

console = Console()


async def main():
    """Main function to run the code generator"""
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[bold red]❌ Error: ANTHROPIC_API_KEY not found![/bold red]")
        console.print("[yellow]Please set your Anthropic API key in .env file[/yellow]")
        console.print("[yellow]Create a .env file and add: ANTHROPIC_API_KEY=your_key_here[/yellow]")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.getenv("OUTPUT_DIR", "./generated_code")
    os.makedirs(output_dir, exist_ok=True)
    console.print(f"[cyan]📁 Output directory: {os.path.abspath(output_dir)}[/cyan]\n")
    
    # Initialize agent
    agent = CodeGeneratorAgent()
    
    try:
        # Async initialization
        await agent.initialize()
        
        # Run the interactive loop
        await agent.run()
        
    except KeyboardInterrupt:
        console.print("\n[bold cyan]👋 Interrupted by user[/bold cyan]")
    except Exception as e:
        console.print(f"[bold red]❌ Fatal error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await agent.cleanup()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())

