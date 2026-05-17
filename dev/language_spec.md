# QFScript 语言规范

> QriaFiction Script（简称 QFScript）是一种面向互动小说的脚本语言。

---

## 1. 概述

QFScript 由词法分析器（Lexer）、语法分析器（Parser）和解释器（Interpreter）组成。语言采用行号分隔的语句格式，使用缩进（4 空格）表示块结构。

### 1.1 项目结构

```
project/
├── script/                  # 所有 .qf 脚本文件
│   ├── main.qf              # 主入口（必需）
│   ├── ch1_prologue.qf      # 其他脚本（可选）
│   └── events.qf            # 其他脚本（可选）
├── assets/
│   ├── bg/                  # 背景图片
│   ├── avatar/              # 角色头像
│   └── audio/
│       ├── bgm/             # 背景音乐
│       └── sfx/             # 音效
└── project.toml             # 项目配置
```

### 1.2 多脚本命名规则

引擎自动扫描 `script/` 目录下所有 `.qf` 文件：

- `main.qf` 中的标签**不加命名空间前缀**（如 `jump start`）
- 其他 `.qf` 文件的标签自动以文件名作为命名空间前缀（如 `ch1_prologue.qf` 中的 `label begin:` 变为 `ch1_prologue.begin`）
- 引用格式：`文件名.标签名`（不含 `.qf` 扩展名）

### 1.3 词法规则

- **标识符**：以字母或下划线开头，后续可跟字母、数字、下划线、点号（`.`）
- **字符串**：双引号 `"..."` 或单引号 `'...'`，支持转义 `\n`、`\t`、`\"`、`\'`
- **数字**：整数或浮点数（`123`、`3.14`）
- **布尔值**：`true`、`false`
- **注释**：`#` 开头，至行尾

---

## 2. 数据类型

| 类型 | 字面量 | 说明 |
|------|--------|------|
| 字符串 | `"文本"`、`'文本'` | 支持 `{variable}` 和 `{python: expr}` 插值 |
| 整数 | `0`、`42` | — |
| 浮点数 | `3.14`、`0.5` | — |
| 布尔值 | `true`、`false` | — |
| 标识符 | `name`、`has_key` | 变量名、标签名、角色名 |

---

## 3. 角色定义

```qfscript
define <角色名> = character(name="<名称>", avatar="<路径>", color="<颜色>")
```

**参数：**

- `name` — 显示名称（空字符串表示不显示名称栏）
- `avatar` — 头像图片路径，相对于项目 `assets/` 目录（空字符串表示无头像）
- `color` — 名称文字颜色（十六进制格式）

**示例：**

```qfscript
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
define narrator = character(name="", avatar="", color="#888888")
```

---

## 4. 语句

### 4.1 对话 (Dialogue)

```
[<角色名>] <字符串> "\n"
```

- 带角色名：显示角色名称、头像和颜色
- 不带角色名：纯旁白

```qfscript
yuki "早上好！"
"那是一个普通的早晨..."
narrator "故事就这样开始了..."
```

### 4.2 背景 (Background)

```
"bg" (<字符串> | "none") "\n"
```

路径相对于 `assets/bg/` 目录。`bg none` 清除背景。

```qfscript
bg "school.png"
bg none
```

### 4.3 标签 (Label)

```
"label" <标识符> ":" "\n"
    <语句>*
"end" "\n"
```

标签是游戏流程的基本单位，支持跳转和调用。

```qfscript
label start:
    yuki "你好！"
    jump next_scene
end
```

### 4.4 跳转 (Jump)

```
"jump" <标识符> ["if" <表达式>] "\n"
"jump" <标识符> "otherwise" "\n"
```

- `jump <标签>` — 无条件跳转
- `jump <标签> if <表达式>` — 条件跳转（表达式为真时跳转）
- `jump <标签> otherwise` — 否则跳转

```qfscript
jump scene_a
jump good_end if relationship >= 80
jump normal_end otherwise
```

### 4.5 调用 (Call)

```
"call" <标识符> ["if" <表达式>] "\n"
```

调用标签，执行完毕后返回调用位置。

```qfscript
call daily_event
call intro if day == 1
```

### 4.6 返回 (Return)

```
"return" "\n"
```

从 `call` 调用中返回。

### 4.7 变量声明 (Var)

```
"var" <标识符> "=" <表达式> "\n"
```

```qfscript
var name = "勇者"
var relationship = 0
var has_key = false
```

### 4.8 变量赋值 (Set)

```
"set" <标识符> <赋值运算符> <表达式> "\n"
```

赋值运算符：`=`、`+=`、`-=`、`*=`、`/=`

```qfscript
set name = "樱"
set relationship += 10
set has_key = true
```

### 4.9 玩家输入 (Input)

```
"input" <标识符> <字符串> "\n"
```

获取玩家文本输入，存入变量。`<字符串>` 为提示语。

```qfscript
input name "请输入你的名字："
```

### 4.10 条件 (If)

```
"if" <表达式> ":" "\n"
    <语句>*
["elseif" <表达式> ":" "\n" <语句>*]*
["else:" "\n" <语句>*]?
"end" "\n"
```

```qfscript
if relationship >= 50:
    yuki "我很喜欢你呢！"
else:
    yuki "我们还不熟..."
end
```

### 4.11 循环 (While)

```
"while" <表达式> ":" "\n"
    <语句>*
"end" "\n"
```

```qfscript
var i = 0
while i < 3:
    "次数：{i}"
    set i += 1
end
```

### 4.12 等待 (Wait)

```
"wait" (<数字> | "click") "\n"
```

- `wait <秒数>` — 等待指定秒数
- `wait click` — 等待玩家点击

### 4.13 系统命令 (System)

```
("save" | "load" | "quit") "\n"
```

- `save` — 保存游戏
- `load` — 加载游戏
- `quit` — 退出游戏

### 4.14 互动模式 (Interact)

```
"interact:" "\n"
    <互动项>*
    <fallback>+
"end" "\n"
```

互动项：
```
<字符串> "->" <标识符> "(" "desc" "=" <字符串> ["," "condition" "=" <表达式>] ")" "\n"
```

Fallback：
```
"fallback" <字符串> "\n"
```

互动模式等待玩家输入文本，AI 匹配到对应动作后跳转。

```qfscript
interact:
    "打招呼" -> greet (desc="向她问候、说你好")
    "离开" -> leave (desc="告别并离开")
    fallback "她看着你，等待你说些别的..."
end
```

**规则：**

- `desc` — 必需，描述该动作的含义，用于 AI 意图识别
- `condition` — 可选，条件表达式为真时该动作才可用
- `fallback` — **必需**，至少一条，匹配失败时显示的回复
- 匹配成功 → 跳转至对应标签，退出互动模式
- 匹配失败 → 显示 fallback，继续等待输入

### 4.15 固定选项 (Options)

```
"options:" "\n"
    <选项项>+
"end" "\n"
```

选项项：
```
<字符串> "->" <标识符> "(" "desc" "=" <字符串> ["," "condition" "=" <表达式>] ")" "\n"
```

固定选项直接显示按钮，玩家点击后跳转，无需 AI 匹配。

```qfscript
options:
    "去学校" -> school (desc="前往学校")
    "待在家里" -> stay (desc="待在家里")
end
```

**规则：**

- 显示为按钮，玩家点击即跳转
- 不支持 fallback（与 interact 的区别）
- 条件选项（`condition`）仅在表达式为真时显示

### 4.16 音频

#### 背景音乐

```
"music" <字符串> ["loop" <布尔值>] ["volume" <数字>] ["with" "fade" <数字>] "\n"
```

```qfscript
music "audio/bgm/main.mp3"
music "audio/bgm/tension.mp3" with fade 2.0
music "audio/bgm/sad.mp3" volume 0.5
music "audio/bgm/intro.mp3" loop false
```

停止背景音乐：
```
"stop" "music" ["with" "fade" <数字>] "\n"
```

```qfscript
stop music
stop music with fade 3.0
```

#### 音效

```
"sound" <字符串> ["volume" <数字>] "\n"
```

```qfscript
sound "audio/sfx/door.wav"
sound "audio/sfx/explosion.wav" volume 0.8
```

停止音效：
```
"stop" "sound" "\n"
```

#### 音量控制

```
"volume" ("music" | "sound") "=" <数字> "\n"
```

```qfscript
volume music = 0.7
volume sound = 0.5
```

### 4.17 嵌入 Python

```
"python:" "\n"
    <Python 代码>
"end" "\n"
```

在脚本中直接执行 Python 代码。

```qfscript
python:
    import random
    qf.set("dice_roll", random.randint(1, 6))
end
```

**Python API：**

| 方法 | 说明 |
|------|------|
| `qf.get(name)` | 获取变量 |
| `qf.set(name, value)` | 设置变量 |
| `qf.jump(label)` | 跳转到标签 |
| `qf.call(label)` | 调用标签 |
| `qf.show_message(char, text)` | 显示消息 |
| `qf.set_bg(path)` | 设置背景 |
| `qf.save()` | 保存 |
| `qf.load()` | 加载 |
| `qf.user_input` | 用户最后输入的内容 |
| `qf.matched_action` | 当前匹配到的动作名 |

**Python 表达式插值：**

```qfscript
yuki "你掷出了 {python: random.randint(1, 6)} 点"
```

---

## 5. 表达式

### 5.1 运算符

| 运算符 | 类型 | 示例 |
|--------|------|------|
| `+` | 加法/字符串连接 | `a + 1`、`"hi " + name` |
| `-` | 减法 | `a - 1` |
| `*` | 乘法 | `a * 2` |
| `/` | 除法 | `a / 2` |
| `==` | 等于 | `a == b` |
| `!=` | 不等于 | `a != b` |
| `<` | 小于 | `a < b` |
| `>` | 大于 | `a > b` |
| `<=` | 小于等于 | `a <= b` |
| `>=` | 大于等于 | `a >= b` |
| `and` | 逻辑与 | `a and b` |
| `or` | 逻辑或 | `a or b` |
| `not` | 逻辑非 | `not a` |

### 5.2 函数调用

```
<标识符> "(" [<参数列表>] ")"
```

```qfscript
result = max(a, b)
```

---

## 6. 内置变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `_user_input` | `string` | 用户最后输入的内容 |
| `_matched_action` | `string` | 当前匹配到的动作名 |
| `_label` | `string` | 当前标签名 |
| `_playtime` | `float` | 游戏运行时间（秒） |

---

## 7. 完整语法 BNF

```ebnf
<program> ::= <statement>*

<statement> ::= <comment>
              | <define_stmt>
              | <dialogue_stmt>
              | <bg_stmt>
              | <interact_stmt>
              | <options_stmt>
              | <label_stmt>
              | <jump_stmt>
              | <call_stmt>
              | <return_stmt>
              | <var_stmt>
              | <set_stmt>
              | <input_stmt>
              | <if_stmt>
              | <while_stmt>
              | <wait_stmt>
              | <system_stmt>
              | <python_block>
              | <music_stmt>
              | <sound_stmt>
              | <stop_audio_stmt>
              | <volume_stmt>

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

<music_stmt> ::= "music" <string>
                 ["loop" <boolean>]
                 ["volume" <number>]
                 ["with" "fade" <number>] "\n"

<sound_stmt> ::= "sound" <string>
                 ["volume" <number>] "\n"

<stop_audio_stmt> ::= "stop" ("music" ["with" "fade" <number>] | "sound") "\n"

<volume_stmt> ::= "volume" ("music" | "sound") "=" <number> "\n"

<interact_stmt> ::= "interact:" "\n"
                    <interact_item>*
                    <interact_fallback>+
                    "end" "\n"

<interact_item> ::= <interact_action>

<interact_action> ::= <string> "->" <identifier>
                      "(" <action_param_list> ")" "\n"

<action_param_list> ::= "desc" "=" <string>
                        ["," "condition" "=" <expr>]

<interact_fallback> ::= "fallback" <string> "\n"

<options_stmt> ::= "options:" "\n"
                   <option_item>+
                   "end" "\n"

<option_item> ::= <string> "->" <identifier>
                  "(" <option_param_list> ")" "\n"

<option_param_list> ::= "desc" "=" <string>
                        ["," "condition" "=" <expr>]

<expr> ::= <literal>
         | <identifier>
         | <expr> <binary_op> <expr>
         | "(" <expr> ")"
         | <function_call>

<binary_op> ::= "+" | "-" | "*" | "/" | "==" | "!=" | "<" | ">" | "<=" | ">=" | "and" | "or"

<literal> ::= <string> | <number> | "true" | "false"

<string> ::= '"' <chars>* '"' | "'" <chars>* "'"

<identifier> ::= <letter> (<letter> | <digit> | "_")*

<number> ::= <digit>+ ("." <digit>+)?

<boolean> ::= "true" | "false"
```

---

## 8. 错误处理

所有语法和运行时错误会输出错误信息，包含文件路径、行号、列号。

**语法错误示例：**

```
SyntaxError: 未知角色 'unknown_character'
  --> script/main.qf:15:1
   |
15 | unknown_character "你好"
   | ^^^^^^^^^^^^^^^^^ 角色未定义
   |
   = 提示: 请先使用 define 语句定义角色
```

---

## 9. 命令行接口

```bash
qf run script/main.qf      # 运行脚本
qf check script/main.qf    # 检查语法
qf dump-ast script/main.qf # 显示 AST（调试）
```

---

## 10. 完整示例

```qfscript
# 定义角色
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
define narrator = character(name="", avatar="", color="#888888")

# 初始化变量
var name = "勇者"
var relationship = 0

label start:
    narrator "欢迎来到这个世界！"
    input name "请输入你的名字："
    
    bg "school_gate.png"
    
    yuki "早上好，{name}！"
    yuki "今天要去哪里呢？"
    
    interact:
        "去游乐园" -> route_park (desc="前往游乐园玩")
        "去图书馆" -> route_library (desc="去图书馆看书")
        fallback "你不确定要去哪里..."
    end
end

label route_park:
    yuki "好主意！"
    set relationship += 10
    bg "amusement_park.png"
    yuki "好开心啊！"
    jump route_end
end

label route_library:
    narrator "你来到了图书馆。"
    bg "library.png"
    jump route_end
end

label route_end:
    wait click
    quit
end
```
