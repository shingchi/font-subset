#!/usr/bin/env python3
"""
快速测试脚本

用于验证项目配置和脚本是否正常工作
"""
import sys
import json
from pathlib import Path


def test_config_files():
    """测试配置文件"""
    print("测试配置文件...")

    config_files = [
        'config/fonts.json',
        'config/unicode_ranges.json'
    ]

    all_ok = True

    for config_file in config_files:
        path = Path(config_file)
        if not path.exists():
            print(f"  ✗ {config_file} 不存在")
            all_ok = False
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  ✓ {config_file} 格式正确")
        except Exception as e:
            print(f"  ✗ {config_file} 解析失败: {e}")
            all_ok = False

    return all_ok


def test_unicode_ranges():
    """测试 Unicode 范围解析"""
    print("\n测试 Unicode 范围解析...")

    sys.path.insert(0, 'scripts')
    from utils import parse_unicode_range

    test_cases = [
        ("U+0-FF", [(0, 255)]),
        ("U+4E00-9FFF", [(0x4E00, 0x9FFF)]),
        ("U+3000-303F", [(0x3000, 0x303F)]),
    ]

    all_ok = True

    for range_str, expected in test_cases:
        result = parse_unicode_range(range_str)
        print(result)
        if result == expected:
            print(f"  ✓ {range_str} → {result}")
        else:
            print(f"  ✗ {range_str} → {result} (期望: {expected})")
            all_ok = False

    return all_ok


def test_font_config():
    """测试字体配置"""
    print("\n测试字体配置...")

    with open('config/fonts.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    all_ok = True

    for font in config['fonts']:
        name = font.get('name')
        repo = font.get('repo')
        files = font.get('files', [])

        if not name or not repo:
            print(f"  ✗ 字体配置缺少必需字段")
            all_ok = False
            continue

        if not files:
            print(f"  ✗ {name} 没有配置文件")
            all_ok = False
            continue

        print(f"  ✓ {name} ({repo}): {len(files)} 个变体")

    return all_ok


def test_unicode_range_config():
    """测试 Unicode 范围配置"""
    print("\n测试 Unicode 范围配置...")

    with open('config/unicode_ranges.json', 'r', encoding='utf-8') as f:
        ranges = json.load(f)

    if not ranges:
        print("  ✗ 没有配置 Unicode 范围")
        return False

    print(f"  ✓ 配置了 {len(ranges)} 个 Unicode 范围")

    return True


def test_directory_structure():
    """测试目录结构"""
    print("\n测试目录结构...")

    required_dirs = [
        'config',
        'scripts',
        'data',
        '.github/workflows'
    ]

    all_ok = True

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ 不存在")
            all_ok = False

    return all_ok


def main():
    print("=" * 60)
    print("Font Subsetter CDN - 快速测试")
    print("=" * 60)

    tests = [
        ("目录结构", test_directory_structure),
        ("配置文件", test_config_files),
        ("字体配置", test_font_config),
        ("Unicode 范围配置", test_unicode_range_config),
        ("Unicode 范围解析", test_unicode_ranges),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n测试 {test_name} 时出错: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
