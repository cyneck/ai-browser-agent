#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Natural Language Interaction Demo for Xiaohongshu

This demonstrates the correct approach for testing Xiaohongshu with natural language:
- Uses keywords for search instead of full sentences
- Leverages aria-snapshots for DOM perception
- Uses LLM reasoning for selector and action selection
- Generates dynamic execution steps
"""

import requests
import json
import time
from pathlib import Path


class NaturalLanguageDemo:
    """Demonstration of proper natural language interaction with AI Browser Agent"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.session_id = "demo_session"
    
    def send_instruction(self, instruction: str, description: str = ""):
        """Send natural language instruction and display results"""
        print(f"\n{'='*60}")
        print(f"📝 Instruction: {instruction}")
        if description:
            print(f"🎯 Purpose: {description}")
        print(f"{'='*60}")
        
        payload = {"text": instruction, "session_id": self.session_id}
        
        try:
            response = requests.post(f"{self.base_url}/api/execute", json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {result.get('success', False)}")
                print(f"📋 Message: {result.get('message', 'No message')}")
                
                if result.get('error'):
                    print(f"❌ Error: {result.get('error')}")
                
                return result
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"💥 Exception: {e}")
            return {"success": False, "error": str(e)}
    
    def demonstrate_proper_approach(self):
        """Demonstrate the proper natural language approach"""
        print("🧠 AI Browser Agent - Natural Language Interaction Demo")
        print("=" * 60)
        print("🎯 Objective: Proper Xiaohongshu search using natural language")
        print("🔧 Method: LLM reasoning + DOM perception + Dynamic actions")
        print("=" * 60)
        
        # Step 1: Navigate using natural language
        self.send_instruction(
            "打开小红书网站",
            "Navigate to Xiaohongshu using natural language"
        )
        time.sleep(3)
        
        # Step 2: Analyze page structure intelligently
        self.send_instruction(
            "分析当前页面结构，识别搜索功能区域和可交互元素",
            "Use LLM to analyze DOM structure and identify search elements"
        )
        time.sleep(2)
        
        # Step 3: Search using keywords (not full sentences)
        self.send_instruction(
            "在搜索框输入关键词：北京 秋天",
            "Use keywords for search, not full sentences - proper approach"
        )
        time.sleep(3)
        
        # Step 4: Trigger search action
        self.send_instruction(
            "点击搜索按钮或按回车键开始检索",
            "Trigger search action using LLM-selected interaction method"
        )
        time.sleep(4)
        
        # Step 5: Extract content intelligently
        self.send_instruction(
            "提取前10个搜索结果，包括标题、作者、内容预览",
            "Use LLM reasoning to extract structured content from search results"
        )
        time.sleep(2)
        
        # Step 6: Take screenshot for documentation
        self.send_instruction(
            "截取屏幕截图记录搜索结果",
            "Capture evidence of successful search execution"
        )
        
    def demonstrate_fallback_strategies(self):
        """Demonstrate intelligent fallback strategies"""
        print(f"\n🔄 Demonstrating Fallback Strategies")
        print("=" * 60)
        
        # Alternative approach via search engines
        self.send_instruction(
            "如果直接访问有困难，请通过百度搜索'小红书 北京秋天'然后点击相关链接",
            "Intelligent fallback using search engines"
        )
        time.sleep(4)
        
        # Alternative keywords
        self.send_instruction(
            "尝试搜索相关关键词：北京 秋季 风景",
            "Try alternative but related search terms"
        )
        time.sleep(3)
    
    def demonstrate_advanced_interaction(self):
        """Demonstrate advanced natural language interaction"""
        print(f"\n🧠 Advanced Natural Language Interaction")
        print("=" * 60)
        
        # Context-aware interaction
        self.send_instruction(
            "如果页面显示登录提示，先关闭登录弹窗，然后继续搜索",
            "Context-aware handling of login popups"
        )
        time.sleep(2)
        
        # Intelligent scrolling and exploration
        self.send_instruction(
            "向下滚动查看更多搜索结果，如果有'加载更多'按钮请点击",
            "Intelligent content exploration and pagination"
        )
        time.sleep(3)
        
        # Content analysis
        self.send_instruction(
            "分析当前页面的内容质量，识别最相关的北京秋天相关帖子",
            "Use LLM for content quality analysis and relevance ranking"
        )
    
    def run_demo(self):
        """Run the complete demonstration"""
        try:
            # Check server availability
            print("🔍 Checking AI Browser Agent availability...")
            response = requests.get(f"{self.base_url}/")
            
            if response.status_code != 200:
                print(f"❌ Web server not available. Please start it with:")
                print(f"   python src/main.py --web")
                return False
            
            print("✅ AI Browser Agent is ready!")
            
            # Run demonstrations
            self.demonstrate_proper_approach()
            self.demonstrate_fallback_strategies()
            self.demonstrate_advanced_interaction()
            
            print(f"\n🎊 Natural Language Interaction Demo Completed!")
            print(f"\n💡 Key Points Demonstrated:")
            print(f"  ✓ Use keywords instead of full sentences for search")
            print(f"  ✓ LLM analyzes DOM structure via aria-snapshots")  
            print(f"  ✓ Dynamic selector generation based on page analysis")
            print(f"  ✓ Context-aware interaction handling")
            print(f"  ✓ Intelligent fallback strategies")
            print(f"  ✓ Chinese language processing capabilities")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ Demo interrupted by user")
            return False
        except Exception as e:
            print(f"\n💥 Demo failed: {e}")
            return False
        finally:
            # Cleanup session
            try:
                requests.delete(f"{self.base_url}/api/sessions/{self.session_id}")
                print("🧹 Session cleaned up")
            except:
                pass


def show_command_examples():
    """Show examples of proper natural language commands"""
    print("\n📚 Natural Language Command Examples")
    print("=" * 50)
    
    examples = [
        {
            "category": "Navigation Commands",
            "commands": [
                "打开小红书网站",
                "访问 xiaohongshu.com",
                "导航到小红书首页"
            ]
        },
        {
            "category": "Search Commands (Proper Approach)",
            "commands": [
                "在搜索框输入关键词：北京 秋天",
                "搜索关键词：北京秋季风景",
                "查找：秋天 北京 旅游"
            ]
        },
        {
            "category": "DOM Analysis Commands",
            "commands": [
                "分析页面结构，找到搜索功能",
                "识别当前页面的主要交互元素",
                "检测页面上的搜索框和按钮"
            ]
        },
        {
            "category": "Action Commands",
            "commands": [
                "点击搜索按钮",
                "按回车键执行搜索",
                "滚动页面查看更多内容"
            ]
        },
        {
            "category": "Content Extraction Commands",
            "commands": [
                "提取前10个搜索结果",
                "获取页面上的图片和文字信息",
                "分析搜索结果的相关性"
            ]
        }
    ]
    
    for example in examples:
        print(f"\n🏷️ {example['category']}:")
        for cmd in example['commands']:
            print(f"   • {cmd}")
    
    print(f"\n⚠️ Important Notes:")
    print(f"   • Use keywords instead of full sentences for search queries")
    print(f"   • Let LLM analyze DOM structure for element detection")  
    print(f"   • Use natural language to describe desired actions")
    print(f"   • Allow LLM reasoning to select appropriate selectors")


def main():
    """Main function"""
    print("🌸 Natural Language Interaction Demo for Xiaohongshu")
    print("🎯 Demonstrates proper AI Browser Agent usage")
    
    show_command_examples()
    
    demo = NaturalLanguageDemo()
    success = demo.run_demo()
    
    if success:
        print(f"\n🎉 Demo completed successfully!")
        print(f"📋 This demonstrates the correct approach for AI browser automation")
    else:
        print(f"\n🔧 Please ensure the web server is running:")
        print(f"   python src/main.py --web")


if __name__ == "__main__":
    main()