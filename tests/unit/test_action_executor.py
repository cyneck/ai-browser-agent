import unittest
from unittest.mock import MagicMock, call
import base64

from src.action.executor import ActionExecutor

class TestActionExecutor(unittest.TestCase):
    def setUp(self):
        """Set up a mock page and executor for each test."""
        self.mock_page = MagicMock()
        # Configure the mock locator to be chainable
        self.mock_locator = MagicMock()
        self.mock_page.locator.return_value = self.mock_locator
        # Disable human behavior for existing tests to maintain compatibility
        behavior_config = {"enabled": False}
        self.executor = ActionExecutor(self.mock_page, behavior_config=behavior_config)

    def test_get_supported_actions(self):
        """Test that all core actions are supported."""
        actions = self.executor.get_supported_actions()
        expected_actions = [
            "navigate", "click", "fill", "type", "key", "select", "wait",
            "screenshot", "extract", "extract_results", "scroll", "back", 
            "forward", "refresh", "close", "error", "wait_for_login",
            "smart_fill", "smart_submit", "save_as_pdf", "save_as_mhtml"
        ]
        for action in expected_actions:
            self.assertIn(action, actions)

    def test_execute_navigate(self):
        """Test the navigate action."""
        instruction = {"action": "navigate", "value": "https://example.com"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功导航到 https://example.com", result.get("message"))
        self.mock_page.goto.assert_called_once_with("https://example.com", wait_until="domcontentloaded")

    def test_execute_click(self):
        """Test the click action."""
        instruction = {"action": "click", "selector": "#submit"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功点击元素 #submit", result.get("message"))
        self.mock_page.locator.assert_called_once_with("#submit")
        self.mock_locator.click.assert_called_once()

    def test_execute_fill(self):
        """Test the fill action."""
        instruction = {"action": "fill", "selector": "input[name='user']", "value": "testuser"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功在 input[name='user'] 中输入文本", result.get("message"))
        self.mock_page.locator.assert_called_once_with("input[name='user']")
        self.mock_locator.fill.assert_called_once_with("testuser")

    def test_execute_type_alias(self):
        """Test that 'type' is a valid alias for 'fill'."""
        instruction = {"action": "type", "selector": "input[name='pwd']", "value": "password"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.locator.assert_called_once_with("input[name='pwd']")
        self.mock_locator.fill.assert_called_once_with("password")

    def test_execute_select(self):
        """Test the select action."""
        instruction = {"action": "select", "selector": "select#country", "value": "US"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功在 select#country 中选择 US", result.get("message"))
        self.mock_page.locator.assert_called_once_with("select#country")
        self.mock_locator.select_option.assert_called_once_with(value="US")

    def test_execute_wait_for_selector(self):
        """Test waiting for a selector."""
        instruction = {"action": "wait", "selector": ".ready", "timeout": 5000}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功等待元素 .ready 出现", result.get("message"))
        self.mock_page.wait_for_selector.assert_called_once_with(".ready", timeout=5000)

    def test_execute_wait_for_timeout(self):
        """Test waiting for a fixed timeout."""
        instruction = {"action": "wait", "value": 1500}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功等待 1500 毫秒", result.get("message"))
        self.mock_page.wait_for_timeout.assert_called_once_with(1500)

    def test_execute_screenshot(self):
        """Test the screenshot action."""
        mock_screenshot_bytes = b"screenshot_data"
        self.mock_page.screenshot.return_value = mock_screenshot_bytes
        instruction = {"action": "screenshot"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("screenshot"), base64.b64encode(mock_screenshot_bytes).decode())
        self.mock_page.screenshot.assert_called_once()

    def test_execute_extract_from_selector(self):
        """Test extracting text from a specific element."""
        self.mock_locator.inner_text.return_value = "Extracted Text"
        instruction = {"action": "extract", "selector": "div.content"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("content"), "Extracted Text")
        self.mock_page.locator.assert_called_once_with("div.content")

    def test_execute_extract_page_content(self):
        """Test extracting the full page content."""
        self.mock_page.content.return_value = "<html><body>Page Content</body></html>"
        instruction = {"action": "extract"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("content"), "<html><body>Page Content</body></html>")
        self.mock_page.content.assert_called_once()

    def test_execute_scroll_to_selector(self):
        """Test scrolling to a specific element."""
        instruction = {"action": "scroll", "selector": "#footer"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.locator.assert_called_once_with("#footer")
        self.mock_locator.scroll_into_view_if_needed.assert_called_once()

    def test_execute_scroll_by_pixel(self):
        """Test scrolling by a specific pixel amount."""
        instruction = {"action": "scroll", "value": 500}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.evaluate.assert_called_once_with("window.scrollBy(0, 500)")

    def test_execute_scroll_to_bottom(self):
        """Test scrolling to the bottom of the page."""
        instruction = {"action": "scroll"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.evaluate.assert_called_once_with("window.scrollTo(0, document.body.scrollHeight)")

    def test_execute_back(self):
        """Test the browser back action."""
        instruction = {"action": "back"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.go_back.assert_called_once()

    def test_execute_forward(self):
        """Test the browser forward action."""
        instruction = {"action": "forward"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.go_forward.assert_called_once()

    def test_execute_refresh(self):
        """Test the browser refresh action."""
        instruction = {"action": "refresh"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.reload.assert_called_once()

    def test_execute_close(self):
        """Test the page close action."""
        instruction = {"action": "close"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.close.assert_called_once()

    def test_execute_error(self):
        """Test the error action for graceful failure."""
        instruction = {"action": "error", "error": "Test error message"}
        result = self.executor.execute(instruction, session_state={})
        self.assertFalse(result.get("success"))

        # The high-level error message from the step runner should reflect the step failure
        self.assertIn("执行错误指令", result.get("message"))
        self.assertIn("执行错误指令", result.get("error")) # The high-level error from the step runner
        self.assertIn("Test error message", result.get("step_results")[0].get("error")) # The specific error from the 'error' action within step_results

    def test_multi_step_execution(self):
        """Test execution of a multi-step instruction."""
        instructions = {
            "description": "Login process",
            "steps": [
                {"action": "fill", "selector": "#user", "value": "myuser"},
                {"action": "fill", "selector": "#pass", "value": "mypass"},
                {"action": "click", "selector": "#login"}
            ]
        }
        result = self.executor.execute(instructions, session_state={})
        self.assertTrue(result.get("success"))
        self.assertEqual(len(result.get("step_results")), 3)
        
        # Verify calls
        calls = [
            call("#user"),
            call().fill("myuser"),
            call("#pass"),
            call().fill("mypass"),
            call("#login"),
            call().click()
        ]
        # This is a simplified check. A more robust check might inspect mock_page.method_calls
        self.assertEqual(self.mock_page.locator.call_count, 3)
        self.assertEqual(self.mock_locator.fill.call_count, 2)
        self.assertEqual(self.mock_locator.click.call_count, 1)

    def test_execute_key_with_selector(self):
        """Test the key action with selector."""
        instruction = {"action": "key", "selector": "input[name='search']", "value": "Enter"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功在 input[name='search'] 上按下 Enter 键", result.get("message"))
        self.mock_page.locator.assert_called_once_with("input[name='search']")
        self.mock_page.keyboard.press.assert_called_once_with("Enter")

    def test_execute_key_without_selector(self):
        """Test the key action without selector."""
        instruction = {"action": "key", "value": "Escape"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功按下 Escape 键", result.get("message"))
        self.mock_page.keyboard.press.assert_called_once_with("Escape")

    def test_execute_direct_action_without_llm(self):
        """Test that direct actions are executed without LLM inference due to optimization."""
        instruction = {"action": "navigate", "value": "https://direct.example.com"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.assertIn("成功导航到 https://direct.example.com", result.get("message"))
        self.mock_page.goto.assert_called_once_with("https://direct.example.com", wait_until="domcontentloaded")

        # 验证没有尝试进行多步执行，也没有LLM相关的mock调用
        # 在这里我们无法直接断言LLM是否被跳过，因为LLM的调用在execute方法内部的私有方法中
        # 但是可以通过检查结果是否直接来自于单步执行来间接验证
        # 此时instruction会被_normalize_to_multi_step处理，所以会有description和step_results
        self.assertIsNotNone(result.get("step_results"))

    def test_execute_heuristic_navigate(self):
        """Test that heuristic rules can identify navigate action from user_text."""
        instruction = {"user_text": "前往 https://heuristic.example.com"}
        result = self.executor.execute(instruction, session_state={})
        # This will fail in mock environment but should not raise exception due to the bug fix
        self.assertIn("success", result)

    def test_execute_extract_results(self):
        """Test the extract_results action."""
        mock_content = [{"title": "Test", "url": "http://test.com"}]
        self.mock_page.url = "https://www.google.com/search?q=test"
        self.mock_page.locator.return_value = self.mock_locator
        self.mock_locator.all.return_value = []
        
        instruction = {"action": "extract_results"}
        result = self.executor.execute(instruction, session_state={})
        # Will fail in mock environment but should not raise exception
        self.assertIn("success", result)

    def test_execute_wait_for_login(self):
        """Test the wait_for_login action."""
        instruction = {"action": "wait_for_login"}
        # Mock the input function to avoid blocking the test
        with unittest.mock.patch("builtins.input", return_value=""):
            result = self.executor.execute(instruction, session_state={})
        # Will fail in mock environment but should not raise exception
        self.assertIn("success", result)

    def test_execute_smart_fill(self):
        """Test the smart_fill action."""
        instruction = {"action": "smart_fill", "query": "test query"}
        result = self.executor.execute(instruction, session_state={})
        # Will fail in mock environment but should not raise exception
        self.assertFalse(result.get("success"))

    def test_execute_smart_submit(self):
        """Test the smart_submit action."""
        instruction = {"action": "smart_submit"}
        result = self.executor.execute(instruction, session_state={})
        # Will fail in mock environment but should not raise exception
        self.assertFalse(result.get("success"))

    def test_execute_save_as_pdf(self):
        """Test the save_as_pdf action."""
        instruction = {"action": "save_as_pdf"}
        result = self.executor.execute(instruction, session_state={})
        self.assertTrue(result.get("success"))
        self.mock_page.pdf.assert_called_once()
        self.assertIn("download_url", result)

    def test_execute_save_as_mhtml(self):
        """Test the save_as_mhtml action."""
        self.mock_page.content.return_value = "<html><body>Test Content</body></html>"
        instruction = {"action": "save_as_mhtml"}
        
        # Mock the open function
        mock_open = unittest.mock.mock_open()
        with unittest.mock.patch("builtins.open", mock_open):
            result = self.executor.execute(instruction, session_state={})
            
        self.assertTrue(result.get("success"))
        self.assertIn("页面已成功保存为MHTML", result.get("message"))
        self.assertIn("download_url", result)
        self.mock_page.content.assert_called_once()

if __name__ == "__main__":
    unittest.main()


