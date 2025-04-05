"""
Browser action handlers for AI Browser Assistant.
Contains functions for interacting with web pages through Playwright.
"""

import time
import os
import re
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Union

from playwright.async_api import Page, ElementHandle

from config import (
    get_site_name, 
    get_search_selector, 
    get_search_button_selector,
    get_first_item_selectors
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def take_screenshot(page: Page, filename: Optional[str] = None) -> str:
    """
    Take a screenshot of the current page.
    
    Args:
        page: The Playwright page object
        filename: Optional custom filename
        
    Returns:
        Path to the saved screenshot
    """
    if not page:
        logger.error("No browser window open")
        return ""
        
    try:
        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
        # Ensure filename has .png extension
        if not filename.endswith('.png'):
            filename += '.png'
            
        # Full path to save the screenshot
        path = os.path.join("screenshots", filename)
        
        # Take the screenshot
        await page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")
        return path
        
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return ""

async def navigate(page: Page, url: str) -> bool:
    """
    Navigate to a URL.
    
    Args:
        page: The Playwright page object
        url: The URL to navigate to
        
    Returns:
        True if navigation was successful, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
        
    try:
        # Add https:// if not present
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        await page.goto(url)
        await asyncio.sleep(1)  # Wait for page to load
        current_url = page.url
        logger.info(f"Navigated to {current_url}")
        
        # Take a screenshot after navigation
        await take_screenshot(page)
        return True
        
    except Exception as e:
        logger.error(f"Error navigating to {url}: {str(e)}")
        return False

async def search_on_current_site(page: Page, query: str) -> bool:
    """
    Execute a search on the current website.
    
    Args:
        page: The Playwright page object
        query: The search query
        
    Returns:
        True if search was successful, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
    
    try:
        current_url = page.url.lower()
        success = False
        
        # Get site-specific search selector
        search_selector = get_search_selector(current_url)
        
        # Try site-specific search selector
        if isinstance(search_selector, str):
            try:
                await page.fill(search_selector, query)
                
                # Check if we need to click a search button or just press Enter
                button_selector = get_search_button_selector(current_url)
                if button_selector:
                    await page.click(button_selector)
                else:
                    await page.press(search_selector, "Enter")
                    
                success = True
                logger.info(f"Searched for: {query}")
            except Exception as e:
                logger.debug(f"Failed with primary selector: {str(e)}")
        
        # Try generic selectors if site-specific one failed
        if not success and isinstance(search_selector, list):
            for selector in search_selector:
                try:
                    if await page.query_selector(selector):
                        await page.fill(selector, query)
                        await page.press(selector, "Enter")
                        success = True
                        logger.info(f"Searched using {selector} for: {query}")
                        break
                except Exception as e:
                    logger.debug(f"Failed with selector {selector}: {str(e)}")
        
        if not success:
            # Try common search selectors
            common_search_selectors = [
                "input[name='q']",
                "input[type='search']",
                "input[aria-label*='search' i]",
                "input[placeholder*='search' i]",
                ".search-box",
                "#search-input"
            ]
            
            for selector in common_search_selectors:
                try:
                    search_input = await page.query_selector(selector)
                    if search_input:
                        await page.fill(selector, query)
                        await page.press(selector, "Enter")
                        success = True
                        logger.info(f"Searched using common selector {selector} for: {query}")
                        break
                except Exception as e:
                    continue
        
        if success:
            # Wait for results to load
            await asyncio.sleep(2)
            await take_screenshot(page)
            return True
        else:
            logger.warning(f"Could not find a way to search on this site. Falling back to Google search.")
            await navigate(page, f"https://www.google.com/search?q={'+'.join(query.split())}")
            return True
            
    except Exception as e:
        logger.error(f"Error searching on current site: {str(e)}")
        return False

async def click_element_with_text(page: Page, text: str) -> bool:
    """
    Click an element containing the specified text.
    
    Args:
        page: The Playwright page object
        text: The text to look for
        
    Returns:
        True if element was clicked, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
        
    try:
        # Try clicking element with exact text
        selectors = [
            f"text=\"{text}\"",
            f"text='{text}'",
            f"text={text}",
            f"*:has-text(\"{text}\")",
            f"[title=\"{text}\"]",
            f"[aria-label=\"{text}\"]",
            f"[placeholder=\"{text}\"]",
            f"button:has-text(\"{text}\")",
            f"a:has-text(\"{text}\")",
            f"input[value=\"{text}\"]",
        ]
        
        for selector in selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info(f"Clicked element with text: {text}")
                await asyncio.sleep(1)
                await take_screenshot(page)
                return True
            except:
                continue
                
        # If exact match failed, try partial match
        logger.info(f"Exact match failed, trying partial match for: {text}")
        selectors = [
            f"text='{text}'",
            f"*:has-text('{text}')",
            f"[title*='{text}' i]",
            f"[aria-label*='{text}' i]",
            f"button:has-text('{text}')",
            f"a:has-text('{text}')",
        ]
        
        for selector in selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info(f"Clicked element with partial text match: {text}")
                await asyncio.sleep(1)
                await take_screenshot(page)
                return True
            except:
                continue
                
        logger.warning(f"Could not find element with text: {text}")
        return False
        
    except Exception as e:
        logger.error(f"Error clicking element with text: {str(e)}")
        return False

async def click_element_with_selector(page: Page, selector: str) -> bool:
    """
    Click an element matching the CSS selector.
    
    Args:
        page: The Playwright page object
        selector: The CSS selector
        
    Returns:
        True if element was clicked, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
        
    try:
        await page.click(selector, timeout=5000)
        logger.info(f"Clicked element with selector: {selector}")
        await asyncio.sleep(1)
        await take_screenshot(page)
        return True
    except Exception as e:
        logger.error(f"Error clicking element with selector {selector}: {str(e)}")
        return False

async def select_first_item(page: Page, query_terms: Optional[str] = None) -> bool:
    """
    Click on the first item in search results, optionally filtering by query terms.
    
    Args:
        page: The Playwright page object
        query_terms: Optional text to look for in the item
        
    Returns:
        True if an item was clicked, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
    
    # Build a description based on query terms
    if query_terms:
        description = f"first item with {query_terms}"
    else:
        description = "first item"
    
    # Use our smart click implementation
    return await smart_click(page, description)

async def type_text_in_field(page: Page, text: str, field_identifier: str) -> bool:
    """
    Type text into a form field.
    
    Args:
        page: The Playwright page object
        text: The text to type
        field_identifier: Text to identify the field (label, placeholder, etc.)
        
    Returns:
        True if text was typed, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
        
    try:
        selectors = [
            f"input[placeholder=\"{field_identifier}\"]",
            f"input[name=\"{field_identifier}\"]",
            f"input[aria-label=\"{field_identifier}\"]",
            f"textarea[placeholder=\"{field_identifier}\"]",
            f"textarea[name=\"{field_identifier}\"]",
            f"textarea[aria-label=\"{field_identifier}\"]",
            f"input[id=\"{field_identifier}\"]",
            f"textarea[id=\"{field_identifier}\"]",
            f"//label[contains(text(), '{field_identifier}')]//following::input[1]",
            f"//label[contains(text(), '{field_identifier}')]//following::textarea[1]",
        ]
        
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    element = page.locator(selector)
                else:
                    # CSS selector
                    element = page.locator(selector)
                    
                if await element.count() > 0:
                    await element.fill(text)
                    logger.info(f"Typed '{text}' into field: {field_identifier}")
                    return True
            except:
                continue
                
        logger.warning(f"Could not find field: {field_identifier}")
        return False
        
    except Exception as e:
        logger.error(f"Error typing text: {str(e)}")
        return False

async def submit_form(page: Page) -> bool:
    """
    Submit the current form.
    
    Args:
        page: The Playwright page object
        
    Returns:
        True if form was submitted, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
        
    try:
        selectors = [
            "form button[type='submit']",
            "form input[type='submit']",
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Send')",
            "button:has-text('Login')",
            "button:has-text('Sign in')",
            "button:has-text('Register')",
            "button:has-text('Sign up')",
            "button:has-text('Continue')",
            ".submit-button",
            "#submit",
        ]
        
        for selector in selectors:
            try:
                if await page.query_selector(selector):
                    await page.click(selector)
                    logger.info(f"Submitted form using selector: {selector}")
                    await asyncio.sleep(2)  # Wait for form submission
                    await take_screenshot(page)
                    return True
            except:
                continue
                
        # If no submit button found, try pressing Enter on the last input
        try:
            inputs = await page.query_selector_all("form input:not([type='hidden'])")
            if inputs and len(inputs) > 0:
                last_input = inputs[-1]
                await last_input.press("Enter")
                logger.info("Submitted form by pressing Enter on last input")
                await asyncio.sleep(2)
                await take_screenshot(page)
                return True
        except:
            pass
            
        logger.warning("Could not find a way to submit the form")
        return False
        
    except Exception as e:
        logger.error(f"Error submitting form: {str(e)}")
        return False

async def scroll_page(page: Page, direction: str, amount: Optional[int] = None) -> bool:
    """
    Scroll the page up or down.
    
    Args:
        page: The Playwright page object
        direction: "up" or "down"
        amount: Optional pixel amount to scroll
        
    Returns:
        True if scrolled successfully, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
        
    try:
        # Default scroll amount
        scroll_amount = amount or 300
        
        if direction.lower() == "up":
            scroll_amount = -scroll_amount
            
        # Execute scroll
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        
        logger.info(f"Scrolled {direction} by {abs(scroll_amount)} pixels")
        await asyncio.sleep(0.5)
        await take_screenshot(page)
        return True
        
    except Exception as e:
        logger.error(f"Error scrolling page: {str(e)}")
        return False

async def find_text_on_page(page: Page, text: str) -> bool:
    """
    Find and highlight text on the current page.
    
    Args:
        page: The Playwright page object
        text: The text to find
        
    Returns:
        True if text was found, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
        
    try:
        # Use the browser's built-in find functionality
        await page.evaluate(f"window.find('{text}', false, false, true)")
        
        # Try to highlight the text with JavaScript
        highlight_script = """
        (text) => {
            const findInPage = (element, searchText) => {
                if (!element) return;
                
                if (element.nodeType === Node.TEXT_NODE) {
                    const content = element.textContent;
                    if (content.toLowerCase().includes(searchText.toLowerCase())) {
                        const range = document.createRange();
                        range.selectNode(element);
                        
                        const selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                        
                        // Scroll to the element
                        try {
                            element.parentNode.scrollIntoView({
                                behavior: 'smooth',
                                block: 'center'
                            });
                        } catch (e) {
                            // Fallback if scrollIntoView is not available
                            try {
                                element.parentNode.scrollIntoView();
                            } catch (e2) {
                                console.error('Could not scroll to element');
                            }
                        }
                        
                        return true;
                    }
                } else {
                    for (let i = 0; i < element.childNodes.length; i++) {
                        if (findInPage(element.childNodes[i], searchText)) {
                            return true;
                        }
                    }
                }
                
                return false;
            };
            
            return findInPage(document.body, text);
        }
        """
        found = await page.evaluate(highlight_script, text)
        
        if found:
            logger.info(f"Found and highlighted text: {text}")
            await asyncio.sleep(1)
            await take_screenshot(page)
            return True
        else:
            logger.warning(f"Text not found: {text}")
            return False
            
    except Exception as e:
        logger.error(f"Error finding text: {str(e)}")
        return False

async def execute_javascript(page: Page, code: str) -> Any:
    """
    Execute JavaScript code on the page.
    
    Args:
        page: The Playwright page object
        code: The JavaScript code to execute
        
    Returns:
        The result of the JavaScript execution, or None if failed
    """
    if not page:
        logger.error("No browser window open")
        return None
        
    try:
        result = await page.evaluate(code)
        logger.info("Executed JavaScript code")
        return result
        
    except Exception as e:
        logger.error(f"Error executing JavaScript: {str(e)}")
        return None

async def smart_click(page: Page, target_description: str) -> bool:
    """
    Intelligently click on an element based on a description.
    Uses JavaScript to analyze the page and find the best matching element.
    
    Args:
        page: The Playwright page object
        target_description: Description of what to click (e.g., "first product", "login button")
        
    Returns:
        True if an element was clicked, False otherwise
    """
    if not page:
        logger.error("No browser window open")
        return False
    
    try:
        # First, try standard selectors if this is a common element
        if any(term in target_description.lower() for term in ["login", "sign in", "signin"]):
            common_selectors = [
                "button:has-text('Login')", 
                "button:has-text('Sign In')",
                "a:has-text('Login')",
                "a:has-text('Sign In')",
                "[type='submit']:has-text('Login')",
                "[type='submit']:has-text('Sign In')"
            ]
            for selector in common_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        logger.info(f"Clicked login/sign in element with selector: {selector}")
                        return True
                except Exception as e:
                    continue
        
        # Parse the target description
        is_first_item = any(term in target_description.lower() for term in ["first", "1st"])
        is_product = any(term in target_description.lower() for term in ["product", "item", "result"])
        
        # JavaScript function to analyze the page and find clickable elements
        analysis_script = """(targetDescription) => {
            const isFirstItem = targetDescription.toLowerCase().includes('first') || 
                                targetDescription.toLowerCase().includes('1st');
            const isProduct = targetDescription.toLowerCase().includes('product') || 
                            targetDescription.toLowerCase().includes('item') || 
                            targetDescription.toLowerCase().includes('result');
            
            // Helper function to get text content
            const getVisibleText = (element) => {
                return element.innerText || element.textContent || '';
            };
            
            // Helper function to check if an element is visible
            const isVisible = (element) => {
                if (!element) return false;
                
                const style = window.getComputedStyle(element);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                    return false;
                }
                
                const rect = element.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0 && 
                       rect.top >= 0 && rect.top < window.innerHeight &&
                       rect.left >= 0 && rect.left < window.innerWidth;
            };
            
            // Get all clickable elements
            const getAllClickableElements = () => {
                const clickableElements = [];
                
                // Get all potentially clickable elements
                const elements = document.querySelectorAll('a, button, [role="button"], [onclick], [role="link"], input[type="submit"], input[type="button"], .clickable');
                
                elements.forEach(element => {
                    if (!isVisible(element)) return;
                    
                    const rect = element.getBoundingClientRect();
                    const text = getVisibleText(element).trim();
                    const hasImage = element.querySelector('img') !== null;
                    const hasPrice = /[$€£¥]\\s?[0-9]+([.,][0-9]+)?/.test(text);
                    
                    // Score the element based on various factors
                    let score = 0;
                    
                    // Size-based score (bigger is likely more important)
                    score += (rect.width * rect.height) / 10000;
                    
                    // Elements with images are likely products
                    if (hasImage) score += 20;
                    
                    // Elements with prices are likely products
                    if (hasPrice) score += 30;
                    
                    // Elements with meaningful text are more important
                    if (text.length > 0) score += Math.min(text.length, 50) / 5;
                    
                    // Specific element type bonuses
                    if (element.tagName === 'BUTTON') score += 10;
                    if (element.tagName === 'A') score += 5;
                    if (element.getAttribute('role') === 'button') score += 10;
                    
                    // Create a detailed representation of the element
                    clickableElements.push({
                        element: element,
                        tag: element.tagName.toLowerCase(),
                        text: text,
                        x: rect.left,
                        y: rect.top,
                        width: rect.width,
                        height: rect.height,
                        hasImage: hasImage,
                        hasPrice: hasPrice,
                        area: rect.width * rect.height,
                        score: score
                    });
                });
                
                return clickableElements;
            };
            
            // Find product-like elements
            const findProductElements = () => {
                const elements = getAllClickableElements();
                
                // Look for elements inside common product containers
                const productContainers = document.querySelectorAll(
                    '.product, .item, .result, [class*="product"], [class*="item"], [class*="result"], [class*="card"]'
                );
                
                const productsInContainers = [];
                productContainers.forEach(container => {
                    if (!isVisible(container)) return;
                    
                    // Find clickable elements within this container
                    const clickableChildren = [];
                    elements.forEach(el => {
                        if (container.contains(el.element)) {
                            // Boost score for elements in product containers
                            el.score += 15;
                            clickableChildren.push(el);
                        }
                    });
                    
                    // Get the highest scored element in this container
                    if (clickableChildren.length > 0) {
                        clickableChildren.sort((a, b) => b.score - a.score);
                        productsInContainers.push(clickableChildren[0]);
                    }
                });
                
                // Sort all elements by score
                elements.sort((a, b) => b.score - a.score);
                
                // Return both collections
                return {
                    allElements: elements,
                    productsInContainers: productsInContainers
                };
            };
            
            const products = findProductElements();
            
            // Get element to click based on description
            let elementToClick = null;
            
            if (isProduct) {
                // Use products in containers if available
                if (products.productsInContainers.length > 0) {
                    elementToClick = isFirstItem ? 
                        products.productsInContainers[0].element : 
                        products.productsInContainers[Math.floor(Math.random() * products.productsInContainers.length)].element;
                } 
                // Otherwise use the best-scored elements
                else if (products.allElements.length > 0) {
                    elementToClick = isFirstItem ? 
                        products.allElements[0].element : 
                        products.allElements[Math.floor(Math.random() * Math.min(5, products.allElements.length))].element;
                }
            } else {
                // For non-product elements, just get top matching elements
                const elements = getAllClickableElements()
                    .filter(el => {
                        const text = el.text.toLowerCase();
                        // Match elements that contain words from the target description
                        const targetWords = targetDescription.toLowerCase().split(/\\s+/);
                        return targetWords.some(word => text.includes(word));
                    })
                    .sort((a, b) => b.score - a.score);
                
                if (elements.length > 0) {
                    elementToClick = elements[0].element;
                }
            }
            
            // Fallback to highest-scored element
            if (!elementToClick && products.allElements.length > 0) {
                elementToClick = products.allElements[0].element;
            }
            
            if (elementToClick) {
                // Get the element details for logging
                const rect = elementToClick.getBoundingClientRect();
                const details = {
                    tag: elementToClick.tagName,
                    text: getVisibleText(elementToClick).substring(0, 50),
                    hasImage: elementToClick.querySelector('img') !== null,
                    x: rect.left,
                    y: rect.top,
                    width: rect.width,
                    height: rect.height
                };
                
                try {
                    // Highlight element temporarily for visual feedback
                    const originalStyle = elementToClick.getAttribute('style') || '';
                    elementToClick.setAttribute('style', 
                        originalStyle + '; outline: 3px solid red !important; transition: outline 0.3s;');
                    
                    // Scroll element into view
                    elementToClick.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    
                    // Return only the details since we can't return the actual element
                    return details;
                } catch (e) {
                    console.error('Error highlighting element:', e);
                    return details;
                }
            }
            
            return null;
        }"""
        
        # Run the analysis script to find the best element
        element_details = await page.evaluate(analysis_script, target_description)
        
        if element_details:
            # Log the details of the element we found
            logger.info(f"Found element to click: {element_details['tag']} with text: {element_details['text']}")
            
            # Wait briefly for the visual highlight and scrolling
            await asyncio.sleep(0.5)
            
            # Click where the element is
            try:
                await page.mouse.click(
                    element_details['x'] + element_details['width'] / 2,
                    element_details['y'] + element_details['height'] / 2
                )
                logger.info(f"Clicked at position ({element_details['x'] + element_details['width'] / 2}, {element_details['y'] + element_details['height'] / 2})")
                await asyncio.sleep(1)
                await take_screenshot(page)
                return True
            except Exception as e:
                logger.warning(f"Failed to click using mouse: {str(e)}")
                
                # Try clicking using JavaScript as a fallback
                result = await page.evaluate("""(details) => {
                    const elements = document.elementsFromPoint(
                        details.x + details.width / 2, 
                        details.y + details.height / 2
                    );
                    
                    if (elements.length > 0) {
                        elements[0].click();
                        return true;
                    }
                    return false;
                }""", element_details)
                
                if result:
                    logger.info("Clicked element using JavaScript")
                    await asyncio.sleep(1)
                    await take_screenshot(page)
                    return True
        
        # If all else fails, look for large images and try clicking those
        logger.warning("Could not find specific element to click, trying image fallback")
        try:
            image_result = await page.evaluate("""() => {
                const images = Array.from(document.querySelectorAll('img'))
                    .filter(img => {
                        if (!img.isConnected) return false;
                        const rect = img.getBoundingClientRect();
                        return rect.width > 100 && rect.height > 100 && rect.width * rect.height > 10000;
                    })
                    .sort((a, b) => {
                        const aRect = a.getBoundingClientRect();
                        const bRect = b.getBoundingClientRect();
                        return (bRect.width * bRect.height) - (aRect.width * aRect.height);
                    });
                
                if (images.length > 0) {
                    const img = images[0];
                    const rect = img.getBoundingClientRect();
                    
                    // Try finding a clickable parent
                    let clickableParent = img;
                    while (clickableParent && clickableParent !== document.body) {
                        if (clickableParent.tagName === 'A' || 
                            clickableParent.onclick || 
                            clickableParent.getAttribute('role') === 'button') {
                            break;
                        }
                        clickableParent = clickableParent.parentElement;
                    }
                    
                    const elementToClick = clickableParent !== document.body ? clickableParent : img;
                    elementToClick.click();
                    
                    return {
                        success: true,
                        message: `Clicked ${elementToClick.tagName} containing image (${rect.width}x${rect.height})`
                    };
                }
                
                return { success: false };
            }""")
            
            if image_result.get('success'):
                logger.info(image_result.get('message', 'Clicked large image'))
                await asyncio.sleep(1)
                await take_screenshot(page)
                return True
        except Exception as e:
            logger.error(f"Error with image fallback: {str(e)}")
        
        logger.error(f"Could not find any element to click matching: {target_description}")
        return False
    
    except Exception as e:
        logger.error(f"Error in smart_click: {str(e)}")
        return False 