#!/usr/bin/env python3
"""
生成字体列表脚本

扫描字体输出目录，生成包含所有字体信息的 index.json 文件
"""
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict


def scan_fonts_directory(fonts_dir: str) -> List[Dict]:
    """
    扫描字体目录，生成字体列表

    Args:
        fonts_dir: 字体目录路径

    Returns:
        字体列表
    """
    fonts_path = Path(fonts_dir)
    fonts = []

    # 遍历每个字体目录
    for font_dir in sorted(fonts_path.iterdir()):
        if not font_dir.is_dir():
            continue

        font_name = font_dir.name

        # 查找 CSS 文件
        css_files = list(font_dir.glob('*.css'))

        # 查找 woff2 文件
        woff2_files = list(font_dir.glob('*.woff2'))

        if not woff2_files:
            continue

        # 按变体分组
        variants = {}
        for woff2_file in woff2_files:
            # 文件名格式: FontName-Variant-ID.woff2
            parts = woff2_file.stem.split('-')
            if len(parts) >= 3:
                variant = parts[-2]
                subset_id = parts[-1]

                if variant not in variants:
                    variants[variant] = {
                        'variant': variant,
                        'css_file': None,
                        'subsets': []
                    }

                variants[variant]['subsets'].append({
                    # 'id': int(subset_id),
                    'id': subset_id,
                    'filename': woff2_file.name,
                    'size': woff2_file.stat().st_size
                })

        # 匹配 CSS 文件
        for variant_info in variants.values():
            variant = variant_info['variant']
            css_pattern = f"{font_name}-{variant}.css"

            for css_file in css_files:
                if css_file.name == css_pattern:
                    variant_info['css_file'] = css_file.name
                    break

        # 计算总大小
        total_size = sum(
            subset['size']
            for variant_info in variants.values()
            for subset in variant_info['subsets']
        )

        fonts.append({
            'name': font_name,
            'variants': list(variants.values()),
            'total_size': total_size,
            'total_files': len(woff2_files)
        })

    return fonts


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def main():
    parser = argparse.ArgumentParser(description='生成字体列表')
    parser.add_argument('--fonts-dir', default='fonts',
                        help='字体目录路径')
    parser.add_argument('--output', default='fonts/index.json',
                        help='输出文件路径')

    args = parser.parse_args()

    # 扫描字体目录
    fonts = scan_fonts_directory(args.fonts_dir)

    # 生成索引
    index = {
        'generated_at': None,
        'total_fonts': len(fonts),
        'fonts': fonts
    }

    # 添加时间戳
    from datetime import datetime
    index['generated_at'] = datetime.utcnow().isoformat() + 'Z'

    # 保存
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # 打印统计
    print(f"\n字体列表已生成: {args.output}")
    print(f"\n统计:")
    print(f"  - 字体数量: {len(fonts)}")

    total_size = sum(font['total_size'] for font in fonts)
    total_files = sum(font['total_files'] for font in fonts)

    print(f"  - 文件总数: {total_files}")
    print(f"  - 总大小: {format_size(total_size)}")

    print(f"\n字体列表:")
    for font in fonts:
        print(f"  - {font['name']}: {font['total_files']} 文件, "
              f"{format_size(font['total_size'])}")


if __name__ == '__main__':
    main()
