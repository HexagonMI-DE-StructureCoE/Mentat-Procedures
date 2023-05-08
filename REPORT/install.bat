@echo off
rem edita se necessario le due righe seguenti
set PYTHONPATH=..\PYTHON_LIB
set PYTHONHOME=C:\MSC.Software\Marc\2023.1.0\mentat2023.1\python\WIN8664

set PATH=%PYTHONHOME%\PyQt5;%PYTHONHOME%\;%PYTHONHOME%\DLLs;%PYTHONHOME%\Scripts
set PATH=%PATH%;c:\Windows;c:\Windows\System32;c:\Windows\Wbem


SET SUBDIR=%~dp0
cd /D %SUBDIR% 
%PYTHONHOME%\\python -m pip install python-docx --target=..\PYTHON_LIB --no-user 
