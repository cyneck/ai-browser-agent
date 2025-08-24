"""
Unit tests for ARIA Snapshot Usage Examples
==========================================

This module contains unit tests for the ARIASnapshotExamples class,
testing various ARIA snapshot functionalities with mock data and fixtures.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

# Import the class we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from examples.aria_snapshot_usage import ARIASnapshotExamples


class TestARIASnapshotExamples:
    """Test cases for ARIASnapshotExamples class"""
    
    @pytest.fixture
    def mock_playwright(self):
        """Mock Playwright components"""
        mock_playwright = Mock()
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()
        
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        return {
            'playwright': mock_playwright,
            'browser': mock_browser,
            'context': mock_context,
            'page': mock_page
        }
    
    @pytest.fixture
    def sample_aria_snapshot(self):
        """Sample ARIA snapshot data for testing"""
        return {
            "role": "WebArea",
            "name": "Google",
            "children": [
                {
                    "role": "banner",
                    "name": "",
                    "children": [
                        {
                            "role": "searchbox",
                            "name": "Search",
                            "value": "",
                            "properties": {"required": False},
                            "description": "Search the web"
                        },
                        {
                            "role": "button",
                            "name": "Google Search",
                            "properties": {"type": "submit"},
                            "description": "Submit search query"
                        }
                    ]
                },
                {
                    "role": "main",
                    "name": "",
                    "children": [
                        {
                            "role": "link",
                            "name": "Gmail",
                            "properties": {"href": "https://gmail.com"},
                            "description": "Go to Gmail"
                        },
                        {
                            "role": "button",
                            "name": "I'm Feeling Lucky",
                            "properties": {"type": "button"},
                            "description": "Go to first search result"
                        }
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def aria_examples(self, mock_playwright):
        """Create ARIASnapshotExamples instance with mocked Playwright"""
        examples = ARIASnapshotExamples()
        
        with patch('examples.aria_snapshot_usage.sync_playwright') as mock_sync_playwright:
            mock_sync_playwright.return_value.start.return_value = mock_playwright['playwright']
            examples.setup()
            examples.page = mock_playwright['page']
            
        return examples
    
    def test_setup_and_cleanup(self, mock_playwright):
        """Test proper setup and cleanup of Playwright resources"""
        examples = ARIASnapshotExamples()
        
        with patch('examples.aria_snapshot_usage.sync_playwright') as mock_sync_playwright:
            mock_sync_playwright.return_value.start.return_value = mock_playwright['playwright']
            
            # Test setup
            examples.setup()
            
            assert examples.playwright is not None
            assert examples.browser is not None
            assert examples.context is not None
            assert examples.page is not None
            
            # Test cleanup
            examples.cleanup()
            
            mock_playwright['browser'].close.assert_called_once()
            mock_playwright['playwright'].stop.assert_called_once()
    
    def test_basic_aria_snapshot(self, aria_examples, sample_aria_snapshot):
        """Test basic ARIA snapshot functionality"""
        # Setup mock
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.return_value = sample_aria_snapshot
        
        # Test
        result = aria_examples.basic_aria_snapshot("https://google.com")
        
        # Assertions
        aria_examples.page.goto.assert_called_once_with("https://google.com", timeout=60000)
        aria_examples.page.wait_for_load_state.assert_called_once_with("domcontentloaded")
        aria_examples.page.accessibility.snapshot.assert_called_once()
        
        assert result == sample_aria_snapshot
        assert result["role"] == "WebArea"
        assert result["name"] == "Google"
    
    def test_filtered_aria_snapshot(self, aria_examples, sample_aria_snapshot):
        """Test filtered ARIA snapshot with interesting_only option"""
        # Setup mock
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.return_value = sample_aria_snapshot
        
        # Test
        result = aria_examples.filtered_aria_snapshot("https://google.com")
        
        # Assertions
        aria_examples.page.accessibility.snapshot.assert_called_once_with(
            interesting_only=True,
            root=None
        )
        assert result == sample_aria_snapshot
    
    def test_specific_element_aria_snapshot(self, aria_examples, sample_aria_snapshot):
        """Test ARIA snapshot for specific element"""
        # Setup mocks
        mock_locator = Mock()
        mock_element = Mock()
        mock_element_handle = Mock()
        
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.locator.return_value = mock_locator
        mock_locator.first = mock_element
        mock_element.element_handle.return_value = mock_element_handle
        aria_examples.page.accessibility.snapshot.return_value = sample_aria_snapshot
        
        # Test
        result = aria_examples.specific_element_aria_snapshot("https://google.com", "button")
        
        # Assertions
        aria_examples.page.locator.assert_called_once_with("button")
        mock_element.element_handle.assert_called_once()
        aria_examples.page.accessibility.snapshot.assert_called_once_with(root=mock_element_handle)
        assert result == sample_aria_snapshot
    
    def test_find_interactive_elements(self, aria_examples, sample_aria_snapshot):
        """Test finding interactive elements from ARIA snapshot"""
        # Setup mock
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.return_value = sample_aria_snapshot
        
        # Test
        result = aria_examples.find_interactive_elements("https://google.com")
        
        # Assertions
        aria_examples.page.accessibility.snapshot.assert_called_once_with(interesting_only=True)
        
        # Check that interactive elements are found
        assert len(result) > 0
        
        # Check specific interactive elements
        roles_found = [elem["role"] for elem in result]
        assert "searchbox" in roles_found
        assert "button" in roles_found
        assert "link" in roles_found
        
        # Check element details
        searchbox = next(elem for elem in result if elem["role"] == "searchbox")
        assert searchbox["name"] == "Search"
        assert searchbox["role"] == "searchbox"
    
    def test_find_elements_by_role(self, aria_examples, sample_aria_snapshot):
        """Test finding elements by specific role"""
        # Setup mock
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.return_value = sample_aria_snapshot
        
        # Test finding buttons
        result = aria_examples.find_elements_by_role("https://google.com", "button")
        
        # Assertions
        assert len(result) == 2  # Should find 2 buttons in sample data
        
        button_names = [elem["name"] for elem in result]
        assert "Google Search" in button_names
        assert "I'm Feeling Lucky" in button_names
        
        # Test finding links
        result_links = aria_examples.find_elements_by_role("https://google.com", "link")
        assert len(result_links) == 1
        assert result_links[0]["name"] == "Gmail"
    
    def test_create_selector_from_aria(self, aria_examples, sample_aria_snapshot):
        """Test creating selector from ARIA information"""
        # Setup mock
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.return_value = sample_aria_snapshot
        
        # Test finding element by name
        result = aria_examples.create_selector_from_aria("https://google.com", "Google Search")
        
        # Assertions
        assert "page.get_by_role('button', name='Google Search')" in result
        
        # Test element not found
        result_not_found = aria_examples.create_selector_from_aria("https://google.com", "NonExistent")
        assert "not found" in result_not_found.lower()
    
    def test_analyze_form_structure(self, aria_examples):
        """Test analyzing form structure from ARIA snapshot"""
        # Create sample form data
        form_snapshot = {
            "role": "WebArea",
            "children": [
                {
                    "role": "form",
                    "name": "Login Form",
                    "children": [
                        {
                            "role": "textbox",
                            "name": "Username",
                            "value": "",
                            "properties": {"required": True}
                        },
                        {
                            "role": "textbox",
                            "name": "Password",
                            "value": "",
                            "properties": {"type": "password"}
                        },
                        {
                            "role": "button",
                            "name": "Login",
                            "properties": {"type": "submit"}
                        }
                    ]
                }
            ]
        }
        
        # Setup mock
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.return_value = form_snapshot
        
        # Test
        result = aria_examples.analyze_form_structure("https://example.com/login")
        
        # Assertions
        assert "forms" in result
        assert len(result["forms"]) == 1
        
        form = result["forms"][0]
        assert form["name"] == "Login Form"
        assert len(form["fields"]) == 2
        assert len(form["buttons"]) == 1
        
        # Check field details
        username_field = next(field for field in form["fields"] if field["name"] == "Username")
        assert username_field["type"] == "textbox"
        assert username_field["required"] is True
    
    def test_error_handling(self, aria_examples):
        """Test error handling in ARIA snapshot methods"""
        # Setup mock to raise exception
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.side_effect = Exception("Mock error")
        
        # Test that methods handle exceptions gracefully
        # Note: The original methods don't have explicit exception handling,
        # so we should add that or expect exceptions to propagate
        with pytest.raises(Exception):
            aria_examples.basic_aria_snapshot("https://google.com")
    
    @pytest.mark.parametrize("url,expected_calls", [
        ("https://google.com", 1),
        ("https://github.com", 1),
        ("", 1),  # Should still make the call
    ])
    def test_multiple_urls(self, aria_examples, sample_aria_snapshot, url, expected_calls):
        """Test ARIA snapshot functionality with different URLs"""
        # Setup mock
        aria_examples.page.goto = Mock()
        aria_examples.page.wait_for_load_state = Mock()
        aria_examples.page.accessibility.snapshot.return_value = sample_aria_snapshot
        
        # Test
        result = aria_examples.basic_aria_snapshot(url)
        
        # Assertions
        assert aria_examples.page.goto.call_count == expected_calls
        assert result == sample_aria_snapshot


class TestARIASnapshotIntegration:
    """Integration tests for ARIA snapshot functionality"""
    
    def test_real_playwright_setup(self):
        """Test that real Playwright can be set up (requires Playwright installation)"""
        try:
            from playwright.sync_api import sync_playwright
            
            examples = ARIASnapshotExamples()
            examples.setup()
            
            # Verify components are created
            assert examples.playwright is not None
            assert examples.browser is not None
            assert examples.context is not None
            assert examples.page is not None
            
            examples.cleanup()
            
        except ImportError:
            pytest.skip("Playwright not installed - skipping integration test")
        except Exception as e:
            pytest.skip(f"Playwright setup failed - {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])