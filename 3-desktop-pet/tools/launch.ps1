param([string]$Extra = '--debug --sleep-after=6')

$me = $PID
Get-CimInstance Win32_Process -Filter "name='python.exe'" |
    Where-Object { $_.CommandLine -like '*oktopet.py*' -and $_.ProcessId -ne $me } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 500
$py = (Get-Command python).Source
$dir = (Get-Location).Path
$cmd = '"' + $py + '" "' + $dir + '\Oktopet\oktopet.py" ' + $Extra
$r = ([wmiclass]'Win32_Process').Create($cmd, $dir)
Write-Output "PID=$($r.ProcessId) ReturnValue=$($r.ReturnValue)"
