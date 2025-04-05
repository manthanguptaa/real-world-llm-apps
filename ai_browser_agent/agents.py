#!/usr/bin/env python3
"""
AI Browser Assistant - Agents Module
Provides agent functionality for browser automation using natural language processing.
"""

import os
import re
import time
import base64
import io
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import Page, Browser, BrowserContext

from config import (
    is_known_searchable_site,
    get_search_selector,
    get_search_button_selector,
    get_first_item_selectors,
    COMMAND_PATTERNS
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserAgent:
    """Agent that can interpret natural language commands for browser automation."""
    
    def __init__(self, page=None, browser=None, browser_context=None):
        """Initialize the agent with browser objects."""
        self.page = page
        self.browser = browser
        self.browser_context = browser_context
        self.last_screenshot = None
        self.last_html = None
        self.memory = []
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
    def set_browser_objects(self, page, browser=None, browser_context=None):
        """Set the browser objects for this agent."""
        self.page = page
        self.browser = browser
        self.browser_context = browser_context
    
    def add_to_memory(self, step_info: Dict[str, Any]) -> None:
        """Add a step to the agent's memory."""
        self.memory.append(step_info)
        # Limit memory size to prevent token issues
        if len(self.memory) > 20:
            # Keep first steps and most recent ones
            self.memory = self.memory[:5] + self.memory[-15:]
        
    def get_memory_summary(self) -> str:
        """Generate a summary of the agent's memory for context."""
        if not self.memory:
            return "No previous actions."
            
        summary = "Previous actions:\n"
        for i, step in enumerate(self.memory):
            if "action" in step:
                details = ""
                if "url" in step:
                    details += f" URL: {step['url']}"
                if "query" in step:
                    details += f" Query: \"{step['query']}\""
                if "description" in step:
                    details += f" Target: \"{step['description']}\""
                
                summary += f"{i+1}. {step['action'].replace('_', ' ').title()}{details}\n"
        
        return summary
        
    async def take_screenshot(self, save_to_file=True):
        """Take a screenshot of the current page asynchronously."""
        if not self.page:
            logger.error("Browser not open")
            return False
            
        try:
            screenshot_bytes = await self.page.screenshot()
            self.last_screenshot = Image.open(io.BytesIO(screenshot_bytes))
            
            # Also capture HTML for context
            try:
                self.last_html = await self.page.content()
            except Exception as e:
                logger.error(f"Error capturing HTML: {str(e)}")
                self.last_html = None
            
            # Extract DOM structure for better context
            try:
                self.last_dom_structure = await self.extract_dom_structure()
            except Exception as e:
                logger.error(f"Error extracting DOM structure: {str(e)}")
                self.last_dom_structure = None
            
            if save_to_file:
                # Save screenshot to file
                timestamp = int(time.time())
                screenshots_dir = Path("screenshots")
                screenshots_dir.mkdir(exist_ok=True)
                
                filename = screenshots_dir / f"screenshot_{timestamp}.png"
                self.last_screenshot.save(filename)
                logger.info(f"Screenshot saved to: {filename}")
                
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return False
    
    async def extract_dom_structure(self) -> Dict[str, Any]:
        """Extract key elements from the DOM for better context."""
        if not self.page:
            return {}
            
        try:
            # Extract main structural elements
            structure = {}
            
            # Get page metadata
            structure["metadata"] = {
                "url": self.page.url,
                "title": await self.page.title()
            }
            
            # Extract all buttons and links with their text
            buttons_js = """
            Array.from(document.querySelectorAll('button, [role="button"], .btn, input[type="button"], input[type="submit"]'))
            .map(el => {
                return {
                    text: el.innerText || el.textContent || el.value || '',
                    visible: el.offsetParent !== null,
                    disabled: el.disabled || false,
                    location: {
                        x: el.getBoundingClientRect().x,
                        y: el.getBoundingClientRect().y
                    }
                }
            }).filter(b => b.text.trim() !== '')
            """
            structure["buttons"] = await self.page.evaluate(buttons_js)
            
            # Extract all links with their text and href
            links_js = """
            Array.from(document.querySelectorAll('a[href]'))
            .map(el => {
                return {
                    text: el.innerText || el.textContent || '',
                    href: el.href,
                    visible: el.offsetParent !== null,
                    location: {
                        x: el.getBoundingClientRect().x,
                        y: el.getBoundingClientRect().y
                    }
                }
            }).filter(l => l.text.trim() !== '')
            """
            structure["links"] = await self.page.evaluate(links_js)
            
            # Extract all form fields
            fields_js = """
            Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea, select'))
            .map(el => {
                const label = el.labels && el.labels.length > 0 
                    ? el.labels[0].innerText || el.labels[0].textContent 
                    : '';
                return {
                    type: el.type || el.tagName.toLowerCase(),
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    label: label,
                    value: el.value || '',
                    visible: el.offsetParent !== null,
                    disabled: el.disabled || false
                }
            })
            """
            structure["form_fields"] = await self.page.evaluate(fields_js)
            
            # Extract main content sections
            sections_js = """
            Array.from(document.querySelectorAll('main, [role="main"], article, section, .content, #content, .main, #main'))
            .map(el => {
                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    classes: Array.from(el.classList).join(' '),
                    text_sample: (el.innerText || el.textContent || '').substring(0, 100) + '...',
                    children_count: el.children.length
                }
            })
            """
            structure["content_sections"] = await self.page.evaluate(sections_js)
            
            # Extract navigation elements
            nav_js = """
            Array.from(document.querySelectorAll('nav, [role="navigation"], .nav, #nav, .navigation, #navigation, .menu, #menu'))
            .map(el => {
                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    classes: Array.from(el.classList).join(' '),
                    items: Array.from(el.querySelectorAll('a, button')).map(item => item.innerText || item.textContent || '').filter(text => text.trim() !== '')
                }
            })
            """
            structure["navigation"] = await self.page.evaluate(nav_js)
            
            return structure
            
        except Exception as e:
            logger.error(f"Error extracting DOM structure: {str(e)}")
            return {}
    
    async def extract_main_content(self) -> str:
        """Extract the main content text from the page using heuristics."""
        if not self.page or not self.last_html:
            return ""
            
        try:
            # Parse the HTML
            soup = BeautifulSoup(self.last_html, 'html.parser')
            
            # Remove script, style, and hidden elements
            for element in soup(['script', 'style', 'head', 'header', 'footer', '[style*="display:none"]', '[style*="display: none"]']):
                element.decompose()
            
            # Look for main content areas in priority order
            for selector in ['main', '[role="main"]', 'article', '#content', '.content', '#main', '.main', 'section']:
                main_content = soup.select(selector)
                if main_content:
                    return main_content[0].get_text(separator='\n', strip=True)
            
            # Fall back to body content if no main content area found
            return soup.body.get_text(separator='\n', strip=True)
            
        except Exception as e:
            logger.error(f"Error extracting main content: {str(e)}")
            return ""
    
    async def analyze_with_vision(self):
        """Analyze the current page with OpenAI's Vision API."""
        if not self.last_screenshot:
            logger.error("No screenshot available")
            if self.page:
                await self.take_screenshot()
            else:
                return False
                
        try:
            # Get API key
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.error("OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
                return False
                
            # Get page metadata for context
            page_metadata = {}
            if self.page:
                try:
                    page_metadata = {
                        "url": self.page.url,
                        "title": await self.page.title()
                    }
                except:
                    pass
            
            # Convert image to base64
            buffered = io.BytesIO()
            self.last_screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Extract DOM structure information
            dom_info = ""
            dom_structure = await self.extract_dom_structure() if self.page else {}
            if dom_structure:
                # Format key interactive elements
                if "buttons" in dom_structure and dom_structure["buttons"]:
                    dom_info += "\nButtons on the page:\n"
                    for i, btn in enumerate(dom_structure["buttons"][:10]):  # Limit to 10 buttons
                        dom_info += f"- {btn['text']} {'(disabled)' if btn['disabled'] else ''}\n"
                
                if "links" in dom_structure and dom_structure["links"]:
                    dom_info += "\nKey links:\n"
                    for i, link in enumerate(dom_structure["links"][:10]):  # Limit to 10 links
                        dom_info += f"- {link['text']} ({link['href']})\n"
                
                if "form_fields" in dom_structure and dom_structure["form_fields"]:
                    dom_info += "\nForm fields:\n"
                    for i, field in enumerate(dom_structure["form_fields"][:10]):  # Limit to 10 fields
                        field_desc = field['label'] or field['placeholder'] or field['name'] or field['id']
                        dom_info += f"- {field_desc} ({field['type']})\n"
            
            # Extract main content text
            main_content = await self.extract_main_content() if self.last_html else ""
            content_snippet = main_content[:1000] + "..." if len(main_content) > 1000 else main_content
            
            # Prepare prompt with enhanced context
            prompt = """
You are an AI browser assistant analyzing a webpage screenshot.

Please provide a detailed analysis of the page in the following structured format:

## Page Summary
[Brief overview of what this page is about and its purpose]

## Key Elements
- [List the most important UI elements visible, like navigation, search bars, etc.]

## Content Analysis
[Analyze the main content of the page]

## Possible Actions
[List actionable steps a user could take on this page, in order of relevance]

## Recommended Next Steps
[What would be the most logical next action(s) for a user based on the page context?]

Your analysis should help a user understand what they're looking at and what they can do next.
"""
            
            if page_metadata:
                prompt += f"\n\nPage URL: {page_metadata.get('url')}"
                prompt += f"\nPage Title: {page_metadata.get('title')}"
            
            if dom_info:
                prompt += f"\n\n{dom_info}"
                
            if content_snippet:
                prompt += f"\n\nContent extract:\n{content_snippet}"
                
            # Memory summary for context
            memory_summary = self.get_memory_summary()
            if memory_summary:
                prompt += f"\n\n{memory_summary}"
                
            # Initialize OpenAI client
            client = self.client
            
            logger.info("Analyzing page with OpenAI Vision API...")
            
            # Call the API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a highly observant website analyzer that provides detailed, structured analysis of web pages."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_str}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            # Print analysis
            analysis = response.choices[0].message.content
            print("\n[*] AI Analysis:")
            print("=" * 50)
            print(analysis)
            print("=" * 50)
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing with AI: {str(e)}")
            return False
    
    async def create_task_plan(self, task: str) -> List[Dict[str, Any]]:
        """
        Generate a plan for completing a complex task using OpenAI.
        
        Args:
            task: The high-level task description
            
        Returns:
            A list of step dictionaries representing the plan
        """
        try:
            # Construct the prompt for planning
            prompt = f"""
You are an expert browser automation planner. Your job is to break down complex web tasks into specific, executable steps.

TASK: {task}

Create a detailed step-by-step plan that will accomplish this task efficiently. For each step, specify:
1. The exact action to take
2. Any parameters needed for that action
3. A brief explanation of why this step is necessary

Be specific and precise. Consider the most direct path to accomplish the task, but also include necessary verification steps.

Available actions:
- "navigate": Go to a specific URL
  Parameters: "url" (string)

- "navigate_and_search": Go to a site and search for something
  Parameters: "url" (string), "query" (string)

- "search": Search on the current site
  Parameters: "query" (string)

- "back": Go back one page
- "forward": Go forward one page
- "refresh": Refresh the current page

- "select_first_item": Click on the first item in search results
  Parameters: "query_terms" (optional string to filter results)

- "smart_click": Click on an element described in natural language
  Parameters: "description" (string)

- "click_selector": Click on an element matching a CSS selector
  Parameters: "selector" (string)

- "fill_form": Fill in a form field
  Parameters: "field" (string, the label/placeholder/name), "value" (string)

- "submit_form": Submit the current form

- "scroll": Scroll the page
  Parameters: "direction" ("up" or "down"), "amount" (optional pixel amount)

- "find_text": Find text on the page
  Parameters: "query" (string)

- "screenshot": Take a screenshot

- "analyze": Analyze the current page with AI

- "extract_data": Extract structured data from the current page

- "wait": Wait for a specific element or condition
  Parameters: "selector" (string) or "seconds" (integer)

- "handle_dialog": Handle browser dialogs (alerts, confirms, prompts)
  Parameters: "dialog_action" ("accept" or "dismiss"), "prompt_text" (optional string)

Return a JSON array of steps, where each step has an "action" property and any required parameters for that action.
Also include a "description" property for each step that explains its purpose.
"""

            # Get the plan from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a browser automation expert that outputs detailed, practical plans in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            # Parse the response
            result = response.choices[0].message.content
            
            # The result should be a JSON string
            plan_data = json.loads(result)
            
            # Extract the plan array
            if "plan" in plan_data:
                plan = plan_data["plan"]
            elif "steps" in plan_data:
                plan = plan_data["steps"]
            else:
                plan = plan_data
            
            if not isinstance(plan, list):
                logger.error("Plan is not a list")
                return []
            
            logger.info(f"Generated plan with {len(plan)} steps")
            for i, step in enumerate(plan):
                logger.info(f"Step {i+1}: {step}")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating task plan: {str(e)}")
            return []

    async def refine_plan_step(self, step: Dict[str, Any], page_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine a plan step based on the current page state.
        
        Args:
            step: The original plan step
            page_info: Information about the current page
            
        Returns:
            An updated step with more specific details
        """
        try:
            # Capture the current page state
            current_url = page_info.get("url", "")
            page_title = page_info.get("title", "")
            
            # Get DOM structure for context if we have a page
            dom_info = ""
            dom_structure = await self.extract_dom_structure() if self.page else {}
            if dom_structure:
                # Format key interactive elements
                if "buttons" in dom_structure and dom_structure["buttons"]:
                    dom_info += "\nButtons on the page:\n"
                    for i, btn in enumerate(dom_structure["buttons"][:10]):  # Limit to 10 buttons
                        dom_info += f"- {btn['text']} {'(disabled)' if btn['disabled'] else ''}\n"
                
                if "links" in dom_structure and dom_structure["links"]:
                    dom_info += "\nKey links:\n"
                    for i, link in enumerate(dom_structure["links"][:10]):  # Limit to 10 links
                        dom_info += f"- {link['text']} ({link['href']})\n"
                
                if "form_fields" in dom_structure and dom_structure["form_fields"]:
                    dom_info += "\nForm fields:\n"
                    for i, field in enumerate(dom_structure["form_fields"][:10]):  # Limit to 10 fields
                        field_desc = field['label'] or field['placeholder'] or field['name'] or field['id']
                        dom_info += f"- {field_desc} ({field['type']})\n"
            
            # Construct a prompt for refining the step
            prompt = f"""
You are an expert in browser automation. Your task is to refine a planned action based on the current state of the webpage.

## Current Page Information
- URL: {current_url}
- Title: {page_title}

## Interactive Elements
{dom_info}

## Original Planned Step
```
{json.dumps(step, indent=2)}
```

## Instructions
1. Review the original planned step and the current state of the webpage.
2. Refine the step to be more specific and accurate based on what's actually on the page.
3. For click actions, try to identify the exact text or selector that would be most reliable.
4. For form actions, ensure the field identifiers match what's on the page.
5. If the planned step is impossible given the current page state, adapt it to achieve the same goal.
6. Keep the same action type if possible, but you can change it if necessary.

Return a refined step as a JSON object that includes the action and any necessary parameters, plus a brief explanation of your refinements.
"""

            # Get the refined step from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise browser automation expert that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=800
            )
            
            # Parse the response
            result = response.choices[0].message.content
            refined_step = json.loads(result)
            
            logger.info(f"Original step: {step}")
            logger.info(f"Refined step: {refined_step}")
            
            # Add explanation if available
            if "explanation" in refined_step:
                logger.info(f"Refinement explanation: {refined_step.get('explanation')}")
                # Remove explanation from step definition to avoid confusion in execution
                if "explanation" in refined_step:
                    explanation = refined_step.pop("explanation")
            
            return refined_step
            
        except Exception as e:
            logger.error(f"Error refining plan step: {str(e)}")
            return step  # Return the original step if refinement fails
    
    async def process_command(self, command):
        """Process a natural language command."""
        if not command:
            return False
            
        command = command.lower().strip()
        
        # Parse "go to X and search for Y" format
        go_to_and_search_match = re.match(r"go\s+to\s+([a-z0-9.-]+)(?:\.com|\.org|\.net|\.in|\.co|\.io)?\s+and\s+search\s+for\s+(.*)", command)
        if go_to_and_search_match:
            site_name = go_to_and_search_match.group(1)
            search_query = go_to_and_search_match.group(2).strip()
            
            # Construct the URL based on the site name
            site_url = f"https://{site_name}.com"
            
            # Check if the site_name already contains a domain suffix
            if "." in site_name:
                site_url = f"https://{site_name}"
            # Otherwise apply the appropriate domain
            elif ".in" in go_to_and_search_match.group(0):
                site_url = f"https://{site_name}.in"
            elif ".co.uk" in go_to_and_search_match.group(0):
                site_url = f"https://{site_name}.co.uk"
            elif ".co" in go_to_and_search_match.group(0):
                site_url = f"https://{site_name}.co"
            
            result = {
                "action": "navigate_and_search",
                "url": site_url,
                "query": search_query
            }
            self.add_to_memory(result)
            return result
        
        # Parse "on X search for Y" format
        on_site_search_match = re.match(r"on\s+([a-z0-9.-]+)(?:\.com|\.org|\.net|\.in|\.co|\.io)?\s+search\s+for\s+(.*)", command)
        if on_site_search_match:
            site_name = on_site_search_match.group(1)
            search_query = on_site_search_match.group(2).strip()
            
            # Construct URL
            site_url = f"https://{site_name}.com"
            
            # Check if the site_name already contains a domain suffix
            if "." in site_name:
                site_url = f"https://{site_name}"
            # Apply the appropriate domain
            elif ".in" in on_site_search_match.group(0):
                site_url = f"https://{site_name}.in"
            elif ".co.uk" in on_site_search_match.group(0):
                site_url = f"https://{site_name}.co.uk"
            elif ".co" in on_site_search_match.group(0):
                site_url = f"https://{site_name}.co"
            
            result = {
                "action": "navigate_and_search",
                "url": site_url,
                "query": search_query
            }
            self.add_to_memory(result)
            return result
        
        # Search command
        search_match = re.match(r"(search|find)\s+(?:for\s+)?(.*)", command)
        if search_match:
            query = search_match.group(2).strip()
            
            # Check if we're already on a searchable site
            search_on_current = False
            
            if self.page:
                current_url = self.page.url.lower()
                search_on_current = any(site in current_url for site in is_known_searchable_site(current_url))
            
            if search_on_current:
                result = {
                    "action": "search",
                    "query": query
                }
            else:
                # Default to Google search
                result = {
                    "action": "navigate",
                    "url": f"https://www.google.com/search?q={'+'.join(query.split())}"
                }
                
            self.add_to_memory(result)
            return result
            
        # Open/go to URL command
        open_match = re.match(r"(open|go\s+to)\s+(.*)", command)
        if open_match:
            url = open_match.group(2).strip()
            
            # If it's just a domain without http://, add https://
            if not url.startswith(("http://", "https://")):
                # Check if it has a TLD
                if not any(url.endswith(tld) for tld in [".com", ".org", ".net", ".io", ".gov", ".edu", ".co", ".in"]):
                    # If no TLD, assume .com
                    if "." not in url:
                        url = f"{url}.com"
                url = f"https://{url}"
                
            result = {
                "action": "navigate",
                "url": url
            }
            self.add_to_memory(result)
            return result
            
        # Navigation commands
        if command in ["back", "go back"]:
            result = {"action": "back"}
            self.add_to_memory(result)
            return result
            
        if command in ["forward", "go forward"]:
            result = {"action": "forward"}
            self.add_to_memory(result)
            return result
            
        if command in ["refresh", "reload"]:
            result = {"action": "refresh"}
            self.add_to_memory(result)
            return result
            
        # Click commands
        click_match = re.match(r"click\s+(?:on\s+)?(?:the\s+)?(?:button\s+)?(?:link\s+)?(?:with\s+text\s+)?[\"']?([^\"']+)[\"']?", command)
        if click_match:
            text = click_match.group(1).strip()
            result = {
                "action": "smart_click",
                "description": text
            }
            self.add_to_memory(result)
            return result
            
        # Click selector
        click_selector_match = re.match(r"click\s+(?:on\s+)?(?:the\s+)?(?:element\s+with\s+)?(?:selector|css)\s+[\"']?([^\"']+)[\"']?", command)
        if click_selector_match:
            selector = click_selector_match.group(1).strip()
            result = {
                "action": "click_selector",
                "selector": selector
            }
            self.add_to_memory(result)
            return result
            
        # Select first item
        select_first_match = re.match(r"select\s+(?:the\s+)?first\s+(?:item|result)(?:\s+with\s+(.+))?", command)
        if select_first_match:
            terms = select_first_match.group(1).strip() if select_first_match.group(1) else None
            result = {
                "action": "select_first_item",
                "query_terms": terms
            }
            self.add_to_memory(result)
            return result
            
        # Type text in field
        type_match = re.match(r"type\s+[\"']?([^\"']+)[\"']?\s+in(?:to)?\s+(?:the\s+)?[\"']?([^\"']+)[\"']?(?:\s+field)?", command)
        if type_match:
            text = type_match.group(1).strip()
            field = type_match.group(2).strip()
            result = {
                "action": "fill_form",
                "value": text,
                "field": field
            }
            self.add_to_memory(result)
            return result
            
        # Submit form
        if re.match(r"submit(?:\s+form)?", command):
            result = {"action": "submit_form"}
            self.add_to_memory(result)
            return result
            
        # Scroll commands
        scroll_match = re.match(r"scroll\s+(up|down)(?:\s+(\d+))?", command)
        if scroll_match:
            direction = scroll_match.group(1)
            amount = int(scroll_match.group(2)) if scroll_match.group(2) else 300
            result = {
                "action": "scroll",
                "direction": direction,
                "amount": amount
            }
            self.add_to_memory(result)
            return result
            
        # Find text
        find_text_match = re.match(r"find\s+(?:text\s+)?[\"']?([^\"']+)[\"']?(?:\s+on\s+(?:the\s+)?page)?", command)
        if find_text_match:
            text = find_text_match.group(1).strip()
            result = {
                "action": "find_text",
                "query": text
            }
            self.add_to_memory(result)
            return result
            
        # Screenshot
        if command in ["screenshot", "take screenshot", "capture"]:
            result = {"action": "screenshot"}
            self.add_to_memory(result)
            return result
            
        # Analyze
        if command in ["analyze", "analyze page", "what's on this page", "what is on this page"]:
            result = {"action": "analyze"}
            self.add_to_memory(result)
            return result
            
        # Run JavaScript
        js_match = re.match(r"(?:run|execute)\s+(?:js|javascript)\s+(.+)", command)
        if js_match:
            code = js_match.group(1).strip()
            result = {
                "action": "run_js",
                "code": code
            }
            self.add_to_memory(result)
            return result
            
        # Extract data
        if command in ["extract data", "extract info", "get data", "extract"]:
            result = {"action": "extract_data"}
            self.add_to_memory(result)
            return result
            
        # Wait commands
        wait_for_match = re.match(r"wait\s+for\s+(.+)", command)
        if wait_for_match:
            selector = wait_for_match.group(1).strip()
            result = {
                "action": "wait",
                "selector": selector
            }
            self.add_to_memory(result)
            return result
            
        wait_seconds_match = re.match(r"wait\s+(\d+)(?:\s+seconds)?", command)
        if wait_seconds_match:
            seconds = int(wait_seconds_match.group(1))
            result = {
                "action": "wait",
                "seconds": seconds
            }
            self.add_to_memory(result)
            return result
            
        # Dialog handling
        dialog_match = re.match(r"(accept|dismiss|handle)\s+(?:the\s+)?(dialog|alert|popup)(?:\s+with\s+text\s+[\"']?([^\"']+)[\"']?)?", command)
        if dialog_match:
            action = dialog_match.group(1).lower()
            text = dialog_match.group(3).strip() if dialog_match.group(3) else ""
            
            dialog_action = "accept" if action == "accept" else "dismiss"
            
            result = {
                "action": "handle_dialog",
                "dialog_action": dialog_action,
                "prompt_text": text
            }
            self.add_to_memory(result)
            return result
            
        # Exit command
        if command in ["exit", "quit", "close"]:
            return {"action": "exit"}
            
        # Help command
        if command in ["help", "commands", "usage"]:
            return {"action": "help"}
            
        # Could not interpret command
        return False


class TaskAgent(BrowserAgent):
    """Enhanced agent that can plan and execute autonomous tasks."""
    
    def __init__(self, task=None, page=None, browser=None, browser_context=None):
        """Initialize with an optional task."""
        super().__init__(page, browser, browser_context)
        self.task = task
        self.plan = []
        self.current_step = 0
        self.max_steps = 30
        
    def set_task(self, task):
        """Set a new task for the agent."""
        self.task = task
        self.plan = []
        self.current_step = 0
        
    async def create_plan(self):
        """Create a plan for the current task."""
        if not self.task:
            logger.error("No task specified")
            return False
            
        self.plan = await self.create_task_plan(self.task)
        return len(self.plan) > 0
        
    async def get_next_step(self):
        """Get the next step in the plan."""
        if not self.plan or self.current_step >= len(self.plan):
            return None
            
        # Get the current step
        step = self.plan[self.current_step]
        
        # Refine the step based on current page state if we have a page
        if self.page:
            try:
                page_info = {
                    "url": self.page.url,
                    "title": await self.page.title()
                }
                step = await self.refine_plan_step(step, page_info)
            except:
                pass
                
        # Increment step counter
        self.current_step += 1
        
        return step
        
    async def execute_plan(self, callback=None):
        """
        Execute the current plan.
        
        Args:
            callback: Function to call with each step, should return True to continue or False to stop
        
        Returns:
            True if the plan was executed successfully, False otherwise
        """
        if not self.plan:
            logger.error("No plan to execute")
            return False
            
        step_count = 0
        
        # Execute each step in the plan
        while self.current_step < len(self.plan) and step_count < self.max_steps:
            step = await self.get_next_step()
            step_count += 1
            
            # Skip if no step
            if not step:
                continue
                
            # Log the step
            logger.info(f"Executing step {self.current_step}/{len(self.plan)}: {step}")
            
            # Call the callback if provided
            if callback:
                if not await callback(step):
                    logger.info("Execution stopped by callback")
                    return False
                    
            await asyncio.sleep(1)  # Brief pause between steps
            
        logger.info(f"Plan executed with {step_count} steps")
        return True 