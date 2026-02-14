@echo off
chcp 65001 >nul
echo ================================
echo    Git 快速上传工具
echo ================================
echo.

:input_files
set /p files="请输入要上传的文件（输入 . 表示所有文件）: "
if "%files%"=="" (
    echo 错误：文件名不能为空！
    goto input_files
)

:input_commit
set /p commit="请输入 commit 消息: "
if "%commit%"=="" (
    echo 错误：commit 消息不能为空！
    goto input_commit
)

echo.
echo ================================
echo 开始执行 Git 操作...
echo ================================
echo.

echo [1/3] 添加文件...
git add %files%
if errorlevel 1 (
    echo 错误：git add 失败！
    pause
    exit /b 1
)
echo ✓ 文件添加成功

echo.
echo [2/3] 提交更改...
git commit -m "%commit%"
if errorlevel 1 (
    echo 错误：git commit 失败！
    pause
    exit /b 1
)
echo ✓ 提交成功

echo.
echo [3/3] 推送到远程仓库...
git push
if errorlevel 1 (
    echo 错误：git push 失败！
    pause
    exit /b 1
)
echo ✓ 推送成功

echo.
echo ================================
echo    所有操作完成！
echo ================================
pause
