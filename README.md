# Font Subset

<p align="center">
  <img src="https://img.shields.io/github/actions/workflow/status/shingchi/font-subset/check-updates.yml?label=Check%20Updates&style=flat-square" alt="Check Updates">
  <img src="https://img.shields.io/github/actions/workflow/status/shingchi/font-subset/process-fonts.yml?label=Process%20Fonts&style=flat-square" alt="Process Fonts">
  <img src="https://img.shields.io/github/license/shingchi/font-subset?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/repo-size/shingchi/font-subset?style=flat-square" alt="Repo Size">
</p>

自动跟踪中文字体更新，按照 Google Noto Serif SC 切片范围进行子集化处理。

## 功能特性

- 🔄 自动跟踪字体仓库的 releases 更新
- ✂️ 按照 Google Noto Serif SC 的 unicode-range 进行字体切片（可添加自定义范围配置）
- 📦 生成 woff2 格式的子集字体
- 🚀 自动发布到 NPM 仓库

## 工作流程

1. **自动检测更新**：每天检查字体仓库是否有新的 releases（使用轻量级依赖）
2. **下载字体文件**：从 releases 下载原始字体文件
3. **子集化处理**：
   - 按照配置的 unicode-range 切片
   - 跳过字体中不存在的 unicode 字符
   - 生成 woff2 格式
4. **自动发布**：将处理后的字体打包发布到 NPM 仓库

## 项目结构

```
font-subset/
├── .github/
│   └── workflows/
│       ├── check-updates.yml      # 检查更新工作流
│       └── process-fonts.yml      # 字体处理工作流
├── data/
│   └── versions.json  # 版本记录文件
├── config/
│   ├── fonts.json                 # 字体仓库配置
│   └── unicode_ranges.json        # Unicode 切片范围
├── scripts/
│   ├── check_updates.py           # 检查更新脚本
│   ├── process_fonts.py           # 字体处理脚本
│   └── utils.py                   # 工具函数
├── package.json                   # NPM 包配置
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
      "description": "霞鹜文楷 GB",
      "files": [
        {
          "asset_pattern": "LXGWWenKaiGB-Regular.ttf",
          "font_pattern": null,
          "variant": "Regular",
          "weight": 400
        }
      ]
    }
  ]
}
```

### unicode_ranges.json

定义字体切片的 unicode 范围（基于 Google Noto Serif SC）。

## 许可证

本仓库采用 [MIT License](LICENSE) 许可协议。所使用到的字体的许可证请参考字体仓库的 LICENSE 文件。
```
