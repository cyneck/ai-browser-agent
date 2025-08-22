"""
Playwright ARIA Snapshot Usage Examples
=====================================

This file demonstrates various ways to use Playwright's ARIA snapshot functionality
for web automation and accessibility testing.
"""

import json
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


class ARIASnapshotExamples:
    """Examples of using ARIA snapshots in Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def setup(self):
        """Initialize Playwright browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
    
    def cleanup(self):
        """Clean up resources"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def basic_aria_snapshot(self, url: str) -> Dict[str, Any]:
        """
        Basic ARIA snapshot usage - gets the full accessibility tree
        
        Args:
            url: The URL to analyze
            
        Returns:
            Dict containing the ARIA snapshot
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
        # Get the complete ARIA snapshot
        snapshot = self.page.accessibility.snapshot()
        
        print(f"ARIA Snapshot for {url}:")
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        
        return snapshot
    
    def filtered_aria_snapshot(self, url: str) -> Dict[str, Any]:
        """
        Get ARIA snapshot with filtering options
        
        Args:
            url: The URL to analyze
            
        Returns:
            Filtered ARIA snapshot
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
        # Get snapshot with only interesting nodes (interactive elements)
        snapshot = self.page.accessibility.snapshot(
            interesting_only=True,  # Only include nodes that are interesting for automation
            root=None  # Start from document root
        )
        
        print(f"Filtered ARIA Snapshot for {url}:")
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        
        return snapshot
    
    def specific_element_aria_snapshot(self, url: str, selector: str) -> Dict[str, Any]:
        """
        Get ARIA snapshot for a specific element
        
        Args:
            url: The URL to analyze
            selector: CSS selector for the element to analyze
            
        Returns:
            ARIA snapshot of the specific element
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
        # Find the specific element
        element = self.page.locator(selector).first
        
        # Get ARIA snapshot for just this element
        snapshot = self.page.accessibility.snapshot(root=element.element_handle())
        
        print(f"ARIA Snapshot for element '{selector}' on {url}:")
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        
        return snapshot
    
    def find_interactive_elements(self, url: str) -> List[Dict[str, Any]]:
        """
        Use ARIA snapshot to find all interactive elements
        
        Args:
            url: The URL to analyze
            
        Returns:
            List of interactive elements found
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
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
    
    def find_elements_by_role(self, url: str, target_role: str) -> List[Dict[str, Any]]:
        """
        Find all elements with a specific ARIA role
        
        Args:
            url: The URL to analyze
            target_role: The ARIA role to search for (e.g., "button", "link", "textbox")
            
        Returns:
            List of elements with the target role
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
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
    
    def create_selector_from_aria(self, url: str, target_name: str) -> str:
        """
        Create a robust selector using ARIA information
        
        Args:
            url: The URL to analyze
            target_name: The accessible name of the element to find
            
        Returns:
            A selector string that can be used with Playwright
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
        snapshot = self.page.accessibility.snapshot(interesting_only=True)
        
        def find_element_info(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Find element info by accessible name"""
            if not node:
                return None
            
            if node.get("name", "").lower() == target_name.lower():
                return node
            
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
        if role:
            selectors.append(f"page.get_by_role('{role}', name='{name}')")
        
        # Accessible name selector
        if name:
            selectors.append(f"page.get_by_label('{name}')")
            selectors.append(f"page.get_by_text('{name}')")
        
        # Return the most appropriate selector
        selector = selectors[0] if selectors else f"// No suitable selector found for '{target_name}'"
        
        print(f"Suggested selector for '{target_name}': {selector}")
        return selector
    
    def analyze_form_structure(self, url: str) -> Dict[str, Any]:
        """
        Analyze form structure using ARIA snapshot
        
        Args:
            url: The URL to analyze
            
        Returns:
            Form structure information
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        
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
    """Demonstrate ARIA snapshot usage"""
    examples = ARIASnapshotExamples()
    
    try:
        examples.setup()
        
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


if __name__ == "__main__":
    demo_usage()