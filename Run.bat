@echo off

echo.��װPython����

pip install -i https://mirrors.aliyun.com/pypi/simple PyQt5 numpy opencv-python pywin32

if %errorlevel% equ 0 (echo.����ɣ�) else (echo.����δ�ɹ���װ�������в���ԭ��)

pause
