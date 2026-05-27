#Requires -Version 3.0
param(
    [string]$ProjectDir = "C:\Users\Windows\Desktop\论文4\code-projectv2",
    [string]$PythonExe = "C:\Users\Windows\.conda\envs\koopman\python.exe"
)

$ErrorActionPreference = "Continue"
[System.IO.Directory]::SetCurrentDirectory($ProjectDir)

function Dirs {
    param([string]$d)
    $null = New-Item -ItemType Directory -Path $d -Force
}

Dirs "$ProjectDir\results\models"
Dirs "$ProjectDir\results\logs"
Dirs "$ProjectDir\results\traditional_edmd"
Dirs "$ProjectDir\results\mlp_koopman"

function Run-Job {
    param($Name, $Args, $LogFile)
    $logPath = "$ProjectDir\results\$LogFile"
    Write-Host "============================================================"
    Write-Host "$(Get-Date -Format 'HH:mm:ss') Starting: $Name"
    Write-Host "Log: $logPath"
    Write-Host "============================================================"
    & $PythonExe $Args 2>&1 | Tee-Object -FilePath $logPath
    $ec = $LASTEXITCODE
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Job '$Name' exit code: $ec"
    return $ec
}

$jobs = @(
    @{Name="P2 PatchTST-Koopman (EDMD 500ep)";  A=@("scripts/train_patchtst.py","--config","configs/platform2.yaml");          L="train_p2_patchtst.log"},
    @{Name="P2 MLP-Koopman (300ep)";            A=@("scripts/train_mlp_koopman.py","--config","configs/platform2.yaml");       L="train_p2_mlp.log"},
    @{Name="P2 Traditional EDMD";               A=@("scripts/train_traditional_edmd.py","--config","configs/platform2.yaml");  L="train_p2_traditional.log"},
    @{Name="P1 PatchTST-Koopman (EDMD 500ep)";  A=@("scripts/train_patchtst.py","--config","configs/platform1.yaml");          L="train_p1_patchtst.log"},
    @{Name="P1 MLP-Koopman (300ep)";            A=@("scripts/train_mlp_koopman.py","--config","configs/platform1.yaml");       L="train_p1_mlp.log"},
    @{Name="P1 Traditional EDMD";               A=@("scripts/train_traditional_edmd.py","--config","configs/platform1.yaml");  L="train_p1_traditional.log"}
)

foreach ($j in $jobs) {
    $ec = Run-Job -Name $j.Name -Args $j.A -LogFile $j.L
    if ($ec -ne 0) {
        Write-Warning "Job '$($j.Name)' failed with exit code $ec"
    }
}

Write-Host "`n============================================================"
Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ALL 6 TRAINING JOBS COMPLETED"
Write-Host "============================================================"

$marker = "$ProjectDir\results\TRAINING_COMPLETE.txt"
"All 6 jobs finished at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $marker -Encoding utf8
