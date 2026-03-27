pyinstaller -F -w main.py
MOVE dist\main.exe .\main.exe
RMDIR dist /s /q
RMDIR build /s /q
DEL main.spec
pause