$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$report = Join-Path $root 'milestone5\reports\main_final_report.html'

Start-Process $report
