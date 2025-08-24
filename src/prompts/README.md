# Prompt Management System

The AI Browser Agent now uses a modular prompt management system that separates prompt logic from business logic for better maintainability, testing, and extensibility.

## Architecture

The prompt system is organized into several specialized modules:

### Core Components

1. **`PromptManager`** - Main interface for prompt generation
2. **`SystemPrompts`** - Contains all system-level prompts that define the AI's role and behavior
3. **`UserPrompts`** - Handles user prompt templates with context and page data
4. **`SelectorRules`** - Contains CSS selector generation rules and best practices
5. **`PromptFactory`** - Assembles complete prompts from individual components

## File Structure

```
src/prompts/
├── __init__.py           # Module exports
├── prompt_manager.py     # Main PromptManager class
├── system_prompts.py     # System prompt templates
├── user_prompts.py       # User prompt generation
├── selector_rules.py     # CSS selector rules and validation
└── prompt_factory.py     # Prompt assembly factory
```

## Usage

### Basic Usage

```python
from src.prompts import PromptManager

# Initialize the prompt manager
manager = PromptManager()

# Generate a complete prompt
user_text = "在百度搜索人工智能"
page_data = {
    "url": "https://www.baidu.com",
    "title": "百度一下，你就知道",
    "elements": [{"tag": "input", "name": "wd"}]
}

prompt = manager.build_complete_prompt(user_text, page_data)
```

### Advanced Usage with Context

```python
# Enhanced prompt with context analysis
context_analysis = {
    "search_intent": True,
    "search_keywords": ["人工智能"],
    "interaction_type": "search"
}

enhanced_prompt = manager.build_enhanced_prompt(
    user_text, page_data, [], context_analysis
)
```

### Individual Components

```python
from src.prompts import SystemPrompts, UserPrompts, SelectorRules

# Use individual components
system_prompts = SystemPrompts()
default_system = system_prompts.get_default_system_prompt()
enhanced_system = system_prompts.get_enhanced_system_prompt()

user_prompts = UserPrompts()
user_prompt = user_prompts.build_basic_user_prompt(user_text, page_data)

selector_rules = SelectorRules()
principles = selector_rules.get_selector_principles()
```

## Key Features

### System Prompts

- **Default System Prompt**: Standard web automation assistant behavior
- **Enhanced System Prompt**: Advanced workflow generation for complex tasks
- **Action Types**: Complete list of supported automation actions
- **JSON Format Examples**: Template examples for single and multi-step instructions

### User Prompts

- **Basic User Prompts**: Standard page context with user instructions
- **Enhanced User Prompts**: Context-aware prompts with intent analysis
- **Conversation History**: Automatic integration of previous conversation context
- **Page Data Formatting**: Structured presentation of page information

### Selector Rules

- **Priority-Based Rules**: Hierarchical selector generation principles
- **Precision Guidelines**: Rules for ensuring selector uniqueness and reliability
- **Best Practices**: Comprehensive list of selector best practices
- **Fragile Pattern Detection**: Identification and avoidance of unreliable selectors
- **Validation Tools**: Automated selector quality assessment

### Prompt Factory

- **Component Assembly**: Intelligent combination of system prompts, user prompts, and selector rules
- **Context Integration**: Seamless integration of conversation history and intent analysis
- **Type-Safe Generation**: Proper handling of different prompt types and configurations
- **Validation**: Built-in validation of prompt components and assembly

## Benefits

### 1. **Maintainability**
- Clear separation of concerns
- Centralized prompt management
- Easy to modify individual components without affecting others

### 2. **Testability**
- Comprehensive unit test coverage
- Individual component testing
- Integration testing for end-to-end scenarios

### 3. **Extensibility**
- Easy to add new prompt types
- Pluggable architecture for new components
- Support for custom prompt variations

### 4. **Consistency**
- Standardized prompt generation across the system
- Consistent application of selector rules
- Uniform handling of context and conversation history

### 5. **Quality Assurance**
- Built-in validation for selector precision
- Automated detection of fragile patterns
- Comprehensive documentation and examples

## Testing

The prompt system includes comprehensive test coverage:

```bash
# Run all prompt system tests
python -m pytest tests/unit/test_prompt_system.py -v

# Run specific test classes
python -m pytest tests/unit/test_prompt_system.py::TestSystemPrompts -v
python -m pytest tests/unit/test_prompt_system.py::TestPromptFactory -v
```

## Migrating from Old System

The new system is fully integrated with the existing `InstructionBuilder`. No changes are required for existing code that uses the `InstructionBuilder` interface.

### Before (Internal Implementation)
```python
# Old approach - hardcoded prompts in InstructionBuilder
prompt = self._build_prompt(user_text, page_data, conversation_history)
```

### After (New System)
```python
# New approach - uses PromptManager internally
prompt = self.prompt_manager.build_complete_prompt(
    user_text, page_data, conversation_history
)
```

## Future Enhancements

The modular architecture supports future enhancements such as:

1. **Prompt Templates**: Jinja2-based templating for dynamic prompt generation
2. **Multi-Language Support**: Localized prompts for different languages
3. **Custom Prompt Types**: Domain-specific prompts for specialized use cases
4. **A/B Testing**: Framework for testing different prompt variations
5. **Prompt Analytics**: Metrics and analysis for prompt effectiveness

## Contributing

When adding new prompt functionality:

1. Follow the established modular pattern
2. Add appropriate unit tests
3. Update documentation
4. Consider backward compatibility
5. Validate selector rules and best practices

For detailed implementation guidelines, see the individual module documentation and existing test cases.