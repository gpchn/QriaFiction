# QriaFiction Language Specification

> QriaFiction Script（简称 QFScript）是一种类似聊天界面的互动小说脚本语言。

---

## 1. 项目结构

```
project/
├── script/              # 脚本目录
│   ├── main.qf          # 主脚本
│   └── chapter1.qf      # 其他章节
├── assets/              # 资源目录
│   ├── bg/              # 背景图片
│   └── avatar/          # 头像图片
├── project.toml         # 项目配置
└── main.py              # 启动入口（可选）
```

### project.toml

```toml
[project]
title = "我的故事"
author = "作者名"
version = "0.1.0"

[display]
width = 800
height = 600
bg_default = "assets/bg/default.png"

[characters]
# 角色配置在此定义（也可在脚本中定义）
```

---

## 2. 基础语法

### 2.1 注释

```qfscript
# 这是注释
```

### 2.2 字符串

```qfscript
"普通字符串"
'也可以用单引号'

# 变量插值
"你好，{name}！"

# 转义
"他说：\"你好\""
'换行\n制表符\t'
```

---

## 3. 角色定义

```qfscript
# 定义角色（头像 + 显示名 + 颜色）
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
define haru = character(name="春", avatar="avatar/haru.png", color="#ffb6c1")
define narrator = character(name="", avatar="", color="#888888")
```

**参数说明：**
- `name`：显示名称（空字符串则不显示名称）
- `avatar`：头像图片路径（空字符串则无头像）
- `color`：名称颜色

---

## 4. 核心语句

### 4.1 对话

```qfscript
# 基本对话
yuki "早上好！"
haru "你好呀！"

# 无角色（纯旁白）
"那是一个普通的早晨..."

# 使用 narrator 角色
narrator "故事就这样开始了..."
```

### 4.2 背景

```qfscript
# 设置背景
bg "bg/school.png"
bg "bg/classroom.png"

# 清除背景（透明）
bg none
```

### 4.3 互动模式 (interact)

`interact` 让用户进入一个循环输入状态，AI 理解用户意图后跳转到对应标签。

```qfscript
interact:
    "打招呼" -> greet (desc="向她问候、说你好、搭话")
    "搭话" -> greet (desc="和她开始对话、聊天")
    "离开" -> leave (desc="告别并离开教室")
    fallback "雪歪了歪头，似乎没太理解你的意思。"
    fallback "雪看着你，等待你说些别的..."
end

# 带条件的动作
interact:
    "送她礼物" -> give_gift (desc="给她礼物", condition=_has_gift)
    "离开" -> leave (desc="离开")
    fallback "她没有回应你的话。"
end
```

**语法规则：**
- `"动作名" -> 标签 (desc="描述")` - 可匹配的动作
- `"动作名" -> 标签 (desc="...", condition=表达式)` - 条件动作（变量表达式为真时才可用）
- `fallback "..."` - 匹配失败时的回复（**必需**，至少一条）

**行为：**
1. 等待用户输入
2. AI 匹配用户输入到某个动作
3. **匹配成功** → 更新 `_user_input` 和 `_matched_action`，跳转到对应标签，退出
4. **匹配失败** → 随机显示一条 fallback，**继续等待输入**（不退出）

**运行模式：**
| 模式 | 输入方式 |
|------|----------|
| 终端 | 命令行输入 |
| webview | 输入框 + 发送按钮 |

提示语等 UI 相关逻辑由前端处理，不在脚本中定义。

### 4.4 标签与跳转

```qfscript
# 定义标签
label start:
    yuki "你好！"
    jump next_scene
end

label next_scene:
    haru "欢迎来到这里！"
end

# 条件跳转
jump scene_a if flag_a == true
jump scene_b otherwise

# 调用（会返回）
call event_daily
call intro if day == 1

# 返回
return
```

### 4.5 变量

```qfscript
# 声明变量
var name = "勇者"
var relationship = 0
var has_key = false

# 修改变量
set name = "樱"
set relationship += 10
set has_key = true

# 玩家输入
input name "请输入你的名字："
```

### 4.6 条件

```qfscript
# if-else
if relationship >= 50:
    yuki "我很喜欢你呢！"
else:
    yuki "我们还不熟..."
end

# if-elseif-else
if day == 1:
    "第一天..."
elseif day == 2:
    "第二天..."
else:
    "很多天以后..."
end
```

### 4.7 循环

```qfscript
var i = 0
while i < 3:
    "次数：{i}"
    set i += 1
end
```

### 4.8 等待

```qfscript
wait 1.5       # 等待1.5秒
wait click     # 等待点击
```

### 4.9 系统

```qfscript
save           # 保存游戏
load           # 加载游戏
quit           # 退出游戏
```

---

## 5. 嵌入 Python

对于复杂逻辑，直接嵌入 Python 代码：

```qfscript
# 执行 Python 代码
python:
    import random
    qf.set("dice_roll", random.randint(1, 6))
    qf.set("bonus", qf.get("level") * 10)
end

# 调用 Python 函数
python:
    def check_victory():
        return qf.get("hp") > 0 and qf.get("enemy_hp") <= 0
    
    if check_victory():
        qf.jump("victory_scene")
    else:
        qf.jump("continue_fight")
end

# Python 表达式作为值
yuki "你掷出了 {python: random.randint(1, 6)} 点"
```

**Python 上下文提供的 API：**

```python
qf.get(name)           # 获取变量
qf.set(name, value)    # 设置变量
qf.jump(label)         # 跳转到标签
qf.call(label)         # 调用标签
qf.show_message(char, text)  # 显示消息
qf.set_bg(path)        # 设置背景
qf.save()              # 保存
qf.load()              # 加载
qf.user_input          # 内置变量: 用户最后输入的内容
qf.matched_action      # 内置变量: 当前匹配到的动作名
```

---

## 7. 完整语法 BNF

```ebnf
<program> ::= <statement>*

<statement> ::= <comment>
              | <define_stmt>
              | <dialogue_stmt>
              | <bg_stmt>
              | <interact_stmt>
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
              | <include_stmt>

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

<interact_stmt> ::= "interact:" "\n" 
                    <interact_item>* 
                    "end" "\n"

<interact_item> ::= <interact_action>
                  | <interact_fallback>

<interact_action> ::= <string> "->" <identifier> 
                      "(" <action_param_list> ")" "\n"

<action_param_list> ::= "desc" "=" <string> 
                        ["," "condition" "=" <expr>]

<interact_fallback> ::= "fallback" <string> "\n"

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
```

---

## 7. 解释器架构

### 7.1 执行流程

```
源文件 (.qf)
    │
    ▼
┌──────────────┐
│   词法分析    │  Lexer
└──────────────┘
    │
    ▼  Token 流
┌──────────────┘
│   语法分析    │  Parser  
└──────────────┘
    │
    ▼  AST
┌──────────────┐
│  解释执行     │  Interpreter
│  (直接执行)   │
└──────────────┘
    │
    ▼
运行时效果
```

### 7.2 解释器结构

```python
class Interpreter:
    def __init__(self):
        self.variables = {}          # 变量存储
        self.labels = {}             # 标签位置映射
        self.characters = {}         # 角色定义
        self.call_stack = []         # 调用栈
        self.current_pos = 0         # 当前执行位置
        self.ast = None              # 解析后的 AST
    
    def execute(self, node):
        """执行单个 AST 节点"""
        pass
    
    def execute_program(self, ast):
        """执行程序"""
        pass
```

### 7.3 模块结构

```
src/compiler/
├── __init__.py
├── tokens.py        # Token 类型
├── lexer.py         # 词法分析
├── parser.py        # 语法分析
├── ast.py           # AST 节点
├── interpreter.py   # 解释器
├── runtime.py       # 运行时环境
├── ai_engine.py     # AI 意图识别引擎
├── errors.py        # 错误处理
└── cli.py           # 命令行接口
```

### 7.4 AI 引擎

```python
class AIEngine:
    def __init__(self, config: AIConfig):
        self.provider = config.provider
        self.model = config.model
        self.api_key = config.api_key
    
    def match_action(self, 
                     user_input: str, 
                     actions: List[Action],
                     runtime: Runtime) -> Optional[str]:
        """
        将用户输入匹配到可用动作
        
        自动获取上下文：
        - 当前标签
        - 角色列表及其设定
        - 当前背景
        - 变量状态
        
        返回: 匹配的动作名称，或 None（未匹配）
        """
        prompt = self._build_prompt(user_input, actions, runtime)
        response = self._call_llm(prompt)
        return self._parse_response(response)
    
    def _build_prompt(self, 
                      user_input: str, 
                      actions: List[Action],
                      runtime: Runtime) -> str:
        """
        构建 AI 提示词
        
        自动包含：
        - 角色定义（name, 性格暗示）
        - 当前场景状态
        - 可用动作列表
        """
        prompt = f"""你是一个互动小说的意图识别助手。

【角色】
"""
        for char in runtime.characters.values():
            prompt += f"- {char.name}\n"
        
        prompt += f"""
【当前状态】
标签: {runtime.current_label}

【可用动作】
"""
        for i, action in enumerate(actions, 1):
            prompt += f"{i}. {action.name} - {action.desc}\n"
        
        prompt += f"""
【用户输入】
{user_input}

请从可用动作中选择最匹配的一个，只返回动作名称。如果无法匹配，返回 NONE。"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        pass
    
    def _parse_response(self, response: str) -> Optional[str]:
        """解析 LLM 返回的动作名"""
        response = response.strip()
        if response == "NONE":
            return None
        return response
```

### 7.5 互动模式实现

```python
class InteractProcessor:
    """互动模式处理器"""
    
    def __init__(self, interpreter: Interpreter, ai_engine: AIEngine):
        self.interpreter = interpreter
        self.ai = ai_engine
    
    def run(self, 
            prompt: str = None,
            timeout: float = None,
            default_label: str = None,
            actions: List[Action] = None,
            fallback_msgs: List[str] = None):
        """
        运行互动模式
        
        循环直到：
        1. 匹配到动作 → 跳转并退出
        2. 超时 → 跳转 default 并退出
        """
        if prompt:
            self.show_message(prompt)
        
        while True:
            user_input = self.get_user_input(timeout=timeout)
            
            if user_input is None:  # 超时
                if default_label:
                    self.interpreter.jump(default_label)
                return
            
            # AI 匹配
            matched = self.ai.match_action(
                user_input, 
                actions, 
                self.interpreter.runtime
            )
            
            if matched:
                # 匹配成功，更新内置变量
                self.interpreter.runtime.set("_user_input", user_input)
                self.interpreter.runtime.set("_matched_action", matched)
                # 跳转到对应标签，退出循环
                self.interpreter.jump(matched)
                return
            else:
                # 匹配失败，显示 fallback
                msg = random.choice(fallback_msgs)
                self.show_message(msg)
                # 继续循环，不退出
```

### 7.6 自由输入 (Input)

用于获取玩家的文本输入（如名字）：

```qfscript
input _name "请输入你的名字："
```

**与互动模式的区别：**
- `interact` - 用户输入被 AI 理解并映射到预定义动作，循环直到匹配成功
- `input` - 获取一次文本输入，存入变量，由作者处理

---

## 8. 错误处理

```
Error: 未知角色 'unknown_character'
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
# 运行脚本
qf run script/main.qf

# 检查语法
qf check script/main.qf

# 显示 AST（调试）
qf dump-ast script/main.qf
```

---

## 10. 完整示例

```qfscript
# 定义角色
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
define haru = character(name="春", avatar="avatar/haru.png", color="#ffb6c1")
define system = character(name="", avatar="", color="#888888")

# 初始化变量
var _name = "勇者"
var relationship = 0

# 主流程
label start:
    system "欢迎来到这个世界！"
    input _name "请输入你的名字："
    
    bg "bg/school_gate.png"
    
    yuki "早上好，{_name}！"
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
    bg "bg/amusement_park.png"
    yuki "好开心啊！"
    jump route_end
end

label route_library:
    haru "你也来图书馆啊！"
    bg "bg/library.png"
    haru "一起看书吧~"
    jump route_end
end

label route_end:
    wait click
    quit
end
```

---

## 11. 嵌入 Python 示例

```qfscript
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")

var hp = 100
var enemy_hp = 50

label fight:
    python:
        import random
        damage = random.randint(10, 30)
        qf.set("enemy_hp", qf.get("enemy_hp") - damage)
        qf.set("hp", qf.get("hp") - random.randint(5, 15))
    end
    
    yuki "造成了伤害！"
    
    # 检查胜负
    python:
        if qf.get("enemy_hp") <= 0:
            qf.jump("victory")
        elif qf.get("hp") <= 0:
            qf.jump("defeat")
        else:
            qf.jump("fight")  # 继续战斗
    end
end

label victory:
    yuki "我们赢了！"
    quit
end

label defeat:
    system "你被打败了..."
    quit
end
```
