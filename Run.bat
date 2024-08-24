@echo off

echo.安装Python依赖

pip install -i https://mirrors.aliyun.com/pypi/simple PyQt5 numpy opencv-python pywin32

if %errorlevel% equ 0 (echo.已完成！) else (echo.可能未成功安装，请自行查明原因。)

pause
