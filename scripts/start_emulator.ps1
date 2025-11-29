#!/usr/bin/env pwsh
param(
    [string]$avdName = 'GeoPicAVD'
)

Write-Output "Starting emulator: $avdName"
Start-Process -NoNewWindow -FilePath "$env:ANDROID_SDK_ROOT\emulator\emulator.exe" -ArgumentList "-avd", $avdName
