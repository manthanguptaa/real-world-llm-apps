#!/usr/bin/env python3
"""
AI Browser Assistant CLI
Command-line interface for browser automation using natural language commands.
"""

import argparse
import os
import time
import signal
import atexit
import sys
import asyncio
import logging
from playwright.async_api import async_playwright
import json

# Import the agent
from agents import BrowserAgent, TaskAgent
from browser_actions import (
    smart_click, select_first_item, click_element_with_text, 
    click_element_with_selector, type_text_in_field, submit_form,
    scroll_page, find_text_on_page, execute_javascript,
    take_screenshot, navigate, search_on_current_site
)
from config import is_known_searchable_site

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Global variables
playwright = None
browser = None
browser_context = None
page = None
agent = None
task_agent = None

def cleanup_resources():
    """Clean up browser resources when the application exits."""
    global browser, playwright, browser_context, page
    
    print("[*] Cleaning up resources...")
    
    # Use asyncio to clean up async resources
    loop = asyncio.get_event_loop()
    if loop.is_running():
        async def cleanup():
            if page:
                try:
                    await page.close()
                except:
                    pass
                
            if browser_context:
                try:
                    await browser_context.close()
                except:
                    pass
                
            if browser:
                try:
                    await browser.close()
                except:
                    pass
                
            if playwright:
                try:
                    await playwright.stop()
                except:
                    pass
                
        future = asyncio.ensure_future(cleanup())
        loop.run_until_complete(future)
    else:
        # If loop is not running, create a new one for cleanup
        async def cleanup():
            if page:
                try:
                    await page.close()
                except:
                    pass
                
            if browser_context:
                try:
                    await browser_context.close()
                except:
                    pass
                
            if browser:
                try:
                    await browser.close()
                except:
                    pass
                
            if playwright:
                try:
                    await playwright.stop()
                except:
                    pass
                
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup())
        loop.close()

# Register cleanup handlers
atexit.register(cleanup_resources)
signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

async def init_playwright():
    """Initialize Playwright."""
    global playwright
    
    try:
        if not playwright:
            print("[*] Initializing Playwright...")
            playwright = await async_playwright().start()
        return True
    except Exception as e:
        print(f"[!] Error initializing Playwright: {str(e)}")
        return False

async def launch_browser(url=None):
    """Launch a browser instance."""
    global playwright, browser, browser_context, page, agent
    
    if url is None:
        url = "https://www.google.com"
        
    try:
        # Check if we already have a browser instance
        if browser:
            # If we have a browser but no page/context, create new ones
            if not page or not browser_context:
                try:
                    # Create a new context and page in the existing browser
                    browser_context = await browser.new_context(viewport={"width": 1280, "height": 800})
                    page = await browser_context.new_page()
                    await page.goto(url)
                    agent.set_browser_objects(page, browser, browser_context)
                    await agent.take_screenshot()
                    return True
                except Exception as e:
                    print(f"[!] Error creating new context in existing browser: {str(e)}. Will try with a new browser.")
                    # Close the existing browser as it might be in an invalid state
                    try:
                        await browser.close()
                    except:
                        pass
                    browser = None
        
        # Make sure Playwright is initialized
        if not await init_playwright():
            return False
            
        # Start a new browser session if needed
        if not browser:
            print(f"[*] Launching new browser window with URL: {url}")
            browser = await playwright.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
        
        # Create a new context and page
        browser_context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await browser_context.new_page()
        await page.goto(url)
        
        # Set up agent if not already set
        if not agent:
            agent = BrowserAgent(page, browser, browser_context)
        else:
            agent.set_browser_objects(page, browser, browser_context)
            
        await agent.take_screenshot()
        return True
    except Exception as e:
        print(f"[!] Error launching browser: {str(e)}")
        return False

# Wrapper function for browser actions
async def process_command_dict(command_dict):
    """Process a command dictionary."""
    global page, agent, browser
    
    if not command_dict or not isinstance(command_dict, dict):
        return False
    
    # Ensure browser is launched when needed
    if not page or not browser:
        if command_dict.get("action") == "navigate":
            print("[*] Launching browser for navigation...")
            if not await launch_browser(command_dict.get("url")):
                print("[!] Failed to launch browser")
                return False
        else:
            print("[*] Launching browser...")
            if not await launch_browser():
                print("[!] Failed to launch browser")
                return False
    
    action = command_dict.get("action")
    
    # Handle different action types
    if action == "navigate":
        return await navigate(page, command_dict.get("url"))
        
    elif action == "navigate_and_search":
        url = command_dict.get("url")
        query = command_dict.get("query")
        
        if await navigate(page, url):
            await asyncio.sleep(2)  # Wait for page to load
            return await search_on_current_site(page, query)
        return False
        
    elif action == "search":
        return await search_on_current_site(page, command_dict.get("query"))
        
    elif action == "back":
        if page:
            await page.go_back()
            await agent.take_screenshot()
            print(f"[*] Navigated back to: {page.url}")
            return True
        return False
        
    elif action == "forward":
        if page:
            await page.go_forward()
            await agent.take_screenshot()
            print(f"[*] Navigated forward to: {page.url}")
            return True
        return False
        
    elif action == "refresh":
        if page:
            await page.reload()
            await agent.take_screenshot()
            print(f"[*] Page refreshed: {page.url}")
            return True
        return False
        
    elif action == "select_first_item":
        return await select_first_item(page, command_dict.get("query_terms"))
        
    elif action == "smart_click":
        return await smart_click(page, command_dict.get("description"))
        
    elif action == "click_selector":
        return await click_element_with_selector(page, command_dict.get("selector"))
        
    elif action == "fill_form":
        return await type_text_in_field(page, command_dict.get("value"), command_dict.get("field"))
        
    elif action == "submit_form":
        return await submit_form(page)
        
    elif action == "scroll":
        return await scroll_page(page, command_dict.get("direction", "down"), command_dict.get("amount", 300))
        
    elif action == "find_text":
        return await find_text_on_page(page, command_dict.get("query"))
        
    elif action == "screenshot":
        return await agent.take_screenshot()
        
    elif action == "analyze":
        return await agent.analyze_with_vision()
        
    elif action == "run_js":
        return await execute_javascript(page, command_dict.get("code"))
        
    elif action == "extract_data":
        # Extract structured data from the page
        try:
            structure = await agent.extract_dom_structure()
            print(f"[*] Extracted data from page")
            print(json.dumps(structure, indent=2))
            return True
        except Exception as e:
            print(f"[!] Error extracting data: {str(e)}")
            return False
            
    elif action == "wait":
        # Wait for an element or timeout
        try:
            selector = command_dict.get("selector")
            if selector:
                await page.wait_for_selector(selector, timeout=command_dict.get("timeout", 30000))
                print(f"[*] Element matching '{selector}' found")
            else:
                await asyncio.sleep(command_dict.get("seconds", 3))
                print(f"[*] Waited for {command_dict.get('seconds', 3)} seconds")
            return True
        except Exception as e:
            print(f"[!] Wait timeout: {str(e)}")
            return False
            
    elif action == "handle_dialog":
        # Set up a dialog handler
        dialog_action = command_dict.get("dialog_action", "accept")
        
        async def handle_dialog(dialog):
            if dialog_action == "accept":
                await dialog.accept(command_dict.get("prompt_text", ""))
            else:
                await dialog.dismiss()
                
        page.on("dialog", handle_dialog)
        print(f"[*] Dialog handler set to {dialog_action}")
        return True
        
    elif action == "exit":
        print("[*] Exiting...")
        sys.exit(0)
        
    elif action == "help":
        print_help()
        return True
        
    elif action == "plan_task":
        return await plan_task(command_dict.get("task"))
        
    elif action == "execute_task":
        return await execute_planned_task()
        
    else:
        print(f"[!] Unknown action: {action}")
        return False

async def process_command(command):
    """Process a command using the agent to interpret it and execute the appropriate action."""
    global page, browser, agent, task_agent
    
    if not command:
        return False
    
    # Handle task planning and execution commands directly
    if command.lower().startswith("plan "):
        task = command[len("plan "):].strip()
        return await plan_task(task)
        
    elif command.lower() in ["execute plan", "run plan", "execute task"]:
        return await execute_planned_task()
    
    # Initialize the browser agent if it doesn't exist
    if not agent:
        agent = BrowserAgent(page, browser, browser_context)
        
    # Let the agent interpret the command
    result = await agent.process_command(command)
    
    if not result:
        print("[!] Could not understand command")
        return False
        
    # Execute the command based on the action type
    return await process_command_dict(result)

def print_help():
    """Print help information."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                       AI BROWSER AGENT                            ║
║                       COMMAND REFERENCE                           ║
╚═══════════════════════════════════════════════════════════════════╝

🧭 NAVIGATION:
  go to <site>                    Navigate to a website
  back / forward / refresh        Basic navigation controls
  
🔍 SEARCHING:
  search for <query>              Search on current website or Google
  on <site> search for <query>    Go to site and search
  find <text>                     Find text on current page
  
🖱️ INTERACTION:
  click "<text>"                  Click element with specific text
  click selector "<css>"          Click element by CSS selector
  select first item               Click first item in results
  type "<text>" in "<field>"      Enter text in a form field
  submit                          Submit the current form
  scroll down/up [amount]         Scroll the page
  
🛠️ TOOLS:
  screenshot                      Take a screenshot
  analyze                         Analyze page with AI vision
  extract data                    Extract structured data
  run js <code>                   Execute JavaScript
  wait <seconds>                  Wait for specified time
  wait for <selector>             Wait for element to appear
  
🤖 AUTONOMOUS MODE:
  plan <task>                     Create a multi-step plan
  execute plan                    Execute current plan
  
💡 TIP: You can use natural language for most commands!

Examples:
  > go to amazon.com and search for wireless headphones
  > click "Add to Cart"
  > analyze
  > plan research the best laptop under $1000 and compare top 3 options
""")

async def plan_task(task):
    """Create a plan for a complex task."""
    global task_agent, agent, page, browser, browser_context
    
    if not task_agent:
        # Initialize task agent if it doesn't exist
        if agent:
            # Use existing browser objects if available
            task_agent = TaskAgent(task, page, browser, browser_context)
        else:
            # Create a fresh task agent
            task_agent = TaskAgent(task)
    else:
        # Update the existing task agent
        task_agent.set_task(task)
        
    # Create the plan
    success = await task_agent.create_plan()
    
    if success:
        # Print the plan
        print("\n[*] Task Plan:")
        print("=" * 50)
        for i, step in enumerate(task_agent.plan):
            print(f"Step {i+1}: {step}")
        print("=" * 50)
        
        print(f"\n[*] Created plan with {len(task_agent.plan)} steps for task: {task}")
        return True
    else:
        print(f"[!] Failed to create plan for task: {task}")
        return False

async def execute_planned_task():
    """Execute the current task plan."""
    global task_agent, page
    
    if not task_agent or not task_agent.plan:
        print("[!] No task plan available. Use 'plan <task>' first.")
        return False
        
    # Make sure we have a browser open
    if not page:
        print("[*] Opening browser for task execution...")
        if not await launch_browser():
            return False
            
    # Update browser objects in the task agent
    task_agent.set_browser_objects(page, browser, browser_context)
    
    # Define a callback to execute each step
    async def step_callback(step):
        action = step.get("action")
        print(f"\n[*] Executing step: {action}")
        
        # Execute the step using the appropriate function
        result = await process_command_dict(step)
        
        # Brief pause between steps
        await asyncio.sleep(1)
        
        return result
    
    # Execute the plan
    return await task_agent.execute_plan(step_callback)

async def main_async():
    """Async main function for the CLI."""
    global agent, task_agent
    
    print("""
╭───────────────────────────────────────────────────────────────────╮
│                                                                   │
│                  🌐 AI BROWSER AGENT 1.0 🤖                       │
│                                                                   │
│          The Next Generation of Intelligent Web Automation        │
│                                                                   │
╰───────────────────────────────────────────────────────────────────╯
    
    🧠 NATURAL LANGUAGE CONTROL  |  👁️  VISION-POWERED ANALYSIS
    🤖 AUTONOMOUS TASK PLANNING  |  🔍 ADVANCED DOM UNDERSTANDING

Type 'help' to see available commands
Type 'analyze' on any page to get AI insights
Type 'plan <task>' to create an autonomous plan
""")
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[!] Warning: OpenAI API key not found. Set the OPENAI_API_KEY environment variable for AI analysis.")
    
    # Initialize the agents
    agent = BrowserAgent()
    task_agent = None  # Will be initialized when needed
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI Browser Agent CLI")
    parser.add_argument("url", nargs="?", help="URL to open on startup")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no browser UI)")
    parser.add_argument("--task", type=str, help="Autonomous task to plan and execute")
    args = parser.parse_args()
    
    # If task is provided, create and execute a plan
    if args.task:
        await plan_task(args.task)
        await launch_browser(args.url or "https://www.google.com")
        await execute_planned_task()
    # Launch browser if URL provided
    elif args.url:
        await launch_browser(args.url)
    
    # Interactive command loop
    try:
        while True:
            command = input("\n> ").strip()
            if not command:
                continue
                
            await process_command(command)
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Exiting...")
        sys.exit(0)

def main():
    """Main function that runs the async event loop."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 