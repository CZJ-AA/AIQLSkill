---
name: gui-diff
description: 用于前端UI自动化验收和自动修复。当AI生成HTML/CSS/React代码后，或用户要求“检测UI”、“对比设计稿”、“检查页面样式”时触发。本插件会动态检查元素样式、文本、属性，并自动修正不符之处。 / Used for frontend UI validation and auto-fix. Triggered after AI generates HTML/CSS/React code, or when user asks to "check UI", "compare with design", etc. This plugin dynamically checks element styles, text, attributes and automatically fixes discrepancies.
allowed-tools: ["execute", "read", "write"]
---

# GUI Diff Skill

## 中文说明

### 调用前准备
在调用本插件前，你必须根据用户的需求，构造一个 **JSON 规则数组**，用于指定要检查的元素和预期值。

**规则格式**：
```json
[
  {"selector": "CSS选择器", "property": "属性名", "expected": "期望值"}
]
