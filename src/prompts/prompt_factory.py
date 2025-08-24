#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prompt Factory

Assembles complete prompts by coordinating system prompts, user prompts, and selector rules.
Provides the main interface for generating context-aware prompts for the LLM.
"""

from typing import Dict, Any, List, Optional
from .system_prompts import SystemPrompts
from .user_prompts import UserPrompts
from .selector_rules import SelectorRules


class PromptFactory:
    """Factory class for assembling complete prompts from components"""
    
    def __init__(self, system_prompts: SystemPrompts, user_prompts: UserPrompts, 
                 selector_rules: SelectorRules):
        """Initialize the prompt factory with component instances
        
        Args:
            system_prompts: SystemPrompts instance
            user_prompts: UserPrompts instance  
            selector_rules: SelectorRules instance
        """
        self.system_prompts = system_prompts
        self.user_prompts = user_prompts
        self.selector_rules = selector_rules
    
    def build_system_prompt(self, prompt_type: str = "default") -> str:
        """Build system prompt with selector rules integrated
        
        Args:
            prompt_type: Type of system prompt (default, enhanced)
            
        Returns:
            Complete system prompt with selector rules
        """
        base_prompt = self.system_prompts.get_prompt_by_type(prompt_type)
        
        # Add selector rules to the system prompt
        selector_principles = self.selector_rules.get_selector_principles()
        precision_guidelines = self.selector_rules.get_precision_guidelines()
        
        return f"{base_prompt}\n\n{selector_principles}\n\n{precision_guidelines}"
    
    def build_user_prompt(self, user_text: str, page_data: Dict[str, Any], 
                         conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Build user prompt with page data and optional conversation history
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            conversation_history: Previous conversation messages
            
        Returns:
            Complete user prompt
        """
        base_prompt = self.user_prompts.build_basic_user_prompt(user_text, page_data)
        
        if conversation_history:
            return self.user_prompts.add_conversation_history(base_prompt, conversation_history)
        
        return base_prompt
    
    def build_enhanced_user_prompt(self, user_text: str, page_data: Dict[str, Any],
                                  context_analysis: Dict[str, Any],
                                  conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Build enhanced user prompt with context analysis
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            context_analysis: Analysis of user context and intent
            conversation_history: Previous conversation messages
            
        Returns:
            Enhanced user prompt with context
        """
        base_prompt = self.user_prompts.build_enhanced_user_prompt(
            user_text, page_data, context_analysis
        )
        
        if conversation_history:
            return self.user_prompts.add_conversation_history(base_prompt, conversation_history)
        
        return base_prompt
    
    def build_complete_prompt(self, user_text: str, page_data: Dict[str, Any],
                             conversation_history: Optional[List[Dict[str, str]]] = None,
                             prompt_type: str = "default") -> str:
        """Build complete prompt combining system and user parts
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            conversation_history: Previous conversation messages
            prompt_type: Type of system prompt to use
            
        Returns:
            Complete assembled prompt
        """
        system_prompt = self.build_system_prompt(prompt_type)
        user_prompt = self.build_user_prompt(user_text, page_data, conversation_history)
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    def build_enhanced_prompt(self, user_text: str, page_data: Dict[str, Any],
                             conversation_history: List[Dict[str, str]],
                             context_analysis: Dict[str, Any]) -> str:
        """Build enhanced prompt with context analysis for complete workflows
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            conversation_history: Previous conversation messages
            context_analysis: Analysis of user context and intent
            
        Returns:
            Enhanced complete prompt
        """
        # Use enhanced system prompt for this type
        system_prompt = self.build_system_prompt("enhanced")
        user_prompt = self.build_enhanced_user_prompt(
            user_text, page_data, context_analysis, conversation_history
        )
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    def validate_prompt_components(self) -> Dict[str, bool]:
        """Validate that all prompt components are properly initialized
        
        Returns:
            Dictionary indicating which components are available
        """
        return {
            "system_prompts": self.system_prompts is not None,
            "user_prompts": self.user_prompts is not None,
            "selector_rules": self.selector_rules is not None,
            "default_system_prompt": bool(self.system_prompts.get_default_system_prompt()),
            "enhanced_system_prompt": bool(self.system_prompts.get_enhanced_system_prompt()),
            "selector_principles": bool(self.selector_rules.get_selector_principles()),
        }
    
    def get_prompt_metadata(self, prompt_type: str = "default") -> Dict[str, Any]:
        """Get metadata about the generated prompt
        
        Args:
            prompt_type: Type of prompt to analyze
            
        Returns:
            Metadata including component counts and characteristics
        """
        system_prompt = self.build_system_prompt(prompt_type)
        selector_principles = self.selector_rules.get_selector_principles()
        
        return {
            "prompt_type": prompt_type,
            "system_prompt_length": len(system_prompt),
            "includes_selector_rules": len(selector_principles) > 0,
            "supported_actions": list(self.system_prompts.get_action_types().keys()),
            "selector_priority_levels": len(self.selector_rules.get_selector_priority_list()),
            "best_practices_count": len(self.selector_rules.get_best_practices())
        }
    
    def get_action_documentation(self) -> str:
        """Get formatted documentation of supported actions
        
        Returns:
            Formatted string describing all supported actions
        """
        actions = self.system_prompts.get_action_types()
        doc = "支持的操作类型：\n"
        
        for action, description in actions.items():
            doc += f"- {action}: {description}\n"
        
        return doc
    
    def get_selector_documentation(self) -> str:
        """Get complete selector rules documentation
        
        Returns:
            Complete selector documentation
        """
        return self.selector_rules.generate_selector_documentation()
    
    def create_debug_prompt(self, user_text: str, page_data: Dict[str, Any],
                           prompt_type: str = "default") -> Dict[str, str]:
        """Create a debug version of the prompt with separated components
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            prompt_type: Type of system prompt to use
            
        Returns:
            Dictionary with separated prompt components
        """
        system_prompt = self.system_prompts.get_prompt_by_type(prompt_type)
        selector_rules = self.selector_rules.get_selector_principles()
        precision_guidelines = self.selector_rules.get_precision_guidelines()
        user_prompt = self.user_prompts.build_basic_user_prompt(user_text, page_data)
        
        return {
            "system_prompt": system_prompt,
            "selector_rules": selector_rules,
            "precision_guidelines": precision_guidelines,
            "user_prompt": user_prompt,
            "complete_prompt": f"{system_prompt}\n\n{selector_rules}\n\n{precision_guidelines}\n\n{user_prompt}"
        }