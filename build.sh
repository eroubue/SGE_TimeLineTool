#!/bin/bash

echo "技能时间轴查看器 - 打包工具"
echo "================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python"
    exit 1
fi

# 检查是否存在主程序文件
if [ ! -f "timeline_viewer.py" ]; then
    echo "错误：未找到 timeline_viewer.py 文件"
    exit 1
fi

# 检查PyInstaller是否安装
if ! python3 -c "import pyinstaller" &> /dev/null; then
    echo "安装PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "错误：PyInstaller安装失败"
        exit 1
    fi
fi

# 运行打包脚本
echo "开始打包..."
python3 build.py

if [ $? -eq 0 ]; then
    echo "打包成功！"
    echo "文件位置: dist/技能时间轴查看器"

    # 询问是否打开输出目录
    read -p "是否打开输出目录？(y/N): " choice
    case "$choice" in 
        y|Y ) 
            if command -v xdg-open &> /dev/null; then
                xdg-open dist
            elif command -v open &> /dev/null; then
                open dist
            fi
            ;;
        * ) 
            echo "打包完成"
            ;;
    esac
else
    echo "打包失败！"
    exit 1
fi
