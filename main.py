#!/usr/bin/env python3
"""
GUI Diff Skill - Frontend UI Automation Validation & Auto-Fix Plugin
GUI Diff Skill - 前端UI自动化验收与自动修复插件

Usage / 用法:
  python gui_plugin.py --mode check/auto_fix --file <path> --rules '<json>' --req "<text>" [--api_key key] [--max_retries 3]

Output / 输出:
  Prints JSON to stdout / 将JSON打印到标准输出
"""

import argparse
import asyncio
import json
import sys
from playwright.async_api import async_playwright
from openai import OpenAI


# ---------- Core Check Function / 核心检查函数 ----------
async def run_check(html_path, rules):
    """
    Perform UI checks based on dynamic rules.
    根据动态规则执行UI检查。

    :param html_path: Path to the HTML file / HTML文件路径
    :param rules: List of rules [{"selector": str, "property": str, "expected": str}]
                  规则列表 [{"selector": 选择器, "property": 属性, "expected": 期望值}]
    :return: {"status": "pass"|"fail", "errors": [str, ...]}
    """
    async with async_playwright() as p:
        # Launch headless browser / 启动无头浏览器
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        # Load the HTML file / 加载HTML文件
        with open(html_path, "r", encoding="utf-8") as f:
            await page.set_content(f.read())
        await page.wait_for_timeout(300)  # Wait for rendering / 等待渲染完成

        errors = []  # Collect error messages / 收集错误信息

        # Iterate through each rule / 遍历每条规则
        for rule in rules:
            selector = rule["selector"]
            prop = rule["property"]
            expected = rule["expected"]

            # Find elements matching the selector / 查找匹配选择器的元素
            elements = await page.query_selector_all(selector)
            if not elements:
                errors.append(
                    f"Selector '{selector}' matched no elements / 选择器 '{selector}' 未匹配到任何元素"
                )
                continue

            # Check each matched element / 检查每个匹配的元素
            for el in elements:
                actual = None  # Actual value / 实际值

                # Obtain the actual property value / 获取实际属性值
                if prop in ["background-color", "color", "font-size", "border-radius", "text-align"]:
                    # CSS computed style / CSS计算样式
                    actual = await el.evaluate(f"(el) => getComputedStyle(el)['{prop}']")
                elif prop == "innerText":
                    # Inner text / 内部文本
                    actual = (await el.inner_text()).strip()
                elif prop in ["placeholder", "value", "href", "src"]:
                    # HTML attributes / HTML属性
                    actual = await el.get_attribute(prop)
                else:
                    # Fallback: try as CSS property / 后备：尝试作为CSS属性
                    actual = await el.evaluate(f"(el) => getComputedStyle(el)['{prop}']")

                # Compare and record errors / 比较并记录错误
                if actual is None:
                    errors.append(
                        f"Unable to get property '{prop}' / 无法获取属性 '{prop}'"
                    )
                elif expected not in actual and actual != expected:
                    errors.append(
                        f"Selector '{selector}' property '{prop}' expected to contain '{expected}', got '{actual}' / "
                        f"选择器 '{selector}' 的属性 '{prop}' 期望包含 '{expected}'，实际为 '{actual}'"
                    )

        await browser.close()
        return {"status": "pass" if not errors else "fail", "errors": errors}


# ---------- AI Fix Function / AI修复函数 ----------
def ai_fix_code(html_content, errors, requirement, api_key):
    """
    Call OpenAI to fix the HTML based on error reports.
    调用OpenAI根据错误报告修复HTML代码。

    :param html_content: Current HTML code / 当前HTML代码
    :param errors: List of error strings / 错误字符串列表
    :param requirement: Original user requirement / 用户原始需求
    :param api_key: OpenAI API key / OpenAI API密钥
    :return: Fixed HTML code or None / 修复后的HTML代码，失败返回None
    """
    if not api_key:
        return None

    client = OpenAI(api_key=api_key)

    # Build the prompt for AI / 构建AI提示词
    prompt = f"""
User requirement / 用户需求: {requirement}

Current HTML / 当前HTML:
```html
{html_content}
