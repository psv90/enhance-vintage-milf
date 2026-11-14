@echo off
rem Pelna poprawa filmu: upusc film na ten plik albo kliknij dwa razy i wybierz film.
chcp 65001 >nul
title Enhance Vintage Milf
if not exist "%~dp0silnik\zainstalowane.txt" (
  echo Pierwsze uruchomienie: instaluje potrzebne programy i modele.
  echo Potrzeba ok. 20 GB miejsca i internetu, moze to potrwac od kilkunastu minut do godziny.
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instaluj.ps1"
  if errorlevel 1 ( echo. & pause & exit /b 1 )
)
"%~dp0silnik\RelayVSR\.venv\Scripts\python.exe" "%~dp0popraw.py" %1
echo.
pause
