"""
Integration tests for ARIA Snapshot Usage
=========================================

This module contains integration tests that use real web pages
to test ARIA snapshot functionality end-to-end.
"""

import pytest
import json
import os
from typing import Dict, Any

# Import the class we're testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from examples.aria_snapshot_usage import ARIASnapshotExamples


class TestARIASnapshotIntegration:
    """Integration tests using real web pages"""
    
    @pytest.fixture(scope="class")
    def examples(self):
        """Create ARIASnapshotExamples instance for integration tests"""
        try:
            examples = ARIASnapshotExamples()
            examples.setup()
            yield examples
            examples.cleanup()
        except Exception as e:
            pytest.skip(f"Could not setup Playwright: {e}")
    
    @pytest.fixture
    def test_html_file(self, tmp_path):
        """Create a test HTML file for consistent testing"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Test Page for ARIA Snapshot</title>
        </head>
        <body>
            <header>
                <h1>Test Website</h1>
                <nav aria-label="Main navigation">
                    <ul>
                        <li><a href="#home">Home</a></li>
                        <li><a href="#about">About</a></li>
                        <li><a href="#contact">Contact</a></li>
                    </ul>
                </nav>
            </header>
            
            <main>
                <section>
                    <h2>Search Section</h2>
                    <form role="search" aria-label="Site search">
                        <label for="search-input">Search:</label>
                        <input type="search" 
                               id="search-input" 
                               name="q" 
                               aria-describedby="search-help"
                               placeholder="Enter search terms">
                        <button type="submit" aria-label="Submit search">Search</button>
                        <p id="search-help">Enter keywords to search the site</p>
                    </form>
                </section>
                
                <section>
                    <h2>Contact Form</h2>
                    <form aria-label="Contact form">
                        <div>
                            <label for="name">Name:</label>
                            <input type="text" 
                                   id="name" 
                                   name="name" 
                                   required 
                                   aria-describedby="name-help">
                            <p id="name-help">Enter your full name</p>
                        </div>
                        
                        <div>
                            <label for="email">Email:</label>
                            <input type="email" 
                                   id="email" 
                                   name="email" 
                                   required>
                        </div>
                        
                        <div>
                            <label for="message">Message:</label>
                            <textarea id="message" 
                                     name="message" 
                                     rows="4" 
                                     aria-describedby="message-help"></textarea>
                            <p id="message-help">Describe your inquiry</p>
                        </div>
                        
                        <div>
                            <input type="checkbox" 
                                   id="newsletter" 
                                   name="newsletter">
                            <label for="newsletter">Subscribe to newsletter</label>
                        </div>
                        
                        <button type="submit">Send Message</button>
                        <button type="reset">Clear Form</button>
                    </form>
                </section>
                
                <section>
                    <h2>Interactive Elements</h2>
                    <button onclick="alert('Hello!')">Click Me</button>
                    <a href="https://example.com" target="_blank">External Link</a>
                    
                    <div role="tablist" aria-label="Example tabs">
                        <button role="tab" 
                                aria-selected="true" 
                                aria-controls="tab1-panel" 
                                id="tab1">Tab 1</button>
                        <button role="tab" 
                                aria-selected="false" 
                                aria-controls="tab2-panel" 
                                id="tab2">Tab 2</button>
                    </div>
                    
                    <div role="tabpanel" 
                         aria-labelledby="tab1" 
                         id="tab1-panel">
                        <p>Content for tab 1</p>
                    </div>
                    
                    <div role="tabpanel" 
                         aria-labelledby="tab2" 
                         id="tab2-panel" 
                         hidden>
                        <p>Content for tab 2</p>
                    </div>
                </section>
            </main>
            
            <footer>
                <p>&copy; 2024 Test Website. All rights reserved.</p>
            </footer>
        </body>
        </html>
        """
        
        test_file = tmp_path / "test_page.html"
        test_file.write_text(html_content, encoding='utf-8')
        return f"file://{test_file.resolve()}"
    
    def test_basic_aria_snapshot_with_real_page(self, examples, test_html_file):
        """Test basic ARIA snapshot with a real HTML page"""
        snapshot = examples.basic_aria_snapshot(test_html_file)
        
        # Verify basic structure
        assert snapshot is not None
        assert "role" in snapshot
        assert snapshot["role"] in ["WebArea", "document"]  # Different browsers may return different roles
        
        # Should have children
        assert "children" in snapshot
        assert len(snapshot["children"]) > 0
    
    def test_find_interactive_elements_real_page(self, examples, test_html_file):
        """Test finding interactive elements on real page"""
        interactive_elements = examples.find_interactive_elements(test_html_file)
        
        # Verify we found interactive elements
        assert len(interactive_elements) > 0
        
        # Check for specific element types we expect
        roles_found = [elem["role"] for elem in interactive_elements]
        
        # Should find various interactive elements
        expected_roles = ["button", "link", "textbox", "searchbox", "checkbox"]
        found_expected = [role for role in expected_roles if role in roles_found]
        assert len(found_expected) > 0, f"Expected to find some of {expected_roles}, but only found {roles_found}"
        
        # Verify element details
        for elem in interactive_elements:
            assert "role" in elem
            assert "name" in elem
            assert "path" in elem
    
    def test_find_buttons_real_page(self, examples, test_html_file):
        """Test finding buttons on real page"""
        buttons = examples.find_elements_by_role(test_html_file, "button")
        
        # Should find multiple buttons
        assert len(buttons) >= 3  # Search, Send Message, Clear Form, Click Me, Tab buttons
        
        # Check button names
        button_names = [btn["name"] for btn in buttons]
        expected_names = ["Search", "Send Message", "Clear Form", "Click Me"]
        
        found_names = [name for name in expected_names if any(expected in btn_name for expected in [name] for btn_name in button_names)]
        assert len(found_names) > 0, f"Expected to find buttons with names like {expected_names}, but found {button_names}"
    
    def test_find_forms_real_page(self, examples, test_html_file):
        """Test finding and analyzing forms on real page"""
        form_analysis = examples.analyze_form_structure(test_html_file)
        
        # Should find forms
        assert "forms" in form_analysis
        forms = form_analysis["forms"]
        assert len(forms) >= 2  # Search form and Contact form
        
        # Check form details
        for form in forms:
            assert "name" in form
            assert "fields" in form
            assert "buttons" in form
            
            # Should have some fields
            if form["fields"]:  # Some forms might not be detected correctly
                for field in form["fields"]:
                    assert "type" in field
                    assert "name" in field
    
    def test_create_selectors_real_page(self, examples, test_html_file):
        """Test creating selectors from real page elements"""
        # Test creating selector for search button
        search_selector = examples.create_selector_from_aria(test_html_file, "Search")
        assert "page.get_by_role" in search_selector or "page.get_by_label" in search_selector
        
        # Test creating selector for non-existent element
        nonexistent_selector = examples.create_selector_from_aria(test_html_file, "NonExistentElement")
        assert "not found" in nonexistent_selector.lower()
    
    def test_specific_element_snapshot_real_page(self, examples, test_html_file):
        """Test getting ARIA snapshot for specific elements"""
        # Navigate to page first
        examples.page.goto(test_html_file)
        examples.page.wait_for_load_state("networkidle")
        
        # Test getting snapshot for search form
        form_snapshot = examples.specific_element_aria_snapshot(test_html_file, "form")
        
        assert form_snapshot is not None
        # Should have form-related structure
        assert "role" in form_snapshot
    
    @pytest.mark.slow
    def test_with_external_site(self, examples):
        """Test ARIA snapshot with a real external site (marked as slow)"""
        try:
            # Use a simple, stable website
            snapshot = examples.basic_aria_snapshot("https://httpbin.org/")
            
            assert snapshot is not None
            assert "role" in snapshot
            assert "children" in snapshot
            
        except Exception as e:
            pytest.skip(f"External site test failed (network issue?): {e}")
    
    def test_filtered_vs_full_snapshot(self, examples, test_html_file):
        """Compare filtered and full ARIA snapshots"""
        # Get both snapshots
        full_snapshot = examples.basic_aria_snapshot(test_html_file)
        filtered_snapshot = examples.filtered_aria_snapshot(test_html_file)
        
        # Both should exist
        assert full_snapshot is not None
        assert filtered_snapshot is not None
        
        # They might be the same or different depending on the page
        # The key is that both calls succeed
        assert "role" in full_snapshot
        assert "role" in filtered_snapshot
    
    def test_error_handling_invalid_url(self, examples):
        """Test error handling with invalid URLs"""
        with pytest.raises(Exception):
            examples.basic_aria_snapshot("invalid://not.a.real.url")
    
    def test_aria_snapshot_performance(self, examples, test_html_file):
        """Test performance of ARIA snapshot operations"""
        import time
        
        start_time = time.time()
        snapshot = examples.basic_aria_snapshot(test_html_file)
        end_time = time.time()
        
        # Should complete within reasonable time (adjust as needed)
        duration = end_time - start_time
        assert duration < 10.0, f"ARIA snapshot took too long: {duration} seconds"
        
        # Snapshot should be generated
        assert snapshot is not None
    
    def test_snapshot_content_consistency(self, examples, test_html_file):
        """Test that ARIA snapshots are consistent across multiple calls"""
        # Get snapshot twice
        snapshot1 = examples.basic_aria_snapshot(test_html_file)
        snapshot2 = examples.basic_aria_snapshot(test_html_file)
        
        # Should be consistent (though may not be identical due to timing)
        assert snapshot1["role"] == snapshot2["role"]
        assert len(snapshot1.get("children", [])) == len(snapshot2.get("children", []))


class TestARIASnapshotEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def examples(self):
        """Create ARIASnapshotExamples instance"""
        examples = ARIASnapshotExamples()
        try:
            examples.setup()
            yield examples
        finally:
            examples.cleanup()
    
    def test_empty_page(self, examples, tmp_path):
        """Test ARIA snapshot with minimal HTML"""
        minimal_html = """<!DOCTYPE html><html><head><title>Empty</title></head><body></body></html>"""
        test_file = tmp_path / "empty.html"
        test_file.write_text(minimal_html)
        
        snapshot = examples.basic_aria_snapshot(f"file://{test_file.resolve()}")
        
        assert snapshot is not None
        assert "role" in snapshot
    
    def test_page_with_no_interactive_elements(self, examples, tmp_path):
        """Test with page that has no interactive elements"""
        static_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Static Page</title></head>
        <body>
            <h1>Just Text</h1>
            <p>This page has no interactive elements.</p>
        </body>
        </html>
        """
        test_file = tmp_path / "static.html"
        test_file.write_text(static_html)
        
        interactive_elements = examples.find_interactive_elements(f"file://{test_file.resolve()}")
        
        # Should return empty list or very few elements
        assert isinstance(interactive_elements, list)
        # Might find some elements like document, but should be minimal


if __name__ == "__main__":
    # Run specific test classes
    pytest.main([__file__, "-v", "-m", "not slow"])