#!/usr/bin/env python3
"""
检查字体仓库更新脚本

该脚本会检查配置文件中所有字体仓库的最新 release，
并与当前已处理的版本进行比较，生成需要更新的字体列表。
"""
import os
import sys
import json
import argparse
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from utils import get_latest_release


def load_config(config_path: str) -> dict:
    """加载字体配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_versions(versions_file: str) -> dict:
    """加载已处理的版本信息"""
    if not os.path.exists(versions_file):
        return {}

    with open(versions_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_versions(versions: dict, versions_file: str):
    """保存版本信息"""
    os.makedirs(os.path.dirname(versions_file), exist_ok=True)
    with open(versions_file, 'w', encoding='utf-8') as f:
        json.dump(versions, f, indent=2, ensure_ascii=False)


def check_updates(config_path: str, versions_file: str, github_token: str = None) -> list:
    """
    检查字体更新

    Returns:
        需要更新的字体列表
    """
    config = load_config(config_path)
    current_versions = load_versions(versions_file)

    updates = []

    for font in config['fonts']:
        font_name = font['name']
        repo = font['repo']

        print(f"检查 {font_name} ({repo})...")

        try:
            release = get_latest_release(repo, github_token)
            latest_version = release['tag_name']

            current_version = current_versions.get(font_name, {}).get('version')

            if current_version != latest_version:
                print(f"  发现新版本: {current_version or '无'} -> {latest_version}")
                updates.append({
                    'name': font_name,
                    'repo': repo,
                    'version': latest_version,
                    'release_url': release['html_url'],
                    'assets': release['assets']
                })
            else:
                print(f"  当前版本已是最新: {latest_version}")

        except Exception as e:
            print(f"  错误: {e}")
            continue

    return updates


def main():
    parser = argparse.ArgumentParser(description='检查字体仓库更新')
    parser.add_argument('--config', default='config/fonts.json',
                        help='字体配置文件路径')
    parser.add_argument('--versions', default='data/versions.json',
                        help='版本信息文件路径')
    parser.add_argument('--output', default='data/updates.json',
                        help='输出更新信息文件路径')
    parser.add_argument('--token', help='GitHub token')

    args = parser.parse_args()

    # 获取环境变量中的 token
    github_token = args.token or os.environ.get('GITHUB_TOKEN')

    # 检查更新
    updates = check_updates(args.config, args.versions, github_token)

    # 保存更新信息
    if updates:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(updates, f, indent=2, ensure_ascii=False)

        print(f"\n发现 {len(updates)} 个字体需要更新")
        print(f"更新信息已保存到: {args.output}")

        # 为 GitHub Actions 设置输出
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"has_updates=true\n")
                f.write(f"update_count={len(updates)}\n")
    else:
        print("\n所有字体都是最新版本")

        # 为 GitHub Actions 设置输出
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"has_updates=false\n")
                f.write(f"update_count=0\n")


if __name__ == '__main__':
    main()
