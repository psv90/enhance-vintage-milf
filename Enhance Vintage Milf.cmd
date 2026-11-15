@echo off
rem Okno programu: kliknij dwa razy albo upusc filmy na ten plik (trafia do kolejki).
chcp 65001 >nul
title Enhance Vintage Milf
if not exist "%~dp0silnik\zainstalowane.txt" (
  echo Pierwsze uruchomienie: instaluje potrzebne programy i modele.
  echo Potrzeba ok. 20 GB miejsca i internetu, moze to potrwac od kilkunastu minut do godziny.
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instaluj.ps1"
  if errorlevel 1 ( echo. & pause & exit /b 1 )
)
rem Okno programu (bez konsoli). Stara wersja w konsoli: python popraw.py FILM
start "" "%~dp0silnik\RelayVSR\.venv\Scripts\pythonw.exe" "%~dp0aplikacja.py" %*
