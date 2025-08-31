#!/usr/bin/env python3
"""
Simple ARIA Snapshot Function Debugging Examples
================================================

This script shows how to run individual ARIA snapshot functions
for debugging specific websites like www.jd.com
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from examples.aria_snapshot_usage import ARIASnapshotExamples


def debug_local_search_elements():
    """Debug finding search-related elements on the local test page"""
    print("🔍 Debugging local search elements")
    print("="*50)
    
    examples = ARIASnapshotExamples()
    
    try:
        examples.setup()
        
        # Define the path to the local HTML file
        local_page_path = project_root / "tests" / "fixtures" / "sample_pages" / "search_page.html"
        
        # Find search-related elements
        search_elements = examples.find_elements_by_role(str(local_page_path), "textbox")
        
        print(f"Found {len(search_elements)} textbox elements:")
        for elem in search_elements:
            print(f"  - Name: {elem.get('name', '(no name)')}")
            print(f"    Description: {elem.get('description', '(no description)')}")
            print(f"    Value: {elem.get('value', '(empty)')}")
            print()
        
        # Try to create a selector for the search box
        print("Creating selector for search button...")
        selector = examples.create_selector_from_aria(str(local_page_path), "搜索")
        print(f"Generated selector: {selector}")
        
    finally:
        examples.cleanup()


def debug_local_buttons():
    """Debug finding buttons on the local test page"""
    print("🔍 Debugging local buttons")
    print("="*50)
    
    examples = ARIASnapshotExamples()
    
    try:
        examples.setup()
        
        # Define the path to the local HTML file
        local_page_path = project_root / "tests" / "fixtures" / "sample_pages" / "search_page.html"
        
        # Find all buttons
        buttons = examples.find_elements_by_role(str(local_page_path), "button")
        
        print(f"Found {len(buttons)} button elements:")
        for i, button in enumerate(buttons):
            print(f"  {i+1}. Name: {button.get('name', '(no name)')}")
            print(f"     Description: {button.get('description', '(no description)')}")
            print()
        
    finally:
        examples.cleanup()


def debug_local_full_snapshot():
    """Debug getting full ARIA snapshot of the local test page"""
    print("🔍 Debugging local full snapshot")
    print("="*50)
    
    examples = ARIASnapshotExamples()
    
    try:
        examples.setup()
        
        # Define the path to the local HTML file
        local_page_path = project_root / "tests" / "fixtures" / "sample_pages" / "search_page.html"
        
        # Get basic snapshot info (truncated for readability)
        snapshot = examples.basic_aria_snapshot(str(local_page_path))
        
        print(f"Root role: {snapshot.get('role')}")
        print(f"Page name: {snapshot.get('name')}")
        print(f"Number of children: {len(snapshot.get('children', []))}")
        
        # Show first few children
        children = snapshot.get('children', [])
        print(f"\nFirst 5 child elements:")
        for i, child in enumerate(children[:5]):
            role = child.get('role', 'unknown')
            name = child.get('name', '(no name)')[:50]
            print(f"  {i+1}. {role}: {name}")
        
        if len(children) > 5:
            print(f"  ... and {len(children) - 5} more children")
            
        # Save snapshot to file for detailed analysis
        import json
        import time
        filename = f"local_debug_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Full snapshot saved to: {filename}")
        
    finally:
        examples.cleanup()


def debug_specific_website(url):
    """Debug a specific website's ARIA structure"""
    print(f"🔍 Debugging ARIA structure for: {url}")
    print("="*60)
    
    examples = ARIASnapshotExamples()
    
    try:
        examples.setup()
        
        # Get page info with custom timeout
        print(f"Navigating to {url}")
        examples.page.goto(url, timeout=60000)  # Increased timeout to 60 seconds
        
        # Wait for initial page load but don't wait for all network activity
        examples.page.wait_for_load_state("domcontentloaded")  # Changed from networkidle to domcontentloaded
        print("Page DOM loaded")
        
        # Wait a bit more for JavaScript to settle
        examples.page.wait_for_timeout(5000)  # Wait 5 seconds for JS to settle
        
        title = examples.page.title()
        print(f"📄 Page Title: {title}")
        
        # Find interactive elements
        try:
            interactive = examples.find_interactive_elements(url)
            
            # Group by role
            by_role = {}
            for elem in interactive:
                role = elem.get('role', 'unknown')
                if role not in by_role:
                    by_role[role] = 0
                by_role[role] += 1
            
            print(f"\n📊 Interactive elements summary:")
            for role, count in sorted(by_role.items()):
                print(f"  {role}: {count}")
            
            # Try common element searches
            print(f"\n🔍 Looking for common elements:")
            
            # Search boxes
            search_boxes = examples.find_elements_by_role(url, "searchbox")
            textboxes = examples.find_elements_by_role(url, "textbox")
            print(f"  Search boxes: {len(search_boxes)}")
            print(f"  Text inputs: {len(textboxes)}")
            
            # Buttons
            buttons = examples.find_elements_by_role(url, "button")
            print(f"  Buttons: {len(buttons)}")
            
            # Links
            links = examples.find_elements_by_role(url, "link")
            print(f"  Links: {len(links)}")
            
            if search_boxes or textboxes:
                search_elements = search_boxes + textboxes
                first_search = search_elements[0]
                search_name = first_search.get('name', 'search')
                print(f"\n🎯 Creating selector for search element: '{search_name}'")
                selector = examples.create_selector_from_aria(url, search_name)
                print(f"   Selector: {selector}")
        except Exception as e:
            print(f"❌ Error during ARIA analysis: {e}")
            
    finally:
        examples.cleanup()


if __name__ == "__main__":
    print("ARIA Snapshot Function Debugging Examples")
    print("="*50)
    
    # Choose what to run
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "search":
            debug_local_search_elements()
        elif command == "buttons":
            debug_local_buttons()
        elif command == "full":
            debug_local_full_snapshot()
        elif command == "site" and len(sys.argv) > 2:
            debug_specific_website(sys.argv[2])
        else:
            print("❌ Unknown command or missing URL")
            print("Usage:")
            print("  python simple_aria_debug.py search     # Debug JD.com search elements")
            print("  python simple_aria_debug.py buttons    # Debug JD.com buttons") 
            print("  python simple_aria_debug.py full       # Debug JD.com full snapshot")
            print("  python simple_aria_debug.py site <URL> # Debug specific website")
    else:
        print("Choose what to debug:")
        print("1. JD.com search elements")
        print("2. JD.com buttons") 
        print("3. JD.com full snapshot")
        print("4. Custom website")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            debug_local_search_elements()
        elif choice == "2":
            debug_local_buttons()
        elif choice == "3":
            debug_local_full_snapshot()
        elif choice == "4":
            url = input("Enter website URL: ").strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            debug_specific_website(url)
        else:
            print("❌ Invalid choice")