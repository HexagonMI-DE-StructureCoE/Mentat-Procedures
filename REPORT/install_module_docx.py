

import os
import sys 

import subprocess

def installa_modulo():

    current_path = os.path.dirname(os.path.abspath(__file__))
    mypythonlib = "PYTHON_LIB"
    new_path = os.path.join(current_path, "..", mypythonlib)

    print(new_path)

    sys.path.append(new_path)


    try:
        from docx import Document
        print("ok package is installed.")
    except:

        python_path = sys.executable
        python_0 = os.path.dirname(python_path)
        if os.name == "nt":
            python_home = os.path.join(python_0,"..","..","python","WIN8664")
        else:
            python_home = os.path.join(python_0,"..","..","python","LX8664")

        try:

            if os.name == "nt":
                fileo = open("installa.bat","w")
                fileo.write("@echo off\n")
                fileo.write("\n")
                fileo.write("set PYTHONPATH=..\%s\n" % mypythonlib)
                fileo.write("set PYTHONHOME=%s\n" % python_home )
                fileo.write("\n")
                fileo.write("set PATH=%PYTHONHOME%\PyQt5;%PYTHONHOME%\;%PYTHONHOME%\DLLs;%PYTHONHOME%\Scripts\n")
                fileo.write("set PATH=%PATH%;c:\Windows;c:\Windows\System32;c:\Windows\Wbem\n")
                fileo.write("\n")
                fileo.write("\n")
                fileo.write("SET SUBDIR=%~dp0\n")
                fileo.write("cd /D %SUBDIR% \n")

                fileo.write("echo Do you want to execute the next command? (Y/N)\n")
                fileo.write("choice /c YN\n")
                fileo.write("\n")
                fileo.write("if errorlevel 2 (\n")
                fileo.write("    echo Command execution canceled.\n")
                fileo.write("exit")
                fileo.write(") else (\n")
                fileo.write("    echo Proceeding with the next command.\n")


                fileo.write("cd /D %s\n" % new_path)
                stringa = f'"%PYTHONHOME%\\python\" -m pip install python-docx --target="..\\{mypythonlib}" --no-user \n' 
                print(stringa)
                fileo.write(stringa)

                fileo.write("echo ....\n")
                fileo.write("echo Exit from Mentat and rerun the tool \n")


                fileo.write("pause\n")
                fileo.write("exit\n")
                fileo.write(")\n")

                fileo.close()



                cur_file_dir= os.path.dirname(os.path.abspath(__file__))
                install_location = os.path.join(cur_file_dir,"..",mypythonlib)

                if not os.path.exists(install_location):
                    print("creating folder")
                    os.makedirs(install_location)
                
                if os.name == "nt":
                    subprocess.Popen(['start', 'cmd', '/k', 'installa.bat'], shell=True)

            else:
                print("The python-docx package was not installed.")
        
        except:
            print("Error trying to install docx module\n")
            print("Please check that you can write into target folder : ", python_home )

if __name__ == "__main__":
    print("installo modulo ")
    installa_modulo()
    print("Done")
