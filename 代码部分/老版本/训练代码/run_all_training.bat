@echo off
setlocal
echo ============================================================
echo Starting 6 training jobs sequentially
echo ============================================================
echo.

rem 项目目录取自本脚本所在位置，不再硬编码机器路径（修复 ALN-006）。
set "PROJECT=%~dp0"
if "%PROJECT:~-1%"=="\" set "PROJECT=%PROJECT:~0,-1%"
cd /d "%PROJECT%"

rem 解释器可用环境变量覆盖；项目环境为 conda env edmddl2（见 DEC-009）。
if not defined PYTHON_EXE set "PYTHON_EXE=python"

echo Job 1/6: Platform 2 - PatchTST-Koopman (EDMD, 500 epochs)
echo ============================================================
%PYTHON_EXE% scripts\train_patchtst.py --config configs\platform2.yaml > "results\train_p2_patchtst.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 2/6: Platform 2 - MLP-Koopman (300 epochs)
echo ============================================================
%PYTHON_EXE% scripts\train_mlp_koopman.py --config configs\platform2.yaml > "results\train_p2_mlp.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 3/6: Platform 2 - Traditional EDMD
echo ============================================================
%PYTHON_EXE% scripts\train_traditional_edmd.py --config configs\platform2.yaml > "results\train_p2_traditional.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 4/6: Platform 1 - PatchTST-Koopman (EDMD, 500 epochs)
echo ============================================================
%PYTHON_EXE% scripts\train_patchtst.py --config configs\platform1.yaml > "results\train_p1_patchtst.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 5/6: Platform 1 - MLP-Koopman (300 epochs)
echo ============================================================
%PYTHON_EXE% scripts\train_mlp_koopman.py --config configs\platform1.yaml > "results\train_p1_mlp.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 6/6: Platform 1 - Traditional EDMD
echo ============================================================
%PYTHON_EXE% scripts\train_traditional_edmd.py --config configs\platform1.yaml > "results\train_p1_traditional.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo ============================================================
echo All 6 training jobs completed!
echo ============================================================
pause
