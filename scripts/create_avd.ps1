#!/usr/bin/env pwsh
param(
    [string]$avdName = 'GeoPicAVD',
    [string]$systemImage = 'system-images;android-33;google_apis;x86_64'
)

Write-Output "Creating AVD '$avdName' with image $systemImage"
& "$env:ANDROID_SDK_ROOT\cmdline-tools\latest\bin\avdmanager" create avd -n $avdName -k $systemImage --device "pixel" -f
Write-Output "AVD created. Use emulator -list-avds and emulator -avd <name> to run it."
