import os
import subprocess
import sys

import threading
import multiprocessing as mp
import time 

def cancella(filename, id1):
    
    print("in funzione cancella",filename)

    print(os.path.exists(filename))
    
    while 1:
        try:
            if os.path.exists(filename):    
                
                os.remove(filename)

                print("fatto",filename)
                break
        except:
            # print("child ", mp.current_process().pid)
            if id1 == 2:
                if os.path.exists("tempfile"):
                    os.remove("tempfile")
                os.kill(os.getppid() ,  9)
                time.sleep(3)
            else:
                time.sleep(5)

    return

def vai(filename):

    pid = os.getpid()

    print("pid",pid)

    print("in vai ", filename)
    #t1 = threading.Thread(target=cancella, args=(filename,),daemon=True)
    t1 = mp.Process(target=cancella, args=(filename,1))
    t1.daemon = True
    t1.start()
    print("main0 ",mp.current_process().pid)
    t1.join()

    filename=filename.replace(".log",".proc")   # devo killare mentat
    t1 = mp.Process(target=cancella, args=(filename,2))
    t1.daemon = True
    t1.start()
    pid = mp.current_process().pid
    print("main2 ",mp.current_process().pid)
    t1.join()

    

    return

def main():
    tempfile = "tempfile"
    if os.path.exists(tempfile):
        filei=open(tempfile,"r")
        nome_file = filei.readline()
        filei.close()
        print("nome ",nome_file)
        
        vai(nome_file)

    if os.path.exists(tempfile):
        os.remove(tempfile)



if __name__ == '__main__':
    #sys.argv.append(r"C:\MSC.Software\Marc\2021.2.0\mentat2021.2\menus\UTILITIES\mentat.6.log")
    print("Argomenti",sys.argv)
    print("curdir",os.getcwd())
    #nome_file=r"C:\MSC.Software\Marc\2021.2.0\mentat2021.2\menus\UTILITIES\mentat.1.log"
    main()
