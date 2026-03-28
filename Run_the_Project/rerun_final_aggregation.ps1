$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root 'mne\Scripts\python.exe'
$script = Join-Path $root 'scripts\aggregate_final_pipeline.py'

& $python $script
