$ErrorActionPreference = 'Stop'
$studioRoot = $PSScriptRoot
$studioPython = Join-Path $studioRoot '.venv-facefit\Scripts\python.exe'
& $studioPython (Join-Path $studioRoot 'webapp\connect_blender.py')
try { $null = Invoke-WebRequest 'http://127.0.0.1:8080/api/state' -TimeoutSec 2 }
catch {
    Start-Process -FilePath $studioPython -ArgumentList ('"' + (Join-Path $studioRoot 'webapp\server.py') + '"') -WorkingDirectory $studioRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $studioRoot 'mocap\web_server.log') -RedirectStandardError (Join-Path $studioRoot 'mocap\web_server_error.log')
}
Start-Process 'http://127.0.0.1:8080'
