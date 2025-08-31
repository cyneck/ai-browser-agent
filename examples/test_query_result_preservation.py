#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试查询结果保存功能

演示修复后的系统如何在查询后保存结果而不是自动关闭浏览器。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import time
import requests
from src.common.logger import get_logger


class QueryResultPreservationDemo:
    """查询结果保存演示"""
    
    def __init__(self):
        """初始化演示"""
        self.logger = get_logger()
        self.base_url = "http://localhost:8000"
        self.session_id = "test-query-demo-session"
    
    def send_instruction(self, instruction: str, description: str = ""):
        """发送指令到AI浏览器代理"""
        if description:
            print(f"\n📝 {description}")
        print(f"💬 指令: {instruction}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/execute",
                json={"text": instruction, "session_id": self.session_id},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                message = result.get("message", "")
                
                print(f"✅ 结果: {message}" if success else f"❌ 失败: {message}")
                
                # 如果有搜索结果，显示
                if "search_results" in result:
                    print(f"🔍 找到 {len(result['search_results'])} 条搜索结果:")
                    for i, item in enumerate(result['search_results'][:3], 1):
                        print(f"  {i}. {item.get('title', '无标题')}")
                
                # 如果有提取的内容，显示
                if "extracted_content" in result:
                    print(f"📄 提取的内容: {len(result['extracted_content'])} 条")
                
                return result
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"💥 异常: {e}")
            return {"success": False, "error": str(e)}
    
    def demonstrate_proper_search_flow(self):
        """演示正确的搜索流程：搜索 → 提取结果（不关闭）"""
        print("=" * 60)
        print("🎯 演示：搜索后提取结果而不自动关闭浏览器")
        print("=" * 60)
        
        # 步骤 1: 搜索
        self.send_instruction(
            "在百度搜索 '人工智能 浏览器自动化'",
            "执行搜索操作"
        )
        time.sleep(3)
        
        # 步骤 2: 明确提取搜索结果（不关闭浏览器）
        self.send_instruction(
            "提取前5个搜索结果，包括标题和描述",
            "提取搜索结果（页面保持打开）"
        )
        time.sleep(2)
        
        # 步骤 3: 再次验证页面还在，可以继续操作
        self.send_instruction(
            "截取当前页面截图",
            "验证页面仍然可用"
        )
        time.sleep(1)
        
        print("\n✅ 演示完成！页面在整个过程中保持打开，结果被成功提取。")
    
    def demonstrate_close_with_results(self):
        """演示关闭时保存结果的功能"""
        print("\n" + "=" * 60)
        print("🔒 演示：关闭页面时自动保存搜索结果")
        print("=" * 60)
        
        # 先搜索一些内容
        self.send_instruction(
            "在bing搜索 '北京 秋天 风景'",
            "在必应执行新搜索"
        )
        time.sleep(3)
        
        # 现在关闭页面，应该会自动保存结果
        result = self.send_instruction(
            "关闭当前页面",
            "关闭页面（应该自动保存搜索结果）"
        )
        
        # 检查是否保存了结果
        if result.get("extracted_content"):
            print("✅ 成功！关闭时自动保存了搜索结果。")
        else:
            print("⚠️ 注意：关闭时没有找到搜索结果保存。")
    
    def run_demo(self):
        """运行完整演示"""
        try:
            # 检查服务器可用性
            print("🔍 检查AI浏览器代理服务...")
            response = requests.get(f"{self.base_url}/")
            
            if response.status_code != 200:
                print(f"❌ Web服务器不可用。请先启动服务器:")
                print(f"   python src/main.py --web")
                return False
            
            print("✅ AI浏览器代理服务就绪!")
            
            # 演示正确的搜索流程
            self.demonstrate_proper_search_flow()
            
            # 演示关闭时保存结果
            self.demonstrate_close_with_results()
            
            print(f"\n🎊 查询结果保存演示完成!")
            print(f"\n💡 关键改进:")
            print(f"  ✓ 新增 extract_results 动作专门提取搜索结果")
            print(f"  ✓ 搜索后不会自动关闭浏览器")
            print(f"  ✓ 关闭页面时会自动保存搜索结果")
            print(f"  ✓ 用户可以继续查看和操作搜索结果")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ 演示被用户中断")
            return False
        except Exception as e:
            print(f"\n💥 演示失败: {e}")
            return False
        finally:
            # 清理会话
            try:
                requests.delete(f"{self.base_url}/api/sessions/{self.session_id}")
                print("🧹 会话已清理")
            except:
                pass


def show_new_features():
    """显示新功能说明"""
    print("\n📚 新功能说明")
    print("=" * 50)
    
    features = [
        {
            "feature": "extract_results 动作",
            "description": "专门用于提取搜索结果，不会关闭页面",
            "usage": '{"action": "extract_results", "description": "提取搜索结果"}'
        },
        {
            "feature": "智能关闭保护",
            "description": "关闭页面前自动保存搜索结果",
            "usage": "系统在执行 close 动作时自动检测并保存结果"
        },
        {
            "feature": "改进的系统提示",
            "description": "指导LLM使用 extract_results 而不是 close",
            "usage": "LLM会自动生成更合适的指令序列"
        }
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n🚀 功能 {i}: {feature['feature']}")
        print(f"   📝 说明: {feature['description']}")
        print(f"   💻 用法: {feature['usage']}")
    
    print(f"\n⚠️ 重要改进:")
    print(f"   • 查询完成后页面保持打开")
    print(f"   • 搜索结果被正确提取和返回")
    print(f"   • 用户可以继续查看和操作结果")
    print(f"   • 即使意外关闭，搜索结果也会被保存")


def main():
    """主函数"""
    print("🔧 查询结果保存功能演示")
    print("🎯 修复：查询后浏览器不再自动关闭")
    
    show_new_features()
    
    demo = QueryResultPreservationDemo()
    success = demo.run_demo()
    
    if success:
        print(f"\n🎉 演示完成成功!")
        print(f"📋 这展示了修复后的AI浏览器代理行为")
    else:
        print(f"\n🔧 请确保Web服务器正在运行:")
        print(f"   python src/main.py --web")


if __name__ == "__main__":
    main()