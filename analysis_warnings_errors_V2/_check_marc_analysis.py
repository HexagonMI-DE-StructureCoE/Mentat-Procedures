#!/usr/bin/python

# original perl code : andrew.bell@hexagon.com 
# python code : fabio.scannavino@hexagon.com
#               marco.bernasconi@hexagon.com
#               simone.bobbio@hexagon.com


import sys
import os 
import datetime 

try:
    from py_mentat import *
except:
    print("cannot import py_mentat ")
 
import shutil

def main():

    print("\n--- in main ---")

    #---------------------------------------------------------------------
    # Description
    # Python script to search through a marc output file and extract the 
    # nodes or elements associated with common warnings or errors

    # This original code was written in Perl language
    # this script is a tranlation into Python code 

    #
    # The nodes or elements for each type of warning or error are
    # accumulated, sorted and then stored in separate arrays. these
    # arrays are then used to create either a mentat proc or patran 
    # session file which, when run in the corresponding gui, will 
    # create a corresponding series of SETS or GROUPS which may be 
    # visualised as an aid in troubleshooting analyses
    #
    # current warning/error messages that are searched for are:
    #   0  => list of nodes that are separating
    #   1  => list of INSERT nodes that have not converged
    #   2  => list of contact node sliding along segment
    #   3  => list of contact nodes belonging to more than 1 body
    #   4  => list of contact nodes that have a DOF conflict
    #   5  => list of inside out elements
    #   6  => list of nodes that have max displacement change and increment
    #         from convergence criteria
    #   7  => list of nodes that have max residual change and increment
    #         from convergence criteria
    #   8  => Contacting Nodes
    #   9  => Bad beam section
    #  10  => Bad quadratic projection
    #  11  => IPC check (ddu multiplied by x to avoid large displacements...)
    #  12  => IPC check (ddu multiplied by x to avoid penetration)
    #  13  => too many nodes joined to node
    #  14  => Projection for contact node failed
    #  15  => Bad rigid body orientation
    #  16  => Node separated 5 times and will be skipped 
    #  17  => Incorrect degenerated Hex elements
    #  18  => start of assembly
    #  19  => start of matrix solution
    #  20  => end of matrix solution
    #  21  => start of global remeshng
    #  22  => axisymmetric element has negative radius
    #  23  => IPC check (ddu multiplied by x to avoid penetration) - but only 1e-6 values
    #  24  => zero length in element
    #  25  => tying debug capture
    #
    # Usage
    # type the following in a command window, when in the same directory
    # as the output file:
    #
    #   python   this_script   output_file   gui_flag   ddm_flag   result_flag
    #
    #   where:
    #
    #       output_file 
    #         full name of output file
    #
    #         in the case of ddm, specify the first output file only (i,e, 
    #         the one with the number "1" preceding)
    #         e.g. given a set of output files named:
    #            1ddm_test_job1.out
    #            2ddm_test_job1.out
    #            3ddm_test_job1.out
    #            etc
    #
    #         specify the output filename as:
    #            1ddm_test_job1.out
    #
    #       gui_flag:
    #         1 => mentat
    #         2 => patran
    #
    #       ddm_flag:
    #         number of processors used for ddm run
    #
    #       result_flag:
    #         1 => check for warnings and errors only - don't create any
    #              groups or sets
    #
    # typically, when using Marc without DDM parallelisation, the command required is:
    #
    #    c:\path_to_python\python.exe _check_marc_analysis.py outputfile.out   1   0   0
    #
    # a single _check_analysis.proc/ses file will be created that can then 
    # be run within mentat (proc) or patran (ses) to generate the sets or
    # groups
    #
    # the groups created in the gui will be named as follows (corresponding 
    # to each of the types of message searched for):
    #   _separating, _inserts, _sliding, _contact_belonging, _dof_conflict
    #   _inside_out, _disp_convergence, _res_convergence, _contacting_nodes, 
    #   _bad_beams, bad_projection, _iterative_penetration_d, 
    #   _iterative_penetration_p, _nodes_joined_to_nodes, _bad_contact_projection,
    #   _bad_rigid_orientation, _separated_5_times, _bad_degenerate_hex,
    #   _neg_axisymmetric_node, _IPC_small, _zero_length, _tying_debug
    #
    # Note: 
    #       print,5 is needed in the marc data file to generate the contact
    #       messages that script will pick up
    #
    #       Error messages will be seen in the dialog area of mentat to do 
    #       with SETS not being found - this is ok since the script will try 
    #       and delete any previously existing sets first...
    #
    #       Reading the proc/ses file can take a little while on larger jobs 
    #       whilst it reads through the long lists of elements within each 
    #       set
    #
    #       User variables have the word (CHANGE) added to the corresponding
    #       comment - that is, there are the commands to change when adding
    #       a new trap for a warning/error message
    #
    #
    # to get a listing of what is found during the reading of the output
    # file, set $debug=1 below
    #
    #---------------------------------------------------------------------
    #

    filename_out = "output_python.txt"
    fileo = open( filename_out ,"w")

    now = datetime.datetime.now().replace(microsecond=0) 
    fileo.write("Created : " + str(now))


    fileo.write("\n\n\n-----------------------------------------\n")
    fileo.write("------- OUTPUT File Check START ---------\n")
    fileo.write("-----------------------------------------\n\n")
    #
    #---------------------------------------------------------------------
    # initialise variables
    #---------------------------------------------------------------------
    i = 0           #                            ...word counter
    continue1 = 0   #                            ...loadcase counter
    nmemory = 0     #                            ...number of memory increases
    tmemory = 0     #                            ...total memory increase
    pdmemory = 0    #                             ...peak domain memory usage
    #                             ...first pass flag for iterative projection 

    #                                warning
    projection = 0
    nfile = 0      #                             ...output file counter for ddm
    debug = 99     #                             ...debug flag (CHANGE)
    iprint = 0     #                             ...print warning/errors found (CHANGE)
    #                                           ...maximum number of warning/error message 
    #                                              types to be searched for (CHANGE)

    maxcol = 26
    maxsel = 90000000 #                             ...maximum number of words in output file (CHANGE)
    maxnode = 1000000 #                             ...maximum number of nodes/elements to 

    #                             ...detailed timing flag (CHANGE)
    #                                0 = no details of assembly, solution and recovery per iteration (only summary)
    #                                1 = print details
    timing = 0
    outfile = None   #                             ...output filename specified
    guiflag = None   #                             ...flag to determine whether proc or ses 
    ddmflag = None   #                             ...flag to indicate multiple output files 
    #                             ...flag to indicate whether to create 
    #                                groups/sets or not
    resflag = None
    ttime = None #                             ...total time for solution
    ttime_a = None #                                assembly
    ttime_m = None #                                matrix solution
    ttime_r = None #                                recovery
    ttime_g = None #                                global remeshing
    tpercent = None #                             ...percentage time taken in each phase
    niterations = None #                             ...total number of iterations in analysis
    nincrement = None #                             ...total number of increments in analysis
    nproceed = 0 #                             ...total number of continues if not converged
    nowarning = 0 #                             ...flag to ignore certain types of longwinded warnings
    DATA = None #                             ...handle to ses/proc file to be created
    TYING = None #                             ...handle to debug tying file to be created
    data_lines = [0] * maxsel #                             ...list of all words in the output file(s)
    nselected = [0] * maxcol #                             ...selected variable counter - initialised to zero
    nselected_sorted = [1] * maxcol #                             ...unselected variable counter - initialised to zero


    #                             ...sorted 2d array (CHANGE)
    #                                if maxcol is CHANGEd, then add/remove 
    #                                another array and its reference here

    messages = ["_separating", "_inserts", "_sliding", "_contact_belonging", \
               "_dof_conflict", "_inside_out", "_disp_convergence", "_res_convergence", \
               "_contacting_nodes", "_bad_beams","_bad_projection","_iterative_penetration_d",\
               "_iterative_penetration_p12","_nodes_joined_to_nodes","_bad_contact_projection","_bad_rigid_orientation",\
               "_separated_5_times","_bad_degenerate_hex","_assembly_start","_matrix_start",\
               "_matrix_end","_global_remeshing","_neg_axisymmetric_node","_IPC_small",\
               "_zero_length","_tying_debug"]

    # ...populate (CHANGE)
    selected        = []    #   26 positions  unsorted
    selected_sorted = []    #   26 positions 
    for _i in range(26):
        selected.append([])
        selected_sorted.append([])

    # ...unsorted 2d array (CHANGE)
    maxnode = 100  # assuming maxnode is 10, change it accordingly


    tying = []

    # extract command line parameters
    if True:
        outfile = py_get_string("outfilename")
    else:
        print("No parameter filename outfilename ")
        return

    guiflag = 1  
    ddmflag = 0
    resflag = 0

    #if len(sys.argv) > 2:
    #    guiflag = int(sys.argv[2])
    #    ddmflag = int(sys.argv[3])
    #    resflag = sys.argv[4]

        

    # checks on input parameters
    # ...outfile has been specified
    if "out" not in outfile:
        fileo.write("\nOutput file has not defined correctly (the extension is required)\n")
        fileo.write("  See instructions at top of perl script for usage details\n\n")
        #exit(3)

    # ...guiflag is defined
    if guiflag not in [ 1 , 2 ] :
        fileo.write("\nGUI flag is not defined: Specify 1 (mentat) or 2 (patran) on the command line)\n")
        fileo.write("  See instructions at top of perl script for usage details\n\n")
        #exit(3)

    # loop over number of processors used to concatenate the output files
    # crea un unico file
    if ddmflag > 0:
        # remove previous concatenated results
        os.remove("check_analysis.out")
        # remove preceding "1,2,3" etc to get base name
        base_name = outfile[1:]
        # open temporary outfile for appending
        with open("check_analysis.out", "a") as outfile_ddm:
            # loop over each ddm output file and write contents to ddm output file
            for iddm in range(1, ddmflag+1):
                next_name = str(iddm) + base_name
                fileo.write("\nConcatenating output file: " + next_name + " into check_analysis.out")
                # open output file for reading
                with open(next_name, "r") as datafile_ddm:
                    # write contents of next output file to ddm output file
                    for line in datafile_ddm:
                        outfile_ddm.write(line)
                # close next output file
                datafile_ddm.close()


    if ddmflag <= 0:
        fileo.write("\n\nDDM flag is not defined    : single output file will be searched: " + outfile + "\n")
    else:
        fileo.write("\n\nFile Name to Process       : check_analysis.out\n")
        fileo.write("                             concatenated from *" + outfile + " ddm files\n")

    if ddmflag > 0:   
        outfile = "check_analysis.out"  # redefine output file as newly concatenated file


    # open output file (name from runtime argument list or concatenated file for ddm runs)
    try:
        datafile = open(outfile,"r")
    except:
        fileo.write("\n\nCould not open file:", outfile, "($!)\n")
        #exit(1)

    # print summary of input information
    if ddmflag > 0:
        fileo.write("GUI chosen                 : "+ str(guiflag) + " (1=mentat / 2=patran)\n")
        fileo.write("Number of Processors used  : "+ str(ddmflag) + " \n")
    else:
        fileo.write("GUI chosen                 : "+ str(guiflag) + " (1=mentat / 2=patran)\n\n")

    # open results file 
    # ...mentat proc file
    if guiflag == 1:
        DATA = open("check_analysis_python.proc", "w")
        fileo.write("GUI commands will be written to check_analysis_python.proc\n")
        #DATA_res  = open("check_analysis_python_res.proc" , "w")
        #DATA_disp = open("check_analysis_python_disp.proc", "w")
        # ...additional output for tying debug messages if required
        # TYING = open("check_analysis_tying_python", "w")
        fileo.write("Debug TYING commands will be written to check_analysis_tying.proc\n")
    # ...patran ses file
    else:
        DATA = open("check_analysis_python.ses", "w")
        fileo.write("GUI commands will be written to check_analysis_python.ses")

    # loop over all the lines in the file and store the data locally
    fileo.write("\nLooping over output file to create a list of keywords\n")
    fileo.write("  Any errors or warnings will also be printed....\n")

    nfile = 0
    nowarning = 0
    iprint = 0
    maxsel = 1000
    i = 0
    continue1 = 0
    data_lines = []   # in perl dataitem
    skippa_c1 = True

    with open(outfile, 'r') as datafile:
        for line in datafile:

            if line.strip()=="":
                continue

            # search for warning and error messages
            start_file = line.find("version: Marc")
            if start_file > 0:
                nfile += 1
                fileo.write(f"\n\nStart of Output File for Domain # {nfile}\n")

            # errors
            error = line.find("*** error")
            if error > 0:
                dummy = line
                if iprint > 0:
                    fileo.write("   error: ", dummy.lstrip())

            # warnings
            warning = line.find("warning")
            if warning > 0:
                dummy = line
                dummy2 = line
                # specify warning messages to be ignored here
                for dummy2 in line.split():
                    if dummy2 == "interdomain":
                        nowarning += 1

                if nowarning == 0:
                    if iprint > 0:
                        fileo.write("   warning: ", dummy.lstrip())

            warning = line.find(" words failed")
            if warning > 0:
                dummy = line
                fileo.write("   warning: ", dummy.lstrip())

            if "continue" in line :
                continue1 += 1

            i +=1
            
            #if i == maxsel:
            #    fileo.write(f"   Warning: MAXSEL ({maxsel}) has been exceeded - increase this value \n\n")

            data_lines.append(line)
            
        # close file
        datafile.close()

    nitems = len(data_lines)

    # store and print number of words found

    fileo.write("\nNumber of full lines in File        : %d \n"% nitems)

    # print number of loadcases
    if ddmflag > 0:
        fileo.write("Number of Loadcases            : %d \n"% (continue1 / ddmflag))
    else:
        fileo.write("Number of Loadcases            : %d \n"% continue1)

    # error and stop if output file not found
    if nitems == 0:
        fileo.write("No OUTPUT file found. Check:\n")
        fileo.write("   a) The output file is in the same directory as this perl script\n")
        fileo.write("   b) The output file exists\n")
        #exit(2)

    # reinitialise domain file counter
    nfile = 0

    # loop over number of words in data file, search for specific keywords to print a summary of some overall analysis settings
    for idat in range(nitems):
        # extract data item
        # ...current
        linea = data_lines[idat]
        lineas = linea.split()
        nitems1 = len(lineas)

        word = lineas[0]
        # ...next(s)
        word_next   =  lineas[  1] if nitems1 > 1  else None
        word_next2  =  lineas[  2] if nitems1 > 2  else None
        word_next3  =  lineas[  3] if nitems1 > 3  else None
        word_next4  =  lineas[  4] if nitems1 > 4  else None
        word_next5  =  lineas[  5] if nitems1 > 5  else None
        word_next6  =  lineas[  6] if nitems1 > 6  else None
        word_next7  =  lineas[  7] if nitems1 > 7  else None
        word_next8  =  lineas[  8] if nitems1 > 8  else None
        word_next9  =  lineas[  9] if nitems1 > 9  else None
        word_next10 =  lineas[ 10] if nitems1 > 10 else None
        word_next11 =  lineas[ 11] if nitems1 > 11 else None
        word_next13 =  lineas[ 13] if nitems1 > 13 else None
        word_next16 =  lineas[ 16] if nitems1 > 16 else None
        # ...last
        word_last  = None # lineas[ - 1] if idat - 1 >= 0 else None
        word_last4 = None # lineas[ - 4] if idat - 4 >= 0 else None
        word_last5 = None # lineas[ - 5] if idat - 5 >= 0 else None

        if word == "version:" and word_next == "Marc":
            # initialise variables for each domain
            print(linea)
            nmemory = 0
            tmemory = 0
            projection = 0
            # increment domain number
            nfile += 1
            fileo.write("\nStart of Output File for Domain # %d\n" % nfile)


        # ----------------------------- check for global PARAMETER commands

        # version: Marc 2014.0.0, Build 282796 build date: Mon Jul 21 20:26:04 2014
        if word == "version:" and word_next == "Marc":
            fileo.write("...Marc Version                       : %s \n" % word_next2)

        # machine type: Windows
        if word == "machine" and word_next == "type:":
            fileo.write("...Machine Type                       : %s \n" % word_next2)

        if word == "sizing" and word_next5 == "elements":
            fileo.write("...Number of Elements                 : %s \n" % word_next2 )
            fileo.write("...Number of Nodes                    : %s \n" % word_next3 )
            fileo.write("...Number of DOFs Constrained         : %s \n" % word_next4 )

        if word == "element" and word_next == "type" and word_next2 == "requested*************************":
            fileo.write("...Element Type                       : %s \n" % word_next3)

        if word == "number" and word_next2 == "elements" and word_next4 == "mesh*********************":
            fileo.write("...Number of Elements                 : %s \n" % word_next5)

        if word == "number" and word_next2 == "nodes" and word_next4 == "mesh************************":
            fileo.write("...Number of Nodes                    : %s \n" % word_next5)

        #fabio material name
        if word == "material" and word_next == "name":
            fileo.write("\n...material name                      : %s \n" % word_next3)

        if word == "Youngs" and word_next == "modulus":
            if word_next2 != "-":
                fileo.write("...Youngs Modulus                     : %s \n" % word_next2)

        if word == "Poissons" and word_next == "ratio":
            if word_next2 != "-":
                fileo.write("   Poissons Ratio                     : %s \n" % word_next2)

        if word == "mass" and word_next == "density" and word_next3 == "heat":
            if word_next4 != "-":
                fileo.write("...Density                            : %s \n" % word_next5)

        if word == "Coefficient" and word_next2 == "thermal":
            if word_next4 != "-":
                fileo.write("   Thermal Expansion Coeff.           : %s \n" % word_next4)

        if word == "Yield" and word_next == "stress":
            if word_next2 == "-" or "1.00000E+20" in word_next2:
                pass
            else:
                fileo.write("   Yield Stress                       : %s \n" % word_next2)

        #                             flag for element storage (ielsto)  0
        if word == "flag" and word_next2 == "element" and word_next3 == "storage":
            fileo.write("...Out of Core Element Storage Flag   : %s \n" % word_next5)

        #                             include interlaminar shear for thick shells/beams
        if word == "interlaminar" and word_next == "shear" and word_next2 == "for":
            fileo.write("...Interlaminar Shear for Shells/Beams: ON \n")

        if word == "number" and word_next == "of" and word_next2 == "processors":
            fileo.write("...Number of Processors used          : %s \n" % word_next5)

        if word == "element" and word_next == "type" and word_next3 == "":
            fileo.write("...Element Topology                   : %s %s \n" % (word_next3, word_next4))

        if word == "large" and word_next == "displacement" and word_next2 == "analysis":
            fileo.write("...Large Displacement                 : ON \n")

        if word == "geometry" and word_next == "updated":
            fileo.write("...Updated Lagrange                   : ON \n")

        #tolto volutamente
        #if word == "constant" and word_next == "dilatation":
        #    fileo.write("...Constant Dilatation                : ON \n")

        if word == "plasticity" and word_next == "3":
            fileo.write("...Additive Plasticity                : ON \n")

        # number of element groups used:         2
        # group     # elements     element type     material  formulation#
        #    1      242688           139                1         UAF
        #    2       54500           139                2         UAF

        if word == "number" and word_next2 == "element" and word_next3 == "groups":
            fileo.write("\n...Formulation for Group\n")
            for ig in range(int(word_next5)+2):
                #ip = idat+17+5*ig
                #iq = idat+13+5*ig
                #fileo.write(f"...Formulation for Group              : #{data_lines[iq]} = {data_lines[ip]} \n")
                fileo.write(data_lines[idat+ig])

        #fabio
        if word == "*" and word_next=="*" and word_next2=="*" and word_next3=="*" and skippa_c1:
            fileo.write("\n\n... * * * * * * \n")
            for ig in range(200):
                linea = data_lines[idat+1+ig]
                if "*********" in linea:
                    ig = 200
                    fileo.write("\n... * * * * * * \n")
                    break
                fileo.write(linea[12:])
                skippa_c1 = False


        if word == "dynamic" and word_next.isdigit():
            fileo.write("...Dynamic                            : ON \n")

        if word == "solver" and word_next is None :
            try:
                linea_next = data_lines[idat+2]
                #print(linea_next)
                linea_nexts = linea_next.split()
                word_next  = linea_nexts[0]
                word_next3 = linea_nexts[1]
                fileo.write(f"...{word_next} {word_next3} is used \n")
            except:
                pass

        if word == "work" and word_next == "hard":
            fileo.write("...Work Hardening                     : ON \n")

        if word == "mechanical" and word_next == "convergence":
            fileo.write(f"...Tolerance for Iterative Solver     : {word_next4} (default: 1.0E-03)")

        if word == "transformation" and word_next is None: 
            fileo.write("...Transformations are present \n")

        if word == "number" and word_next == "of" and word_next2 == "bodies":
            fileo.write(f"\n...Number of Contact Bodies           : {word_next4} \n")

        # body number     3 is a displacement controlled rigid surface 
        if word == "body" and word_next == "number" and word_next7 == "rigid":
            fileo.write(f"...Displacement Controlled Rigid Body : {word_next2} \n")

        if word == "no" and word_next == "friction" and word_next2 == "selected":
            fileo.write("...Friction                           : OFF \n")

        if word == "separation" and word_next == "threshold" and word_next2 == "=":
            fileo.write(f"...Global Separation Threshold        : {word_next3} \n")


        if word == "contact" and word_next == "bias" and word_next2 == "factor":
            if word_next5 == "reset":
                fileo.write("...Global Bias Factor Reset to    : %s \n" % word_next8)
            else:
                fileo.write("...Global Bias Factor                 : %s \n" % word_next4)

        if word == "spline" and word_next is None:
            fileo.write("...Analytic SPLINE                    : ON \n")

        if word == "distance" and word_next6 == "considered" and word_next10 == "=":
            fileo.write("...User Contact Distance Bias         : %s \n" % word_next11)

        if word == "distance" and word_next6 == "considered" and word_next10 == "is":
            fileo.write("...Marc Contact Distance : %s \n" % word_next11)

        # rbe2
        # ---------

        if word == "rbe2" and word_next == "----------":
            fileo.write("...RBE2 Constraints Found \n")

        if word == "memory" and word_next == "increasing":
            nmemory += 1
            tmemory += float(word_next6)

        if word == "timing" and word_next == "information:":
            if ddmflag > 0:
                fileo.write("...Peak Memory (this domain) : " + pdmemory + " Mb \n")
                fileo.write("...Peak Memory (all domains) : " + word_last4 + " Mb \n")

        if word == "memory" and word_next2 == "summed":
            #TODO: sistemare
            #pdmemory = data_lines[idat-2]
            pass

        if word == "convergence" and word_next == "testing" and word_next4 == "both":
            fileo.write("...Convergence on Both Residual And Displacement \n")

        if word == "s" and word_next == "t" and word_next5 == "o":
            if debug == 1:
                fileo.write("\nStart of Increment : %s \n" % word_next16)

        if word == "out-of-core" and word_next == "matrix" and word_last5 != "estimated":
            fileo.write("...Out of Core Solver : ON \n")

        if word == "iteration" and word_next2 == "projection" and projection == 0:
            fileo.write("...WARNING: Iteration During Projection on Quadratic Segment Not Converged")
            projection = 1

        if word == "total" and word_next == "time:":
            ttime = word_next2
            #TODO: sistemare
            # ttime_min = ttime / 60.0
            # ttime_hour = ttime_min / 60.0
            # fileo.write("...Total Time for Solution : %8.2f sec" % ttime)
            # fileo.write(" : %8.2f min" % ttime_min)
            # fileo.write(" : %8.2f hour" % ttime_hour)

        # requested number of element threads************ 4
        if word == "requested" and word_next == "number" and word_next3 == "element":
            fileo.write("...Element Threads                    : %s \n" % word_next5 )

        # requested number of solver threads************* 4
        if word == "requested" and word_next == "number" and word_next3 == "solver":
            fileo.write("...Solver Threads                     : %s \n" % word_next5)
        
        if word == "integer*8" and word_next == "version":
            fileo.write("...Integer*8 Version Used \n")

        if word == "integer*4" and word_next == "version":
            fileo.write("...Integer*4 Version Used \n")

        if word == "heat" and word_next == "transfer" and word_next2 == "analysis":
            fileo.write("...Heat Transfer Analysis             : ON \n")

        if word == "elastic" and word_next == "harmonic":
            fileo.write("...Elastic Harmonic Analysis          : ON \n")

        if word == "complex" and word_next == "damping":
            fileo.write("...Complex Damping Matrix             : ON \n")

        if word == "new" and word_next2 == "input":
            fileo.write("...New Style Input                    : ON \n")
            
        if word == "electro" and word_next == "magnetic" and word_next2 == "harmonic":
            fileo.write("...ElectroMagnetic Harmonic Analysis  : ON \n")

        if word == "Marc" and word_next == "version":
            fileo.write(f"...Marc Input Version                 : {word_next4} \n")

        if word == "mesh" and word_next == "rezoning" and word_next4 == "switched":
            fileo.write("...Global Remeshing                   : ON \n")

        if word == "s" and word_next == "t" and word_next2 == "a":
            nincrement = word_next16
            if debug == 1:
                fileo.write(f"...start of increment               : {nincrement} \n")

        if word == "increment" and word_next3 == "converged" and word_next8 == "continued":
            nproceed += 1
            if debug == 1:
                fileo.write(f"...increment has not converged      : {nproceed} \n")



        # now search for specific words from the warning/error messages, store
        # the node/element numbers for later use
        #---------------------------------------------------------------------
        #                             Polyline point    174075 is separating from body       9
        #                             Required separation stress:   6.50000E-02  Current normal stress:   6.75231E-02
        #-----------------------------nodes separating
        if word == "separating" and word_next == "from" and word_last4 != "Polyline":
            if debug == 2:
                fileo.write(f"...Separation Node Found {word_last4}\n")
            # ...store each node number in an array
            selected[0].append( word_last4 )
            # ...increment counter
            nselected[0] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[0]) == int(maxnode):
                #fileo.write(f"Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass
        
        
        #--- bobbio
        # node 149642 body 2 is separating from body 9 separation force 1.35764E-03 (2017)
        # node 219672 is separating from body 7 separation force 2.80726E+02 (2015?)
        # new solution will be sought
        if word == "node" and word_next6 == "separating" and word_next8 == "body":
            if debug == 2:
                #TODO: sistemare
                #fileo.write("...Separating Node Found", data_lines[idat + 1], " Separation force", data_lines[idat + 11])
                pass
            # store each node number in an array
            selected[0].append( word_next )
            # increment counter
            nselected[0] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[0]) == int(maxnode):
                #fileo.write("Warning: MAXNODE ({}) has been exceeded - increase value to more than {}\n\n".format(maxnode, maxnode))
                pass 
                
        # insert node not converged
        if word == "if" and word_next == "node":
            if debug == 1:
                fileo.write("...INSERT Problem Node Found", word_next6)
            # store each node number in an array
            selected[1].append( word_next6 )
            # increment counter
            nselected[1] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[1]) == int(maxnode):
                #fileo.write("Warning: MAXNODE ({}) has been exceeded - increase value to more than {}\n\n".format(maxnode, maxnode))
                pass
                
        # contact node sliding along segment / being released / hitting concave edge
        # node x is sliding along body 6 from segment y to segment z
        # polygon point x is sliding along body y from segment z to segment a
        if word == "node" and word_next3 == "sliding" and word_next4 == "along":
            if debug == 1:
                #TODO: sistemare
                #fileo.write("...Contact Node Sliding Along Segment Found", data_lines[idat + 1], " Body =", data_lines[idat + 6])
                pass
            # store each node number in an array
            selected[2].append( word_next )
            # increment counter
            nselected[2] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[2]) == int(maxnode):
                #fileo.write("Warning: MAXNODE ({}) has been exceeded - increase value to more than {}\n\n".format(maxnode, maxnode))
                pass 
                
        # node x is sliding out of last segment of body y and will be released
        if word == "node" and word_next3 == "sliding" and word_next4 == "out":
            if debug == 1:
                #TODO: sistemare
                #fileo.write("...Contact Node Sliding Out of Last Segment Found", data_lines[idat + 1], " Body =", data_lines[idat + 11])
                pass
            # store each node number in an array
            selected[2].append( word_next )
            # increment counter
            nselected[2] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[2]) == int(maxnode):
                #fileo.write("Warning: MAXNODE ({}) has been exceeded - increase value to more than {}\n\n".format(maxnode, maxnode))
                pass 
                
        # node x hits concave edge on body
        if word == "node" and word_next2 == "hits":
            if debug == 1:
                #TODO : da sitemare
                #fileo.write(f"...Contact Node Hitting Concave Edge Found {data_lines[idat+1]}  Body = {data_lines[idat+8]}")
                pass
            # ...store each node number in an array
            selected[2].append( word_next )
            # ...increment counter
            nselected[2] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[2]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        # -- marco 1001-1100
        #-----------------------------contact node belonging to more than 1 body
        if word == "node" and word_next2 == "belongs" and word_next4 == "bodies":
            if debug == 1:
                #TODO: da sist
                #fileo.write(f"...Contact Node Belonging To More Than One Body: {data_lines[idat+1]}\n")
                pass
            selected[3].append( word_next )
            nselected[3] += 1
            if int(nselected[3]) == int(maxnode):
                #fileo.write(f" Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------tying node conflict

        # contact node constraints not applied due to conflict
        #*** warning: node 23641 has a boundary condition which might
        #be conflicting with glued contact
        if word == "node" and word_next2 == "has" and word_next4 == "boundary":
            #if debug == 1:
                #fileo.write(f"...Glued Contact Node With Constraint Conflict: {data_lines[idat+1]}\n")
            selected[4].append( word_next )
            nselected[4] += 1
            if int(nselected[4]) == int(maxnode):
                #fileo.write(f" Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------*** warning: contact constraints for node 30077

        #with respect to body 2 patch 1025
        #nodes 46013 46014 46015 46016
        #will not be applied due to an inconsistency with
        #the boundary conditions
        if word == "contact" and word_next == "constraints" and word_next2 == "for":
            #if debug == 1:
            #    fileo.write(f"...Contact Node With Constraint Conflict: {data_lines[idat+4]}\n")
            selected[4].append( word_next4 )
            nselected[4] += 1
            if int(nselected[4]) == int(maxnode):
                #fileo.write(f" Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------*** warning - node 5628 degree of freedom 3 was already tied in tying equation 26700

        #and cannot be prescribed anymore
        if word == "-" and word_next == "node" and word_next3 == "degree":
            #if debug == 1:
            #    fileo.write(f"...Tying Node Conflict Found {data_lines[idat+2]} DOF = {data_lines[idat+6]}\n")
            selected[4].append( word_next2  )
            nselected[4] += 1
            if int(nselected[4]) == int(maxnode):
                #fileo.write(f" Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------inside out elements

        #*** error - element inside out at element 102460 integration point 1
        #*** warning - element inside out at element 657008 it will be deactivated due to IO-DEACT parameter
        if word == "inside" and word_next == "out":
            #if debug == 6 and word_next5 == "integration":
            #    fileo.write(f"...Inside Out Element Found {data_lines[idat+4]} Gauss Point {data_lines[idat+7]}  \n")
            if debug == 6 and word_next8 == "deactivated":
                fileo.write(f"...Inside Out Element Found {word_next4} \n")

        #  simone 1100-1200
            #...store each element number in an array
            selected[5].append( word_next4 )
            #...increment counter
            nselected[5] += 1
            #...check number of words allowed has not been exceeded
            if int(nselected[5]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass
                
        #-----------------------------zero or negative principal stretch found in element 4415
        if word == "zero" and word_next3 == "principal":
            #
            if debug == 1:
                fileo.write(f"...Zero or Negative Principal Stretch Found {word_next8} \n")
            #...store each element number in an array
            selected[5].append( word_next8 )
            #...increment counter
            nselected[5] += 1
            #...check number of words allowed has not been exceeded
            if int(nselected[5]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------displacement convergence nodes
        #-----------------------------maximum displacement change at node 141 degree of freedom  2 is equal to 1.837E-01
        #-----------------------------maximum displacement increment at node 675 degree of freedom 2 is equal to 2.054E+01
        if word == "maximum" and word_next == "displacement" and word_next6 == "degree":
            if debug == 1:
                fileo.write(f"...Displacement Convergence Node Found {word_next5} \n")
            #...store each node number in an array
            selected[6].append( word_next5 )

            #...increment counter
            nselected[6] += 1
            #...check number of words allowed has not been exceeded
            if int(nselected[6]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------residual convergence nodes
        #-----------------------------maximum residual force at node   703 degree of freedom 1 is equal to 1.970E+04
        #-----------------------------maximum reaction force at node 14304 degree of freedom 2 is equal to 2.881E+05  
        if word == "maximum" and word_next == "residual" and word_next6 == "degree":
            #if debug == 6:
                #fileo.write(f"...Residual Convergence Node Found {word_next5}  Residual = {word_next13}\n")
            
            #...store each node number in an array
            #fileo.write(selected[7])
            selected[7].append( word_next5 )
            #...increment counter
            nselected[7] += 1
            #...check number of words allowed has not been exceeded
            if int(nselected[7]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------touching contact
        #-----------------------------node 1066 of body 1 is touching body 3 patch 1
        #-----------------------------the internal NURBS id is: 1
        #-----------------------------the normal vector of the patch is      0.00000    -1.00000     0.
        #-----------------------------
        #-----------------------------node 8 of body 1 is touching body 5 segment 1
        #-----------------------------the normal vector is 0.00000 1.00000
        # ----------------------------
        # node 101 of body 1 is touching body 2 segment 24
        # the retained nodes are 59 5

        if word == "node" and word_next3 == "body" and word_next6 == "touching":
            # Node Contacting Found
            #if debug == 1:
            #    fileo.write("...Node Contacting Found", data_lines[idat + 1])
            # store each node number in an array
            selected[8].append( word_next  )
            # increment counter
            nselected[8] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[8]) == int(maxnode):
                #fileo.write(f"Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n")
                pass 
                
        #  marco 1201-1300
        
        #-----------------------------bad beam section
        #*** error - element 4811 has bad cross section direction specification
        if word == "bad" and word_next == "cross" and word_next2 == "section":
            #if debug == 1:
            #    fileo.write("...Element Bad Beam Section Found", data_lines[idat-2], "\n")
            # ...store each element number in an array
            selected[9].append( [word_last4 ])
            # ...increment counter
            nselected[9] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[9]) == int(maxnode):
                #fileo.write(" Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass 
                
        #-----------------------------bad beam section
        #*** error - bad beam section number specified for element 341580
        if word == "bad" and word_next == "beam" and word_next2 == "section":
            #if debug == 1:
            #    fileo.write("...Element Bad Beam Section Found", data_lines[idat+7], "\n")
            # ...store each element number in an array
            selected[9].append( [word_next7 ])
            # ...increment counter
            nselected[9] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[9]) == int(maxnode):
                #fileo.write(" Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass
                
        #-----------------------------bad contact projection
        #iteration during projection on quadratic segment did not converge
        if word == "iteration" and word_next == "during" and word_next2 == "projection":
            #if debug == 1:
            #    fileo.write("...Warning during contact quadratic projection", data_lines[idat+13])
            # ...store each node number in an array
            selected[10].append( word_next13 )
            # ...increment counter
            nselected[10] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[10]) == int(maxnode):
                #fileo.write("Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass 
                
        #---------------------------- iterative penetration check (displacement)
        #ddu multiplied by 2.8E-01 due to large displacement value of 4.39E+00 at node 67640 dof 1
        if word == "ddu" and word_next7 == "displacement":
            #if debug == 1:
            #    fileo.write("...Iterative penetration check (displacement)", data_lines[idat+13])

            # ...store each node number in an array
            selected[11].append(  word_next13  )
            
            # ...increment counter
            nselected[11] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[11]) == int(maxnode):
                #fileo.write("Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass 
                
        #---------------------------- iterative penetration check (penetration)(NTS)
        #ddu multiplied by 2.4E-01 to avoid penetration of node 93811 into body 5 segment 112
        if word == "ddu" and word_next6 == "penetration" and word_next8 == "node":
            if debug == 1:
                fileo.write("...Iterative penetration check (penetration)", data_lines[idat+9])
            # ...store each node number in an array
            selected[12].append (  word_next9  )
            
            # ...increment counter
            nselected[12] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[12]) == int(maxnode):
                #fileo.write("Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass

        # fabio 

        if word == "node" and word_next2 == "hits":
            if debug == 1:
                fileo.write("...Contact Node Hitting Concave Edge Found", data_lines[idat+1], "Body =", data_lines[idat+8])

            print(lineas) 
            selected[2].append(  data_lines[idat+1]  )
            
            nselected[2] += 1
            if int(nselected[2]) == int(maxnode):
                #fileo.write("   Warning: MAXNODE ("+ str(maxnode)+ ") has been exceeded - increase value to more than" + str(maxnode) + "\n\n")
                pass 
                
        if word == "ddu" and word_next6 == "penetration" and word_next8 == "body":
            if debug == 1:
                fileo.write("...Iterative penetration check (penetration)", data_lines[idat+31])

            #TODO: sistemare
            #print(lineas) 

            #selected[12].append(   )
            #nselected[12] += 1

            #if int(nselected[12]) == int(maxnode):
                #fileo.write("   Warning: MAXNODE ("+ str(maxnode)+ ") has been exceeded - increase value to more than" + str(maxnode) + "\n\n")
            #    pass 
                
        if word == "too" and word_next3 == "joined":
            if debug == 1:
                fileo.write("...Too many nodes joined", data_lines[idat+6])
            
            selected[13].append(  word_next6 )
            nselected[13] += 1
            if int(nselected[13]) == int(maxnode):
                #fileo.write("   Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass 
                
        if word == "projection" and word_next2 == "node":
            if debug == 1:
                fileo.write("...projection for contact node failed", data_lines[idat+3])

            print(lineas) 
            selected[14].append( data_lines[idat+3] )
            nselected[14] += 1
            if int(nselected[14]) == int(maxnode):
                #fileo.write("   Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass 
                
        if word == "contact" and word_next6 == "indicates":
            if debug == 1:
                fileo.write("...bad rigid body orientation", data_lines[idat+13])
            
            selected[15].append( data_lines[idat+13] )
            nselected[15] += 1
            if int(nselected[15]) == int(maxnode):
                #fileo.write("   Warning: MAXNODE (", maxnode, ") has been exceeded - increase value to more than", maxnode, "\n\n")
                pass 
                
        if word == "node" and word_next2 == "separated":
            if debug == 1:
                fileo.write(f"...node separated 5 times and will be skipped {data_lines[idat+1]}")
            # store each node number in an array
            print(lineas)
            selected[16].append( data_lines[idat+1] )
            # increment counter
            nselected[16] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[16]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        # marco 
        #-----------------------------incorrect degenerated Hex elements
        # identical nodal coordinates found for:
        #   element number: 20348
        #   node numbers  : 11067     11066
        #   repeated node numbers are expected.
        if word == "incorrect" and word_next == "degenerated":
            if debug == 1:
                fileo.write(f"...incorrect degenerated hex element {data_lines[idat+11]} \n")
            # ...store each node number in an array
            
            selected[17].append( data_lines[idat+11] )
            # ...increment counter
            nselected[17] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[17]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------start of assembly   cycle number is 0
        # wall time = 4753.00
        if word == "start" and word_next2 == "assembly":
            if debug == 1:
                fileo.write(f"...start of assembly: {data_lines[idat+10]} \n")
            # ...store each assembly start time in an array
            #print(lineas)
            #TODO: controllare
            selected[18].append(  word_next7  )
            # ...increment counter
            nselected[18] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[18]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------start of matrix solution
        # wall time = 5029.00
        if word == "start" and word_next2 == "matrix":
            if debug == 1:
                fileo.write(f"...start of matrix solution: {data_lines[idat+7]} \n")
            # ...store each matrix solve start time in an array
            selected[19].append(  word_next7  )
            # ...increment counter
            nselected[19] += 1
            # ...increment number of iterations
            niterations = nselected[19]
            # ...check number of words allowed has not been exceeded
            if int(nselected[19]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------end of matrix solution
        # wall time = 9277.00
        if word == "end" and word_next2 == "matrix":
            if debug == 1:
                fileo.write(f"...end of matrix solution: {data_lines[idat+7]} \n")
            # ...store each matrix solve end time in an array
            #print(lineas)
            selected[20].append(  data_lines[idat+7]  )
            # ...increment counter
            nselected[20] += 1
            # ...check number of words allowed has not been exceeded
            if int(nselected[20]) == int(maxnode):
                #fileo.write(f" Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        #-----------------------------binary post data at increment 3. subincrement 0. on file 16
        #wall time = 1019.00
        #remeshing body 1 due to increment number

        #if word == "remeshing" and word_next == "body" and word_next5 == "increment":
        
        # simone 1500-1600
        
        if word == "remeshing" and word_next == "body" and word_next5 == "increment":
            if debug == 1:
                fileo.write(f"...start of global remeshing: {data_lines[idat-1]}")
            # store each global remeshing time in an array
            print(lineas)
            selected[21].append(  data_lines[idat-1]  )
            # increment counter
            nselected[21] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[21]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        elif word == "axisymmetric" and word_next == "element" and word_next4 == "negative":
            if debug == 1:
                fileo.write(f"...axisymmetric element: {data_lines[idat+2]} has negative radius \n")
            # store each global remeshing time in an array
            #print(lineas)
            selected[22].append( word_next2 )
            # increment counter
            nselected[22] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[22]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        elif word == "ddu" and word_next3 == "1.00000E-06" and word_next6 == "penetration":
            if debug == 1:
                fileo.write(f"...Iterative penetration check (penetration)(bad) {data_lines[idat+9]} \n")
                 
                
            # store each node number in an array
            #print(lineas)
            selected[23].append( word_next9 )
            # increment counter
            nselected[23] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[23]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
        elif word == "zero" and word_next == "length" and word_next3 == "element":
            if debug == 1:
                fileo.write(f"...Zero length element check {data_lines[idat+4]} \n")
            # store each node number in an array
            print(lineas)
            selected[24].append( word_next4 )
            # increment counter
            nselected[24] += 1
            # check number of words allowed has not been exceeded
            if int(nselected[24]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 
                
        elif word == "debug" and word_next == "printout" and word_next3 == "tying":
            if debug == 1:
                fileo.write(f"...Tying matrix debug check - tied node: {data_lines[idat+11]} \n")
            # store each INSERTED node number in an array
            selected[25].append( data_lines[idat+11] )
            # increment counter
            nselected[25] += 1
            # store the INSERT node ID
            tying[0][nselected[25]] = data_lines[idat+11]
            # store the associated host node IDs
            tying[1][nselected[25]] = data_lines[idat+14]
            tying[2][nselected[25]] = data_lines[idat+15]
            tying[3][nselected[25]] = data_lines[idat+16]
            tying[4][nselected[25]] = data_lines[idat+17]
            
            fileo.write(f"{tying[0][nselected[25]]} {tying[1][nselected[25]]} {tying[2][nselected[25]]} {tying[3][nselected[25]]} {tying[4][nselected[25]]}\n")
            
            # check number of words allowed has not been exceeded
            if int(nselected[25]) == int(maxnode):
                #fileo.write(f"   Warning: MAXNODE ({maxnode}) has been exceeded - increase value to more than {maxnode}\n\n")
                pass 

        #  marco 1601 - 1700
        
        if int(nselected[25]) == int(maxnode):
            fileo.write("   Warning: MAXNODE ({0}) has been exceeded - increase value to more than {0}\n\n".format(maxnode))

    # fileo.write("\n\t    Summary of Output Check Before Sorting:\n\n")
    # fileo.write("\tTotal Number of (unsorted) Separating Nodes Found: {0} \n".format(nselected[0]))
    # fileo.write("\tTotal Number of INSERT problem Nodes Found: {0} \n".format(nselected[1]))
    # fileo.write("\tTotal Number of Nodes Sliding/Released Along Segments or Hitting Concave Edges: {0} \n".format(nselected[2]))
    # fileo.write("\tTotal Number of Contact Nodes Belonging To More Than 1 Body: {0} \n".format(nselected[3]))
    # fileo.write("\tTotal Number of Nodes With Constraint Conflicts: {0} \n".format(nselected[4]))
    # fileo.write("\tTotal Number of Inside Out Element Found: {0} \n".format(nselected[5]))
    # fileo.write("\tTotal Number of Displacement Convergence Nodes Found: {0} \n".format(nselected[6]))
    # fileo.write("\tTotal Number of Residual Convergence Nodes Found: {0} \n".format(nselected[7]))
    # fileo.write("\tTotal Number of Touching Nodes Found: {0} \n".format(nselected[8]))
    # fileo.write("\tTotal Number of Elements Having a Bad Beam Section: {0} \n".format(nselected[9]))
    # fileo.write("\tTotal Number of Nodes with Bad Iterative Contact Projection: {0} \n".format(nselected[10]))
    # fileo.write("\tTotal Number of Iterative Penetration Checks (displacement): {0} \n".format(nselected[11]))
    # fileo.write("\tTotal Number of Iterative Penetration Checks (penetration): {0} \n".format(nselected[12]))
    # fileo.write("\tTotal Number of Nodes Joined to a Node Checks: {0} \n".format(nselected[13]))
    # fileo.write("\tTotal Projection for Contact Node Failed Checks: {0} \n".format(nselected[14]))
    # fileo.write("\tTotal Number of Bad Rigid Body Orientation Checks: {0} \n".format(nselected[15]))
    # fileo.write("\tTotal Number of Nodes Separating 5 times Checks: {0} \n".format(nselected[16]))
    # fileo.write("\tTotal Number of Incorrect Degenerated Hex Elements: {0} \n".format(nselected[17]))
    # fileo.write("\tTotal Number of Element Assemblies: {0} \n".format(nselected[18]))
    # fileo.write("\tTotal Number of Matrix Solutions: {0} \n".format(nselected[19]))
    # fileo.write("\tTotal Number of Global Remeshes: {0} \n".format(nselected[21]))
    # fileo.write("\tTotal Number of Axisymmetric Elements with Negative Radius: {0} \n".format(nselected[22]))
    # fileo.write("\tTotal Number of Iterative Penetration Checks (penetration)(bad): {0} \n".format(nselected[23]))

    # fileo.write("\tTotal Number of Zero Length Element Checks: {0} \n".format(nselected[24]))
    # fileo.write("\tTotal Number of Inserted nodes: {0} \n".format(nselected[25]))
    # # total number of increments
    # fileo.write("\tTotal Number of Increments: %s \n" % nincrement)
    # # total number of "proceed when not converged"
    # fileo.write("\tTotal Number of \"Proceed when not Converged\": %d \n" % nproceed)
    # # total number of iterations (equal to number of matrix solutions)
    # fileo.write("\tTotal Number of Iterations: %d \n" % nselected[19])

    # correct niterations if none available
    if niterations == 0:
        niterations = 1

    #---------------------------------------------------------------------
    # print a summary of the time taken in the assembly, solve and recovery 
    # stages of the analysis 
    #---------------------------------------------------------------------
    # loop over each set of element/node lists
    for imode in range(maxcol):
        # extract number of items for this set of messages
        nmode_items = nselected[imode]

        # global remeshing time (not working since no remesh end time yet)
        # remeshing body 1 due to increment number
        if imode == 21:
            # initialise total time spent in this phase
            ttime_g = 0.0
            for atime in range(nmode_items):
                # print list of remeshing times
                dtime = selected[18][atime] - selected[imode][atime]


                # simone 1700-1800

                #INDENTARE
                if timing == 1:
                    atime_next = atime + 1
                    # printf ("\tRemeshing #%4d: Time = %10.4f\n","$atime_next","$dtime");
                ttime_g += dtime
                
        #-----------------------------assembly time
        if imode == 180:
            # initialise total time spent in this phase
            ttime_a = 0.0
            fileo.write("\n")
            for atime in range(nmode_items):
                # extract assembly time for each iteration
                # print(selected[imode+1] , selected[imode] )
                dtime = float(selected[imode+1][atime]) - float(selected[imode][atime])

                # ignore if negative since this means that there 
                # is not a finishing end of increment timing (the 
                # result of running this script on an unfinished 
                # output file
                if dtime > 0:
                    atime_next = atime + 1
                    # print list of assembly times
                    if timing == 1:
                        fileo.write(f"\tAssembly #{atime_next}: Time = {dtime:10.4f}")
                    # accumulate time spent in assembly phase
                    ttime_a += dtime
            # percentage time taken of total in this phase
            # ttime won't be available if the analysis has 
            # not finished
            tpercent = 0.0
            if ttime :
                print(ttime_a,ttime)
                
                tpercent = (ttime_a * 100.0) / ttime
                
            fileo.write("\n	    Summary of Timings:\n\n")
            fileo.write(f"\tTotal Time Spent in Element Assembly:\t{ttime_a:10.4f} ({tpercent:10.2f}%)")

        #-----------------------------matrix solution time
        if imode == 190:
            # initialise total time spent in this phase
            ttime_m = 0.0
            fileo.write("\n")
            for atime in range(nmode_items):
                # extract assembly time for each iteration
                #TODO: to be fixed
                if atime <9 :
                    dtime = float(selected[20][atime]) - float(selected[imode][atime])
                # ignore if negative since this means that there 
                # is not a finishing end of increment timing (the 
                # result of running this script on an unfinished 
                # output file
                if dtime > 0:
                    atime_next = atime + 1
                    # print list of matrix solution times
                    if timing == 1:
                        fileo.write(f"\tMatrix Solution #{atime_next}: Time = {dtime:10.4f}")
                    # accumulate time spent in matrix solution phase
                    ttime_m += dtime
            # percentage time taken of total in this phase
            tpercent = 0
            if ttime :  # None if analysis is not completed
                tpercent = (ttime_m * 100.0) / ttime
            fileo.write(f"\tTotal Time Spent in Matrix Solution:\t{ttime_m:10.4f} ({tpercent:10.2f}%)")

        #-----------------------------recovery time
        if imode == 200:
            # initialise total time spent in this phase
            ttime_r = 0.0
            fileo.write("\n")
            for atime in range(nmode_items):
                # recovery time is from end of matrix to 
                # next assembly - that needs special 
                # handling for the last recovery phase
                #TODO: da fissare
                if atime <9 and ttime is not None:
                    dtime = float(ttime) - float(selected[imode][atime])
                nmode_pen = nmode_items - 1
                if atime < nmode_pen:
                    #TODO: da fissare
                    if atime <8 :
                        dtime = float(selected[18][atime+1]) - float(selected[imode][atime])

                #marco da 1801 1900

                
                atime_next = atime + 1
                if timing == 1:
                    fileo.write(f"\tRecovery #{atime_next}: Time = {dtime:.4f}")
                
                ttime_r += dtime
            
            tpercent = 0.0
            if ttime is not None :  # None if not completed
                tpercent = (ttime_r*100.0)/ttime
            fileo.write(f"\tTotal Time Spent in Stress Recovery:\t{ttime_r:.4f} ({tpercent:.2f}%)")

            ttime_elt = ttime_r + ttime_a

            tpercent = 0.0
            if ttime :  # None if not completed
                tpercent = (ttime_elt*100.0)/ttime
            fileo.write(f"\n\tTotal Time Spent in Element Loops:\t{ttime_elt:.4f} ({tpercent:.2f}%)")

            ttime_iterative = 0.0
            if ttime:
                ttime_iterative = ttime/niterations
            fileo.write(f"\n\tAverage Time For Each Iteration:\t{ttime_iterative:.4f}")

    if resflag == 1:
        fileo.write("\n\nScanning output files only was requested - now stopping")
        #exit(3)

    for imode in range(maxcol):
        
        if debug == 1:
            fileo.write(f"\n IMODE: {imode}") 
        
        #if imode==6:
        #    print(selected[6])
            
        if nselected[imode] > 0:
            # print("--", imode, selected[imode])
            # my_list = list(set(selected[imode]))
           
            for item1 in selected[imode]:
                if item1 not in selected_sorted[imode]:
                    selected_sorted[imode].append(item1)
        
                    
            #selected_sorted[imode][0] = selected[imode][0]
            #for unsorted in range(nselected[imode]):
            #    foundit = 0
            #    for sorted1 in range(nselected_sorted[imode]):
            #        #fileo.write(len(selected_sorted[imode]),sorted1, len(selected[imode]),unsorted)
            #        #if unsorted >9:
            #        #    break 
            #        if selected_sorted[imode][sorted1] == selected[imode][unsorted]:
            #            foundit = 1
            #            if debug == 1:
            #                fileo.write(f"\n found it: {selected_sorted[imode][sorted1]} - {foundit}")
            #    if foundit == 0:
            #        if unsorted < 9:
            #            selected_sorted[imode][nselected_sorted[imode]] = selected[imode][unsorted]
            #            nselected_sorted[imode] += 1
            #            if debug == 1:
            #                fileo.write(f"\n adding to sorted list: {selected_sorted[imode][nselected_sorted[imode]]} - {foundit}")
        
        nselected_sorted[imode] = len(selected_sorted[imode]) 


    # simone 1900 - 2000
    #---------------------------------------------------------------------
    # print a summary list of the number of sorted nodes/elements 
    # associated with each of the warning/error messages searched for
    #---------------------------------------------------------------------

    fileo.write("\n\n\t    Summary of Output Check After Sorting:\n")
    #                             nodes separating
    fileo.write(f"\n\tTotal Number of Separating Nodes Found: {nselected_sorted[0]} \n")
    #                             insert node problem found
    fileo.write(f"\tTotal Number of INSERT problem Nodes Found: {nselected_sorted[1]} \n")
    #                             contact node sliding along segment
    fileo.write(f"\tTotal Number of Nodes Sliding/Released Along Segments or Hitting Concave Edges: {nselected_sorted[2]} \n")
    #                             contact node belonging to more than 1 body
    fileo.write(f"\tTotal Number of Contact Nodes Belonging To More Than 1 Body: {nselected_sorted[3]} \n")
    #                             contact node constraint conflict
    fileo.write(f"\tTotal Number of Nodes With Constraint Conflicts: {nselected_sorted[4]} \n")
    #                             inside out elements
    fileo.write(f"\tTotal Number of Inside Out Element Found: {nselected_sorted[5]} \n")
    #                             displacement convergence nodes
    fileo.write(f"\tTotal Number of Displacement Convergence Nodes Found: {nselected_sorted[6]} \n")
    #                             residual convergence nodes
    fileo.write(f"\tTotal Number of Residual Convergence Nodes Found: {nselected_sorted[7]} \n")
    #                             contact with nurbs
    fileo.write(f"\tTotal Number of Touching Nodes Found: {nselected_sorted[8]} \n")
    #                             bad beam section
    fileo.write(f"\tTotal Number of Elements Having a Bad Beam Section: {nselected_sorted[9]} \n")
    #                             bad iterative contact projection
    fileo.write(f"\tTotal Number of Nodes with Bad Iterative Contact Projection: {nselected_sorted[10]} \n")
    #                             bad iterative penetration check (displacement)
    fileo.write(f"\tTotal Number of Iterative Penetration Checks (displacement): {nselected_sorted[11]} \n")
    #                             bad iterative penetration check (penetration)
    fileo.write(f"\tTotal Number of Iterative Penetration Checks (penetration): {nselected_sorted[12]} \n")
    #                             number of nodes joined to a node 
    fileo.write(f"\tTotal Number of Nodes Joined to a Node Checks: {nselected_sorted[13]} \n")
    #                             projection for contact node failed 
    fileo.write(f"\tTotal Projection for Contact Node Failed Checks: {nselected_sorted[14]} \n")
    #                             bad rigid body orientation
    fileo.write(f"\tTotal Number of Bad Rigid Body Orientation Checks: {nselected_sorted[15]} \n")
    #                             node separated 5 times and will be skipped 
    fileo.write(f"\tTotal Number of Nodes Separating 5 times Checks: {nselected_sorted[16]} \n")
    #                             incorrect degenerated hex elements
    fileo.write(f"\tTotal Number of Incorrect Degenerated Hex Elements: {nselected[17]} \n")
    #                             total number of element assemblies
    fileo.write(f"\tTotal Number of Element Assemblies: {nselected[18]} \n")
    #                             total number of matrix solutions
    fileo.write(f"\tTotal Number of Matrix Solutions: {nselected[19]} \n")
    #                             total number of remeshes
    fileo.write(f"\tTotal Number of Global Remeshes: {nselected_sorted[21]} \n")
    #                             axisymmetric element has negative radius
    fileo.write(f"\tTotal Number of Axisymmetric Elements with Negative Radius: {nselected_sorted[22]} \n")
    #                             bad iterative penetration check (penetration)
    fileo.write(f"\tTotal Number of Iterative Penetration Checks (penetration)(bad): {nselected_sorted[23]} \n")
    #                             zero length
    fileo.write(f"\tTotal Number of Zero Length Element Checks: {nselected_sorted[24]} \n")
    #                             debug tying messages
    fileo.write(f"\tTotal Number of Inserted nodes: {nselected_sorted[25]} \n")

    #---------------------------------------------------------------------
    # print general command to mentat proc file
    #---------------------------------------------------------------------

    # print("----",selected_sorted[6])

    if guiflag == 1:
        # turn off echoes
        DATA.write("*command_group_begin\n")
        DATA.write("*set_proc_echo off\n")
        DATA.write("*py_echo off\n")
        
        # loop over each set of element/node lists and write commands to the session file to create a SET/GROUP
        for imode in range(maxcol):
            # extract number of items for this set of messages
            nmode_items = nselected_sorted[imode]
            # don't process the timing data
            if nmode_items > 0 and imode not in [18, 19, 20, 21]:
                # remove any previously created set
                DATA.write("*remove_set_entries\n")
                DATA.write(f"{messages[imode]}\n")
                DATA.write("all_existing\n")
                # appropriate mentat command to select elements
                if imode in [5, 9, 17, 22, 24]:
                    # elements directly associated with this set of messages
                    DATA.write("*select_clear\n")
                    DATA.write("*select_elements\n")
                # appropriate mentat command to select surfaces
                elif imode == 15:
                    # surfaces associated with this set of messages
                    DATA.write("*select_clear\n")
                    DATA.write("*select_faces\n")

                elif imode == 25:

                    # marco 2000 - fine
                    pass 
                    
                    #print inserted node to the external tying file
                    #print {$TYING} "$selected_sorted[$imode][$itie1] \n";
                    #for itie1 in range(nmode_items):
                        #for itie2 in range(nmode_items+1):
                            #fileo.write(f"{itie1}: {selected_sorted[imode][itie1]}")
                            #fileo.write(f"{itie2}: {tying[0][itie2]}")
                            #fileo.write(f"{tying[0][itie2]} {tying[1][itie2]} {tying[2][itie2]} {tying[3][itie2]} {tying[4][itie2]}")
                            #if selected_sorted[imode][itie1] == tying[0][itie2]:
                                # print host nodes to the external tying file
                                #TYING.write(f"{tying[0][itie2]} {tying[1][itie2]} {tying[2][itie2]} {tying[3][itie2]} {tying[4][itie2]}\n")
                    
                else:
                    # nodes were selected with this set of
                    # messages, so select the elements
                    # associated with these nodes instead
                    DATA.write("*select_clear\n")
                    DATA.write("*select_elements_nodes\n")
                
                    for nelts in range(nmode_items):
                        # print list of nodes/elements to results
                        # proc file
                        #if imode == 6:
                        #    print("--",imode,selected_sorted[imode][nelts])
                        DATA.write(f"{selected_sorted[imode][nelts]}\n")
                
                # print mentat command to proc file
                DATA.write("# | End of List\n")
                # store the selected elements into a
                # temporary group
                DATA.write(f"*store_elements {messages[imode]}\n")
                DATA.write("all_selected\n")
            
        DATA.write("*command_group_end\n")

    #-----------------------------loop over each set of element/node lists
    else:   # qui per Patran

        DATA.write( "gu_fit_view(  )\n")
        #and write commands to the session file
        #to create a SET/GROUP
        for imode in range(maxcol):
            # extract number of items for this set of
            # messages
            nmode_items = nselected_sorted[imode]
            # don't do messages without node or elements lists (CHANGE)
            if nmode_items > 0 and imode not in [18, 19, 20, 21]:
                # remove any previously created set
                DATA.write("sys_poll_option( 2 )\n")
                DATA.write(f"bv_group_clear(\"{messages[imode]}\" )\n")
                DATA.write("sys_poll_option( 0 )\n")
                #-----------------------------appropriate patran command to select
                #                             elements directly (CHANGE)
                if imode in [5, 9, 17, 22]:
                    #                             elements associated with this set of
                    #                             messages
                    DATA.write("sys_poll_option( 2 )\n")
                    DATA.write(f"ga_group_create( \"{messages[imode]}\" )\n")
                    DATA.write(f"ga_group_entity_add( \"{messages[imode]}\", @\n")
                    DATA.write("\"Elm ")
                else:
                    #                             nodes were selected with this set of
                    #                             messages, so select the elements
                    #                             associated with these nodes instead
                    DATA.write("STRING _elem_list[VIRTUAL]\n")
                    DATA.write("list_create_elem_ass_node( 0, \"Node ")
                    
                #----------------------------print list of elements to results session file
                for nelts in range(nmode_items):
                    DATA.write(f"{selected_sorted[imode][nelts]} //@ \n")
            
                #-----------------------------commands to finish off the element lists (CHANGE)
                if imode in [5, 9, 17, 22]:
                    DATA.write("\") \n")
                    DATA.write("sys_poll_option( 0 ) \n")
                else:
                    DATA.write("\", \"lista\", _elem_list )\n")
                    DATA.write("sys_poll_option( 0 ) \n")
                    DATA.write("sys_poll_option( 2 )\n")
                    DATA.write(f"ga_group_create( \"{messages[imode]}\" )\n")
                    DATA.write(f"ga_group_entity_add( \"{messages[imode]}\", _elem_list) \n")
            
    #-----------------------------print main header
    fileo.write("\n\n\n-----------------------------------------\n")
    fileo.write("------- OUTPUT File Check END -----------\n")
    fileo.write("-----------------------------------------\n\n")

    #                             close mentat proc file
    DATA.close()
    #DATA_res.close()
    #DATA_res.close()

    #                             sound a bell on finish
    #fileo.write("\a")

    ## Python trim function to remove whitespace from the start and end of the string
    #def trim(string):
    #    return string.strip()
    #
    ## Left trim function to remove leading whitespace
    #def ltrim(string):
    #    return string.lstrip()
    #
    ## Right trim function to remove trailing whitespace
    #def rtrim(string):
    #    return string.rstrip()


    fileo.close()

    #outfile
    try:
        #creatnig a copy of the python report
        shutil.copy(filename_out, outfile.replace(".out","_python.txt"))
    except:
        print("no copy")
    return 

if __name__ == '__main__':

    #TODO: an idea could be to mantain the possibility to run it from shell


    main()
    
    print("Done")