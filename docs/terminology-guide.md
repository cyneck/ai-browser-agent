# AI Browser Agent Terminology Guide

## Important Terminology Distinction

To avoid confusion and maintain clarity in the codebase, we use specific terminology:

### Text vs Instruction

**Text (自然语言文本)**
- What users input in natural language
- Example: "在bing网站检索北京秋天" (Search for Beijing autumn on Bing website)
- Used in CLI parameter: `--text`
- Used in code variables: `user_text`, `text`

**Instruction (可执行指令)**
- Internal JSON format commands that the system executes
- Example: `{"action": "navigate", "value": "https://bing.com", "description": "Navigate to Bing"}`
- Used in code variables: `json_instruction`, `instruction`

## CLI Usage Examples

### Direct Execution with Natural Language Text
```bash
# New correct usage
python src/main.py --cli --text "在bing网站检索北京秋天"

# Old usage (no longer supported)
python src/main.py --cli --instruction "在bing网站检索北京秋天"  # ❌ Error
```

### Interactive Mode
```bash
python src/main.py --cli
# Then enter natural language text at the prompt
> 在bing网站检索北京秋天
```

## Code Architecture Flow

1. **User Input**: Natural language text (用户输入的自然语言文本)
2. **Processing**: Text → JSON Instruction conversion (文本转换为JSON指令)
3. **Execution**: JSON Instruction execution (JSON指令执行)

```
User Text → InstructionBuilder → JSON Instruction → ActionExecutor
"在bing网站检索北京秋天" → {"action": "navigate", ...} → Browser Actions
```

## Why This Matters

- **Clarity**: Developers understand what type of data they're working with
- **Maintainability**: Code is more readable and self-documenting
- **User Experience**: Users understand they input natural language, not JSON
- **API Design**: Clear distinction between user input and internal commands