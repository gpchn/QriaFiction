# QriaFiction Script Language - VS Code Extension

为 QriaFiction Script（.qf 文件）提供 VS Code 语法高亮支持。

## 功能特性

- 语法高亮（关键字、字符串、数字、注释等）
- 自动缩进（基于 `label:`、`if:`、`while:`、`end` 等关键字）
- 自动闭合引号和括号
- Python 代码块嵌入支持（`python:` 块）
- 字符串内插高亮（`{variable}` 和 `{python:expression}`）

## 安装

### 方法一：开发模式安装

1. 在 VS Code 中打开 `tools/vscode-qfs-syntax` 文件夹
2. 按 `F5` 运行扩展开发主机
3. 在开发主机中打开 `.qf` 文件即可看到语法高亮效果

### 方法二：本地安装

1. 打开 VS Code 命令面板（`Ctrl+Shift+P`）
2. 选择 `Developer: Install Extension from Location...`
3. 选择 `tools/vscode-qfs-syntax` 文件夹

## 语法高亮说明

### 关键字

所有 QFS 语言关键字将被高亮显示，包括：

| 分类 | 关键字 |
|------|--------|
| 控制流 | `label`, `jump`, `call`, `return`, `if`, `elseif`, `else`, `while`, `break`, `continue`, `end` |
| 变量 | `var`, `set`, `input` |
| 交互 | `define`, `character`, `interact`, `fallback`, `options` |
| 场景 | `bg`, `wait`, `click` |
| 音频 | `music`, `sound`, `volume`, `fade`, `stop`, `loop` |
| 系统 | `save`, `load`, `quit`, `python` |
| 修饰符 | `with`, `at`, `otherwise`, `desc`, `condition` |
| 逻辑 | `and`, `or`, `not`, `true`, `false` |
| 特殊 | `none` |

### 内置变量

- `_user_input` - 用户最后输入的内容
- `_matched_action` - 当前匹配到的动作名
- `_label` - 当前标签名
- `_playtime` - 游戏运行时间（秒）

### 字符串

- 双引号字符串 `"..."`
- 单引号字符串 `'...'`
- 支持转义字符：`\n`, `\t`, `\\`, `\"`, `\'`

### 注释

使用 `#` 开头的行注释

### Python 嵌入

```qf
python:
    score = qf.get("score")
    qf.set("level", score // 100)
```

### 字符串内插

```qf
"欢迎来到 {place}！"
"分数: {python: qf.get('score')}"
```

## 开发

如需修改语法高亮规则，编辑 `syntaxes/qfs.tmLanguage.json` 文件。

## License

MIT
