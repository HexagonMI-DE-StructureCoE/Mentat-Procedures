#!/usr/bin/env python
#---------------------------------------------------------------------
# Purpose:
import sys
import os
from py_mentat import *
from py_post import *

def main():
#                             headers for cmd and dialogue windows
  py_prompt("START User Procedure")

  print ("\n\n ---------------------------------------\n")
  print ("\tSTART User Procedure")
  print (" ---------------------------------------\n")
#                          extract 
#                             ...name of current model/post file
  mname = py_get_string("model_name()")
  if (py_ms_bool("exists_post_model", 0)):
      res=mname.rsplit('.', 1)
      marc_out_file=res[0]
  else:
      #                             ...name of current job
      jname_out = py_get_string("job_name()")
      #                             ...name of associated output file
      marc_out_file = mname + "_" + jname_out
  
  marc_out_filename=marc_out_file + ".out"

  if os.path.exists(marc_out_filename)== False:
      py_prompt("Error: No such file.[%s]" % marc_out_filename)
      return

# domains

  domains = py_ms_int('valid_domains',0)
  print('Domains = ',domains)


#                             run perl script
  print ("...parsing output file ",marc_out_filename)
  dirLcl = os.path.dirname(os.path.realpath(__file__))
  pathname = dirLcl + "/_check_marc_analysis.py"
  strv = "*py_file_run " + pathname
  # print("here ", marc_out_filename )
  # py_send("*py_call_arguments %s 1 " % marc_out_filename )
  py_send("*define outfilename %s " % marc_out_filename )
  if domains > 0:
    strv += " "
    strv += str(domains)
  print('Command = ',strv)
  py_send(strv)


# run the resulting proc file
  print ("...running procedure file to select nodes/elements")
  py_send("*exec_procedure check_analysis.proc")

  py_send("*edit_file \"output_python.txt\" ")

#                             print tail to activity
  print ("\n ---------------------------------------\n")
  print ("\tEND User Procedure")
  print (" ---------------------------------------\n")

  py_send("*set_proc_echo off")

  return 1


#if __name__ == '__main__':
#  py_connect('',40007)
#  main()
#  py_disconnect()
