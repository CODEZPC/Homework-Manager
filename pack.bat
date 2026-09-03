pyinstaller -F -w .\src\main.py -i .\src\HM.ico
MOVE dist\main.exe docs\main.exe
RMDIR dist /s /q
RMDIR build /s /q
DEL main.spec
pause