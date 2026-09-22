@echo off
rem ==== 1) onedir (-D) build: dist\main\ (main.exe + _internal\) -> docs\main.zip ====
pyinstaller -D -w .\src\main.py -i .\src\HM.ico
if exist "docs\main.zip" del /q "docs\main.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\main\*' -DestinationPath 'docs\main.zip' -Force"
RMDIR dist /s /q
RMDIR build /s /q
DEL main.spec

rem ==== 2) onefile legacy build: docs\main.exe (for old clients downloading only main.exe) ====
pyinstaller -F -w .\src\main.py -i .\src\HM.ico
MOVE /Y dist\main.exe docs\main.exe
RMDIR dist /s /q
RMDIR build /s /q
DEL main.spec

pause