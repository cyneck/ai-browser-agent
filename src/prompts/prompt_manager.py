#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Prompt Manager

Provides the main interface for prompt generation and management across the system.
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod


class BasePromptManager(ABC):
    """Abstract base class for prompt managers"""
    
    @abstractmethod
    def build_system_prompt(self, prompt_type: str = "default") -> str:
        """Build system prompt for the LLM"""
        pass
    
    @abstractmethod 
    def build_user_prompt(self, user_text: str, page_data: Dict[str, Any], 
                         conversation_history: List[Dict[str, str]] = None) -> str:
        """Build user prompt with context"""
        pass
    
    @abstractmethod
    def build_complete_prompt(self, user_text: str, page_data: Dict[str, Any],
                             conversation_history: List[Dict[str, str]] = None,
                             prompt_type: str = "default") -> str:
        """Build complete prompt combining system and user parts"""
        pass


class PromptManager(BasePromptManager):
    """Main prompt manager that coordinates all prompt generation"""
    
    def __init__(self):
        """Initialize the prompt manager"""
        # Import here to avoid circular imports
        from .system_prompts import SystemPrompts
        from .user_prompts import UserPrompts
        from .selector_rules import SelectorRules
        from .prompt_factory import PromptFactory
        
        self.system_prompts = SystemPrompts()
        self.user_prompts = UserPrompts()
        self.selector_rules = SelectorRules()
        self.prompt_factory = PromptFactory(
            self.system_prompts,
            self.user_prompts, 
            self.selector_rules
        )
    
    def build_system_prompt(self, prompt_type: str = "default") -> str:
        """Build system prompt for the LLM
        
        Args:
            prompt_type: Type of system prompt to build (default, enhanced, etc.)
            
        Returns:
            System prompt string
        """
        return self.prompt_factory.build_system_prompt(prompt_type)
    
    def build_user_prompt(self, user_text: str, page_data: Dict[str, Any], 
                         conversation_history: List[Dict[str, str]] = None) -> str:
        """Build user prompt with context
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            conversation_history: Previous conversation messages
            
        Returns:
            User prompt string
        """
        return self.prompt_factory.build_user_prompt(
            user_text, page_data, conversation_history
        )
    
    def build_complete_prompt(self, user_text: str, page_data: Dict[str, Any],
                             conversation_history: List[Dict[str, str]] = None,
                             prompt_type: str = "default") -> str:
        """Build complete prompt combining system and user parts
        
        Args:
            user_text: User's natural language input
            page_data: Current page information 
            conversation_history: Previous conversation messages
            prompt_type: Type of system prompt to use
            
        Returns:
            Complete prompt string
        """
        return self.prompt_factory.build_complete_prompt(
            user_text, page_data, conversation_history, prompt_type
        )
    
    def build_enhanced_prompt(self, user_text: str, page_data: Dict[str, Any],
                             conversation_history: List[Dict[str, str]],
                             context_analysis: Dict[str, Any]) -> str:
        """Build enhanced prompt with context analysis
        
        Args:
            user_text: User's natural language input
            page_data: Current page information
            conversation_history: Previous conversation messages  
            context_analysis: Analysis of user context and intent
            
        Returns:
            Enhanced prompt string
        """
        return self.prompt_factory.build_enhanced_prompt(
            user_text, page_data, conversation_history, context_analysis
        )