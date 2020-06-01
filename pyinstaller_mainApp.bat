:: 需要进入py37_natux虚拟环境下执行
pyinstaller -y -w .\src\mainApp.py
copy .\src\equipCfg.ini .\dist\mainApp\equipCfg.ini
pause