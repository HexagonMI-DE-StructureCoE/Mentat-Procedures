@echo off

set PYTHONPATH=..\PYTHON LIB
set PYTHONHOME=C:\MSC.Software\Marc\2023.1.0\mentat2023.1\python\WIN8664\..\..\python\WIN8664

set PATH=%PYTHONHOME%\PyQt5;%PYTHONHOME%\;%PYTHONHOME%\DLLs;%PYTHONHOME%\Scripts
set PATH=%PATH%;c:\Windows;c:\Windows\System32;c:\Windows\Wbem


SET SUBDIR=%~dp0
cd /D %SUBDIR% 
echo Do you want to execute the next command? (Y/N)
choice /c YN

if errorlevel 2 (
    echo Command execution canceled.
exit) else (
    echo Proceeding with the next command.
cd /D C:\Projects\Mentat-Procedures\REPORT\..\PYTHON LIB
"%PYTHONHOME%\python" -m pip install python-docx --target="..\PYTHON LIB" --no-user 
echo ....
echo Exit from Mentat and rerun the tool 
pause
exit
)
