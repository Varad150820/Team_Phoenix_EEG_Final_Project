$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root 'mne\Scripts\python.exe'
$script = Join-Path $root 'scripts\run_all_recordings.py'

& $python $script
