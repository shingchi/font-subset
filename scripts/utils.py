"""
工具函数模块
"""
import os
import re
import requests
from typing import List, Tuple, Union
from hashlib import sha256


def parse_unicode_range(range_str: str) -> List[Tuple[int, int]]:
    """
    解析 unicode-range 字符串，返回 (start, end) 元组列表

    例如:
    - "U+0-FF" -> [(0, 255)]
    - "U+4E00-9FFF" -> [(0x4E00, 0x9FFF)]
    - "U+20000-2A6DF" -> [(0x20000, 0x2A6DF)]
    """
    ranges = []

    # 移除 "U+" 前缀
    range_str = range_str.replace('U+', '').strip()

    # 支持逗号分隔的多个范围
    parts = [p.strip() for p in range_str.split(',')]

    for part in parts:
        if '-' in part:
            # 范围格式: "4E00-9FFF"
            start_hex, end_hex = part.split('-')
            start = int(start_hex, 16)
            end = int(end_hex, 16)
            ranges.append((start, end))
        else:
            # 单个字符: "4E00"
            code = int(part, 16)
            ranges.append((code, code))

    return ranges


def get_latest_release(repo: str, github_token: str = None) -> dict:
    """
    获取 GitHub 仓库的最新 release 信息

    Args:
        repo: 仓库名称，格式为 "owner/repo"
        github_token: GitHub token（可选，用于提高 API 限制）

    Returns:
        release 信息字典，包含 tag_name, assets 等
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"

    headers = {
        "Accept": "application/vnd.github.v3+json"
    }

    if github_token:
        headers["Authorization"] = f"token {github_token}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def download_file(url: str, output_path: str, filename: str = None, chunk_size: int = 8192):
    """
    下载文件

    Args:
        url: 文件 URL
        output_path: 输出路径
        filename: 文件名（可选，用于显示进度）
        chunk_size: 下载块大小
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))

    with open(output_path, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"\r{filename} 下载进度: {progress:.1f}%", end='')

    print()  # 换行


def extract_font_from_archive(archive_path: str, output_dir: str, pattern: str,
                              extraction_cache: dict = None) -> str:
    """
    从压缩包中提取字体文件

    Args:
        archive_path: 压缩包路径
        output_dir: 输出目录
        pattern: 字体文件名模式（正则表达式）
        extraction_cache: 提取缓存字典 {(archive_path, pattern): extracted_path}

    Returns:
        提取的字体文件路径，如果没找到返回 None
    """
    import zipfile
    import re

    # 检查缓存
    cache_key = (archive_path, pattern)
    if extraction_cache is not None and cache_key in extraction_cache:
        cached_path = extraction_cache[cache_key]
        if os.path.exists(cached_path):
            print(f"  使用已提取的字体: {os.path.basename(cached_path)}")
            return cached_path

    regex = re.compile(pattern, re.IGNORECASE)

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        # 查找匹配的字体文件
        for file_name in zip_ref.namelist():
            if regex.search(file_name) and file_name.lower().endswith(('.ttf', '.otf')):
                # 提取文件
                zip_ref.extract(file_name, output_dir)
                extracted_path = os.path.join(output_dir, file_name)
                print(f"  从压缩包提取: {file_name}")

                # 添加到缓存
                if extraction_cache is not None:
                    extraction_cache[cache_key] = extracted_path

                return extracted_path

    return None


def find_asset_by_pattern(assets: list, pattern: str) -> dict:
    """
    根据文件名模式在 release assets 中查找文件

    Args:
        assets: release assets 列表
        pattern: 文件名模式（支持正则表达式）

    Returns:
        匹配的 asset 字典，如果没找到返回 None
    """
    regex = re.compile(pattern)

    for asset in assets:
        if regex.search(asset['name']):
            return asset

    return None


def generate_css(font_name: str, variant: str, weight: int,
                 subsets: List[dict], cdn_base_url: str) -> Tuple[str, str]:
    """
    生成字体 CSS

    Args:
        font_name: 字体名称
        variant: 字体变体
        weight: 字重
        subsets: 子集列表，包含 id 和 unicode_range
        cdn_base_url: CDN 基础 URL

    Returns:
        包含普通 CSS 和压缩 CSS 的元组 (css_content, css_min_content)
    """
    css_parts = []
    css_min_parts = []

    for subset in subsets:
        subset_id = subset['id']
        unicode_range = subset['unicode_range']
        filename = subset['filename']

        css = f"""/* {subset_id} */
@font-face {{
  font-family: '{font_name}';
  font-style: normal;
  font-weight: {weight};
  font-display: swap;
  src: url({filename}) format('woff2');
  unicode-range: {unicode_range};
}}"""
        css_parts.append(css)

        css_min = f"""@font-face{{font-family:'{font_name}';font-style:normal;font-weight:{weight};font-display:swap;src:url({filename}) format('woff2');unicode-range:{unicode_range}}}"""
        css_min_parts.append(css_min)

    return ('\n'.join(css_parts), ''.join(css_min_parts))


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的字符串，如 "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def hash_id(id_value: Union[str, int], length: int = 32, salt: str = 'font-subset') -> str:
    """
    生成哈希 ID

    Args:
        id_value: 输入值，支持字符串和整数
        length: 哈希长度（默认 32 字符）
        salt: 盐值（默认 'font-subset'）

    Returns:
        哈希字符串
    """
    data = f"{id_value}{salt}".encode('utf-8')
    hash_hex = sha256(data).hexdigest()
    return hash_hex[:length]
