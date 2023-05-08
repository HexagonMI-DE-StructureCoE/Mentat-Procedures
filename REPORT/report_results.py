from py_mentat import * 

import os
import sys 

current_path = os.path.dirname(os.path.abspath(__file__))
new_path = os.path.join(current_path, "..", "PYTHON_LIB")

print(new_path)
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def main():

    #sys.path.append(r"C:\MSC.Software\Marc\2021.2.0\mentat2021.2\menus")

    document = Document()

    
    modelname0 = py_get_string("filename()")
    modelname1 = modelname0.replace(".t16","").replace(".t19","")
    
    titolo = "Report Model\n" + modelname1
    titolo = titolo
    d = document.add_heading(titolo , 0)
    d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = document.add_paragraph('')
    p.add_run("\n")
    modelname = py_get_string('model_name()')
    p.add_run(f" Model name: {modelname} \n")

    py_send("*fill_view")
    py_send("*post_rewind")
    py_send("*post_off")
    py_send('*image_save_current "results.png" yes')
    
    if os.path.exists("model.png"):
        document.add_picture('model.png' , width=Inches(6.0) )
    
    #Numero elementi
    document.add_heading("Model description\n" , 1)
    p1 = document.add_paragraph('')
    nodi = py_get_int("nnodes()")
    str1 = " Number of Nodes       %g \n" % (nodi)
    p1.add_run(str1)
    elementi = py_get_int("nelements()")
    str1 = " Number of Elements %g \n" % (elementi)
    p1.add_run(str1)
    
      
    document.add_page_break()
    
    


    document.add_heading("Results description\n" , 1)
    p1 = document.add_paragraph('')
    #p1.add_run(stri)
    
    
    lista_res = ["Displacement"]    # , "Total Equivalent Plastic Strain","Equivalent Von Mises Stress"]
    
    py_send("*post_skip_to_last")
    py_send("*system_grid_display_off")
    
    py_send("*post_contour_bands")

    print(lista_res)
    
    for val1 in lista_res:
        py_send("*post_value %s" % val1 )
        py_send('*image_save_current "%s.png" yes' % val1)
        if os.path.exists("%s.png" % val1 ):
            p1 = document.add_paragraph('')
            p1.add_run("Displacement\n")
            document.add_picture('Displacement.png' , width=Inches(6.0) )
            document.add_page_break()
    
    filename = "report_" + str(modelname1) + "_results.docx"

    document.save(filename)

    py_prompt("Done")