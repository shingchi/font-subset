# Font Subset

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/font-subsetter-cdn/check-updates.yml?label=Check%20Updates&style=flat-square" alt="Check Updates">
  <img src="https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/font-subsetter-cdn/process-fonts.yml?label=Process%20Fonts&style=flat-square" alt="Process Fonts">
  <img src="https://img.shields.io/github/license/YOUR_USERNAME/font-subsetter-cdn?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/repo-size/YOUR_USERNAME/font-subsetter-cdn?style=flat-square" alt="Repo Size">
</p>

自动跟踪中文字体更新，按照 Google Noto Serif SC 切片范围进行子集化处理，并通过 jsDelivr CDN 提供服务。

> ⚠️ **注意**: 请将所有 `YOUR_USERNAME` 替换为你的 GitHub 用户名

## 功能特性

- 🔄 自动跟踪字体仓库的 releases 更新
- ✂️ 按照 Google Noto Serif SC 的 unicode-range 进行字体切片
- 📦 生成 woff2 格式的子集字体
- 🚀 自动发布到 GitHub Releases，支持 jsDelivr CDN 加速
- 🎨 支持多个主流中文字体

## 快速开始

### 1. Fork 本仓库

点击右上角的 "Fork" 按钮，将仓库 Fork 到你的账号下。

### 2. 启用 GitHub Actions

1. 进入你 Fork 的仓库
2. 点击 "Actions" 标签
3. 点击 "I understand my workflows, go ahead and enable them"

### 3. 运行工作流

进入 "Actions" 标签，选择 "Check Font Updates"，点击 "Run workflow" 触发首次运行。

### 4. 使用字体

```bash
# 安装依赖
pip install -r requirements.txt

# 运行字体处理脚本
python scripts/process_fonts.py
```

工作流完成后，通过 jsDelivr CDN 引用处理后的字体：

```html
<!-- 方式 1: 直接引用完整 CSS -->
<link rel="stylesheet" 
      href="https://cdn.jsdelivr.net/gh/YOUR_USERNAME/font-subsetter-cdn@latest/fonts/LxgwWenkaiGB/LxgwWenkaiGB-Regular.css">
```

```css
/* 方式 2: 手动引用单个切片 */
@font-face {
  font-family: 'LxgwWenKai';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('https://cdn.jsdelivr.net/gh/YOUR_USERNAME/font-subsetter-cdn@latest/fonts/LxgwWenkaiGB/LxgwWenkaiGB-Regular-0.woff2') format('woff2');
  unicode-range: U+0-FF;
}

/* 更多切片... */
```

## 工作流程

1. **自动检测更新**：每天检查字体仓库是否有新的 releases（使用轻量级依赖）
2. **下载字体文件**：从 releases 下载原始字体文件
3. **子集化处理**：
   - 按照 Noto Serif SC 的 unicode-range 切片
   - 跳过字体中不存在的 unicode 字符
   - 生成 woff2 格式
4. **发布 Release**：将处理后的字体打包发布到 GitHub Releases
5. **CDN 加速**：通过 jsDelivr 自动提供 CDN 服务

**性能优化**：项目使用分离的依赖文件，检查更新仅需 ~5 秒，处理字体时才安装完整依赖

## 项目结构

```
font-subset/
├── .github/
│   └── workflows/
│       ├── check-updates.yml      # 检查更新工作流
│       └── process-fonts.yml      # 字体处理工作流
├── config/
│   ├── fonts.json                 # 字体仓库配置
│   └── unicode_ranges.json        # Unicode 切片范围
├── scripts/
│   ├── check_updates.py           # 检查更新脚本
│   ├── process_fonts.py           # 字体处理脚本
│   └── utils.py                   # 工具函数
├── fonts/                         # 输出目录
├── requirements.txt               # Python 依赖
└── README.md
```

## 配置说明

### fonts.json

配置需要跟踪的字体仓库：

```json
{
  "fonts": [
    {
      "name": "LxgwWenkaiGB",
      "repo": "lxgw/LxgwWenkaiGB",
      "files": ["LXGWWenKaiGB-Regular.ttf"],
      "variants": ["Regular"]
    }
  ]
}
```

### unicode_ranges.json

定义字体切片的 unicode 范围（基于 Google Noto Serif SC）。

## 许可证

MIT License
