# QriaFiction 游戏开发新手指引

5 分钟上手，从零开始制作你的第一个互动小说游戏。

---

## 第一步：准备环境

1. 安装 Python 3.12+（[python.org](https://python.org)）
2. 安装 QriaFiction 依赖：

```bash
uv sync
# 或
pip install -e .
```

3. 启动应用，确认界面正常显示：

```bash
uv run qriafiction
```

---

## 第二步：创建游戏项目

在你的工作目录下创建一个游戏目录：

```bash
mkdir my_first_game
cd my_first_game
mkdir -p script assets/bg assets/avatar
```

创建 `project.toml`：

```toml
[project]
title = "我的第一个游戏"
author = "你的名字"
version = "0.1.0"

[display]
width = 800
height = 600
```

---

## 第三步：编写第一个脚本

创建 `script/main.qf`：

```qfscript
# 定义角色
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
define narrator = character(name="", avatar="", color="#888888")

# 游戏入口
label start:
    narrator "欢迎来到这个世界！"
    bg "school.png"
    yuki "你好！我是雪。"
    yuki "很高兴认识你！"
    wait click
    quit
end
```

---

## 第四步：运行游戏

1. 在 QriaFiction 应用界面中点击"导入项目"
2. 选择你的 `my_first_game` 目录
3. 点击"启动游戏"

现在你应该能看到游戏的运行效果。

---

## 第五步：添加互动选择

修改 `main.qf`，添加玩家选择：

```qfscript
define yuki = character(name="雪", avatar="avatar/yuki.png", color="#87ceeb")
define narrator = character(name="", avatar="", color="#888888")

var relationship = 0

label start:
    narrator "放学后，雪叫住了你。"
    bg "classroom.png"
    
    yuki "放学后有空吗？要不要一起走？"
    
    options:
        "一起走吧" -> walk_together (desc="同意和她一起走")
        "我还有点事" -> stay_behind (desc="委婉拒绝")
    end
end

label walk_together:
    set relationship += 10
    bg "street.png"
    yuki "太好了！我们走吧~"
    jump ending
end

label stay_behind:
    bg "classroom.png"
    yuki "好吧，那我先走了..."
    jump ending
end

label ending:
    wait click
    narrator "故事结束了。"
    quit
end
```

---

## 第六步：添加 AI 互动模式

如果你想让玩家用自然语言与游戏互动，使用 `interact`：

```qfscript
label school_gate:
    bg "school_gate.png"
    yuki "早上好！今天想去哪里玩？"
    
    interact:
        "去游乐园" -> park (desc="去游乐园、去玩、去游乐场")
        "去图书馆" -> library (desc="去图书馆看书、去阅读、去借书")
        "回家" -> go_home (desc="回家、回宿舍、离开学校")
        fallback "雪歪了歪头，似乎没听懂。"
    end
end
```

**关键要点：**

- `desc` 要包含多种可能的玩家表达方式
- `fallback` 至少写 1-2 条，提供有意义的反馈

---

## 进阶：多文件组织

当脚本变长时，拆分成多个文件：

```
my_game/
├── script/
│   ├── main.qf              # 入口和第一章
│   ├── ch2_school.qf        # 第二章
│   └── events.qf            # 日常事件
```

`main.qf`：
```qfscript
label start:
    yuki "欢迎来到第一章..."
    jump ch2_school.begin    # 跳转到 ch2_school.qf
end
```

`ch2_school.qf`：
```qfscript
label begin:                 # 在 main.qf 中引用为 ch2_school.begin
    yuki "这是第二章..."
    call events.greeting     # 调用 events.qf 的标签
end
```

`events.qf`：
```qfscript
label greeting:
    yuki "早上好！"
    return                   # 返回调用位置
end
```

**规则：**

- `main.qf` 的标签不加前缀（如 `jump start`）
- 其他文件的标签以文件名作为前缀（如 `jump ch2_school.begin`）

---

## 进阶：添加音频

```qfscript
# 播放背景音乐
music "audio/bgm/main.mp3"

# 淡入播放
music "audio/bgm/tension.mp3" with fade 2.0

# 播放音效
sound "audio/sfx/door.wav"

# 停止音乐（淡出）
stop music with fade 3.0
```

音频文件放在项目 `assets/audio/` 目录下。

---

## 进阶：使用变量实现多结局

```qfscript
var good_points = 0

label choice1:
    options:
        "帮助她" -> help (desc="伸出援手、帮忙")
        "无视她" -> ignore (desc="离开、不管她")
    end
end

label help:
    set good_points += 1
    yuki "谢谢你！"
    jump continue
end

label ignore:
    narrator "你转身离开了..."
    jump continue
end

label final_choice:
    if good_points >= 3:
        jump good_end
    else:
        jump normal_end
    end
end

label good_end:
    yuki "我们永远是最好的朋友！"
    wait click
    quit
end

label normal_end:
    narrator "你们渐渐疏远了..."
    wait click
    quit
end
```

---

## 常见问题

### Q：图片放在哪里？

背景图片放在 `assets/bg/`，角色头像放在 `assets/avatar/`。`bg` 语句的路径相对于 `assets/bg/` 目录。

### Q：`interact` 和 `options` 有什么区别？

- `interact`：玩家输入文本，AI 匹配意图。适合开放式互动。
- `options`：显示按钮，玩家点击选择。适合固定分支。

### Q：如何存档？

使用 `save` 和 `load` 语句。玩家也可以在游戏界面中使用存档管理。

### Q：如何调试？

使用 `qf check script/main.qf` 检查语法，使用 `qf dump-ast script/main.qf` 查看 AST。

---

## 下一步

- 查看完整的语言规范：[language_spec.md](language_spec.md)
- 使用 AI 辅助开发：将 [prompt.md](prompt.md) 粘贴到 ChatGPT
- 查看内置的 `demo` 项目学习完整示例
