#!/usr/bin/env python
#
from py_mentat import *
import os
import sys

#import threading
#import multiprocessing as mp
import time 
import subprocess


def main():

    py_send("*py_separate_process off")
    directory = py_get_string("getcwd()")
    
    for i in range(100):
        if i==0:
            filename = os.path.join(directory, "mentat.log")
        
        else:
            filename = os.path.join(directory, "mentat." + str(i) + ".log")
        
        filename2 = filename.replace(".log",".proc")
        
        if os.path.exists(filename) or os.path.exists(filename2):
            try:
                if os.path.exists(filename):  os.remove(filename)
                if os.path.exists(filename2): os.remove(filename2)
            except:
                print("cannot remove", filename)
                ultimo=filename

                fileo =open("tempfile","w")
                fileo.write(ultimo)
                fileo.close()

                # py_send("*py_call_arguments %s" % ultimo)
                py_send("*py_echo off *set_proc_echo off")
                py_send("*py_separate_process on")
                dir1 = os.path.dirname(os.path.abspath(__file__))
                percorso = os.path.join(dir1,"daemon_delete.py")
                print("percorso", percorso)
                if os.path.exists(percorso):    
                    py_send("*py_file_run %s %s" % (percorso,ultimo ))
                else:
                    print("worng path ", percorso)
                #py_send("*py_separate_process off")
                py_send("*py_echo on *set_proc_echo on")
                py_send("|")
                py_send("| run completed")
    

    return 

if __name__ == '__main__':
    main()

