pack.exe -F -w .\src\main.py
MOVE dist\main.exe docs\main.exe
RMDIR dist /s /q
RMDIR build /s /q
DEL main.spec
pause