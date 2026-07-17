pack.exe -F -w .\src\new\app.py
MOVE dist\app.exe docs\main.exe
RMDIR dist /s /q
RMDIR build /s /q
DEL app.spec
pause