"""
Playwright ARIA Snapshot Usage Examples
=====================================

This file demonstrates various ways to use Playwright's ARIA snapshot functionality
for web automation and accessibility testing.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


class ARIASnapshotExamples:
    """Examples of using ARIA snapshots in Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def setup(self, headless: bool = False, slow_mo: int = 0):
        """Initialize Playwright browser with configurable options
        
        Args:
            headless: Whether to run browser in headless mode
            slow_mo: Slow down operations by this many milliseconds
        """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            devtools=not headless  # Open devtools in non-headless mode
        )
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # Enable console logging
        self.page.on("console", lambda msg: print(f"🖥️  Browser Console: {msg.text}"))
        
        print(f"✅ Setup complete - Headless: {headless}, SlowMo: {slow_mo}ms")
    
    def cleanup(self):
        """Clean up resources"""
        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                print(f"⚠️  Error closing browser: {e}")
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                print(f"⚠️  Error stopping Playwright: {e}")

    def navigate_to_page(self, url: str, timeout: int = 60000):
        """Navigate to a local file or remote URL"""
        if os.path.exists(url):
            # Local file
            abs_path = Path(url).resolve()
            page_url = abs_path.as_uri()
            print(f"Navigating to local file: {page_url}")
        else:
            # Remote URL
            page_url = url
            print(f"Navigating to remote URL: {page_url}")

        self.page.goto(page_url, timeout=timeout)
    
    def basic_aria_snapshot(self, url: str, timeout: int = 60000) -> Dict[str, Any]:
        """
        Basic ARIA snapshot usage - gets the full accessibility tree
        
        Args:
            url: The URL to analyze
            timeout: Maximum time to wait for page load (ms)
            
        Returns:
            Dict containing the ARIA snapshot
        """
        self.navigate_to_page(url, timeout=timeout)
        
        # First wait for DOM to load
        self.page.wait_for_load_state("domcontentloaded")
        print("Page DOM loaded")
        
        # Then wait a bit more for JS to settle
        self.page.wait_for_timeout(5000)
        print("Additional wait completed")
        
        # Get the complete ARIA snapshot
        snapshot = self.page.accessibility.snapshot()
        
        print(f"ARIA Snapshot for {url}:")
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        
        return snapshot
    
    def filtered_aria_snapshot(self, url: str, timeout: int = 60000) -> Dict[str, Any]:
        """
        Get ARIA snapshot with filtering options
        
        Args:
            url: The URL to analyze
            timeout: Maximum time to wait for page load (ms)
            
        Returns:
            Filtered ARIA snapshot
        """
        self.navigate_to_page(url, timeout=timeout)
        
        # First wait for DOM to load
        self.page.wait_for_load_state("domcontentloaded")
        print("Page DOM loaded")
        
        # Then wait a bit more for JS to settle
        self.page.wait_for_timeout(5000)
        print("Additional wait completed")
        
        # Get snapshot with only interesting nodes (interactive elements)
        snapshot = self.page.accessibility.snapshot(
            interesting_only=True,  # Only include nodes that are interesting for automation
            root=None  # Start from document root
        )
        
        print(f"Filtered ARIA Snapshot for {url}: {json.dumps(snapshot, ensure_ascii=False)[:100]}...")
        
        return snapshot
    
    def specific_element_aria_snapshot(self, url: str, selector: str, timeout: int = 60000) -> Dict[str, Any]:
        """
        Get ARIA snapshot for a specific element
        
        Args:
            url: The URL to analyze
            selector: CSS selector for the element to analyze
            timeout: Maximum time to wait for page load (ms)
            
        Returns:
            ARIA snapshot of the specific element
        """
        self.navigate_to_page(url, timeout=timeout)
        
        # First wait for DOM to load
        self.page.wait_for_load_state("domcontentloaded")
        print("Page DOM loaded")
        
        # Then wait a bit more for JS to settle
        self.page.wait_for_timeout(5000)
        print("Additional wait completed")
        
        # Find the specific element
        element = self.page.locator(selector).first
        
        # Get ARIA snapshot for just this element
        snapshot = self.page.accessibility.snapshot(root=element.element_handle())
        
        print(f"ARIA Snapshot for element '{selector}' on {url}: {json.dumps(snapshot, ensure_ascii=False)[:100]}...")
        
        return snapshot
    
    def find_interactive_elements(self, url: str, timeout: int = 60000) -> List[Dict[str, Any]]:
        """
        Use ARIA snapshot to find all interactive elements
        
        Args:
            url: The URL to analyze
            timeout: Maximum time to wait for page load (ms)
            
        Returns:
            List of interactive elements found
        """
        self.navigate_to_page(url, timeout=timeout)
        
        # First wait for DOM to load
        self.page.wait_for_load_state("domcontentloaded")
        print("Page DOM loaded")
        
        # Then wait a bit more for JS to settle
        self.page.wait_for_timeout(5000)
        print("Additional wait completed")
        
        snapshot = self.page.accessibility.snapshot(interesting_only=True)
        
        interactive_elements = []
        
        def extract_interactive_nodes(node: Dict[str, Any], path: str = ""):
            """Recursively extract interactive nodes"""
            if not node:
                return
            
            # Check if this node is interactive
            role = node.get("role", "")
            name = node.get("name", "")
            
            if role in ["button", "link", "textbox", "searchbox", "combobox", "checkbox", "radio", "tab"]:
                interactive_elements.append({
                    "role": role,
                    "name": name,
                    "path": path,
                    "properties": node.get("properties", {}),
                    "value": node.get("value", ""),
                    "description": node.get("description", "")
                })
            
            # Recursively check children
            children = node.get("children", [])
            for i, child in enumerate(children):
                child_path = f"{path} > {role}[{i}]" if path else f"{role}[{i}]"
                extract_interactive_nodes(child, child_path)
        
        extract_interactive_nodes(snapshot)
        
        print(f"Found {len(interactive_elements)} interactive elements:")
        for elem in interactive_elements:
            print(f"  - {elem['role']}: {elem['name']} ({elem['path']})")
        
        return interactive_elements
    
    def find_elements_by_role(self, url: str, target_role: str, timeout: int = 60000) -> List[Dict[str, Any]]:
        """
        Find all elements with a specific ARIA role
        
        Args:
            url: The URL to analyze
            target_role: The ARIA role to search for (e.g., "button", "link", "textbox")
            timeout: Maximum time to wait for page load (ms)
            
        Returns:
            List of elements with the target role
        """
        self.navigate_to_page(url, timeout=timeout)
        
        # First wait for DOM to load
        self.page.wait_for_load_state("domcontentloaded")
        print("Page DOM loaded")
        
        # Then wait a bit more for JS to settle
        self.page.wait_for_timeout(5000)
        print("Additional wait completed")
        
        snapshot = self.page.accessibility.snapshot(interesting_only=True)
        
        matching_elements = []
        
        def find_by_role(node: Dict[str, Any]):
            """Recursively find nodes with target role"""
            if not node:
                return
            
            if node.get("role") == target_role:
                matching_elements.append({
                    "role": node.get("role"),
                    "name": node.get("name", ""),
                    "value": node.get("value", ""),
                    "description": node.get("description", ""),
                    "properties": node.get("properties", {})
                })
            
            # Check children
            for child in node.get("children", []):
                find_by_role(child)
        
        find_by_role(snapshot)
        
        print(f"Found {len(matching_elements)} elements with role '{target_role}':")
        for elem in matching_elements:
            print(f"  - {elem['name']} ({elem['role']})")
        
        return matching_elements
    
    def create_selector_from_aria(self, url: str, target_name: str, timeout: int = 60000) -> str:
        """
        Create a robust selector using ARIA information
        
        Args:
            url: The URL to analyze
            target_name: The accessible name of the element to find
            timeout: Maximum time to wait for page load (ms)
            
        Returns:
            A selector string that can be used with Playwright
        """
        self.navigate_to_page(url, timeout=timeout)
        
        # First wait for DOM to load
        self.page.wait_for_load_state("domcontentloaded")
        print("Page DOM loaded")
        
        # Then wait a bit more for JS to settle
        self.page.wait_for_timeout(5000)
        print("Additional wait completed")
        
        snapshot = self.page.accessibility.snapshot(interesting_only=True)
        
        def find_element_info(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Recursively find element info by accessible name"""
            if not node:
                return None
            
            # Check if this is the element we're looking for
            if node.get("name", "").lower() == target_name.lower():
                return node
            
            # Recursively check children
            for child in node.get("children", []):
                result = find_element_info(child)
                if result:
                    return result
            
            return None
        
        element_info = find_element_info(snapshot)
        
        if not element_info:
            return f"// Element with name '{target_name}' not found"
        
        role = element_info.get("role", "")
        name = element_info.get("name", "")
        
        # Create different types of selectors
        selectors = []
        
        # ARIA role selector
        if role and name:
            selectors.append(f"page.get_by_role('{role}', name='{name}')")
        
        # Accessible name selector
        if name:
            selectors.append(f"page.get_by_label('{name}')")
            selectors.append(f"page.get_by_text('{name}')")
        
        # Return the most appropriate selector
        selector = selectors[0] if selectors else f"// No suitable selector found for '{target_name}'"
        
        print(f"Suggested selector for '{target_name}': {selector}")
        return selector
    
    def analyze_form_structure(self, url: str, timeout: int = 60000) -> Dict[str, Any]:
        """
        Analyze form structure using ARIA snapshot
        
        Args:
            url: The URL to analyze
            timeout: Maximum time to wait for page load (ms)
            
        Returns:
            Form structure information
        """
        self.navigate_to_page(url, timeout=timeout)
        
        # First wait for DOM to load
        self.page.wait_for_load_state("domcontentloaded")
        print("Page DOM loaded")
        
        # Then wait a bit more for JS to settle
        self.page.wait_for_timeout(5000)
        print("Additional wait completed")
        
        snapshot = self.page.accessibility.snapshot(interesting_only=True)
        
        forms = []
        
        def analyze_node(node: Dict[str, Any], parent_form: Optional[Dict] = None):
            """Recursively analyze nodes for form structure"""
            if not node:
                return
            
            role = node.get("role", "")
            name = node.get("name", "")
            
            current_form = parent_form
            
            # Start a new form
            if role == "form":
                current_form = {
                    "name": name,
                    "fields": [],
                    "buttons": []
                }
                forms.append(current_form)
            
            # Add form fields
            elif current_form and role in ["textbox", "searchbox", "combobox", "checkbox", "radio"]:
                current_form["fields"].append({
                    "type": role,
                    "name": name,
                    "value": node.get("value", ""),
                    "required": "required" in node.get("properties", {})
                })
            
            # Add form buttons
            elif current_form and role == "button":
                current_form["buttons"].append({
                    "name": name,
                    "type": node.get("properties", {}).get("type", "button")
                })
            
            # Recursively analyze children
            for child in node.get("children", []):
                analyze_node(child, current_form)
        
        analyze_node(snapshot)
        
        print(f"Found {len(forms)} forms:")
        for i, form in enumerate(forms):
            print(f"  Form {i+1}: {form['name']}")
            print(f"    Fields: {len(form['fields'])}")
            print(f"    Buttons: {len(form['buttons'])}")
        
        return {"forms": forms}


def demo_usage():
    """Demonstrate ARIA snapshot usage examples"""
    examples = ARIASnapshotExamples()
    
    try:
        examples.setup(headless=True, slow_mo=0)  # Run in headless mode by default
        
        # Example 1: Basic ARIA snapshot
        print("=== Basic ARIA Snapshot ===")
        examples.basic_aria_snapshot("https://www.google.com")
        
        print("\n" + "="*50 + "\n")
        
        # Example 2: Find interactive elements
        print("=== Finding Interactive Elements ===")
        examples.find_interactive_elements("https://www.google.com")
        
        print("\n" + "="*50 + "\n")
        
        # Example 3: Find buttons
        print("=== Finding Buttons ===")
        examples.find_elements_by_role("https://www.google.com", "button")
        
        print("\n" + "="*50 + "\n")
        
        # Example 4: Create selector
        print("=== Creating Selector ===")
        examples.create_selector_from_aria("https://www.google.com", "Google Search")
        
    finally:
        examples.cleanup()