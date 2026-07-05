pyinstaller -F -w -i .\src\HM.ico .\src\main.py
MOVE dist\main.exe docs\main.exe
RMDIR dist /s /q
RMDIR build /s /q
DEL main.spec
pause