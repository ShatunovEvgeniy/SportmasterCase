<#
  Sportmaster AI-Summary demo — запуск всего стека одной командой.

  Поднимает по порядку (пропускает то, что уже запущено):
    1. MySQL       (порт 3306)
    2. FastAPI      (порт 8000, слушает 0.0.0.0 — доступен и из локальной сети)
    3. Tomcat       (порт 8080, слушает 0.0.0.0 — доступен и из локальной сети)

  Использование:
    powershell -ExecutionPolicy Bypass -File .\start-all.ps1

  Пути ниже соответствуют тому, как всё было установлено при разработке.
  Если у тебя другие пути — поправь переменные в начале файла.
#>

$ErrorActionPreference = "Stop"

$Root        = $PSScriptRoot
$Backend     = Join-Path $Root "backend"
$Frontend    = Join-Path $Root "Sportmaster_frontend"

$MysqldExe   = "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe"
$MysqlIni    = "C:\ProgramData\MySQL\MySQL Server 8.4\my.ini"
$JavaHome    = "C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"
$MavenHome   = "C:\Users\vin05\AppData\Local\Programs\apache-maven\apache-maven-3.9.16"
$CatalinaHome= "C:\Users\vin05\AppData\Local\Programs\tomcat10\apache-tomcat-10.1.57"
$VenvPython  = Join-Path $Backend ".venv\Scripts\python.exe"

function Test-PortOpen($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

Write-Host "=== 1. MySQL (3306) ===" -ForegroundColor Cyan
if (Test-PortOpen 3306) {
    Write-Host "уже запущен, пропускаю"
} else {
    Start-Process -FilePath $MysqldExe -ArgumentList @("--defaults-file=$MysqlIni", "--console") -WindowStyle Hidden
    Start-Sleep -Seconds 5
    if (Test-PortOpen 3306) { Write-Host "MySQL поднят" -ForegroundColor Green }
    else { Write-Host "MySQL не поднялся, проверь лог ошибок MySQL" -ForegroundColor Red }
}

Write-Host "`n=== 2. FastAPI (8000) ===" -ForegroundColor Cyan
if (Test-PortOpen 8000) {
    Write-Host "уже запущен, пропускаю"
} else {
    if (-not (Test-Path $VenvPython)) {
        Write-Host "Не найден venv: $VenvPython" -ForegroundColor Red
        Write-Host "Создай его один раз: cd `"$Backend`"; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
    } else {
        Push-Location $Backend
        $env:PYTHONIOENCODING = "utf-8"
        Start-Process -FilePath $VenvPython -ArgumentList @("-m","uvicorn","src.api.app:app","--host","0.0.0.0","--port","8000") `
            -WindowStyle Hidden -RedirectStandardOutput "$Backend\uvicorn.log" -RedirectStandardError "$Backend\uvicorn.err.log"
        Pop-Location
        Start-Sleep -Seconds 5
        if (Test-PortOpen 8000) { Write-Host "FastAPI поднят" -ForegroundColor Green }
        else { Write-Host "FastAPI не поднялся, смотри $Backend\uvicorn.err.log" -ForegroundColor Red }
    }
}

Write-Host "`n=== 3. Tomcat (8080) ===" -ForegroundColor Cyan
if (Test-PortOpen 8080) {
    Write-Host "уже запущен, пропускаю"
} else {
    $env:JAVA_HOME = $JavaHome
    $war = Join-Path $Frontend "target\Project-1.0-SNAPSHOT.war"
    if (-not (Test-Path $war)) {
        Write-Host "WAR не найден — собираю Maven'ом (может занять минуту)..."
        $env:Path = "$MavenHome\bin;$JavaHome\bin;$env:Path"
        Push-Location $Frontend
        mvn -q package -DskipTests
        Pop-Location
    }
    Copy-Item $war (Join-Path $CatalinaHome "webapps\ROOT.war") -Force
    $env:CATALINA_HOME = $CatalinaHome
    Start-Process -FilePath (Join-Path $CatalinaHome "bin\startup.bat") -WindowStyle Hidden
    Start-Sleep -Seconds 8
    if (Test-PortOpen 8080) { Write-Host "Tomcat поднят" -ForegroundColor Green }
    else { Write-Host "Tomcat не поднялся, смотри $CatalinaHome\logs\catalina.out" -ForegroundColor Red }
}

$lanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notmatch 'Loopback|vEthernet|WSL' -and $_.IPAddress -notlike '169.254*'
} | Select-Object -First 1 -ExpandProperty IPAddress)

Write-Host "`n=== Готово ===" -ForegroundColor Green
Write-Host "На этом компьютере:  http://localhost:8080/sportmaster-case.html"
if ($lanIp) {
    Write-Host "В локальной сети:    http://$($lanIp):8080/sportmaster-case.html"
    Write-Host "(порты 8080 и 8000 должны быть разрешены в файрволе — см. README.md)"
}

