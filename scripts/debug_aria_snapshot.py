#!/usr/bin/env python3
"""
ARIA Snapshot Debug Script
==========================

This script allows you to debug ARIA snapshot functionality directly
with real websites for technical debugging and analysis.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from examples.aria_snapshot_usage import ARIASnapshotExamples


class ARIADebugger:
    """Debug ARIA snapshot functionality with real websites"""
    
    def __init__(self, headless: bool = False, slow_mo: int = 0):
        """
        Initialize the debugger
        
        Args:
            headless: Whether to run browser in headless mode (False for visual debugging)
            slow_mo: Slow down operations by this many milliseconds (useful for visual debugging)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.examples = None
    
    def setup(self):
        """Setup the ARIA examples with debug-friendly configuration"""
        self.examples = ARIASnapshotExamples()
        
        # Override the setup method to use our debug configuration
        from playwright.sync_api import sync_playwright
        
        self.examples.playwright = sync_playwright().start()
        self.examples.browser = self.examples.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            devtools=not self.headless  # Open devtools in non-headless mode
        )
        self.examples.context = self.examples.browser.new_context(
            viewport={'width': 1920, 'height': 1080}  # Large viewport for debugging
        )
        self.examples.page = self.examples.context.new_page()
        
        # Enable console logging
        self.examples.page.on("console", lambda msg: print(f"🖥️  Browser Console: {msg.text}"))
        
        print(f"✅ Setup complete - Headless: {self.headless}, SlowMo: {self.slow_mo}ms")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.examples:
            self.examples.cleanup()
    
    def debug_basic_snapshot(self, url: str) -> Dict[str, Any]:
        """
        Debug basic ARIA snapshot functionality
        
        Args:
            url: The URL to debug (e.g., 'https://www.jd.com')
            
        Returns:
            ARIA snapshot data
        """
        print(f"\n🔍 Debugging basic ARIA snapshot for: {url}")
        print("-" * 60)
        
        try:
            snapshot = self.examples.basic_aria_snapshot(url)
            
            print(f"✅ Snapshot captured successfully")
            print(f"📊 Root role: {snapshot.get('role', 'Unknown')}")
            print(f"📋 Page name: {snapshot.get('name', 'Unknown')}")
            print(f"🌳 Number of children: {len(snapshot.get('children', []))}")
            
            return snapshot
            
        except Exception as e:
            print(f"❌ Error during basic snapshot: {e}")
            raise
    
    def debug_interactive_elements(self, url: str) -> List[Dict[str, Any]]:
        """
        Debug finding interactive elements
        
        Args:
            url: The URL to debug
            
        Returns:
            List of interactive elements found
        """
        print(f"\n🔍 Debugging interactive elements for: {url}")
        print("-" * 60)
        
        try:
            elements = self.examples.find_interactive_elements(url)
            
            print(f"✅ Found {len(elements)} interactive elements")
            
            # Group by role for better analysis
            by_role = {}
            for elem in elements:
                role = elem.get('role', 'unknown')
                if role not in by_role:
                    by_role[role] = []
                by_role[role].append(elem)
            
            print("\n📊 Elements by role:")
            for role, role_elements in by_role.items():
                print(f"  {role}: {len(role_elements)} elements")
                
                # Show first few examples
                for i, elem in enumerate(role_elements[:3]):
                    name = elem.get('name', '(no name)')
                    print(f"    - {name[:50]}{'...' if len(name) > 50 else ''}")
                
                if len(role_elements) > 3:
                    print(f"    ... and {len(role_elements) - 3} more")
            
            return elements
            
        except Exception as e:
            print(f"❌ Error finding interactive elements: {e}")
            raise
    
    def debug_specific_role(self, url: str, role: str) -> List[Dict[str, Any]]:
        """
        Debug finding elements by specific role
        
        Args:
            url: The URL to debug
            role: The ARIA role to search for (e.g., 'button', 'link', 'textbox')
            
        Returns:
            List of elements with the specified role
        """
        print(f"\n🔍 Debugging elements with role '{role}' for: {url}")
        print("-" * 60)
        
        try:
            elements = self.examples.find_elements_by_role(url, role)
            
            print(f"✅ Found {len(elements)} elements with role '{role}'")
            
            if elements:
                print(f"\n📋 Details for '{role}' elements:")
                for i, elem in enumerate(elements):
                    name = elem.get('name', '(no name)')
                    value = elem.get('value', '')
                    description = elem.get('description', '')
                    
                    print(f"  {i+1}. Name: {name}")
                    if value:
                        print(f"     Value: {value}")
                    if description:
                        print(f"     Description: {description}")
                    print()
            
            return elements
            
        except Exception as e:
            print(f"❌ Error finding elements with role '{role}': {e}")
            raise
    
    def debug_form_analysis(self, url: str) -> Dict[str, Any]:
        """
        Debug form structure analysis
        
        Args:
            url: The URL to debug
            
        Returns:
            Form analysis data
        """
        print(f"\n🔍 Debugging form analysis for: {url}")
        print("-" * 60)
        
        try:
            analysis = self.examples.analyze_form_structure(url)
            
            forms = analysis.get('forms', [])
            print(f"✅ Found {len(forms)} forms")
            
            for i, form in enumerate(forms):
                print(f"\n📋 Form {i+1}: {form.get('name', '(unnamed)')}")
                print(f"  Fields: {len(form.get('fields', []))}")
                print(f"  Buttons: {len(form.get('buttons', []))}")
                
                # Show field details
                for field in form.get('fields', []):
                    field_type = field.get('type', 'unknown')
                    field_name = field.get('name', '(no name)')
                    required = field.get('required', False)
                    req_text = " (required)" if required else ""
                    print(f"    - {field_type}: {field_name}{req_text}")
                
                # Show button details
                for button in form.get('buttons', []):
                    button_name = button.get('name', '(no name)')
                    button_type = button.get('type', 'button')
                    print(f"    - Button: {button_name} ({button_type})")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing forms: {e}")
            raise
    
    def debug_selector_creation(self, url: str, element_name: str) -> str:
        """
        Debug selector creation for a specific element
        
        Args:
            url: The URL to debug
            element_name: The accessible name of the element to find
            
        Returns:
            Generated selector string
        """
        print(f"\n🔍 Debugging selector creation for '{element_name}' on: {url}")
        print("-" * 60)
        
        try:
            selector = self.examples.create_selector_from_aria(url, element_name)
            
            print(f"✅ Generated selector: {selector}")
            
            # Try to test the selector if it looks valid
            if "page.get_by_" in selector and "not found" not in selector.lower():
                print("\n🧪 Testing the generated selector...")
                try:
                    # Navigate to the page first
                    self.examples.page.goto(url)
                    self.examples.page.wait_for_load_state("networkidle")
                    
                    # Try to find the element using different strategies
                    if "get_by_role" in selector:
                        # Extract role and name from selector
                        import re
                        match = re.search(r"get_by_role\('([^']+)', name='([^']+)'\)", selector)
                        if match:
                            role, name = match.groups()
                            element = self.examples.page.get_by_role(role, name=name)
                            if element.count() > 0:
                                print(f"    ✅ Element found using get_by_role('{role}', name='{name}')")
                                print(f"    📊 Found {element.count()} matching elements")
                            else:
                                print(f"    ❌ No elements found using get_by_role('{role}', name='{name}')")
                
                except Exception as test_e:
                    print(f"    ⚠️  Could not test selector: {test_e}")
            
            return selector
            
        except Exception as e:
            print(f"❌ Error creating selector: {e}")
            raise
    
    def debug_page_info(self, url: str):
        """
        Debug general page information
        
        Args:
            url: The URL to debug
        """
        print(f"\n🔍 Debugging page information for: {url}")
        print("-" * 60)
        
        try:
            # Navigate to the page
            self.examples.page.goto(url)
            self.examples.page.wait_for_load_state("networkidle")
            
            # Get basic page info
            title = self.examples.page.title()
            current_url = self.examples.page.url
            
            print(f"📄 Page Title: {title}")
            print(f"🔗 Final URL: {current_url}")
            print(f"🖼️  Viewport: {self.examples.page.viewport_size}")
            
            # Check for common elements
            buttons = self.examples.page.locator("button").count()
            links = self.examples.page.locator("a").count()
            inputs = self.examples.page.locator("input").count()
            
            print(f"\n📊 Element counts:")
            print(f"  Buttons: {buttons}")
            print(f"  Links: {links}")
            print(f"  Inputs: {inputs}")
            
            # Check if page has accessibility tree
            try:
                snapshot = self.examples.page.accessibility.snapshot(interesting_only=True)
                if snapshot:
                    print(f"  ✅ Accessibility tree available")
                    print(f"  🌳 Root role: {snapshot.get('role', 'Unknown')}")
                else:
                    print(f"  ❌ No accessibility tree available")
            except Exception:
                print(f"  ❌ Error accessing accessibility tree")
            
        except Exception as e:
            print(f"❌ Error getting page info: {e}")
            raise
    
    def interactive_debug(self):
        """Run interactive debugging session"""
        print("🔧 ARIA Snapshot Interactive Debugger")
        print("=" * 50)
        
        # Get URL from user
        default_url = "https://www.jd.com"
        url = input(f"Enter URL to debug (default: {default_url}): ").strip()
        if not url:
            url = default_url
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"\n🎯 Target URL: {url}")
        
        try:
            self.setup()
            
            while True:
                print("\n" + "="*50)
                print("Debug Options:")
                print("1. Basic ARIA snapshot")
                print("2. Find interactive elements")
                print("3. Find specific role elements")
                print("4. Analyze forms")
                print("5. Create selector for element")
                print("6. Page information")
                print("7. Change URL")
                print("8. Save snapshot to file")
                print("0. Exit")
                
                choice = input("\nEnter your choice (0-8): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.debug_basic_snapshot(url)
                elif choice == "2":
                    self.debug_interactive_elements(url)
                elif choice == "3":
                    role = input("Enter ARIA role (button, link, textbox, etc.): ").strip()
                    if role:
                        self.debug_specific_role(url, role)
                elif choice == "4":
                    self.debug_form_analysis(url)
                elif choice == "5":
                    element_name = input("Enter element name to find: ").strip()
                    if element_name:
                        self.debug_selector_creation(url, element_name)
                elif choice == "6":
                    self.debug_page_info(url)
                elif choice == "7":
                    new_url = input("Enter new URL: ").strip()
                    if new_url:
                        if not new_url.startswith(('http://', 'https://')):
                            new_url = 'https://' + new_url
                        url = new_url
                        print(f"🎯 New target URL: {url}")
                elif choice == "8":
                    self.save_snapshot_to_file(url)
                else:
                    print("❌ Invalid choice. Please enter a number between 0-8.")
        
        finally:
            self.cleanup()
    
    def save_snapshot_to_file(self, url: str):
        """Save ARIA snapshot to a JSON file"""
        try:
            snapshot = self.debug_basic_snapshot(url)
            
            # Create filename from URL
            import re
            clean_url = re.sub(r'[^\w\-_\.]', '_', url.replace('https://', '').replace('http://', ''))
            filename = f"aria_snapshot_{clean_url}_{int(__import__('time').time())}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Snapshot saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error saving snapshot: {e}")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug ARIA snapshot functionality with real websites")
    parser.add_argument("--url", "-u", default="https://www.jd.com", 
                        help="URL to debug (default: https://www.jd.com)")
    parser.add_argument("--function", "-f", choices=[
        "basic", "interactive", "forms", "elements", "role", "selector", "info"
    ], help="Specific function to debug")
    parser.add_argument("--role", "-r", help="ARIA role to search for (use with --function role)")
    parser.add_argument("--element", "-e", help="Element name to create selector for (use with --function selector)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no browser window)")
    parser.add_argument("--slow", type=int, default=0, help="Slow down operations by N milliseconds")
    
    args = parser.parse_args()
    
    debugger = ARIADebugger(headless=args.headless, slow_mo=args.slow)
    
    try:
        debugger.setup()
        
        if args.function == "basic":
            debugger.debug_basic_snapshot(args.url)
        elif args.function == "interactive":
            debugger.debug_interactive_elements(args.url)
        elif args.function == "forms":
            debugger.debug_form_analysis(args.url)
        elif args.function == "elements":
            debugger.debug_interactive_elements(args.url)
        elif args.function == "role":
            if not args.role:
                print("❌ --role parameter required for 'role' function")
                return 1
            debugger.debug_specific_role(args.url, args.role)
        elif args.function == "selector":
            if not args.element:
                print("❌ --element parameter required for 'selector' function")
                return 1
            debugger.debug_selector_creation(args.url, args.element)
        elif args.function == "info":
            debugger.debug_page_info(args.url)
        else:
            # Interactive mode
            debugger.cleanup()
            debugger.interactive_debug()
            return 0
        
    finally:
        debugger.cleanup()
    
    return 0


if __name__ == "__main__":
    exit(main())