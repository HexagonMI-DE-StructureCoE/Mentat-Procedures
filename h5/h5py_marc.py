# ---------------------------------------------------------------------
# description
# script to evaluate displacement resultant and then write as a new
# user-defined result to the h5 file
#
# it also serves as an example of extracting various dataset, group
# and results from the h5 dataset
#
# usage
# open CMD shell in same folder as h5 file and then type:
#   python py_displacement_resultant.py gearpair_hdf_job1.h5
#
# Notes:
# an important resource is the h5py module that is used to read the
# h5 file. some useful documentation can be found here:
#  https://docs.h5py.org/en/stable/quick.html#quick
#
# The xml template is stored in the mentat development folder:
#     ...\source\marc\hdf\schema\Marc_2021.3.xml
#
# with the implementation of file locking, the library uses the status_
# flags field in the superblock to mark a file as in writing or SWMR
# writing mode when a file is opened. The library will clear this field
# when the file closes. However, a situation may occur where an open
# file is closed without going through the normal library file closing
# procedure, and this field will not be cleared as a result. An example
# would be if an application program crashed. This situation will
# prevent a user from opening the file. The h5clear tool will clear the
# status_flags field. To use, open a CMD shell in the following folder
# and type:
# c:\yourpath\mentat\python\win8664\bin\h5clear-shared.exe -s h5file.h5
#
# ---------------------------------------------------------------------
import numpy as np
import h5py
import math
import sys

#
print('\n HDF5 Results File Processing')
print(' ----------------------------\n')
# specify h5 results file
if len(sys.argv) > 1:
    file = sys.argv[1]
else:
    file = input("Enter HDF5 file : ")
    
# inform user of h5 file to be used
print(' HDF5 file being used: ', file)

# open the h5 results file with hdf specified
# as the object - (a)ppend mode)
# : in conjunction with a with-statement,
#   myfile.close() will be called automatically
#   when python leaves the with-statement
with h5py.File(file, 'a') as hdf:
    #
    # ---------------------------------------------------------------------
    # high level commands to interrogate the h5 file
    # ---------------------------------------------------------------------
    #
    # list items in the h5 file
    # : .items is a standard python object
    #   operator
    ls = list(hdf.items())
    print(' : List of items: \t', ls)
    # list of datasets in the h5 file
    # : .keys is a standard python object
    #   operator
    ls = list(hdf.keys())
    print(' : List of datasets: \t', ls)
    #
    ls = list(hdf.values())
    print(' : List of values: \t', ls)
    # define and print the top hdf5 dataset
    # object
    dsetm = hdf['/Marc']
    print(' : Marc dataset:\t', dsetm)
    print(' : Main dataset name:\t', dsetm.name)
    # define and print the top hdf5 dataset
    # object (alternative)
    # define object for the "marc" group
    # : defined at the top of the xml template
    #   file as:   <group name="Marc">
    g1 = hdf.get('Marc')
    # extract a summary list of sub-groups in
    # the h5 file
    print(' : Sub-Groups in Marc (summary):\t', list(g1.keys()))
    # extract a fuller list of the sub-groups
    # in the h5 file (with members)
    print(' : Sub-Groups in Marc (details):\t', list(g1.items()))
    # print dataset groups available
    print(' : Dataset groups (top level):')
    for name in dsetm:
        print('   - ', name)
    # print attributes associated with dataset
    print(' : Dataset Attributes (top level):')
    for k in dsetm.attrs.keys():
        print(f"   - {k}\t- {dsetm.attrs[k][0]}")
    # h5py object
    print(' : h5py object:\t', h5py.Dataset)
    # traverse all groups in main dataset
    keys = []
    hdf.visit(lambda key: keys.append(key))
    print(' : Group/Dataset Hierarchy:')
    # print group name
    for name in keys:
        print('   -', name)
        dset = hdf[name]
        #
        try:
            d1 = dset.shape
        except:
            d1 = 0
        else:
            print('     | Data shape:\t', dset.shape)
            print('     | # Dimensions:\t', dset.ndim)
            print('     | Data type:\t', dset.dtype)
            print('     | # Bytes:\t\t', dset.nbytes)
        # print attributes associated with each
        # group if present
        icount = 0
        for k in dset.attrs.keys():
            icount += 1
            label = k
            print('     | label attribute ', icount, ':\t', label)
            value = dset.attrs[k][0]
            print('     | value attribute ', icount, ':\t', value)
    #
    # ---------------------------------------------------------------------
    # evaluate and process the precision of the h5 file
    # 0 = Single Precision
    # 1 = Double Precision
    #
    # this is from the following the main "Marc" attribute section of the
    # xml file:
    #
    # <group name="Marc">
    # <attribute name="version" type="string" description="Marc HDF5 Schema Version"/>
    # <attribute name="analysis_class" type="integer" description="0 : Structural,">
    #      1 : Thermal / Structural,
    #      4 : Current / Thermal,
    #      ...
    #       35: Thermal / Diffusion (Concentration) / Structural
    #  </attribute>
    #  <attribute name="precision" type="integer" description="0:Single Precision, 1:Double Precision"/>
    #  <attribute name="title" type="string" description="Analysis Title"/>
    # ---------------------------------------------------------------------
    #
    # extract the 'precision' attribute for
    # the h5 file. corresponding line in xml is...
    # : <attribute name="precision" type="integer" description="0:Single Precision, 1:Double Precision"/>
    precision = g1.attrs.get('precision')
    # it could be single or double precision
    if precision[0] == 0:
        prec = 'Single'
    elif precision[0] == 1:
        prec = 'Double'
    # inform user
    print(' : H5 File precision:\t', prec)
    # set data types based on precision for
    # later use
    if precision[0] == 0:
        dtype_int = 'i4'
        dtype_float = 'float32'
    elif precision[0] == 1:
        dtype_int = 'i8'
        dtype_float = 'float64'
    #
    # ---------------------------------------------------------------------
    # extract a summary of the h5 result file data
    #
    # the data is described in the following section described by the
    # template xml file
    #
    # <dataset name="Summary" type="Compound">
    #   <dim 0="Increment ID"/>
    #   <dim 1="Data" size="16">
    #     <column  0 name="INC"       type="integer"        description="Increment ID; -1 indicates end of analysis"/>
    #     <column  1 name="SUBINC"    type="integer"        description="Sub-Increment ID"/>
    #     <column  2 name="ITERTN"    type="integer"        description="Iteration ID"/>
    #     <column  3 name="CASE"      type="integer"        description="Loadcase No"/>
    #     <column  4 name="CYCL_INC"  type="integer"        description="# Cycles for Increment"/>
    #     <column  5 name="SEPA_INC"  type="integer"        description="# Separations for Increment"/>
    #     <column  6 name="CUT_INC"   type="integer"        description="# Cutbacks for Increment"/>
    #     <column  7 name="CYCL_TOT"  type="integer"        description="# Total Cycles"/>
    #     <column  8 name="SEPA_TOT"  type="integer"        description="# Total Separations"/>
    #     <column  9 name="CUT_TOT"   type="integer"        description="# Total Cutbacks"/>
    #     <column 10 name="RMESH"     type="integer"        description="Mesh ID"/>
    #     <column 11 name="DEACT"     type="integer"        description="Deactivation ID"/>
    #     <column 12 name="CONT_GEOM" type="integer"        description="Contact Geometry ID"/>
    #     <column 13 name="ANALFLAG"  type="integer"        description="Analysis Type Flag"/>
    #     <column 14 name="TIME_INC"  type="floating-point" description="Timestep for Increment"/>
    #     <column 15 name="TIME_TOT"  type="floating-point" description="Total Time of Job"/>
    #     <column 16 name="TITLE"     type="string"         description="Loadcase Title" length="70"/>
    # ---------------------------------------------------------------------
    #
    # define the summary object from the
    # dataset name = "Summary"
    s = np.array(g1.get('Summary'))
    print('\n Analysis Summary:')
    # extract the number of increments
    # : adjust for zero-based arrays
    ninc = s.shape[0]
    print('\n Number of increments: ', ninc - 1)
    # print some of the analysis statistics
    # the ":4" etc. are standard python print
    # modifiers to align the output
    for i in range(0, ninc - 1):
        print(f'  Inc: {s[i][0]:4} Iterations: {s[i][4]:3} Separations: {s[i][5]:2} Time: {s[i][15]:.6f}')
    #
    # ---------------------------------------------------------------------
    # extract and print the model summary details
    # ---------------------------------------------------------------------
    #
    # print header for section
    print('\n Model Summary:')
    # print h5 job name
    print('   Job Name:\t\t\t', g1.attrs.get('title'))
    # extract initial model statistics
    # : does not account for remeshing changes
    gs = hdf.get('Marc/Input/Analysis Data')
    # print statistics
    # : .shape returns the size - in this case
    #   the number of statistics available
    print('   # Model Statistics:\t\t', gs.shape[0])
    # : gs[] returns the contents
    print('   # Element Post Codes:\t', gs[0, 0, 0])
    print('   Initial # Nodes:\t\t', gs[1, 0, 0])
    print('   Initial # Element Elements:\t', gs[2, 0, 0])
    print('   # DoF per Node:\t\t', gs[3, 0, 0])
    print('   Max # IPs:\t\t\t', gs[4, 0, 0])
    print('   # Coordinates per Node:\t', gs[8, 0, 0])
    print('   Max # Nodes per Element:\t', gs[9, 0, 0])
    print('   # Transformations:\t\t', gs[12, 0, 0])
    print('   # DDM domains:\t\t', gs[13, 0, 0])
    print('   # Distributed Loads:\t\t', gs[14, 0, 0])
    print('   # Springs:\t\t\t', gs[16, 0, 0])
    print('   # Contact Bodies\t\t', gs[17, 0, 0])
    print('   Value?:\t\t\t', gs.shape[1])
    print('   Mesh ID?:\t\t\t', gs.shape[2])
    #
    # ---------------------------------------------------------------------
    # process displacement results
    # the h5 "Displacement" result object is requested - the xml file shows
    # the format of these results:
    #  :  <group name="Node">
    #     <dataset name="Nodal_Result_Quantity_Name" ndims="7 { -1,3,-1,-1,-1,2,-1}" description="Appendix Table 2">
    #       <attribute name="postcode" type="integer" description="Appendix Table 2"/>
    #       <attribute name="user_post_label" type="string" description="User or Default Post Code Label"/>
    #       <dim 0="Node List"/>
    #       <dim 1="Result Value" size="Ndim"/>
    #       <dim 2="Increment ID"/>
    #       <dim 3="Set ID"/>
    #       <dim 4="Sub-increment ID"/>
    #       <dim 5="Real-Imag Values"/>
    #       <dim 6="Iteration ID"/>
    #
    # the "Nodal_Result_Quantity_Name" is specified as the nodal result
    # name that is required - the names possible are given in the list
    # from appendix table 2. in this case it is "Displacement" - it is
    # case sensitive
    # ---------------------------------------------------------------------
    #
    # header for section
    print('\n Model Results:')
    # define object pointing to the nodal
    # displacement section of the h5 file
    gd = hdf.get('Marc/Results/Node')
    # create an array using numpy from the
    # h5 "displacement" result object
    disp = np.array(gd.get('Displacement'))
    # print result attributes ?????
    print('  Postcode: ', gd.attrs.get('postcode'))
    print('  User_post_label: ', gd.attrs.get('user_post_label'))
    # extract some summary details
    # : this is the maximum dimension of the
    #   nodal vector - and so accounts for
    #   remeshing
    nnode = disp.shape[0]
    ndof = disp.shape[1]
    # : adjust because of zero-based vectors
    ninc = disp.shape[2]
    # inform user
    print('  # Nodes:\t', nnode)
    print('  # DoF:\t', ndof)
    print('  # Increments:\t', ninc - 1)
    # create and populate an array of the
    # same shape as "disp" with resultant
    # displacement values
    Resultant = np.zeros((nnode, 1, ninc, 1, 1, 1, 1))
    #
    # -----------------------------loop over increments
    for i in range(0, ninc):
        i += 1
        # -----------------------------loop over nodes
        for k in range(0, nnode):
            k += 1
            # extract x/y-displacements
            x = disp[k - 1, 0, i - 1, 0, 0, 0, 0]
            y = disp[k - 1, 1, i - 1, 0, 0, 0, 0]
            # evaluate resultant and store
            mag = math.sqrt(x * x + y * y)
            Resultant[k - 1, 0, i - 1, 0, 0, 0, 0] = mag
    #
    # ---------------------------------------------------------------------
    # extract and print nodal result details
    # ---------------------------------------------------------------------
    #
    # define object pointing to the nodal
    # results summary
    g3 = hdf.get('Marc/Results/Node')
    node_post_summary = np.array(g3.get('Node Post Summary'))
    # the following 3 print statement variables
    # come from the following "dimx" sections
    # of the xml file:
    #   <group name="Node">
    #     <dataset name="Node Post Summary" type="integer" ndims="7 { -1,5,-1,-1,-1,2,-1}">
    #       <dim 0="List of Nodal Post Codes"/>
    #       <dim 1="Value" size="5">
    #         ...
    #       <dim 2="Increment ID"/>
    #       <dim 3="Set ID"/>
    #       <dim 4="Sub-increment ID"/>
    #       <dim 5="Real-Imag Values"/>
    #       <dim 6="Iteration ID"/>
    # extract the number of nodal post codes
    # available in the h5 file
    npcode = node_post_summary.shape[0]
    print(' Node_Post_Summary:')
    print('  # Post Codes:\t\t\t', node_post_summary.shape[0])
    print('  # Postcode details:\t\t', node_post_summary.shape[1])
    print('  # Increments:\t\t\t', node_post_summary.shape[2])
    print('  # Sets:\t\t\t', node_post_summary.shape[3])
    print('  # Real/Imaginary Results:\t', node_post_summary.shape[4])
    print('  # Iterations:\t\t', node_post_summary.shape[5])
    print('  # Nodal post codes:\t', npcode)
    #
    # -----------------------------loop over the post codes and list them
    for i in range(0, npcode - 1):
        print('    - Post Code:\t', node_post_summary[i][0][0][0][0][0][0])
        # access the secondary data as given in the
        # following xml Node section - in this case,
        # the number of DoFs associated with each
        # post code from sub-column 2:
        #   <column 0 description="Nodal Postcode" description="Appendix Table 2"/>
        #     column1 is the same as dim1
        #   <column 1 description="0:Scalar 1:Vector (used only for UPSTNO_HDF)"/>
        #   <column 2 description="Number of components"/>
        #   <column 3 description="0:Global XYZ 1:Shell Top-Middle-Bottom 2:List eg.1,2,3 (used only for UPSTNO_HDF)"/>
        #   <column 4 description="0:default 1:modal 2:buckle 3:harmonic real 4:harmonic real/imaginary 5:harmonic magnitude/phase"/>
        print('      : # DoFs\t\t :', node_post_summary[i][2][0][0][0][0][0])
    # extract size of secondary data for
    # later use
    npsize = node_post_summary.shape[1]
    #
    # ---------------------------------------------------------------------
    # check whether there are any duplicate post codes in the dataset -
    # this means that this script has been run before and a further entry
    # has been made in to the post summary dataset, which needs to be
    # removed. it is not sufficient to simply delete the dataset as per
    # the line below: del hdf['/Marc/Results/Node/Resultant']
    # ---------------------------------------------------------------------
    #
    # -----------------------------loop over the post codes
    iuser = 0
    for i in range(0, npcode):
        # extract result post codes - a "-1"
        # represents a user post code
        pclabel = node_post_summary[i][0][0][0][0][0][0]
        #
        if pclabel == -1:
            # set flag to indicate that a user result
            # is already present
            iuser = 1
    # inform user of overall node post
    # summary dimensions
    print(' Node_Post_Summary Shape: ', node_post_summary.shape)
    #
    # ---------------------------------------------------------------------
    # add user defined nodal post code to Node Post Summary
    # ---------------------------------------------------------------------
    #
    # define new array of the same shape as
    # defined in the xml template:
    # <dataset name="Nodal_Result_Quantity_Name" ndims="7 { -1,3,-1,-1,-1,2,-1}" description="Appendix Table 2">
    user_postcode = np.zeros((1, npsize, ninc, 1, 1, 1, 1))
    # define the user post code as "1" in
    # the 3rd field for all increments - there
    # is only 1 result being created
    # : the "-" denotes a user field
    user_postcode[0, 0, 0:ninc, 0, 0, 0, 0] = -1
    # define the number of Dofs
    user_postcode[0, 2, 0:ninc, 0, 0, 0, 0] = 1
    # append new node post summary
    if iuser == 0:
        node_post_summary = np.append(node_post_summary, user_postcode, axis=0)
        print('\n  No user result detected - Appending new results')
    # delete user results from the dataset if
    # present:
    if '/Marc/Results/Node/Resultant' in hdf:
        del hdf['/Marc/Results/Node/Resultant']
        print('\n  Old user result deleted...Resultant')
    # write new user defined nodal results
    # to new "Resultant" dataset
    dset = hdf.create_dataset('/Marc/Results/Node/Resultant', dtype=dtype_float, data=Resultant)
    print('\n  New user result created...Resultant')
    # add post code value attribute to the
    # Resultant dataset
    user_post = [-1]
    dset.attrs.create('postcode', user_post, dtype=dtype_int)
    # create new postcode result label
    user_pst_lb = 'Resultant'
    # create a typed null-terminated
    # fixed-length string (C_S1) using h5t
    # : FORTRAN_S1 = Zero padded fixed-length string
    # : VARIABLE = Variable-length string
    tid = h5py.h5t.TypeID.copy(h5py.h5t.C_S1)
    # set the size of the string to match that
    # of the new postcode label
    tid.set_size(len(user_pst_lb))
    # create the postcode label as an attribute
    # of this dataset
    # : changing user_post_label to anything
    #   other than 'user_post_label' will crash
    #   Mentat when trying to access results
    dset.attrs.create('user_post_label', user_pst_lb, None, tid)
    # delete old node post summary from h5
    del hdf['Marc/Results/Node/Node Post Summary']
    # create new node post summary updated
    # with user postcode
    dset = hdf.create_dataset('/Marc/Results/Node/Node Post Summary', dtype=dtype_int, data=node_post_summary)
#
print('\n HDF5 Results File Processing End')
print(' ----------------------------------\n')
