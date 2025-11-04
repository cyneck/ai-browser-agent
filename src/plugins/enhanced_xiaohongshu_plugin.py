#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强的小红书插件

使用新的插件接口实现的小红书优化插件，支持多种内容发现和交互功能。
"""

from typing import Dict, Any, List, Optional
from src.plugins.plugin_interface import (
    PluginInterface, PluginMetadata, PluginType, PluginContext
)


class EnhancedXiaohongshuPlugin(PluginInterface):
    """增强的小红书插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="enhanced_xiaohongshu",
            version="2.0.0",
            description="增强的小红书插件，支持内容搜索、用户关注、笔记互动等功能",
            author="AI Browser Agent Team",
            plugin_type=PluginType.WEBSITE,
            supported_actions=[
                "xhs_search", "xhs_user_search", "xhs_topic_search",
                "xhs_follow_user", "xhs_like_note", "xhs_comment", "xhs_collect",
                "extract_xhs_content", "xhs_login_check"
            ],
            config_schema={
                "auto_login": {"type": "boolean", "default": False},
                "interaction_delay": {"type": "integer", "default": 2000},
                "enable_fallback": {"type": "boolean", "default": True},
                "prefer_mobile": {"type": "boolean", "default": False}
            }
        )
    
    def _on_initialize(self) -> bool:
        """插件初始化"""
        # 设置默认配置
        default_config = {
            "auto_login": False,
            "interaction_delay": 2000,
            "enable_fallback": True,
            "prefer_mobile": False
        }
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        self.logger.info("小红书插件初始化完成")
        return True
    
    def _execute_internal(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件内部逻辑"""
        action = instruction.get("action")
        
        if action == "xhs_search":
            return self._perform_search(instruction, context)
        elif action == "xhs_user_search":
            return self._perform_user_search(instruction, context)
        elif action == "xhs_topic_search":
            return self._perform_topic_search(instruction, context)
        elif action == "xhs_follow_user":
            return self._perform_follow_user(instruction, context)
        elif action == "xhs_like_note":
            return self._perform_like_note(instruction, context)
        elif action == "xhs_comment":
            return self._perform_comment(instruction, context)
        elif action == "xhs_collect":
            return self._perform_collect(instruction, context)
        elif action == "extract_xhs_content":
            return self._extract_content(instruction, context)
        elif action == "xhs_login_check":
            return self._check_login_status(instruction, context)
        else:
            return {
                "success": False,
                "message": f"不支持的操作: {action}"
            }
    
    def _perform_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行小红书内容搜索"""
        query = instruction.get("value", "")
        if not query:
            return {
                "success": False,
                "message": "搜索查询不能为空"
            }
        
        context.log_info(f"执行小红书搜索: {query}")
        
        # 选择搜索URL
        base_url = "https://m.xiaohongshu.com" if self.config.get("prefer_mobile", False) else "https://www.xiaohongshu.com"
        
        # 构建搜索步骤
        search_steps = [
            {
                "action": "navigate",
                "value": base_url,
                "description": "导航到小红书首页"
            }
        ]
        
        # 检查是否需要登录
        if self.config.get("auto_login", False):
            search_steps.append({
                "action": "xhs_login_check",
                "description": "检查登录状态"
            })
        
        # 添加搜索步骤
        search_steps.extend([
            {
                "action": "wait",
                "selector": "input[placeholder*='搜索'], .search-input",
                "timeout": 10000,
                "description": "等待搜索框出现"
            },
            {
                "action": "fill",
                "selector": "input[placeholder*='搜索'], .search-input",
                "value": query,
                "description": f"输入搜索查询: {query}"
            },
            {
                "action": "key",
                "selector": "input[placeholder*='搜索'], .search-input",
                "value": "Enter",
                "description": "按回车键执行搜索"
            },
            {
                "action": "wait",
                "value": 3000,
                "description": "等待搜索结果加载"
            },
            {
                "action": "extract_xhs_content",
                "description": "提取小红书搜索结果"
            }
        ])
        
        return {
            "success": True,
            "message": f"小红书搜索指令已生成: {query}",
            "steps": search_steps,
            "metadata": {
                "platform": "xiaohongshu",
                "query": query,
                "search_type": "content",
                "mobile_mode": self.config.get("prefer_mobile", False)
            }
        }
    
    def _perform_user_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行小红书用户搜索"""
        username = instruction.get("value", "")
        if not username:
            return {
                "success": False,
                "message": "用户名不能为空"
            }
        
        context.log_info(f"执行小红书用户搜索: {username}")
        
        return {
            "success": True,
            "message": f"小红书用户搜索指令已生成: {username}",
            "steps": [
                {
                    "action": "navigate",
                    "value": "https://www.xiaohongshu.com",
                    "description": "导航到小红书首页"
                },
                {
                    "action": "wait",
                    "selector": "input[placeholder*='搜索']",
                    "timeout": 10000,
                    "description": "等待搜索框出现"
                },
                {
                    "action": "fill",
                    "selector": "input[placeholder*='搜索']",
                    "value": username,
                    "description": f"输入用户名: {username}"
                },
                {
                    "action": "key",
                    "selector": "input[placeholder*='搜索']",
                    "value": "Enter",
                    "description": "执行搜索"
                },
                {
                    "action": "wait",
                    "value": 2000,
                    "description": "等待搜索结果"
                },
                {
                    "action": "click",
                    "selector": ".tab-item[data-type='user'], .user-tab",
                    "description": "切换到用户标签",
                    "optional": True
                },
                {
                    "action": "extract",
                    "selector": ".user-item, .user-card",
                    "description": "提取用户搜索结果"
                }
            ],
            "metadata": {
                "platform": "xiaohongshu",
                "query": username,
                "search_type": "user"
            }
        }
    
    def _perform_topic_search(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行小红书话题搜索"""
        topic = instruction.get("value", "")
        if not topic:
            return {
                "success": False,
                "message": "话题不能为空"
            }
        
        # 确保话题格式正确
        if not topic.startswith("#"):
            topic = f"#{topic}"
        
        context.log_info(f"执行小红书话题搜索: {topic}")
        
        return {
            "success": True,
            "message": f"小红书话题搜索指令已生成: {topic}",
            "steps": [
                {
                    "action": "navigate",
                    "value": f"https://www.xiaohongshu.com/search_result?keyword={topic}",
                    "description": f"导航到话题搜索: {topic}"
                },
                {
                    "action": "wait",
                    "value": 3000,
                    "description": "等待话题内容加载"
                },
                {
                    "action": "extract",
                    "selector": ".note-item, .feed-item",
                    "description": "提取话题相关内容"
                }
            ],
            "metadata": {
                "platform": "xiaohongshu",
                "query": topic,
                "search_type": "topic"
            }
        }
    
    def _perform_follow_user(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """关注用户"""
        user_selector = instruction.get("selector", "")
        if not user_selector:
            return {
                "success": False,
                "message": "用户选择器不能为空"
            }
        
        context.log_info("执行关注用户操作")
        
        delay = self.config.get("interaction_delay", 2000)
        
        return {
            "success": True,
            "message": "关注用户指令已生成",
            "steps": [
                {
                    "action": "click",
                    "selector": user_selector,
                    "description": "点击进入用户主页"
                },
                {
                    "action": "wait",
                    "value": delay,
                    "description": "等待页面加载"
                },
                {
                    "action": "click",
                    "selector": ".follow-btn, .btn-follow, button[contains(text(), '关注')]",
                    "description": "点击关注按钮"
                },
                {
                    "action": "wait",
                    "value": 1000,
                    "description": "等待关注操作完成"
                }
            ],
            "metadata": {
                "platform": "xiaohongshu",
                "action_type": "follow_user"
            }
        }
    
    def _perform_like_note(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """点赞笔记"""
        note_selector = instruction.get("selector", "")
        if not note_selector:
            return {
                "success": False,
                "message": "笔记选择器不能为空"
            }
        
        context.log_info("执行点赞笔记操作")
        
        delay = self.config.get("interaction_delay", 2000)
        
        return {
            "success": True,
            "message": "点赞笔记指令已生成",
            "steps": [
                {
                    "action": "click",
                    "selector": f"{note_selector} .like-btn, {note_selector} .heart-icon",
                    "description": "点击点赞按钮"
                },
                {
                    "action": "wait",
                    "value": delay,
                    "description": "等待点赞操作完成"
                }
            ],
            "metadata": {
                "platform": "xiaohongshu",
                "action_type": "like_note"
            }
        }
    
    def _perform_comment(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """评论笔记"""
        comment_text = instruction.get("value", "")
        note_selector = instruction.get("selector", "")
        
        if not comment_text or not note_selector:
            return {
                "success": False,
                "message": "评论内容和笔记选择器不能为空"
            }
        
        context.log_info(f"执行评论操作: {comment_text}")
        
        delay = self.config.get("interaction_delay", 2000)
        
        return {
            "success": True,
            "message": "评论笔记指令已生成",
            "steps": [
                {
                    "action": "click",
                    "selector": f"{note_selector} .comment-btn, {note_selector} .comment-icon",
                    "description": "点击评论按钮"
                },
                {
                    "action": "wait",
                    "value": delay,
                    "description": "等待评论框出现"
                },
                {
                    "action": "fill",
                    "selector": ".comment-input, textarea[placeholder*='评论']",
                    "value": comment_text,
                    "description": f"输入评论: {comment_text}"
                },
                {
                    "action": "click",
                    "selector": ".comment-submit, .send-btn",
                    "description": "发送评论"
                },
                {
                    "action": "wait",
                    "value": delay,
                    "description": "等待评论发送完成"
                }
            ],
            "metadata": {
                "platform": "xiaohongshu",
                "action_type": "comment",
                "comment_text": comment_text
            }
        }
    
    def _perform_collect(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """收藏笔记"""
        note_selector = instruction.get("selector", "")
        if not note_selector:
            return {
                "success": False,
                "message": "笔记选择器不能为空"
            }
        
        context.log_info("执行收藏笔记操作")
        
        delay = self.config.get("interaction_delay", 2000)
        
        return {
            "success": True,
            "message": "收藏笔记指令已生成",
            "steps": [
                {
                    "action": "click",
                    "selector": f"{note_selector} .collect-btn, {note_selector} .star-icon",
                    "description": "点击收藏按钮"
                },
                {
                    "action": "wait",
                    "value": delay,
                    "description": "等待收藏操作完成"
                }
            ],
            "metadata": {
                "platform": "xiaohongshu",
                "action_type": "collect"
            }
        }
    
    def _extract_content(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """提取小红书内容"""
        context.log_info("提取小红书内容")
        
        return {
            "success": True,
            "message": "小红书内容提取指令已生成",
            "steps": [
                {
                    "action": "extract",
                    "selector": ".note-item, .feed-item",
                    "description": "提取笔记列表"
                },
                {
                    "action": "extract",
                    "selector": ".user-info, .author-info",
                    "description": "提取用户信息"
                },
                {
                    "action": "extract",
                    "selector": ".note-content, .desc",
                    "description": "提取笔记内容"
                },
                {
                    "action": "extract",
                    "selector": ".tag, .topic",
                    "description": "提取标签和话题"
                }
            ],
            "metadata": {
                "extraction_type": "xiaohongshu_content"
            }
        }
    
    def _check_login_status(self, instruction: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """检查登录状态"""
        context.log_info("检查小红书登录状态")
        
        return {
            "success": True,
            "message": "登录状态检查指令已生成",
            "steps": [
                {
                    "action": "wait",
                    "selector": ".login-btn, .user-avatar",
                    "timeout": 5000,
                    "description": "检查登录状态"
                },
                {
                    "action": "conditional_wait",
                    "condition": "element_exists",
                    "selector": ".login-btn",
                    "true_action": {
                        "action": "wait_for_manual_login",
                        "message": "请手动登录小红书账号",
                        "timeout": 60000
                    },
                    "false_action": {
                        "action": "log",
                        "message": "用户已登录"
                    },
                    "description": "根据登录状态执行相应操作"
                }
            ],
            "metadata": {
                "platform": "xiaohongshu",
                "action_type": "login_check"
            }
        }
    
    def can_handle_url(self, url: str) -> bool:
        """判断是否可以处理指定URL"""
        return "xiaohongshu.com" in url
    
    def has_access_restrictions(self) -> bool:
        """检查是否存在访问限制"""
        # 小红书可能存在网络访问限制，但可以通过配置禁用
        return not self.config.get("enable_fallback", True)
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        # 验证交互延迟
        interaction_delay = config.get("interaction_delay", 2000)
        if not isinstance(interaction_delay, int) or interaction_delay < 500:
            self.logger.error(f"无效的交互延迟设置: {interaction_delay}")
            return False
        
        return True