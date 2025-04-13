"""
Configuration for the AI Browser Assistant.
Contains site-specific selectors and behaviors to avoid hardcoding them in the main code.
"""

import re
from typing import Dict, List, Union, Callable, Optional, Any

# Site detection patterns
SITE_PATTERNS = {
    "amazon": r"amazon\.(com|in|co\.uk|ca|de|jp|fr)",
    "google": r"google\.(com|co\.in|co\.uk|ca|de|jp|fr)",
    "youtube": r"youtube\.com",
    "github": r"github\.com",
    "twitter": r"(twitter\.com|x\.com)",
    "reddit": r"reddit\.com",
    "ebay": r"ebay\.(com|in|co\.uk|ca|de|jp|fr)",
    "walmart": r"walmart\.com",
    "target": r"target\.com",
    "bestbuy": r"bestbuy\.com",
}

# Search selectors for different sites
SEARCH_SELECTORS = {
    "amazon": "#twotabsearchtextbox",
    "google": "input[name='q']",
    "youtube": "input#search",
    "github": "[data-target='qbsearch-input.queryInput']",
    "twitter": "[data-testid='SearchBox_Search_Input']",
    "reddit": "input[name='q']",
    "ebay": "input[name='_nkw']",
    "walmart": "input[name='q']",
    "target": "input[name='searchTerm']",
    "bestbuy": "input[id='gh-search-input']",
}

# Search button selectors for different sites
SEARCH_BUTTON_SELECTORS = {
    "amazon": "input[type='submit'][value='Go']",
    "google": None,  # Just press Enter
    "youtube": None,  # Just press Enter
    "github": None,  # Just press Enter
    "twitter": None,  # Just press Enter
    "reddit": None,  # Just press Enter
    "ebay": "input[type='submit']",
    "walmart": "[data-automation-id='search-icon']",
    "target": "button[data-test='@web/Search/SearchButton']",
    "bestbuy": "button.header-search-button",
}

# Generic search selectors to try if site-specific ones fail
GENERIC_SEARCH_SELECTORS = [
    "input[type='search']",
    "input[name='q']", 
    "input[name='query']",
    "input[name='search']",
    "input[placeholder*='search' i]",
    "input[aria-label*='search' i]",
    "input.search",
    "#search",
    ".search-input",
    "[role='search'] input"
]

# Generic search button selectors
GENERIC_SEARCH_BUTTON_SELECTORS = [
    "button[type='submit']",
    "input[type='submit']",
    "button:has-text('Search')",
    "[aria-label*='search' i]",
    ".search-button",
    "#search-button"
]

# First item selectors for different sites
FIRST_ITEM_SELECTORS = {
    "amazon": [
        "div[data-component-type='s-search-result'] h2 a",
        ".s-result-item h2 a",
        ".s-search-results .a-link-normal.a-text-normal"
    ],
    "google": [
        ".g a", 
        "div.yuRUbf > a", 
        "#search .g .yuRUbf > a"
    ],
    "youtube": [
        "#contents ytd-video-renderer a#video-title",
        "ytd-video-renderer .title-and-badge a"
    ],
    "ebay": [
        ".s-item__link",
        ".srp-results .s-item__title"
    ],
    "walmart": [
        "a[data-testid='product-title']",
        ".mb1 a"
    ],
    "target": [
        "a[data-test='product-link']",
        ".styles__StyledTitleLink-sc-n8jd6b-0"
    ],
    "bestbuy": [
        ".sku-title a",
        ".shop-sku-list-item a"
    ]
}

# Generic first item selectors
GENERIC_FIRST_ITEM_SELECTORS = [
    ".search-results a", 
    ".results a", 
    ".search-result a",
    "article a",
    ".product-list a",
    ".item a",
    "ul li a",
    "div[role='main'] a"
]

# Command patterns for natural language parsing
COMMAND_PATTERNS = {
    "go_to_and_search": r"go\s+to\s+([a-z0-9.-]+(?:\.[a-z]{2,})?)(?:\s+and\s+|\s+to\s+)?search\s+for\s+(.*)",
    "on_site_search": r"on\s+([a-z0-9.-]+(?:\.[a-z]{2,})?)\s+search\s+for\s+(.*)",
    "search_for": r"^search\s+for\s+(.*)",
    "select_first_item": r"(?:select|click)(?:\s+on)?\s+(?:the\s+)?first\s+(?:item|result)(?:\s+with\s+(.*))?",
    "click_element": r"click(?:\s+on)?\s+[\"']?([^\"']+)[\"']?",
    "click_selector": r"click\s+selector\s+(.*)",
    "type_in_field": r"type\s+[\"']([^\"']+)[\"']\s+in\s+[\"']?([^\"']+)[\"']?",
    "find_text": r"find\s+[\"']?([^\"']+)[\"']?",
    "scroll": r"scroll\s+(up|down)(?:\s+(\d+))?",
    "navigate": r"(?:go\s+to|open|visit|navigate\s+to)\s+(.*)",
}

def get_site_name(url: str) -> Optional[str]:
    """
    Identify the site from the URL.
    
    Args:
        url: The URL to analyze
        
    Returns:
        The site name if recognized, None otherwise
    """
    url = url.lower()
    for site, pattern in SITE_PATTERNS.items():
        if re.search(pattern, url):
            return site
    return None

def get_search_selector(url: str) -> Union[str, List[str]]:
    """
    Get the appropriate search selector for a given site.
    
    Args:
        url: The URL to analyze
        
    Returns:
        A selector string or list of fallback selectors
    """
    site = get_site_name(url)
    if site and site in SEARCH_SELECTORS:
        return SEARCH_SELECTORS[site]
    return GENERIC_SEARCH_SELECTORS

def get_search_button_selector(url: str) -> Optional[str]:
    """
    Get the appropriate search button selector for a given site.
    
    Args:
        url: The URL to analyze
        
    Returns:
        A selector string or None if Enter key should be used
    """
    site = get_site_name(url)
    if site and site in SEARCH_BUTTON_SELECTORS:
        return SEARCH_BUTTON_SELECTORS[site]
    return None

def get_first_item_selectors(url: str) -> List[str]:
    """
    Get selectors for the first item on a search results page.
    
    Args:
        url: The URL to analyze
        
    Returns:
        List of selectors to try
    """
    site = get_site_name(url)
    if site and site in FIRST_ITEM_SELECTORS:
        return FIRST_ITEM_SELECTORS[site]
    return GENERIC_FIRST_ITEM_SELECTORS

def is_known_searchable_site(url: str) -> list:
    """
    Check if the current site is a known site with search capabilities.
    
    Args:
        url: The URL to analyze
        
    Returns:
        List of known searchable site domains
    """
    known_searchable_sites = [
        "google.com",
        "bing.com",
        "duckduckgo.com",
        "yahoo.com",
        "youtube.com",
        "amazon.com",
        "wikipedia.org",
        "reddit.com",
        "twitter.com",
        "linkedin.com"
    ]
    return known_searchable_sites 