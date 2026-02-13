#!/usr/bin/env python3
"""
字体处理脚本

该脚本负责：
1. 下载指定的字体文件
2. 按照 unicode-range 进行子集化
3. 生成 woff2 格式
4. 生成 CSS 文件
"""
import os
import sys
import json
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict

from fontTools import subset
from fontTools.ttLib import TTFont

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from utils import (
    parse_unicode_range,
    download_file,
    extract_font_from_archive,
    find_asset_by_pattern,
    hash_id,
    generate_css,
    format_file_size
)


class FontProcessor:
    """字体处理器"""

    def __init__(self, config_path: str, ranges_path: str, output_dir: str):
        """
        初始化字体处理器

        Args:
            config_path: 字体配置文件路径
            ranges_path: Unicode 范围配置文件路径
            output_dir: 输出目录
        """
        self.config = self._load_json(config_path)
        self.ranges = self._load_json(ranges_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_json(path: str) -> dict:
        """加载 JSON 配置文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_font_glyphs(self, font_path: str) -> set:
        """
        获取字体中所有的字形对应的 Unicode 码点

        Args:
            font_path: 字体文件路径

        Returns:
            Unicode 码点集合
        """
        font = TTFont(font_path)
        cmap = font.getBestCmap()
        font.close()

        if cmap is None:
            return set()

        return set(cmap.keys())

    def create_subset(self, font_path: str, unicode_ranges: List[tuple],
                     output_path: str) -> bool:
        """
        创建字体子集

        Args:
            font_path: 原始字体文件路径
            unicode_ranges: Unicode 范围列表 [(start, end), ...]
            output_path: 输出文件路径

        Returns:
            是否成功创建子集
        """
        # 获取字体中存在的字形
        available_glyphs = self.get_font_glyphs(font_path)

        # 构建需要的 Unicode 集合
        unicodes = set()
        for start, end in unicode_ranges:
            for code in range(start, end + 1):
                if code in available_glyphs:
                    unicodes.add(code)

        # 如果没有匹配的字符，跳过
        if not unicodes:
            return False

        # 创建子集
        options = subset.Options()
        options.flavor = 'woff2'  # 输出 woff2 格式
        options.layout_features = '*'  # 保留所有布局特性
        options.name_IDs = '*'  # 保留所有名称
        options.name_languages = '*'  # 保留所有语言
        options.glyph_names = True  # 保留字形名称
        options.legacy_kern = True  # 保留传统的字距调整表，
        options.symbol_cmap = True  # 保留符号编码的cmap表
        options.notdef_outline = True  # 保留 .notdef 字形轮廓
        options.recalc_bounds = True  # 重新计算字形的边界框
        options.recalc_timestamp = True  # 重新计算时间戳
        options.canonical_order = True  # 采用规范顺序重新排列字体表

        # 转换为十六进制字符串格式
        # unicodes_hex = [f"U+{code:04X}" for code in sorted(unicodes)]

        # 创建子集工具
        subsetter = subset.Subsetter(options=options)
        # 要用整数，不能用16进制字符串
        subsetter.populate(unicodes=sorted(unicodes))

        # 加载字体
        font = TTFont(font_path)

        # 执行子集化
        subsetter.subset(font)

        # 保存
        font.save(output_path)
        font.close()

        return True

    def process_font_variant(self, font_name: str, variant_config: dict,
                            font_path: str) -> Dict[str, any]:
        """
        处理单个字体变体

        Args:
            font_name: 字体名称
            variant_config: 变体配置
            font_path: 字体文件路径

        Returns:
            处理结果统计
        """
        variant = variant_config['variant']
        weight = variant_config['weight']

        print(f"\n处理 {font_name}-{variant} (weight: {weight})...")

        # 创建输出目录
        font_output_dir = self.output_dir / font_name
        font_output_dir.mkdir(parents=True, exist_ok=True)

        # 处理每个 Unicode 范围
        stats = {
            'total_ranges': len(self.ranges),
            'created_subsets': 0,
            'skipped_ranges': 0,
            'total_size': 0,
            'subsets': []
        }

        # for range_info in self.ranges['ranges']:
        for range_id, unicode_range in self.ranges.items():
            print(f"  处理范围 {range_id}")

            # 解析 Unicode 范围
            parsed_ranges = parse_unicode_range(unicode_range)

            # 输出文件名
            hash_str = hash_id(f"{font_name}-{variant}-{range_id}")
            output_filename = f"{font_name}-{variant}-{hash_str}.woff2"
            output_path = font_output_dir / output_filename

            # 创建子集
            try:
                success = self.create_subset(font_path, parsed_ranges, str(output_path))

                if success:
                    file_size = output_path.stat().st_size
                    stats['created_subsets'] += 1
                    stats['total_size'] += file_size
                    stats['subsets'].append({
                        'id': range_id,
                        'unicode_range': unicode_range,
                        'filename': output_filename,
                        'size': file_size
                    })
                    print(f"    ✓ 创建成功: {format_file_size(file_size)}")
                else:
                    stats['skipped_ranges'] += 1
                    print(f"    - 跳过: 无匹配字符")
            except Exception as e:
                stats['skipped_ranges'] += 1
                print(f"    ✗ 错误: {e}")

        # 生成 CSS 文件
        css_content, css_min_content = generate_css(
            font_name=font_name,
            variant=variant,
            weight=weight,
            subsets=stats['subsets'],
            cdn_base_url=f"https://cdn.jsdelivr.net/gh/{{REPO_NAME}}@latest/fonts"
        )

        css_path = font_output_dir / f"{font_name}-{variant}.css"
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)

        css_min_path = font_output_dir / f"{font_name}-{variant}.min.css"
        with open(css_min_path, 'w', encoding='utf-8') as f:
            f.write(css_min_content)

        print(f"\n  总结:")
        print(f"    - 创建子集: {stats['created_subsets']}")
        print(f"    - 跳过范围: {stats['skipped_ranges']}")
        print(f"    - 总大小: {format_file_size(stats['total_size'])}")
        print(f"    - CSS 文件: {css_path.name}")
        print(f"    - CSS 压缩文件: {css_min_path.name}")

        return stats

    def process_update(self, update_info: dict):
        """
        处理单个字体更新

        Args:
            update_info: 更新信息字典
        """
        font_name = update_info['name']
        version = update_info['version']
        assets = update_info['assets']

        print(f"\n{'='*60}")
        print(f"处理字体: {font_name} ({version})")
        print(f"{'='*60}")

        # 获取字体配置
        font_config = None
        for font in self.config['fonts']:
            if font['name'] == font_name:
                font_config = font
                break

        if not font_config:
            print(f"错误: 未找到字体 {font_name} 的配置")
            return

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 下载缓存：避免重复下载同一个文件
            # {download_url: local_path}
            download_cache = {}

            # 提取缓存：避免重复提取同一个 ZIP 中的字体
            # {(archive_path, pattern): extracted_path}
            extraction_cache = {}

            # 处理每个字体文件
            for file_config in font_config['files']:
                # pattern = file_config['pattern']
                asset_pattern = file_config.get('asset_pattern')
                font_pattern = file_config.get('font_pattern')

                if not asset_pattern:
                    print(f"错误: 缺少 asset_pattern 配置")
                    continue

                 # 在 assets 中查找文件（匹配 asset 名称）
                asset = find_asset_by_pattern(assets, asset_pattern)

                if not asset:
                    print(f"警告: 未找到匹配 '{asset_pattern}' 的 asset")
                    continue

                # 下载文件
                asset_filename = asset['name']
                download_url = asset['browser_download_url']
                downloaded_path = temp_path / asset_filename

                # 检查是否已经下载过
                if download_url in download_cache:
                    print(f"\n使用已下载的文件: {asset_filename}")
                    downloaded_path = download_cache[download_url]
                else:
                    # 检查文件是否已存在（可能是之前的变体下载的）
                    if downloaded_path.exists():
                        print(f"\n文件已存在，跳过下载: {asset_filename}")
                    else:
                        print(f"\n下载 asset: {asset_filename}")
                        print(f"URL: {download_url}")
                        try:
                            download_file(download_url, str(downloaded_path))
                        except Exception as e:
                            print(f"下载失败: {e}")
                            continue
                    # 添加到缓存
                    download_cache[download_url] = downloaded_path

                try:
                    # 判断文件类型并处理
                    font_path = None

                    if asset_filename.lower().endswith('.zip'):
                        # 如果是 ZIP 文件，解压并查找字体
                        print(f"  检测到 ZIP 压缩包，正在解压...")

                        # 如果有 font_pattern，使用它；否则尝试猜测
                        search_pattern = font_pattern if font_pattern else f".*{font_name}.*"

                        font_path = extract_font_from_archive(
                            str(downloaded_path),
                            str(temp_path),
                            search_pattern,
                            extraction_cache
                        )

                        if not font_path:
                            print(f"  错误: ZIP 中未找到匹配 '{search_pattern}' 的字体文件")
                            continue

                    elif asset_filename.lower().endswith(('.ttf', '.otf')):
                        # 直接是字体文件
                        font_path = str(downloaded_path)
                        print(f"  检测到字体文件: {asset_filename}")

                    else:
                        print(f"  警告: 不支持的文件格式: {asset_filename}")
                        continue

                    # 处理字体
                    print(f"  使用字体文件: {os.path.basename(font_path)}")
                    self.process_font_variant(
                        font_name=font_name,
                        variant_config=file_config,
                        font_path=font_path
                    )

                except Exception as e:
                    print(f"错误: {e}")
                    import traceback
                    traceback.print_exc()
                    continue


def main():
    parser = argparse.ArgumentParser(description='处理字体文件')
    parser.add_argument('--config', default='config/fonts.json',
                        help='字体配置文件路径')
    parser.add_argument('--ranges', default='config/unicode_ranges.json',
                        help='Unicode 范围配置文件路径')
    parser.add_argument('--updates', default='data/updates.json',
                        help='更新信息文件路径')
    parser.add_argument('--output', default='fonts',
                        help='输出目录')
    parser.add_argument('--versions', default='data/versions.json',
                        help='版本信息文件路径')
    parser.add_argument('--threads', type=int, default=2,
                        help='并行处理字体的线程数（默认: 2）')

    args = parser.parse_args()

    # 加载更新信息
    if not os.path.exists(args.updates):
        print(f"错误: 更新信息文件不存在: {args.updates}")
        sys.exit(1)

    with open(args.updates, 'r', encoding='utf-8') as f:
        updates = json.load(f)

    if not updates:
        print("没有需要处理的更新")
        sys.exit(0)

    # 创建处理器
    processor = FontProcessor(args.config, args.ranges, args.output)

    # 串行处理每个更新
    # for update in updates:
    #     processor.process_update(update)

    # 并行处理多个字体更新
    if len(updates) > 1 and args.threads > 1:
        print(f"\n使用 {min(args.threads, len(updates))} 个线程并行处理 {len(updates)} 个字体...")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        # 使用指定的线程数
        font_workers = min(args.threads, len(updates))

        with ThreadPoolExecutor(max_workers=font_workers) as executor:
            # 提交所有任务
            future_to_update = {
                executor.submit(processor.process_update, update): update
                for update in updates
            }

            # 收集结果
            completed = 0
            failed = 0
            for future in as_completed(future_to_update):
                update = future_to_update[future]
                completed += 1
                try:
                    future.result()
                    print(f"\n[{completed}/{len(updates)}] ✓ {update['name']} 处理完成")
                except Exception as e:
                    failed += 1
                    print(f"\n[{completed}/{len(updates)}] ✗ {update['name']} 处理失败: {e}")
                    import traceback
                    traceback.print_exc()

            if failed > 0:
                print(f"\n警告: {failed} 个字体处理失败")
    else:
        # 单个字体或单线程，串行处理
        for i, update in enumerate(updates, 1):
            try:
                print(f"\n[{i}/{len(updates)}] 处理 {update['name']}...")
                processor.process_update(update)
                print(f"✓ {update['name']} 处理完成")
            except Exception as e:
                print(f"✗ {update['name']} 处理失败: {e}")
                import traceback
                traceback.print_exc()

    # 更新版本信息
    versions = {}
    if os.path.exists(args.versions):
        with open(args.versions, 'r', encoding='utf-8') as f:
            versions = json.load(f)

    for update in updates:
        versions[update['name']] = {
            'version': update['version'],
            'updated_at': update.get('published_at', '')
        }

    os.makedirs(os.path.dirname(args.versions), exist_ok=True)
    with open(args.versions, 'w', encoding='utf-8') as f:
        json.dump(versions, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("处理完成!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
