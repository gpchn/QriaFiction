# QriaFiction

QriaFiction 是一个基于 Python 的互动小说（Interactive Fiction）引擎，包含自定义脚本语言 QFScript、完整解释器、AI 意图识别系统，以及基于 pywebview 的桌面应用界面。

## 特性

- **QFScript 脚本语言** — 专为聊天风格互动小说设计，支持角色定义、对话、分支、变量、循环、音频
- **完整解释器** — Lexer → Parser → Interpreter 管道，支持 Python 嵌入执行
- **AI 意图识别** — 互动模式下支持 OpenAI API、DeepSeek API 和本地模糊匹配
- **多脚本自动加载** — 自动扫描 `script/` 目录，按文件名命名空间管理标签
- **桌面 GUI** — 基于 pywebview + Vue 3 + Tailwind CSS
- **存档系统** — JSON 格式存档，支持多存档槽位
- **音频支持** — 背景音乐（淡入淡出）、音效、音量控制

## 安装

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

**前提条件：** Python 3.12+

## 快速开始

```bash
uv run qriafiction
# 或
python src/main.py
```

启动后进入项目选择器界面，可导入游戏或使用内置 demo 项目。详细开发指南参见 [dev/quick_start.md](dev/quick_start.md)。

## 项目结构

```
QriaFiction/
├── src/
│   ├── main.py                  # 入口：pywebview 窗口创建
│   ├── core/                    # 核心引擎
│   │   ├── tokens.py            # Token 类型定义
│   │   ├── lexer.py             # 词法分析器
│   │   ├── parser.py            # 语法分析器（递归下降）
│   │   ├── ast.py               # AST 节点定义
│   │   ├── interpreter.py       # 解释器
│   │   ├── runtime.py           # 运行时环境
│   │   ├── ai_engine.py         # AI 意图识别引擎
│   │   ├── ai_matchers.py       # AI 提供商匹配器
│   │   ├── text_utils.py        # 字符串插值
│   │   └── errors.py            # 错误类层次结构
│   ├── app/                     # 应用层
│   │   ├── api.py               # GameRunner + LauncherApi
│   │   ├── config.py            # 配置管理 + 项目商店
│   │   ├── logger.py            # 日志系统
│   │   └── api_decorators.py    # API 装饰器
│   └── static/                  # 前端资源
│       ├── index.html           # Vue 3 UI
│       └── app.js               # 前端逻辑
├── data/                        # 运行时数据
│   ├── games/                   # 游戏项目
│   ├── config.json              # 应用配置
│   └── logs/                    # 日志文件
├── dev/                         # 开发文档
│   ├── language_spec.md         # QFScript 语言规范
│   ├── prompt.md                # AI 游戏开发提示词（手动输入）
│   ├── SKILL.md                 # Agent 技能文档（OpenClaw 等）
│   └── quick_start.md           # 游戏开发新手指引
├── tests/                       # 测试套件
└── pyproject.toml
```

## 游戏项目结构

每个游戏项目是一个独立目录，包含以下结构：

```
my_game/
├── script/                      # QFScript 脚本目录
│   ├── main.qf                  # 主脚本（入口）
│   ├── ch1_prologue.qf          # 章节脚本（可选）
│   └── events.qf                # 事件脚本（可选）
├── assets/
│   ├── bg/                      # 背景图片（.png/.jpg/.webp）
│   ├── avatar/                  # 角色头像
│   └── audio/
│       ├── bgm/                 # 背景音乐
│       └── sfx/                 # 音效
└── project.toml                 # 项目配置
```

## QFScript 语言概览

```qfscript
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")

label start:
    bg "school.png"
    yuki "早上好！"
    yuki "今天要去哪里呢？"
    
    options:
        "去学校" -> school (desc="前往学校")
        "待在家" -> stay (desc="待在家里")
    end
end

label school:
    bg "classroom.png"
    yuki "教室到了！"
    interact:
        "打招呼" -> greet (desc="和她搭话")
        "离开" -> leave (desc="离开")
        fallback "她没有回应。"
    end
end

label greet:
    yuki "你好呀！"
    jump start
end

label leave:
    quit
end
```

完整语言规范参见 [dev/language_spec.md](dev/language_spec.md)。

## AI 提供商配置

在应用设置页面可配置意图识别的 AI 提供商：

| 提供商 | 所需配置 | 依赖 |
|--------|---------|------|
| `openai` | api_key, model | openai |
| `deepseek` | api_key, model, base_url | openai |
| `keyword` | 无 | fuzzywuzzy（已内置） |

## 依赖

| 包 | 用途 |
|----|------|
| pywebview | 桌面应用窗口 |
| fuzzywuzzy | 字符串模糊匹配 |
| python-levenshtein | fuzzywuzzy 加速依赖 |
| openai | OpenAI/DeepSeek API 客户端 |
| toml | 项目配置解析 |

## 文档

| 文档 | 说明 |
|------|------|
| [dev/language_spec.md](dev/language_spec.md) | QFScript 语言规范 |
| [dev/prompt.md](dev/prompt.md) | AI 游戏开发提示词（手动粘贴到 ChatGPT 等） |
| [dev/SKILL.md](dev/SKILL.md) | Agent 技能文档（供 OpenClaw 等 Agent 使用） |
| [dev/quick_start.md](dev/quick_start.md) | 游戏开发新手指引 |

## 许可证

Apache 2.0
