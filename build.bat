@echo off
chcp 65001 >nul
echo 技能时间轴查看器 - 打包工具
echo ================================

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 检查是否存在主程序文件
if not exist "timeline_viewer.py" (
    echo 错误：未找到 timeline_viewer.py 文件
    pause
    exit /b 1
)

:: 安装PyInstaller（如果未安装）
echo 检查PyInstaller安装状态...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 错误：PyInstaller安装失败
        pause
        exit /b 1
    )
)

:: 运行打包脚本
echo 开始打包...
python build.py

if errorlevel 1 (
    echo 打包失败！
) else (
    echo 打包成功！
    echo 文件位置: dist\技能时间轴查看器.exe
    if exist "dist\技能时间轴查看器.exe" (
        echo.
        set /p choice=是否打开输出目录？(Y/N): 
        if /i "%choice%"=="Y" (
            explorer dist
        )
    )
)

pause
