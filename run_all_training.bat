@echo off
echo ============================================================
echo Starting 6 training jobs sequentially
echo ============================================================
echo.

set PROJECT=C:\Users\Windows\Desktop\论文4\code-projectv2
cd /d "%PROJECT%"

echo Job 1/6: Platform 2 - PatchTST-Koopman (EDMD, 500 epochs)
echo ============================================================
python scripts\train_patchtst.py --config configs\platform2.yaml > "results\train_p2_patchtst.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 2/6: Platform 2 - MLP-Koopman (300 epochs)
echo ============================================================
python scripts\train_mlp_koopman.py --config configs\platform2.yaml > "results\train_p2_mlp.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 3/6: Platform 2 - Traditional EDMD
echo ============================================================
python scripts\train_traditional_edmd.py --config configs\platform2.yaml > "results\train_p2_traditional.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 4/6: Platform 1 - PatchTST-Koopman (EDMD, 500 epochs)
echo ============================================================
python scripts\train_patchtst.py --config configs\platform1.yaml > "results\train_p1_patchtst.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 5/6: Platform 1 - MLP-Koopman (300 epochs)
echo ============================================================
python scripts\train_mlp_koopman.py --config configs\platform1.yaml > "results\train_p1_mlp.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo Job 6/6: Platform 1 - Traditional EDMD
echo ============================================================
python scripts\train_traditional_edmd.py --config configs\platform1.yaml > "results\train_p1_traditional.log" 2>&1
echo Done. Exit code: %ERRORLEVEL%
echo.

echo ============================================================
echo All 6 training jobs completed!
echo ============================================================
pause
