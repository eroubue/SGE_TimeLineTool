#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能时间轴查看器 - 打包脚本
使用PyInstaller将程序打包为exe文件
"""

import os
import sys
import shutil
from pathlib import Path

def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)

    import glob
    for pattern in files_to_clean:
        for file_path in glob.glob(pattern):
            print(f"删除文件: {file_path}")
            os.remove(file_path)

def build_exe():
    """构建exe文件"""
    print("开始构建exe文件...")

    # PyInstaller命令参数
    cmd_args = [
        'pyinstaller',
        '--onefile',                    # 打包成单个exe文件
        '--windowed',                   # 不显示控制台窗口
        '--name=技能时间轴查看器',        # 设置exe文件名
        '--distpath=dist',              # 输出目录
        '--workpath=build',             # 工作目录
        '--clean',                      # 清理临时文件
        '--noupx',                      # 不使用UPX压缩
        '--add-data=README.md;.',       # 添加README文件
        'timeline_viewer.py'            # 主程序文件
    ]

    # 如果有图标文件，添加图标参数
    icon_files = ['icon.ico', 'app.ico', 'timeline.ico']
    for icon_file in icon_files:
        if os.path.exists(icon_file):
            cmd_args.insert(-1, f'--icon={icon_file}')
            print(f"使用图标文件: {icon_file}")
            break

    # 执行打包命令
    import subprocess
    result = subprocess.run(cmd_args, capture_output=True, text=True, encoding='utf-8')

    if result.returncode == 0:
        print("✓ 打包成功！")
        print(f"exe文件位置: {os.path.abspath('dist/技能时间轴查看器.exe')}")

        # 复制示例文件到dist目录
        if os.path.exists('M1S.txt'):
            shutil.copy2('M1S.txt', 'dist/')
            print("✓ 已复制示例文件 M1S.txt")

        return True
    else:
        print("✗ 打包失败！")
        print("错误信息:")
        print(result.stderr)
        return False

def check_dependencies():
    """检查打包依赖"""
    required_packages = ['pyinstaller']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请先安装依赖:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True

def main():
    """主函数"""
    print("=" * 50)
    print("技能时间轴查看器 - 打包工具")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 清理旧的构建文件
    clean_build()

    # 开始打包
    if build_exe():
        print("\n" + "=" * 50)
        print("打包完成！")
        print("exe文件位于 dist 目录中")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("打包失败！请检查错误信息")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
