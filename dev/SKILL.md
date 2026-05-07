---
name: "qriafiction-dev"
description: "QriaFiction 互动小说引擎开发技能，提供语言规范、架构指导和编码约定。Invoke when developing QriaFiction engine, writing QFScript, adding features, or fixing bugs."
---

# QriaFiction 开发技能

> 本技能用于辅助开发 QriaFiction 互动小说引擎项目。

## 项目概览

QriaFiction 是一个基于 Python 的互动小说引擎，使用自定义脚本语言 QFScript，通过 pywebview 提供桌面 GUI。

### 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| 桌面框架 | pywebview |
| 前端 | Vue 3 + Tailwind CSS |
| AI 匹配 | fuzzywuzzy / OpenAI API / DeepSeek API |
| 包管理 | uv |

### 项目结构

```
QriaFiction/
├── src/
│   ├── main.py              # 入口：pywebview 窗口创建
│   ├── core/                # 核心：解释器 & AI 引擎
│   │   ├── tokens.py        # Token 类型定义（50+ 种）
│   │   ├── lexer.py         # 词法分析器（Python 风格缩进）
│   │   ├── parser.py        # 语法分析器（递归下降）
│   │   ├── ast.py           # AST 节点（dataclass）
│   │   ├── interpreter.py   # 解释器 + QriaContext
│   │   ├── runtime.py       # 运行时环境
│   │   ├── ai_engine.py     # AI 意图识别引擎
│   │   ├── ai_matchers.py   # 各 AI 提供商匹配器
│   │   ├── text_utils.py    # 字符串插值
│   │   └── errors.py        # 错误类层次结构
│   ├── app/                 # 应用层
│   │   ├── api.py           # GameRunner + LauncherApi
│   │   ├── config.py        # ConfigStore + ProjectStore
│   │   ├── logger.py        # 日志系统
│   │   └── api_decorators.py# API 装饰器
│   └── static/              # 前端资源
│       ├── index.html       # Vue 3 UI
│       └── app.js           # 前端逻辑
├── data/
│   ├── games/               # 游戏项目目录
│   │   └── demo/            # 示例项目
│   │       ├── script/
│   │       │   └── main.qf
│   │       └── project.toml
│   ├── config.json          # 应用配置
│   └── logs/                # 日志文件
├── dev/
│   └── language_spec.md     # 语言规范文档
├── pyproject.toml
└── uv.lock
```

## QFScript 语言规范

### 执行流程

```
源文件 (.qf) → Lexer → Token 流 → Parser → AST → Interpreter → 运行时效果
```

### 完整语法 BNF

```ebnf
<program> ::= <statement>*

<statement> ::= <comment> | <define_stmt> | <dialogue_stmt> | <bg_stmt>
              | <interact_stmt> | <label_stmt> | <jump_stmt> | <call_stmt>
              | <return_stmt> | <var_stmt> | <set_stmt> | <input_stmt>
              | <if_stmt> | <while_stmt> | <wait_stmt> | <system_stmt>
              | <python_block> | <include_stmt>

<comment> ::= "#" <text> "\n"

<define_stmt> ::= "define" <identifier> "=" "character" "(" <char_params> ")" "\n"

<char_params> ::= "name" "=" <string> "," "avatar" "=" <string> "," "color" "=" <string>

<dialogue_stmt> ::= [<identifier>] <string> "\n"

<bg_stmt> ::= "bg" (<string> | "none") "\n"

<label_stmt> ::= "label" <identifier> ":" "\n" <statement>* "end" "\n"

<jump_stmt> ::= "jump" <identifier> ["if" <expr>] "\n"
              | "jump" <identifier> "otherwise" "\n"

<call_stmt> ::= "call" <identifier> ["if" <expr>] "\n"

<return_stmt> ::= "return" "\n"

<var_stmt> ::= "var" <identifier> "=" <expr> "\n"

<set_stmt> ::= "set" <identifier> <assign_op> <expr> "\n"

<assign_op> ::= "=" | "+=" | "-=" | "*=" | "/="

<input_stmt> ::= "input" <identifier> <string> "\n"

<if_stmt> ::= "if" <expr> ":" "\n" <statement>*
              ("elseif" <expr> ":" "\n" <statement>*)*
              ("else:" "\n" <statement>*)?
              "end" "\n"

<while_stmt> ::= "while" <expr> ":" "\n" <statement>* "end" "\n"

<wait_stmt> ::= "wait" (<number> | "click") "\n"

<system_stmt> ::= ("save" | "load" | "quit") "\n"

<python_block> ::= "python:" "\n" <python_code> "end" "\n"

<include_stmt> ::= "include" <string> "\n"

<interact_stmt> ::= "interact:" "\n" <interact_item>* "end" "\n"

<interact_item> ::= <interact_action> | <interact_fallback>

<interact_action> ::= <string> "->" <identifier> "(" <action_param_list> ")" "\n"

<action_param_list> ::= "desc" "=" <string> ["," "condition" "=" <expr>]

<interact_fallback> ::= "fallback" <string> "\n"

<expr> ::= <literal> | <identifier> | <expr> <binary_op> <expr>
         | "(" <expr> ")" | <function_call>

<binary_op> ::= "+" | "-" | "*" | "/" | "==" | "!=" | "<" | ">"
              | "<=" | ">=" | "and" | "or"

<literal> ::= <string> | <number> | "true" | "false"

<string> ::= '"' <chars>* '"' | "'" <chars>* "'"

<identifier> ::= <letter> (<letter> | <digit> | "_")*

<number> ::= <digit>+ ("." <digit>+)?
```

### 核心语句示例

**角色定义**
```qfscript
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
```

**对话**
```qfscript
yuki "早上好！"           # 角色对话
"那是一个普通的早晨..."   # 旁白
narrator "故事开始了..."  # 指定旁白角色
```

**互动模式**
```qfscript
interact:
    "打招呼" -> greet (desc="向她问候、说你好")
    "离开" -> leave (desc="告别并离开")
    fallback "雪歪了歪头，似乎没理解你的意思。"
end
```

**标签与跳转**
```qfscript
label start:
    yuki "你好！"
    jump next_scene
end

jump scene_a if flag_a == true
call event_daily
return
```

**变量**
```qfscript
var relationship = 0
set relationship += 10
input name "请输入名字："
```

**条件与循环**
```qfscript
if relationship >= 50:
    yuki "我们是很好的朋友！"
else:
    yuki "我们还不熟..."
end

var i = 0
while i < 3:
    "次数：{i}"
    set i += 1
end
```

**嵌入 Python**
```qfscript
python:
    import random
    qf.set("dice_roll", random.randint(1, 6))
    if qf.get("hp") <= 0:
        qf.jump("defeat")
end
```

**字符串插值**
```qfscript
yuki "你好，{name}！"
yuki "你掷出了 {python: random.randint(1, 6)} 点"
```

### Python 嵌入 API

```python
qf.get(name)                # 获取变量
qf.set(name, value)         # 设置变量
qf.jump(label)              # 跳转到标签
qf.call(label)              # 调用标签
qf.show_message(char, text) # 显示消息
qf.set_bg(path)             # 设置背景
qf.save()                   # 保存
qf.load()                   # 加载
qf.user_input               # 内置变量：用户最后输入的内容
qf.matched_action           # 内置变量：当前匹配到的动作名
```

### 内置变量

| 变量名 | 说明 |
|--------|------|
| `_user_input` | 用户最后输入的内容 |
| `_matched_action` | 当前匹配到的动作名 |
| `_label` | 当前标签名 |
| `_playtime` | 游戏运行时间（秒） |

## 架构指南

### 核心模块职责

| 模块 | 职责 |
|------|------|
| `tokens.py` | 定义所有 Token 类型枚举和关键词映射 |
| `lexer.py` | 将源码转为 Token 流，处理缩进、字符串转义、注释、python: 块 |
| `parser.py` | 递归下降解析，将 Token 流转为 AST，包含表达式优先级处理 |
| `ast.py` | 定义所有 AST 节点类型（Expr 和 Stmt 子类） |
| `interpreter.py` | 解释执行 AST，包含 QriaContext 提供给 Python 嵌入的 API |
| `runtime.py` | 管理运行时状态：变量、角色、背景、调用栈、待处理事件 |
| `ai_engine.py` | AI 意图识别，支持 OpenAI/DeepSeek/自定义/关键词匹配 |
| `ai_matchers.py` | 各提供商的具体匹配器实现 |
| `text_utils.py` | 字符串插值处理 `{var}` 和 `{python: expr}` |
| `errors.py` | 统一的错误类：LexerError, SyntaxError, SemanticError, RuntimeError |

### 应用层模块

| 模块 | 职责 |
|------|------|
| `api.py` | GameRunner（游戏运行器）和 LauncherApi（pywebview API 接口） |
| `config.py` | ConfigStore（配置管理）和 ProjectStore（项目导入/删除/扫描） |
| `logger.py` | 文件日志记录 |
| `api_decorators.py` | `@api_method` 装饰器统一错误处理和响应格式 |

### GameRunner 核心机制

```
启动游戏 → 加载脚本 → 词法分析 → 语法分析 → 收集标签 → 执行程序
                                                      ↓
    对话 → UI 显示 → 等待继续 ← 用户点击
    输入 → 阻塞等待 → 用户输入 → 恢复执行
    互动 → 阻塞等待 → AI 匹配 → 跳转标签
    Python → exec 执行 → 通过 qf 上下文交互
```

## 编码约定

### Python 代码风格

- 使用 `dataclass` 定义 AST 节点
- 异常类继承自基类 `QriaFictionError`
- 使用类型注解
- 模块导入顺序：标准库 → 第三方库 → 本地模块

### 前端风格

- Vue 3 Composition API
- Tailwind CSS + CSS 变量
- 暗黑/明亮双主题
- 通过 `pywebview.api` 调用 Python 方法

### 错误处理

- 所有错误包含文件名、行号、列号
- 使用 `@api_method` 装饰器统一包装 API 返回值
- 运行时错误抛出 `QFRuntimeError`

## AI 引擎

### 支持的提供商

| 提供商 | 配置 key | 依赖 |
|--------|----------|------|
| `openai` | api_key, model | openai |
| `deepseek` | api_key, model, base_url | openai |
| `custom` | api_key, model, url | urllib（内置） |
| `keyword` | 无需配置 | fuzzywuzzy |

### 匹配流程

1. 收集当前可用动作列表（过滤 condition 为真的动作）
2. 调用对应提供商的匹配器
3. 构建提示词（包含角色、状态、动作列表）
4. 解析返回的动作名
5. 匹配成功 → 跳转标签；匹配失败 → 显示 fallback

## 常见开发任务指引

### 添加新语法

1. 在 `tokens.py` 添加 TokenType
2. 在 `KEYWORDS` 字典添加映射（如为关键字）
3. 在 `lexer.py` 处理词法（通常自动处理）
4. 在 `ast.py` 添加 AST 节点类
5. 在 `parser.py` 添加 `_parse_xxx` 方法
6. 在 `interpreter.py` 和 `api.py` 添加执行逻辑
7. 更新 `language_spec.md` 和 `dev/SKILL.md`

### 调试脚本

```python
from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter

src = Path("script.qf").read_text(encoding="utf-8")
tokens = Lexer(src).tokenize()
ast = Parser(tokens).parse()
Interpreter().run(ast)
```

### 运行项目

```bash
uv run qriafiction
# 或
python src/main.py
```
