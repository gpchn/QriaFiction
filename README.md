# QriaFiction

QriaFiction 是一个基于 Python 的互动小说引擎，包含自定义脚本语言 **QFScript**、完整的解释器实现、AI 意图识别引擎，以及基于 pywebview 的桌面应用界面。

## 特性

- **自定义脚本语言** - QFScript，专为聊天风格互动小说设计，支持角色定义、对话、分支、变量、循环等
- **完整解释器** - Lexer → Parser → Interpreter 管道，支持 Python 嵌入执行
- **AI 意图识别** - 互动模式下支持 OpenAI API、DeepSeek API 和本地模糊匹配（fuzzywuzzy）
- **桌面 GUI** - 基于 pywebview + Vue 3 + Tailwind CSS 的现代界面
- **存档系统** - JSON 格式存档，支持多存档槽位
- **多脚本自动加载** - 引擎自动扫描 `script/` 目录下所有 `.qf` 文件，按文件名命名空间管理标签
- **字符串插值** - `{variable}` 和 `{python: expression}` 语法

## 安装

### 前提条件

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)（推荐）或 pip

### 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

## 快速开始

```bash
# 启动应用
uv run qriafiction
# 或
python src/main.py
```

启动后将看到项目选择器界面。导入游戏项目或直接使用内置的 `demo` 项目。

## 项目结构

```
QriaFiction/
├── src/
│   ├── main.py                  # 入口：pywebview 窗口创建
│   ├── core/                    # 核心引擎
│   │   ├── tokens.py            # Token 类型定义（50+ 种）
│   │   ├── lexer.py             # 词法分析器
│   │   ├── parser.py            # 语法分析器（递归下降）
│   │   ├── ast.py               # AST 节点（dataclass）
│   │   ├── interpreter.py       # 解释器 + QriaContext
│   │   ├── runtime.py           # 运行时环境
│   │   ├── ai_engine.py         # AI 意图识别引擎
│   │   ├── ai_matchers.py       # 各 AI 提供商匹配器
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
├── data/
│   ├── games/                   # 游戏项目目录
│   │   └── demo/                # 示例项目
│   ├── config.json              # 应用配置
│   └── logs/                    # 日志文件
├── dev/                         # 开发文档
└── pyproject.toml
```

## QFScript 语言

### 基本语法

#### 角色定义

```qfscript
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
```

#### 对话

```qfscript
yuki "早上好！"           # 角色对话
"那是一个普通的早晨..."   # 旁白
narrator "故事开始了..."  # 指定旁白角色
```

#### 变量

```qfscript
var relationship = 0
set relationship += 10
input name "请输入你的名字："
```

#### 标签与跳转

```qfscript
# main.qf 中的标签（不加命名空间前缀）
label start:
    yuki "你好！"
    jump ch1_prologue.begin  # 跳转到 ch1_prologue.qf
end

# ch1_prologue.qf
label begin:
    yuki "欢迎来到序章..."
    call events.greeting     # 调用 events.qf 中的标签
end

# events.qf
label greeting:
    yuki "早上好！"
    return
end

# 条件跳转
jump scene_a if flag_a == true
call event_daily
return
```

> **多脚本支持**：引擎自动扫描 `script/` 目录下所有 `.qf` 文件。文件名自动成为标签命名空间前缀（如 `ch1_prologue.qf` 中的 `label begin:` 变为 `ch1_prologue.begin`）。`main.qf` 中的标签无前缀。

#### 条件与循环

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

#### 互动模式

```qfscript
interact:
    "打招呼" -> greet (desc="向她问候、说你好")
    "离开" -> leave (desc="告别并离开")
    fallback "雪歪了歪头，似乎没理解你的意思。"
end
```

#### 嵌入 Python

```qfscript
python:
    import random
    dice = random.randint(1, 6)
    qf.set("dice_roll", dice)
end

narrator "你掷出了 {dice_roll} 点！"
```

#### 字符串插值

```qfscript
yuki "你好，{name}！"
yuki "你掷出了 {python: random.randint(1, 6)} 点"
```

#### 其他

```qfscript
bg "bg/school.png"     # 设置背景
bg none                # 清除背景
wait 1.5               # 等待 1.5 秒
wait click             # 等待点击
save                   # 存档
load                   # 读档
quit                   # 结束游戏
```

#### 音频

```qfscript
music "audio/bgm/main.mp3"             # 播放背景音乐（循环）
music "audio/bgm/tension.mp3" with fade 2.0  # 淡入播放
sound "audio/sfx/door.wav"             # 播放音效
stop music                             # 停止音乐
stop music with fade 3.0               # 淡出停止
stop sound                             # 停止音效
volume music = 0.7                     # 设置音乐音量
volume sound = 0.5                     # 设置音效音量
```

### 完整语法规范

参见 [dev/language_spec.md](dev/language_spec.md)

## 配置

### AI 提供商

在应用设置页面可以配置 AI 模型：

| 提供商     | 所需配置                 | 依赖                 |
| ---------- | ------------------------ | -------------------- |
| `openai`   | api_key, model           | openai               |
| `deepseek` | api_key, model, base_url | openai               |
| `keyword`  | 无                       | fuzzywuzzy（已内置） |

### 项目配置

每个游戏项目包含一个 `project.toml` 文件：

```toml
[project]
id = "my-game"
name = "我的游戏"
version = "1.0.0"

[script]
main = "script/main.qf"
```

## API

### Python 嵌入 API

在 `python:` 块中可以通过 `qf` 上下文与脚本交互：

```python
qf.get(name)                # 获取变量
qf.set(name, value)         # 设置变量
qf.jump(label)              # 跳转到标签
qf.call(label)              # 调用标签
qf.show_message(char, text) # 显示消息
qf.set_bg(path)             # 设置背景
qf.save(slot)               # 存档
qf.load(slot)               # 读档
qf.user_input               # 用户最后输入的内容
qf.matched_action           # 当前匹配到的动作名
```

### 内置变量

| 变量名            | 说明               |
| ----------------- | ------------------ |
| `_user_input`     | 用户最后输入的内容 |
| `_matched_action` | 当前匹配到的动作名 |
| `_label`          | 当前标签名         |
| `_playtime`       | 游戏运行时间（秒） |

## 存档

存档以 JSON 格式保存在 `data/games/<项目名>/saves/` 目录下，包含：

- 所有变量值
- 角色定义
- 当前背景
- 当前标签位置
- 游戏运行时长

## 开发 TODO

- 添加音频和音乐支持
- 提高测试覆盖率
- 添加文字打字机动画

## 依赖

| 包                 | 用途                       |
| ------------------ | -------------------------- |
| pywebview          | 桌面应用窗口               |
| fuzzywuzzy         | 字符串模糊匹配             |
| python-levenshtein | fuzzywuzzy 加速依赖        |
| openai             | OpenAI/DeepSeek API 客户端 |
| toml               | 项目配置解析               |

## 许可证

Apache 2.0
