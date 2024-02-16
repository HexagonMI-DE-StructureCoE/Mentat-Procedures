import numpy as np
import tables as tb
import math

print('\n HDF5 Results File Processing')
print(' ----------------------------\n')

file = "gear_failure_small_job1.h5"

print(' HDF5 file being used: ', file)

with tb.open_file(file, 'a') as hdf:
    ls = [node._v_name for node in hdf.root]
    print(' : List of items: \t', ls)

    ls = [node._v_name for node in hdf.root._f_list_nodes()]
    print(' : List of datasets: \t', ls)

    ls = [node for node in hdf.root]
    print(' : List of values: \t', ls)

    dsetm = hdf.root.Marc
    print(' : Marc dataset:\t', dsetm)
    print(' : Main dataset name:\t', dsetm._v_name)

    g1 = hdf.get_node('/Marc')

    print(' : Sub-Groups in Marc (summary):\t', list(g1._f_list_nodes()))
    print(' : Sub-Groups in Marc (details):\t', [(node._v_name, node) for node in g1._f_iter_nodes()])

    print(' : Dataset groups (top level):')
    for name in dsetm:
        print('   - ', name)

    print(' : Dataset Attributes (top level):')
    for attr in dsetm._v_attrs._f_list():
        print(f"   - {attr}\t- {getattr(dsetm._v_attrs, attr)}")

    print(' : Group/Dataset Hierarchy:')
    for node in hdf.walk_nodes():
        print('   -', node._v_pathname)
        try:
            d1 = node.shape
            print('     | Data shape:\t', node.shape)
            print('     | # Dimensions:\t', node.ndim)
            print('     | Data type:\t', node.dtype)
            print('     | # Bytes:\t\t', node.nbytes)
        except AttributeError:
            pass

        icount = 0
        for k in node._v_attrs._f_list():
            icount += 1
            label = k
            print('     | label attribute ', icount, ':\t', label)
            value = getattr(node._v_attrs, k)
            print('     | value attribute ', icount, ':\t', value)

    precision = g1._v_attrs['precision']

    if precision[0] == 0:
        prec = 'Single'
    elif precision[0] == 1:
        prec = 'Double'

    print(' : H5 File precision:\t', prec)

    if precision[0] == 0:
        dtype_int = 'i4'
        dtype_float = 'float32'
    elif precision[0] == 1:
        dtype_int = 'i8'
        dtype_float = 'float64'

    s = np.array(g1.Summary.read())
    print('\n Analysis Summary:')

    ninc = s.shape[0]
    print('\n Number of increments: ', ninc - 1)

    for i in range(0, ninc - 1):
        print(f'  Inc: {s[i][0]:4} Iterations: {s[i][4]:3} Separations: {s[i][5]:2} Time: {s[i][15]:.6f}')

    print('\n Model Summary:')

    print('   Job Name:\t\t\t', g1._v_attrs['title'])

    gs = hdf.get_node('/Marc/Input/Analysis Data')

    print('   # Model Statistics:\t\t', gs.shape[0])

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

    print('\n Model Results:')

    gd = hdf.get_node('/Marc/Results/Node')

    disp = np.array(gd.Displacement.read())

    # print('  Postcode: ', gd._v_attrs['postcode'])
    # print('  User_post_label: ', gd._v_attrs['user_post_label'])

    nnode = disp.shape[0]
    ndof = disp.shape[1]

    ninc = disp.shape[2]

    print('  # Nodes:\t', nnode)
    print('  # DoF:\t', ndof)
    print('  # Increments:\t', ninc - 1)

    Resultant = np.zeros((nnode, 1, ninc, 1, 1, 1, 1))

    for i in range(0, ninc):
        i += 1

        for k in range(0, nnode):
            k += 1

            x = disp[k - 1, 0, i - 1, 0, 0, 0, 0]
            y = disp[k - 1, 1, i - 1, 0, 0, 0, 0]

            mag = math.sqrt(x * x + y * y)
            Resultant[k - 1, 0, i - 1, 0, 0, 0, 0] = mag

    g3 = hdf.get_node('/Marc/Results/Node')
    node_post_summary = np.array(hdf.get_node('/Marc/Results/Node/Node Post Summary'))

    npcode = node_post_summary.shape[0]
    print(' Node Post Summary:')
    print('  # Post Codes:\t\t\t', node_post_summary.shape[0])
    print('  # Postcode details:\t\t', node_post_summary.shape[1])
    print('  # Increments:\t\t\t', node_post_summary.shape[2])
    print('  # Sets:\t\t\t', node_post_summary.shape[3])
    print('  # Real/Imaginary Results:\t', node_post_summary.shape[4])
    print('  # Iterations:\t\t', node_post_summary.shape[5])
    print('  # Nodal post codes:\t', npcode)

    for i in range(0, npcode - 1):
        print('    - Post Code:\t', node_post_summary[i][0][0][0][0][0][0])

        print('      : # DoFs\t\t :', node_post_summary[i][2][0][0][0][0][0])

    npsize = node_post_summary.shape[1]

    iuser = 0
    for i in range(0, npcode):

        pclabel = node_post_summary[i][0][0][0][0][0][0]

        if pclabel == -1:
            iuser = 1

    print(' Node_Post_Summary Shape: ', node_post_summary.shape)

    user_postcode = np.zeros((1, npsize, ninc, 1, 1, 1, 1))

    user_postcode[0, 0, 0:ninc, 0, 0, 0, 0] = -1

    user_postcode[0, 2, 0:ninc, 0, 0, 0, 0] = 1

    if iuser == 0:
        node_post_summary = np.append(node_post_summary, user_postcode, axis=0)
        print('\n  No user result detected - Appending new results')

    if '/Marc/Results/Node/Resultant' in hdf:
        hdf.remove_node('/Marc/Results/Node/Resultant', recursive=True)
        print('\n  Old user result deleted...Resultant')

    dset = hdf.create_carray('/Marc/Results/Node', 'Resultant', atom=tb.Float64Atom(), shape=Resultant.shape)
    dset[:] = Resultant
    print('\n  New user result created...Resultant')

    user_post = [-1]
    dset.attrs['postcode'] = user_post
    user_pst_lb = 'Resultant'

    tid = tb.StringAtom(itemsize=len(user_pst_lb))
    dset.attrs['user_post_label'] = user_pst_lb
    # dset.attrs.create('user_post_label', user_pst_lb, atom=tid)

    hdf.remove_node('/Marc/Results/Node/Node Post Summary', recursive=True)
    dset = hdf.create_carray('/Marc/Results/Node', 'Node Post Summary', atom=tb.Int32Atom(),
                             shape=node_post_summary.shape)
    dset[:] = node_post_summary

print('\n HDF5 Results File Processing End')
print(' ----------------------------------\n')


