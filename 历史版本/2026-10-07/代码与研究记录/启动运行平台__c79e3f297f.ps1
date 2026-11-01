$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonRuntime = Join-Path $projectRoot 'tmp/cad_runtime/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonRuntime)) { $pythonRuntime = 'python' }
& $pythonRuntime (Join-Path $PSScriptRoot 'run_platform.py')
