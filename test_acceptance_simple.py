#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的最终验收测试验证
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from tests.integration.test_final_acceptance import FinalAcceptanceTestSuite

def main():
    """运行简单的验收测试验证"""
    print("🎯 开始执行最终验收测试验证")
    print("=" * 60)
    
    try:
        # 创建测试套件
        test_suite = FinalAcceptanceTestSuite()
        
        # 运行完整验收测试
        print("📋 执行完整系统验收测试...")
        results = test_suite.run_complete_acceptance_tests()
        
        # 生成报告
        print("📊 生成验收测试报告...")
        report = test_suite.generate_acceptance_report(results)
        
        # 输出报告
        print("\n" + report)
        
        # 保存报告
        report_file = Path("final_acceptance_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 报告已保存到: {report_file}")
        
        # 验证结果
        overall_success = results.get("overall_success", False)
        execution_summary = results.get("execution_summary", {})
        
        print("\n" + "=" * 60)
        print("🏁 验收测试执行完成")
        print("=" * 60)
        
        print(f"总体结果: {'✅ 通过' if overall_success else '❌ 未通过'}")
        print(f"测试总数: {execution_summary.get('total_tests', 0)}")
        print(f"通过测试: {execution_summary.get('passed_tests', 0)}")
        print(f"失败测试: {execution_summary.get('failed_tests', 0)}")
        print(f"成功率: {execution_summary.get('overall_success_rate', 0):.2%}")
        
        # 需求覆盖率
        req_coverage = results.get("requirement_coverage", {})
        print(f"需求覆盖率: {req_coverage.get('total_coverage_percentage', 0):.1f}%")
        
        # 用户接受度
        user_acceptance = results.get("user_acceptance_analysis", {})
        print(f"用户接受度: {user_acceptance.get('overall_acceptance_rate', 0):.1f}%")
        
        print("=" * 60)
        
        if overall_success:
            print("🎉 恭喜！AI浏览器代理已通过最终验收测试！")
            print("✅ 系统已准备好进行发布")
        else:
            print("❌ 验收测试未完全通过，请查看详细报告")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ 验收测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)