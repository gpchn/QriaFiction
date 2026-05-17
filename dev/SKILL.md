---
name: "qriafiction-dev"
description: "QriaFiction 互动小说引擎开发技能"
---

# QriaFiction 游戏开发技能

你是一个专业的互动小说游戏开发者，擅长使用 QriaFiction 引擎和 QFScript 语言来制作游戏。

## 创建第一个游戏

1. 创建项目目录结构：

```
my_game/
├── script/
│   └── main.qf
├── assets/
│   ├── bg/
│   └── avatar/
└── project.toml
```

2. 编写 `main.qf`：

```qfscript
define narrator = character(name="", avatar="", color="#888888")
define hero = character(name="主角", avatar="avatar/hero.png", color="#ffffff")

label start:
    bg "school.png"
    narrator "故事开始了..."
    hero "你好，我是主角！"
    wait click
    quit
end
```

3. 配置 `project.toml`：

```toml
[project]
title = "我的第一个游戏"
author = "我"
version = "0.1.0"

[display]
width = 800
height = 600
```

4. 运行：`qf run script/main.qf`

## 语言参考

### 项目组织

- 所有 `.qf` 脚本放在 `script/` 目录
- `main.qf` 为入口，其标签无前缀
- 其他脚本标签以文件名为命名空间（如 `ch1_prologue.qf` 的 `label start:` 变为 `ch1_prologue.start`）
- 引用格式：`jump filename.labelname`

### 角色定义

```qfscript
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
define haru = character(name="春", avatar="avatar/haru.png", color="#ffb6c1")
```

参数：`name`（显示名）、`avatar`（头像路径）、`color`（名称颜色）

### 对话

```qfscript
yuki "你好！"
haru "很高兴见到你！"
"旁白文本..."
narrator "故事就这样开始了..."
```

### 背景

```qfscript
bg "school.png"
bg "classroom.png"
bg none  # 清除背景
```

路径相对于 `assets/bg/` 目录。

### 标签与跳转

```qfscript
label start:
    jump next_scene
    jump scene_a if flag == true
    jump scene_b otherwise
    call daily_event
end

label next_scene:
    return
end
```

### 变量

```qfscript
var name = "勇者"
var relationship = 0
var has_key = false

set name = "樱"
set relationship += 10
input name "请输入你的名字："
```

### 条件与循环

```qfscript
if relationship >= 50:
    yuki "我很喜欢你呢！"
else:
    yuki "我们还不熟..."
end

while i < 3:
    "次数：{i}"
    set i += 1
end
```

### 互动模式 (interact)

玩家输入文本，AI 匹配动作后跳转。

```qfscript
interact:
    "打招呼" -> greet (desc="向她问候、说你好")
    "离开" -> leave (desc="告别并离开")
    fallback "她看着你，等待你说些别的..."
end
```

- `desc` 必需，用于 AI 意图识别
- `condition` 可选
- `fallback` 必需，至少一条

### 固定选项 (options)

显示按钮，玩家点击即跳转。

```qfscript
options:
    "去学校" -> school (desc="前往学校")
    "待在家" -> stay (desc="待在家里", condition=met_yuki)
end
```

### 音频

```qfscript
music "audio/bgm/main.mp3"
music "audio/bgm/tension.mp3" with fade 2.0
sound "audio/sfx/door.wav"
stop music
stop music with fade 3.0
volume music = 0.7
```

### 嵌入 Python

```qfscript
python:
    import random
    qf.set("dice_roll", random.randint(1, 6))
end

yuki "你掷出了 {python: random.randint(1, 6)} 点"
```

Python API：`qf.get(name)`、`qf.set(name, value)`、`qf.jump(label)`、`qf.call(label)`、`qf.show_message(char, text)`、`qf.set_bg(path)`

### 其他

```qfscript
wait 1.5       # 等待秒
wait click     # 等待点击
save           # 存档
load           # 读档
quit           # 退出
```

## 最佳实践

1. 按章节或场景组织脚本文件
2. 使用清晰的命名约定
3. 互动模式的 `desc` 包含多种可能的玩家表达
4. 使用变量跟踪玩家选择，实现多结局
5. 使用 `call`/`return` 创建可重用的子流程

## 示例项目结构

```
my_game/
├── script/
│   ├── main.qf              # 主入口
│   ├── ch1_prologue.qf      # 第一章
│   ├── ch2_school.qf        # 第二章
│   └── events.qf            # 事件
├── assets/
│   ├── bg/                  # 背景图片
│   ├── avatar/              # 角色头像
│   └── audio/
│       ├── bgm/             # 背景音乐
│       └── sfx/             # 音效
└── project.toml
```

## 常见问题

### 多结局

使用变量跟踪选择，条件跳转：

```qfscript
var good_points = 0

label choice1:
    interact:
        "帮助她" -> help (desc="伸出援手")
        "无视她" -> ignore (desc="离开")
        fallback "你需要做出选择..."
    end
end

label help:
    set good_points += 1
    jump continue_story
end

label final_choice:
    if good_points >= 3:
        jump good_end
    else:
        jump normal_end
end
```

### 复杂游戏状态

使用 Python 嵌入处理复杂逻辑：

```qfscript
python:
    def update_game_state():
        hp = qf.get("hp")
        relationship = qf.get("relationship")
        if hp <= 0:
            qf.jump("game_over")
        elif relationship >= 100:
            qf.jump("true_love_end")

    update_game_state()
end
```
