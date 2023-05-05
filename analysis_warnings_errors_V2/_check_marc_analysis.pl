#!/usr/bin/perl
#---------------------------------------------------------------------
# Description
# Perl script to search through a marc output file and extract the 
# nodes or elements associated with common warnings or errors
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
#   perl   this_script   output_file   gui_flag   ddm_flag   result_flag
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
#    c:\path_to_perl\perl.exe _check_marc_analysis.pl outputfile.out   1   0   0
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
#       This was created using perl v5.8.8,and the binary build was 
#       provided by ActiveState http://www.ActiveState.com
#
# to get a listing of what is found during the reading of the output
# file, set $debug=1 below
#
#---------------------------------------------------------------------
#
#use strict;
#use warnings;

#-----------------------------print main header
print "\n\n\n-----------------------------------------\n";
print "------- OUTPUT File Check START ---------\n";
print "-----------------------------------------\n\n";
#
#---------------------------------------------------------------------
# initialise variables
#---------------------------------------------------------------------
#                             ...word counter
my $i = 0;
#                             ...loadcase counter
my $continue = 0;
#                             ...number of memory increases
my $nmemory = 0;
#                             ...total memory increase
my $tmemory = 0;
#                             ...peak domain memory usage
my $pdmemory = 0;
#                             ...first pass flag for iterative projection 
#                                warning
my $projection = 0;
#                             ...output file counter for ddm
my $nfile = 0;
#                             ...debug flag (CHANGE)
my $debug=99;
#                             ...print warning/errors found (CHANGE)
my $iprint=0;
#                             ...maximum nunber of warning/error message 
#                                types to be search for (CHANGE)
my $maxcol = 26;
#                             ...maximum number of words in output file (CHANGE)
my $maxsel = 90000000;
#                             ...maximum number of nodes/elements to 
#                                be found (CHANGE)
my $maxnode = 1000000;
#                             ...detailed timing flag (CHANGE)
#                                0 = no details of assembly, solution and recovery per iteration (only summary)
#                                1 = print details
my $timing = 0;
#                             ...output filename specified
my $outfile;
#                             ...flag to determine whether proc or ses 
#                                file to be created
my $guiflag;
#                             ...flag to indicate multiple output files 
#                                from ddm
my $ddmflag;
#                             ...flag to indicate whether to create 
#                                groups/sets or not
my $resflag;
#                             ...total time for solution
my $ttime;
#                                assembly
my $ttime_a;
#                                matrix solution
my $ttime_m;
#                                recovery
my $ttime_r;
#                                global remeshing
my $ttime_g;
#                             ...percentage time taken in each phase
my $tpercent;
#                             ...total number of iterations in analysis
my $niterations;
#                             ...total number of increments in analysis
my $nincrement;
#                             ...total number of continues if not converged
my $nproceed = 0;
#                             ...flag to ignore certain types of 
#                                longwinded warnings
my $nowarning = 0;
#                             ...handle to ses/proc file to be created
my $DATA;
#                             ...handle to debug tying file to be created
my $TYING;
#                             ...list of all words in the output file(s)
my @dataitem = ((0) x $maxsel);
#                             ...selected variable counter - initialised
#                                to zero
my @nselected = ((0) x $maxcol);
#                             ...unselected variable counter - initialised
#                                to zero
my @nselected_sorted = ((1) x $maxcol);
#                             ...sorted 2d array (CHANGE)
#                                if maxcol is CHANGEd, then add/remove 
#                                another array and its reference here
my @sorted0 = ((1) x $maxnode);
my @sorted1 = ((1) x $maxnode);
my @sorted2 = ((1) x $maxnode);
my @sorted3 = ((1) x $maxnode);
my @sorted4 = ((1) x $maxnode);
my @sorted5 = ((1) x $maxnode);
my @sorted6 = ((1) x $maxnode);
my @sorted7 = ((1) x $maxnode);
my @sorted8 = ((1) x $maxnode);
my @sorted9 = ((1) x $maxnode);
my @sorted10= ((1) x $maxnode);
my @sorted11= ((1) x $maxnode);
my @sorted12= ((1) x $maxnode);
my @sorted13= ((1) x $maxnode);
my @sorted14= ((1) x $maxnode);
my @sorted15= ((1) x $maxnode);
my @sorted16= ((1) x $maxnode);
my @sorted17= ((1) x $maxnode);
my @sorted18= ((1) x $maxnode);
my @sorted19= ((1) x $maxnode);
my @sorted20= ((1) x $maxnode);
my @sorted21= ((1) x $maxnode);
my @sorted22= ((1) x $maxnode);
my @sorted23= ((1) x $maxnode);
my @sorted24= ((1) x $maxnode);
my @sorted25= ((1) x $maxnode);
#                             ...populate (CHANGE)
my @selected_sorted = (\@sorted0,\@sorted1,\@sorted2,\@sorted3,\@sorted4,\@sorted5,\@sorted6,\@sorted7,\@sorted8,\@sorted9,\@sorted10,\@sorted11,\@sorted12,\@sorted13,\@sorted14,\@sorted15,\@sorted16,\@sorted17,\@sorted18,\@sorted19,\@sorted20,\@sorted21,\@sorted22,\@sorted23,\@sorted24,\@sorted25);
#                             ...unsorted 2d array (CHANGE)
my @unsorted0 = ((0) x $maxnode);
my @unsorted1 = ((0) x $maxnode);
my @unsorted2 = ((0) x $maxnode);
my @unsorted3 = ((0) x $maxnode);
my @unsorted4 = ((0) x $maxnode);
my @unsorted5 = ((0) x $maxnode);
my @unsorted6 = ((0) x $maxnode);
my @unsorted7 = ((0) x $maxnode);
my @unsorted8 = ((0) x $maxnode);
my @unsorted9 = ((0) x $maxnode);
my @unsorted10 = ((0) x $maxnode);
my @unsorted11 = ((0) x $maxnode);
my @unsorted12 = ((0) x $maxnode);
my @unsorted13 = ((0) x $maxnode);
my @unsorted14 = ((0) x $maxnode);
my @unsorted15 = ((0) x $maxnode);
my @unsorted16 = ((0) x $maxnode);
my @unsorted17 = ((0) x $maxnode);
my @unsorted18 = ((0) x $maxnode);
my @unsorted19 = ((0) x $maxnode);
my @unsorted20 = ((0) x $maxnode);
my @unsorted21 = ((0) x $maxnode);
my @unsorted22 = ((0) x $maxnode);
my @unsorted23 = ((0) x $maxnode);
my @unsorted24 = ((0) x $maxnode);
my @unsorted25 = ((0) x $maxnode);
#                             ...populate
my @selected = (\@unsorted0,\@unsorted1,\@unsorted2,\@unsorted3,\@unsorted4,\@unsorted5,\@unsorted6,\@unsorted7,\@unsorted8,\@unsorted9,\@unsorted10,\@unsorted11,\@unsorted12,\@unsorted13,\@unsorted14,\@unsorted15,\@unsorted16,\@unsorted17,\@unsorted18,\@unsorted19,\@unsorted20,\@unsorted21,\@unsorted22,\@unsorted23,\@unsorted24);
#                             ...message vector
#                                if maxcol is CHANGEd, then add/remove 
#                                appropriate message here
my @messages = ("_separating", "_inserts", "_sliding", "_contact_belonging", "_dof_conflict", "_inside_out", "_disp_convergence", "_res_convergence", "_contacting_nodes", "_bad_beams","_bad_projection","_iterative_penetration_d","_iterative_penetration_p","_nodes_joined_to_nodes","_bad_contact_projection","_bad_rigid_orientation","_separated_5_times","_bad_degenerate_hex","_assembly_start","_matrix_start","_matrix_end","_global_remeshing","_neg_axisymmetric_node","_IPC_small","_zero_length","_tying_debug");
#
my @tying;
#                             declare subroutines
sub trim($);
sub ltrim($);
sub rtrim($);
#                             extract command line parameters
$outfile = shift(@ARGV) ;
$guiflag = shift(@ARGV) ;
$ddmflag = shift(@ARGV) ;
$ddmflag = int($ddmflag);
$resflag = shift(@ARGV) ;
#-----------------------------checks on input parameters
#                             ...outfile has been specified
if ( index ($outfile, "out") eq -1)
{
  print "\nOutput file has not defined correctly (the extension is required)\n";
  print "  See instructions at top of perl script for usage details\n\n";
  exit 3;
}
#                             ...guiflag is defined
if ( $guiflag <1 or $guiflag>2)
{
  print "\nGUI flag is not defined: Specify 1 (mentat) or 2 (patran) on the command line)\n";
  print "  See instructions at top of perl script for usage details\n\n";
  exit 3;
}
#---------------------------------------------------------------------
# loop over number of processors used to concatenate the output files
# together
#---------------------------------------------------------------------
if ( $ddmflag > 0)
{
#                             remove previous concatenated results
  unlink ("check_analysis.out");
#                             remove preceding "1,2,3" etc to get base name
  my $base_name = substr($outfile, 1);
#                             open temporary outfile for appending
  open (my $outfile_ddm, ">>check_analysis.out")
    or die "Could not open file: check_analysis.out  ($!)";
#-----------------------------loop over each ddm output file and
#                             write contents to ddm output file
  for (my $iddm = 1; $iddm <=$ddmflag; $iddm++)
  {
    my $next_name = $iddm . "$base_name";
    print "\nConcatenating output file: ",$next_name," into check_analysis.out";
#                             open output file for reading
    open ( my $datafile_ddm, "<", "$next_name")
      or die "Could not open file: ",$next_name,"  ($!)";
#                             write contents of next output file to 
#                             ddm output file
    while ( my $line = <$datafile_ddm> ) 
    {
      print $outfile_ddm $line;
    }
#                             close next output file
    close ($datafile_ddm);
  }
}
#                             inform user about output file name used
#                             depending on the ddm flag
if ( $ddmflag <=0 )
{
  print "\n\nDDM flag is not defined    : single output file will be searched: ",$outfile,"\n";
}
else
{
  print "\n\nFile Name to Process       : check_analysis.out\n";
  print "                             concatenated from *",$outfile," ddm files\n";
}

if ( $ddmflag >0 )
{
#                             redefine output file as newly 
#                             concatenated file
  $outfile = "check_analysis.out";
}
#                             open output file (name from runtime argument 
#                             list or concatenated file for ddm runs)
open(my $datafile, "$outfile")
      or die "\n\nCould not open file: ",$outfile,"  ($!)\n";

#---------------------------------------------------------------------
# print summary of input information
#---------------------------------------------------------------------

if( $ddmflag > 0)
{
  print "GUI chosen                 : $guiflag (1=mentat / 2=patran)\n";
  print "Number of Processors used  : $ddmflag \n\n";
}
else
{
  print "GUI chosen                 : $guiflag (1=mentat / 2=patran)\n\n";
}
#                             open results file 
#                             ...mentat proc file
if( $guiflag == 1)
{
  open ($DATA, ">check_analysis.proc");
  print "GUI commands will be written to check_analysis.proc\n";
#                             ...additional output for tying debug 
#                                messages if required
  open ($TYING, ">check_analysis_tying");
  print "Debug TYING commands will be written to check_analysis_tying.proc\n";
}
#                             ...patran ses file
else
{
  open ($DATA, ">check_analysis.ses");
  print "GUI commands will be written to check_analysis.ses\n";
}

#---------------------------------------------------------------------
# loop over all the lines in the file and store the data locally
#---------------------------------------------------------------------
#
print "\nLooping over output file to create a list of keywords\n";
print "  Any errors or warnings will also be printed....\n\n";
#
while (<$datafile>)
{
#-----------------------------search for warning and error messages
  my $start_file = index($_, "version: Marc");
  if ($start_file >0)
  {
    $nfile = $nfile + 1;
    print "\nStart of Output File for Domain # ",$nfile,"\n";
  }
#                             errors
# my $error = index($_, "error");
# if ($error >0)
# {
#   my $dummy = $_ ;
#   print "   error: ", ltrim($dummy);
# }

#                             errors
  my $error = index($_, "*** error");
  if ($error >0)
  {
    my $dummy = $_ ;
    if ($iprint >0)
    {
      print "   error: ", ltrim($dummy);
    }
  }

#                             warnings
  my $warning = index($_, "warning");
  if ($warning >0)
  {
    my $dummy = $_ ;
    my $dummy2 = $_ ;
#                             specify warning messages to be ignored here
    for my $dummy2(split)
    {
      if ($dummy2 eq "interdomain")
      {
        $nowarning = $nowarning + 1
      }
    }
    if ($nowarning eq 0 )
    {
      if ($iprint >0)
      {
        print "   warning: ", ltrim($dummy);
      }
    }
  }
#                             warnings
  $warning = index($_, " words failed");
  if ($warning >0)
  {
    my $dummy = $_ ;
      print "   warning: ", ltrim($dummy);
  }
#                             loop over the number of words in this 
#                             line (split on basis of spaces)
  for my $word(split)
  {
#                             ...store word in array
    $dataitem[$i] = $word;
#                             ...increment word counter
    $i++;
#                             check number of words allowed has not 
#                             been exceeded
    if (int($i) == int($maxsel))
    {
      print "   Warning: MAXSEL ($maxsel) has been exceeded - increase this value \n\n" ;
    }
#
    if ($word eq "continue")
    {
      $continue = $continue + 1
    }
  }
}
#                             close file
close($datafile);
#                             store and print number of words found
my $nitems = $i;
print "\nNumber of Words in File        : $nitems \n";
#                             print number of loadcases
if ($ddmflag > 0)
{
  print "Number of Loadcases            : ", $continue/$ddmflag, "\n";
}
else
{
  print "Number of Loadcases            : $continue \n";
}

#                             error and stop if output file not found
if ($nitems == 0 )
{
  print "No OUTPUT file found. Check:\n" ;
  print "   a) The output file is in the same directory as this perl script\n" ;
  print "   b) The output file exists\n" ;
  exit 2 ;
}

#                             reinitialise domain file counter
$nfile=0;

#---------------------------------------------------------------------
# loop over number of words in data file, search for specific 
# keywords to print a summary of some overall analysis settings
#---------------------------------------------------------------------
#
for (my $idat = 0; $idat <$nitems; $idat++)
{
#                             extract data item
#                             ...current
  my $word = $dataitem[$idat];
#                             ...next(s)
  my $word_next   = $dataitem[$idat+1];
  my $word_next2  = $dataitem[$idat+2];
  my $word_next3  = $dataitem[$idat+3];
  my $word_next4  = $dataitem[$idat+4];
  my $word_next5  = $dataitem[$idat+5];
  my $word_next6  = $dataitem[$idat+6];
  my $word_next7  = $dataitem[$idat+7];
  my $word_next8  = $dataitem[$idat+8];
  my $word_next10 = $dataitem[$idat+10];
  my $word_next11 = $dataitem[$idat+11];
  my $word_next16 = $dataitem[$idat+16];
#                             ...last
  my $word_last  = $dataitem[$idat-1];
  my $word_last4 = $dataitem[$idat-4];
  my $word_last5 = $dataitem[$idat-5];
#
  if ($word eq "version:" & $word_next eq "Marc")
  {
#                             initialise variables for each domain
    $nmemory    = 0 ;
    $tmemory    = 0 ;
    $projection = 0 ;
#                             increment domain number
    $nfile = $nfile + 1;
    print "\nStart of Output File for Domain # ",$nfile,"\n";
  }
#-----------------------------check for global PARAMETER commands

#                             version:  Marc 2014.0.0, Build 282796  build date: Mon Jul 21 20:26:04 2014
  if ($word eq "version:" & $word_next eq "Marc")
  {
    print "...Marc Version                       : $word_next2 \n";
  }

#                             machine type: Windows
  if ($word eq "machine" & $word_next eq "type:")
  {
    print "...Machine Type                       : $word_next2 \n";
  }
             
  if ($word eq "sizing" & $word_next5 eq "elements")
  {
    print "...Number of Elements                 : $dataitem[$idat+2] \n";
    print "...Number of Nodes                    : $dataitem[$idat+3] \n";
    print "...Number of DOFs Constrained         : $dataitem[$idat+4] \n";
  }

  if ($word eq "element" & $word_next eq "type" & $word_next2 eq "requested*************************")
  {
    print "...Element Type                       : $word_next3 \n";
  }

  if ($word eq "number" & $word_next2 eq "elements" & $word_next4 eq "mesh*********************")
  {
    print "...Number of Elements                 : $word_next5 \n";
  }

  if ($word eq "number" & $word_next2 eq "nodes" & $word_next4 eq "mesh************************")
  {
    print "...Number of Nodes                    : $word_next5 \n";
  }

  if ($word eq "Youngs" & $word_next eq "modulus")
  {
    print "...Youngs Modulus                     : $word_next2 \n";
  }

  if ($word eq "Poissons" & $word_next eq "ratio")
  {
    print "   Poissons Ratio                     : $word_next2 \n";
  }

#                             mass density - heat transfer 1.79000E+03 0
  if ($word eq "mass" & $word_next eq "density" & $word_next3 eq "heat")
  {
    print "...Density                            : $word_next5 \n";
  }

  if ($word eq "Coefficient" & $word_next2 eq "thermal")
  {
    print "   Thermal Expansion Coeff.           : $word_next4 \n";
  }

  if ($word eq "Yield" & $word_next eq "stress")
  {
    print "   Yield Stress                       : $word_next2 \n";
  }

#                             flag for element storage (ielsto)  0
  if ($word eq "flag" & $word_next2 eq "element" & $word_next3 eq "storage")
  {
    print "...Out of Core Element Storage Flag   : $word_next5 \n";
  }

#                             include interlaminar shear for thick shells/beams
  if ($word eq "interlaminar" & $word_next eq "shear" & $word_next2 eq "for")
  {
    print "...Interlaminar Shear for Shells/Beams: ON \n";
  }

  if ($word eq "number" & $word_next eq "of" & $word_next2 eq "processors")
  {
    print "...Number of Processors used          : $word_next5 \n";
  }

  if ($word eq "element" & $word_next eq "type" & $word_next3 eq "")
  {
    print "...Element Topology                   : $word_next3 $word_next4 \n";
  }

  if ($word eq "large" & $word_next eq "displacement" & $word_next2 eq "analysis")
  {
    print "...Large Displacement                 : ON \n"
  }

  if ($word eq "geometry" & $word_next eq "updated")
  {
    print "...Updated Lagrange                   : ON \n"
  }

  if ($word eq "constant" & $word_next eq "dilatation")
  {
    print "...Constant Dilatation                : ON \n"
  }

  if ($word eq "plasticity" & $word_next eq "3")
  {
    print "...Additive Plasticity                : ON \n"
  }

  if ($word eq "plasticity" & $word_next eq "5")
  {
    print "...Multiplicative Plasticity          : ON \n"
  }

#                             number of element groups used:         2
#                             group     # elements     element type     material  formulation#
#                                1      242688           139                1         UAF
#                                2       54500           139                2         UAF

  if ($word eq "number" & $word_next2 eq "element" & $word_next3 eq "groups")
  {
    for (my $ig=0; $ig<$word_next5; $ig++)
    {
      $ip = $idat+17+5*$ig;
      $iq = $idat+13+5*$ig;
      print "...Formulation for Group              : #$dataitem[$iq] = $dataitem[$ip] \n";
    }
  }

             
  if ($word eq "dynamic" & $word_next eq (/^-?\d+$/))
  {
    print "...Dynamic                            : ON \n"
  }

  if ($word eq "solver" & $word_next eq "----------")
  {
    print "...$word_next2 $word_next3 is used \n";
  }

  if ($word eq "work" & $word_next eq "hard")
  {
    print "...Work Hardening                     : ON \n"
  }

  if ($word eq "mechanical" & $word_next eq "convergence")
  {
    print "...Tolerance for Iterative Solver     : $word_next4 (default: 1.0E-03) \n"
  }

  if ($word eq "transformation" & $word_next eq "----------")
  {
    print "...Transformations are present \n"
  }

  if ($word eq "number" & $word_next eq "of" & $word_next2 eq "bodies")
  {
    print "...Number of Contact Bodies           : $word_next4 \n"
  }

#                             body number     3 is a displacement controlled rigid surface 
  if ($word eq "body" & $word_next eq "number" & $word_next7 eq "rigid")
  {
    print "...Displacement Controlled Rigid Body : $word_next2 \n"
  }


  if ($word eq "no" & $word_next eq "friction" & $word_next2 eq "selected")
  {
    print "...Friction                           : OFF \n"
  }

  if ($word eq "separation" & $word_next eq "threshold" & $word_next2 eq "=")
  {
    print "...Global Separation Threshold        : $word_next3 \n"
  }

  if ($word eq "contact" & $word_next eq "bias" & $word_next2 eq "factor")
  {
    if ($word_next5 eq "reset")
    {
      print "...Global Bias Factor Reset to        : $word_next8 \n"
    }
    else
    {
      print "...Global Bias Factor                 : $word_next4 \n"
    }
  }

  if ($word eq "spline" & $word_next eq "----------")
  {
    print "...Analytic SPLINE                    : ON \n"
  }

  if ($word eq "distance" & $word_next6 eq "considered" & $word_next10 eq "=")
  {
    print "...User Contact Distance Bias         : $word_next11 \n"
  }

  if ($word eq "distance" & $word_next6 eq "considered" & $word_next10 eq "is")
  {
    print "...Marc Contact Distance              : $word_next11 \n";
  }

#                             rbe2                                                                                                                                                            
#                             ----------
  if ($word eq "rbe2" & $word_next eq "----------")
  {
    print "...RBE2 Constraints Found              \n";
  }

             
  if ($word eq "memory" & $word_next eq "increasing")
  {
    $nmemory = $nmemory + 1;
    $tmemory = $tmemory + $word_next6;
  }

  if ($word eq "timing" & $word_next eq "information:")
  {
    if( $ddmflag > 0)
    {
      print "...Peak Memory (this domain)          : $pdmemory Mb \n" ;
    }
    print "...Peak Memory (all domains)          : $dataitem[$idat-2] Mb \n" ;
  }

  if ($word eq "memory" & $word_next2 eq "summed")
  {
    $pdmemory = $dataitem[$idat-2] ;
  }  

  if ($word eq "convergence" & $word_next eq "testing" & $word_next4 eq "both")
  {
    print "...Convergence on Both Residual And Displacement \n"
  }

  if ($word eq "s" & $word_next eq "t" & $word_next5 eq "o")
  {
    if ($debug == 1)
    {
      print "\nStart of Increment                  : $word_next16 \n";
    }
  }

  if ($word eq "out-of-core" & $word_next eq "matrix" & $word_last5 ne "estimated")
  {
    print "...Out of Core Solver                 : ON \n";
  }

  if ($word eq "iteration" & $word_next2 eq "projection" & $projection eq 0)
  {
    print "...WARNING: Iteration During Projection on Quadratic Segment Not Converged \n";
    $projection = 1;
  }

  if ($word eq "total" & $word_next eq "time:")
  {
    $ttime = $word_next2;
    my $ttime_min  = $ttime/60.0;
    my $ttime_hour = $ttime_min/60.0;
    printf "...Total Time for Solution            : %8.2f sec  \n", "$ttime";
    printf "                                      : %8.2f min  \n", "$ttime_min";
    printf "                                      : %8.2f hour \n", "$ttime_hour";
  }

#                             requested number of element threads************ 4
  if ($word eq "requested" & $word_next eq "number" & $word_next3 eq "element")
  {
    print "...Element Threads                    : $word_next5 \n";
  }
#                             requested number of solver threads************* 4
  if ($word eq "requested" & $word_next eq "number" & $word_next3 eq "solver")
  {
    print "...Solver Threads                     : $word_next5 \n";
  }

#                             integer*8 version
  if ($word eq "integer*8" & $word_next eq "version")
  {
    print "...Integer*8 Version Used \n";
  }

#                             integer*4 version
  if ($word eq "integer*4" & $word_next eq "version")
  {
    print "...Integer*4 Version Used \n";
  }

#                             heat transfer analysis,  extrapolation flag, ** 1
  if ($word eq "heat" & $word_next eq "transfer" & $word_next2 eq "analysis")
  {
    print "...Heat Transfer Analysis             : ON \n";
  }

#                             elastic harmonic response option is flagged****
  if ($word eq "elastic" & $word_next eq "harmonic")
  {
    print "...Elastic Harmonic Analysis          : ON \n";
  }

#                             complex damping matrix will be used************
  if ($word eq "complex" & $word_next eq "damping")
  {
    print "...Complex Damping Matrix             : ON \n";
  }

#                             new style input format will be used************
  if ($word eq "new" & $word_next2 eq "input")
  {
    print "...New Style Input                    : ON \n";
  }

#                             electro magnetic harmonic analysis flagged ****
  if ($word eq "electro" & $word_next eq "magnetic" & $word_next2 eq "harmonic")
  {
    print "...ElectroMagnetic Harmonic Analysis  : ON \n";
  }

#                     Marc input version ****************************        11
  if ($word eq "Marc" & $word_next eq "version")
  {
    print "...Marc Input Version                 : $word_next4 \n";
  }

#                             mesh rezoning option is switched on************
  if ($word eq "mesh" & $word_next eq "rezoning" & $word_next4 eq "switched")
  {
    print "...Global Remeshing                   : ON \n";
  }

#                             s t a r t   o f    i n c r e m e n t
  if ($word eq "s" & $word_next eq "t" & $word_next2 eq "a")
  {
    $nincrement = $word_next16;
#
    if ($debug == 1)
    {
      print "...start of increment               : $nincrement \n";
    }
  }

#                                          increment has not converged but analysis will be continued
  if ($word eq "increment" & $word_next3 eq "converged" & $word_next8 eq "continued")
  {
    $nproceed++;
#
    if ($debug == 1)
    {
      print "...increment has not converged      : $nproceed \n";
    }
  }

#---------------------------------------------------------------------
# now search for specific words from the warning/error messages, store
# the node/element numbers for later use
#---------------------------------------------------------------------
#                             Polyline point    174075 is separating from body       9
#                             Required separation stress:   6.50000E-02  Current normal stress:   6.75231E-02
#-----------------------------nodes separating
  if ($word eq "separating" & $word_next eq "from" & $word_last4 ne "Polyline")
  {
#
    if ($debug == 2)
    {
      print "...Separation Node Found $dataitem[$idat-4]  \n";
    }
#                             ...store each node number in an array
    $selected[0][$nselected[0]] = $dataitem[$idat-4];
#                             ...increment counter
    $nselected[0]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[0]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#                               node    149642 body 2 is separating from body 9 separation force 1.35764E-03 (2017)
#-------------------------------node    219672 is separating from body    7 separation force    2.80726E+02 (2015?)
#                               new solution will be sought
  if ($word eq "node" & $word_next6 eq "separating" & $word_next8 eq "body")
  {
#
    if ($debug == 2)
    {
      print "...Separating Node Found $dataitem[$idat+1]  Separation force $dataitem[$idat+11]  \n";
    }
#                             ...store each node number in an array
    $selected[0][$nselected[0]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[0]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[0]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------insert node not converged
  if ($word eq "if" & $word_next eq "node")
  {
#
    if ($debug == 1)
    {
      print "...INSERT Problem Node Found $dataitem[$idat+6]  \n";
    }
#                             ...store each node number in an array
    $selected[1][$nselected[1]] = $dataitem[$idat+6];
#                             ...increment counter
    $nselected[1]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[1]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }
#-----------------------------contact node sliding along segment / being released / hitting concave edge
#                             node x is sliding along body 6 from segment y to segment z
#                             polygon point x is sliding along body y from segment z to segment a
  if ($word eq "node" & $word_next3 eq "sliding" & $word_next4 eq "along")
  {
#
    if ($debug == 1)
    {
      print "...Contact Node Sliding Along Segment Found $dataitem[$idat+1]  Body = $dataitem[$idat+6]  \n";
    }
#                             ...store each node number in an array
    $selected[2][$nselected[2]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[2]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[2]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------node x is sliding out of last segment of body y and will be released
  if ($word eq "node" & $word_next3 eq "sliding" & $word_next4 eq "out")
  {
#
    if ($debug == 1)
    {
      print "...Contact Node Sliding Out of Last Segment Found $dataitem[$idat+1]  Body = $dataitem[$idat+11]  \n";
    }
#                             ...store each node number in an array
    $selected[2][$nselected[2]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[2]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[2]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------node x hits concave edge on body y between segment z and segment a
  if ($word eq "node" & $word_next2 eq "hits")
  {
#
    if ($debug == 1)
    {
      print "...Contact Node Hitting Concave Edge Found $dataitem[$idat+1]  Body = $dataitem[$idat+8]  \n";
    }
#                             ...store each node number in an array
    $selected[2][$nselected[2]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[2]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[2]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------contact node belonging to more than 1 body
  if ($word eq "node" & $word_next2 eq "belongs" & $word_next4 eq "bodies")
  {
#
    if ($debug == 1)
    {
      print "...Contact Node Belonging To More Than One Body: $dataitem[$idat+1]\n";
    }
#                             ...store each node number in an array
    $selected[3][$nselected[3]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[3]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[3]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------tying node conflict
#                             contact node constraints not applied due to conflict
#                              *** warning: node      23641 has a boundary condition which might 
#                                  be conflicting with glued contact
#
  if ($word eq "node" & $word_next2 eq "has" & $word_next4 eq "boundary")
  {
#
    if ($debug == 1)
    {
      print "...Glued Contact Node With Constraint Conflict: $dataitem[$idat+1]\n";
    }
#                             ...store each node number in an array
    $selected[4][$nselected[4]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[4]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[4]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------*** warning: contact constraints for node      30077
#                                 with respect to body    2 patch       1025
#                                 nodes      46013     46014     46015     46016
#                                 will not be applied due to an inconsistency with 
#                                 the boundary conditions
  if ($word eq "contact" & $word_next eq "constraints" & $word_next2 eq "for")
  {
#
    if ($debug == 1)
    {
      print "...Contact Node With Constraint Conflict: $dataitem[$idat+4]\n";
    }
#                             ...store each node number in an array
    $selected[4][$nselected[4]] = $dataitem[$idat+4];
#                             ...increment counter
    $nselected[4]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[4]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------*** warning - node 5628 degree of freedom 3 was already tied in tying equation 26700
#                                 and cannot be prescribed anymore
  if ($word eq "-" & $word_next eq "node" & $word_next3 eq "degree")
  {
#
    if ($debug == 1)
    {
      print "...Tying Node Conflict Found $dataitem[$idat+2]  DOF = $dataitem[$idat+6]  \n";
    }
#                             ...store each node number in an array
    $selected[4][$nselected[4]] = $dataitem[$idat+2];
#                             ...increment counter
    $nselected[4]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[4]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------inside out elements
#                               *** error - element inside out at element 102460 integration point  1
#                               *** warning - element inside out at element 657008 it will be deactivated due to IO-DEACT parameter
  if ($word eq "inside" & $word_next eq "out")
  {
#
    if ($debug eq 6 & $word_next5 eq "integration")
    {
      print "...Inside Out Element Found $dataitem[$idat+4]  Gauss Point $dataitem[$idat+7]  \n";
    }
    if ($debug eq 6 & $word_next8 eq "deactivated")
    {
      print "...Inside Out Element Found $dataitem[$idat+4] \n";
    }
#                             ...store each element number in an array
    $selected[5][$nselected[5]] = $dataitem[$idat+4];
#                             ...increment counter
    $nselected[5]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[5]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------zero or negative principal stretch found in element 4415
  if ($word eq "zero" & $word_next3 eq "principal")
  {
#
    if ($debug eq 1)
    {
      print "...Zero or Negative Principal Stretch Found $dataitem[$idat+8] \n";
    }
#                             ...store each element number in an array
    $selected[5][$nselected[5]] = $dataitem[$idat+8];
#                             ...increment counter
    $nselected[5]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[5]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------displacement convergence nodes
#                             maximum displacement change at node 141 degree of freedom  2 is equal to 1.837E-01
#                             maximum displacement increment at node 675 degree of freedom 2 is equal to 2.054E+01
  if ($word eq "maximum" & $word_next eq "displacement" & $word_next6 eq "degree")
  {
#
    if ($debug eq 1)
    {
      print "...Displacement Convergence Node Found $dataitem[$idat+5] \n";
    }
#                             ...store each node number in an array
    $selected[6][$nselected[6]] = $dataitem[$idat+5];
#                             ...increment counter
    $nselected[6]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[6]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------residual convergence nodes
#                             maximum residual force at node   703 degree of freedom 1 is equal to 1.970E+04
#                             maximum reaction force at node 14304 degree of freedom 2 is equal to 2.881E+05  
  if ($word eq "maximum" & $word_next eq "residual" & $word_next6 eq "degree")
  {
#
    if ($debug eq 6)
    {
      print "...Residual Convergence Node Found $dataitem[$idat+5]  Residual = $dataitem[$idat+13]\n";
    }
#                             ...store each node number in an array
    $selected[7][$nselected[7]] = $dataitem[$idat+5];
#                             ...increment counter
    $nselected[7]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[7]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------touching contact
#                             node 1066 of body 1 is touching body 3 patch 1
#                             the internal NURBS id is: 1
#                             the normal vector of the patch is      0.00000    -1.00000     0.00000
#
#                             node 8 of body 1 is touching body 5 segment 1
#                             the normal vector is 0.00000 1.00000
#      
#                             node 101 of body 1 is touching body 2 segment 24
#                             the retained nodes are        59         5

  if ($word eq "node" & $word_next3 eq "body" & $word_next6 eq "touching")
  {
#
    if ($debug eq 1)
    {
      print "...Node Contacting Found $dataitem[$idat+1] \n";
    }
#                             ...store each node number in an array
    $selected[8][$nselected[8]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[8]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[8]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------bad beam section
#                             *** error - element 4811 has bad cross section direction specification
  if ($word eq "bad" & $word_next eq "cross" & $word_next2 eq "section")
  {
#
    if ($debug eq 1)
    {
      print "...Element Bad Beam Section Found $dataitem[$idat-2] \n";
    }
#                             ...store each element number in an array
    $selected[9][$nselected[9]] = $dataitem[$idat-2];
#                             ...increment counter
    $nselected[9]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[9]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------bad beam section
#                             *** error - bad beam section number specified for element 341580
  if ($word eq "bad" & $word_next eq "beam" & $word_next2 eq "section")
  {
#
    if ($debug eq 1)
    {
      print "...Element Bad Beam Section Found $dataitem[$idat+7] \n";
    }
#                             ...store each element number in an array
    $selected[9][$nselected[9]] = $dataitem[$idat+7];
#                             ...increment counter
    $nselected[9]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[9]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------bad contact projection
#                             iteration during projection on quadratic segment did not converge
  if ($word eq "iteration" & $word_next eq "during" & $word_next2 eq "projection")
  {
#
    if ($debug == 1)
    {
      print "...Warning during contact quadratic projection $dataitem[$idat+13] \n";
    }
#                             ...store each node number in an array
    $selected[10][$nselected[10]] = $dataitem[$idat+13];
#                             ...increment counter
    $nselected[10]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[10]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------iterative penetration check (displacement)
#                             ddu multiplied by 2.8E-01 due to large displacement value of 4.39E+00 at node 67640 dof 1
  if ($word eq "ddu" & $word_next7 eq "displacement")
  {
#
    if ($debug == 1)
    {
      print "...Iterative penetration check (displacement) $dataitem[$idat+13] \n";
    }
#                             ...store each node number in an array
    $selected[11][$nselected[11]] = $dataitem[$idat+13];
#                             ...increment counter
    $nselected[11]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[11]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------iterative penetration check (penetration)(NTS)
#                             ddu multiplied by 2.4E-01 to avoid penetration of node 93811 into body 5 segment 112

  if ($word eq "ddu" & $word_next6 eq "penetration" & $word_next8 eq "node")
  {
#
    if ($debug == 1)
    {
      print "...Iterative penetration check (penetration) $dataitem[$idat+9] \n";
    }
#                             ...store each node number in an array
    $selected[12][$nselected[12]] = $dataitem[$idat+9];
#                             ...increment counter
    $nselected[12]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[12]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------iterative penetration check (penetration)(STS)
#            ddu multiplied by    3.61977E-02 to avoid penetration of body         1 segment     95510
#                                                                into body         1 segment     96972
#                 body         1 : Rubber
#                 body         1 : Rubber
#                 body         1 element   1007183 segment nodes   1476528   1476656   1476657   1476528
#                 body         1 element     17884 segment nodes   1477426   1477322   1477321   1477426
  if ($word eq "ddu" & $word_next6 eq "penetration" & $word_next8 eq "body")
  {
#
    if ($debug == 1)
    {
      print "...Iterative penetration check (penetration) $dataitem[$idat+31] \n";
    }
#                             ...store each node number in an array
    $selected[12][$nselected[12]] = $dataitem[$idat+31];
#                             ...increment counter
    $nselected[12]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[12]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------too many nodes joined to node
#                             too many nodes joined to node       3124

  if ($word eq "too" & $word_next3 eq "joined")
  {
#
    if ($debug == 1)
    {
      print "...Too many nodes joined $dataitem[$idat+6] \n";
    }
#                             ...store each node number in an array
    $selected[13][$nselected[13]] = $dataitem[$idat+6];
#                             ...increment counter
    $nselected[13]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[13]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------projection for contact node failed
#                             projection for node      1638 on body        7 segment       242
#                             and body        8 segment         3 could not be done
  if ($word eq "projection" & $word_next2 eq "node")
  {
#
    if ($debug == 1)
    {
      print "...projection for contact node failed $dataitem[$idat+3] \n";
    }
#                             ...store each node number in an array
    $selected[14][$nselected[14]] = $dataitem[$idat+3];
#                             ...increment counter
    $nselected[14]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[14]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------bad rigid body orientation
#                             contact between body          2 and          6 indicates that the
#                             orientation of rigid body          6 is probably wrong; this can
#                             cause problems in conjunction with global remeshing
  if ($word eq "contact" & $word_next6 eq "indicates")
  {
#
    if ($debug == 1)
    {
      print "...bad rigid body orientation $dataitem[$idat+13] \n";
    }
#                             ...store each body number in an array
    $selected[15][$nselected[15]] = $dataitem[$idat+13];
#                             ...increment counter
    $nselected[15]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[15]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------node separated 5 times and will be skipped 
#                             node      1639 separated  5 times and will be skipped in separation CHECK
  if ($word eq "node" & $word_next2 eq "separated")
  {
#
    if ($debug == 1)
    {
      print "...node separated 5 times and will be skipped  $dataitem[$idat+1] \n";
    }
#                             ...store each node number in an array
    $selected[16][$nselected[16]] = $dataitem[$idat+1];
#                             ...increment counter
    $nselected[16]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[16]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------incorrect degenerated Hex elements
#                             identical nodal coordinates found for:
#                               element number:      20348
#                               node numbers  :      11067     11066
#                               repeated node numbers are expected.
  if ($word eq "incorrect" & $word_next eq "degenerated")
  {
#
    if ($debug == 1)
    {
      print "...incorrect degenerated hex element $dataitem[$idat+11] \n";
    }
#                             ...store each node number in an array
    $selected[17][$nselected[17]] = $dataitem[$idat+11];
#                             ...increment counter
    $nselected[17]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[17]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------start of assembly   cycle number is 0
#                             wall time = 4753.00
  if ($word eq "start" & $word_next2 eq "assembly")
  {
#
    if ($debug == 1)
    {
      print "...start of assembly: $dataitem[$idat+10] \n";
    } 
#                             ...store each assembly start time in an array
    $selected[18][$nselected[18]] = $dataitem[$idat+10];
#                             ...increment counter
    $nselected[18]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[18]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------start of matrix solution
#                             wall time = 5029.00
  if ($word eq "start" & $word_next2 eq "matrix")
  {
#
    if ($debug == 1)
    {
      print "...start of matrix solution: $dataitem[$idat+7] \n";
    } 
#                             ...store each matrix solve start time in an array
    $selected[19][$nselected[19]] = $dataitem[$idat+7];
#                             ...increment counter
    $nselected[19]++;
#                             ...increment number of iterations
    $niterations = $nselected[19];
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[19]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------end of matrix solution
#                             wall time = 9277.00
  if ($word eq "end" & $word_next2 eq "matrix")
  {
#
    if ($debug == 1)
    {
      print "...end of matrix solution: $dataitem[$idat+7] \n";
    } 
#                             ...store each matrix solve end time in an array
    $selected[20][$nselected[20]] = $dataitem[$idat+7];
#                             ...increment counter
    $nselected[20]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[20]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------binary post data at increment       3.  subincrement    0.  on file 16
#                             wall time =        1019.00
#                             remeshing body 1 due to increment number
  if ($word eq "remeshing" & $word_next eq "body" & $word_next5 eq "increment")
  {
#
    if ($debug == 1)
    {
      print "...start of global remeshing: $dataitem[$idat-1] \n";
    }
#                             ...store each global remeshing time in an array
    $selected[21][$nselected[21]] = $dataitem[$idat-1];
#                             ...increment counter
    $nselected[21]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[21]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------axisymmetric element 30698 has negative radius at node 38538
  if ($word eq "axisymmetric" & $word_next eq "element" & $word_next4 eq "negative")
  {
#
    if ($debug == 1)
    {
      print "...axisymmetric element: $dataitem[$idat+2] has negative radius \n";
    }
#                             ...store each global remeshing time in an array
    $selected[22][$nselected[22]] = $dataitem[$idat+2];
#                             ...increment counter
    $nselected[22]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[22]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------iterative penetration check (penetration)
#                             ddu multiplied by 1.00000E-06 to avoid penetration of node 93811 into body 5 segment 112
  if ($word eq "ddu" & $word_next3 eq "1.00000E-06" & $word_next6 eq "penetration")
  {
#
    if ($debug == 1)
    {
      print "...Iterative penetration check (penetration)(bad) $dataitem[$idat+9] \n";
    }
#                             ...store each node number in an array
    $selected[23][$nselected[23]] = $dataitem[$idat+9];
#                             ...increment counter
    $nselected[23]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[23]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------zero length in element     16994
  if ($word eq "zero" & $word_next eq "length" & $word_next3 eq "element")
  {
#
    if ($debug == 1)
    {
      print "...Zero length element check $dataitem[$idat+4] \n";
    }
#                             ...store each node number in an array
    $selected[24][$nselected[24]] = $dataitem[$idat+4];
#                             ...increment counter
    $nselected[24]++;
#                             ...check number of words allowed has not been exceeded
    if (int($nselected[24]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }

#-----------------------------debug printout of tying matrix for tie = 17 tying node 53
  if ($word eq "debug" & $word_next eq "printout" & $word_next3 eq "tying")
  {
#
    if ($debug == 1)
    {
      print "...Tying matrix debug check - tied node: $dataitem[$idat+11] \n";
    }
#                             ...store each INSERTED node number in an array
    $selected[25][$nselected[25]] = $dataitem[$idat+11];
#                             ...increment counter
    $nselected[25]++;
#                             store the INSERT node ID
    $tying[0][$nselected[25]] = $dataitem[$idat+11];
#                             store the associated host node IDs
    $tying[1][$nselected[25]] = $dataitem[$idat+14];
    $tying[2][$nselected[25]] = $dataitem[$idat+15];
    $tying[3][$nselected[25]] = $dataitem[$idat+16];
    $tying[4][$nselected[25]] = $dataitem[$idat+17];

#   print {$TYING} "$tying[0][$nselected[25]] $tying[1][$nselected[25]] $tying[2][$nselected[25]] $tying[3][$nselected[25]] $tying[4][$nselected[25]] \n";

#                             ...check number of words allowed has not been exceeded
    if (int($nselected[25]) == int($maxnode))
    {
      print "   Warning: MAXNODE ($maxnode) has been exceeded - increase value to more than $maxnode\n\n" ;
    }
  }
}

#---------------------------------------------------------------------
# print a summary list of the number of unsorted nodes/elements 
# associated with each of the warning/error messages searched for
#---------------------------------------------------------------------
# print "\n...Number of General Memory Increases    : $nmemory\n";
# print "...Total General Memory Increases        : $tmemory\n";
#
  print "\n\t    Summary of Output Check Before Sorting:\n";
#                             nodes separating
  print "\n\tTotal Number of (unsorted) Separating Nodes Found: $nselected[0] \n";
#                             insert node problem found
  print "\tTotal Number of INSERT problem Nodes Found: $nselected[1] \n";
#                             contact node sliding along segment
  print "\tTotal Number of Nodes Sliding/Released Along Segments or Hitting Concave Edges: $nselected[2] \n";
#                             contact node belonging to more than 1 body
  print "\tTotal Number of Contact Nodes Belonging To More Than 1 Body: $nselected[3] \n";
#                             contact node constraint conflict
  print "\tTotal Number of Nodes With Constraint Conflicts: $nselected[4] \n";
#                             inside out elements
  print "\tTotal Number of Inside Out Element Found: $nselected[5] \n";
#                             displacement convergence nodes
  print "\tTotal Number of Displacement Convergence Nodes Found: $nselected[6] \n";
#                             residual convergence nodes
  print "\tTotal Number of Residual Convergence Nodes Found: $nselected[7] \n";
#                             contact with nurbs
  print "\tTotal Number of Touching Nodes Found: $nselected[8] \n";
#                             bad beam section
  print "\tTotal Number of Elements Having a Bad Beam Section: $nselected[9] \n";
#                             bad iterative contact projection
  print "\tTotal Number of Nodes with Bad Iterative Contact Projection: $nselected[10] \n";
#                             bad iterative penetration check (displacement)
  print "\tTotal Number of Iterative Penetration Checks (displacement): $nselected[11] \n";
#                             bad iterative penetration check (penetration)
  print "\tTotal Number of Iterative Penetration Checks (penetration): $nselected[12] \n";
#                             number of nodes joined to a node 
  print "\tTotal Number of Nodes Joined to a Node Checks: $nselected[13] \n";
#                             projection for contact node failed 
  print "\tTotal Projection for Contact Node Failed Checks: $nselected[14] \n";
#                             bad rigid body orientation
  print "\tTotal Number of Bad Rigid Body Orientation Checks: $nselected[15] \n";
#                             node separated 5 times and will be skipped 
  print "\tTotal Number of Nodes Separating 5 times Checks: $nselected[16] \n";
#                             incorrect degenerated hex elements
  print "\tTotal Number of Incorrect Degenerated Hex Elements: $nselected[17] \n";
#                             total number of element assemblies
  print "\tTotal Number of Element Assemblies: $nselected[18] \n";
#                             total number of matrix solutions
  print "\tTotal Number of Matrix Solutions: $nselected[19] \n";
#                             total number of remeshes
  print "\tTotal Number of Global Remeshes: $nselected[21] \n";
#                             axisymmetric element has negative radius
  print "\tTotal Number of Axisymmetric Elements with Negative Radius: $nselected[22] \n";
#                             bad iterative penetration check (penetration)
  print "\tTotal Number of Iterative Penetration Checks (penetration)(bad): $nselected[23] \n";
#                             zero length element
  print "\tTotal Number of Zero Length Element Checks: $nselected[24] \n";
#                             debug tying messages
  print "\tTotal Number of Inserted nodes: $nselected[25] \n";

#                             total number of increments
  print "\tTotal Number of Increments: $nincrement \n";
#                             total number of "proceed when not converged"
  print "\tTotal Number of \"Proceed when not Converged\": $nproceed \n";
#                             total number of iterations (equal to number of matrix solutions)
  print "\tTotal Number of Iterations: $nselected[19] \n";

#                             correct niterations if none available
  if( $niterations == 0 )
  {
    $niterations = 1;
  }

#---------------------------------------------------------------------
# print a summary of the time taken in the assembly, solve and recovery 
# stages of the analysis 
#---------------------------------------------------------------------
#-----------------------------loop over each set of element/node lists 
for (my $imode=0; $imode<$maxcol; $imode++)
{
#                             extract number of items for this set of 
#                             messages
  my $nmode_items = $nselected[$imode];

#-----------------------------global remeshing time (not working since no remesh end time yet)
#                             remeshing body 1 due to increment number
  if( $imode == 21 )
  {
#                             initialise total time spent in this phase
    $ttime_g= 0.0;
#
    for (my $atime=0; $atime<$nmode_items; $atime++)
    {
#                             print list of remeshing times
      my $dtime = $selected[18][$atime]- $selected[$imode][$atime];
#
      if( $timing == 1 ) 
      {
        my $atime_next = $atime+1;
#       printf ("\tRemeshing #%4d: Time = %10.4f\n","$atime_next","$dtime");
      }
#                             accumulate time spent in assembly phase
      $ttime_g = $ttime_g + $dtime;
    }
#   print "\tTotal Time Spent in Gobal Remeshing:\t$ttime_g\n";
  }

#-----------------------------assembly time
  if( $imode == 18 )
  {
#                             initialise total time spent in this phase
    $ttime_a = 0.0;
    print "\n";
    for (my $atime=0; $atime<$nmode_items; $atime++)
    {
#                             extract assembly time for each iteration
      my $dtime = $selected[$imode+1][$atime]- $selected[$imode][$atime];
#                             ignore if negative since this means that there 
#                             is not a finishing end of increment timing (the 
#                             result of running this script on an unfinished 
#                             output file
      if( $dtime > 0 )
      {
        my $atime_next = $atime+1;
#                             print list of assembly times
        if( $timing == 1 ) 
        {
          printf ("\tAssembly #%4d: Time = %10.4f\n","$atime_next","$dtime");
        }
#                             accumulate time spent in assembly phase
        $ttime_a = $ttime_a + $dtime;
      }
    }
#                             percentage time taken of total in this phase
#                             : ttime won't be available if the analysis has 
#                               not finished
    $tpercent = 0.0;
    if( $ttime != 0) 
    {
      $tpercent = ($ttime_a*100.0)/($ttime);
    }
    print "\n\t    Summary of Timings:\n\n";
    printf ("\tTotal Time Spent in Element Assembly:\t%10.4f (%10.2f%)","$ttime_a","$tpercent");
  }
#-----------------------------matrix solution time
  if( $imode == 19 )
  {
#                             initialise total time spent in this phase
    $ttime_m = 0.0;
    print "\n";
    for (my $atime=0; $atime<$nmode_items; $atime++)
    {
#                             extract assembly time for each iteration
      my $dtime = $selected[20][$atime]- $selected[$imode][$atime];
#                             ignore if negative since this means that there 
#                             is not a finishing end of increment timing (the 
#                             result of running this script on an unfinished 
#                             output file
      if( $dtime > 0 )
      {

        my $atime_next = $atime+1;
#                             print list of matrix solution times
        if( $timing == 1 ) 
        {
          printf ("\tMatrix Solution #%4d: Time = %10.4f\n","$atime_next","$dtime");
        }
#                             accumulate time spent in matrix solution phase
        $ttime_m = $ttime_m + $dtime;
      }
    }
#                             percentage time taken of total in this phase
    $tpercent = 0;
    if( $ttime != 0) 
    {
      $tpercent = ($ttime_m*100.0)/($ttime);
    }
    printf ("\tTotal Time Spent in Matrix Solution:\t%10.4f (%10.2f%)","$ttime_m","$tpercent");
  }
#-----------------------------recovery time
  if( $imode == 20 )
  {
#                             initialise total time spent in this phase
    $ttime_r = 0.0;
    print "\n";
    for (my $atime=0; $atime<$nmode_items; $atime++)
    {
#                             recovery time is from end of matrix to 
#                             next assembly - that needs special 
#                             handling for the last recovery phase
      my $dtime = $ttime - $selected[$imode][$atime];
#
      my $nmode_pen = $nmode_items-1;
#
      if($atime < $nmode_pen )
      {
        $dtime = $selected[18][$atime+1]- $selected[$imode][$atime];
      }
      my $atime_next = $atime+1;
      if( $timing == 1 ) 
      {
        printf ("\tRecovery #%4d: Time = %10.4f\n","$atime_next","$dtime");
      }
#                             accumulate time spent in recovery phase
      $ttime_r = $ttime_r + $dtime;
    }
#                             percentage time taken of total in this phase
    $tpercent = 0;
    if( $ttime != 0) 
    {
      $tpercent = ($ttime_r*100.0)/($ttime);
    }
    printf ("\tTotal Time Spent in Stress Recovery:\t%10.4f (%10.2f%)","$ttime_r","$tpercent");
#                             evaluate time spent in element loops
    my $ttime_elt = $ttime_r + $ttime_a;
#                             percentage time taken of total in this phase
    $tpercent = 0;
    if( $ttime != 0) 
    {
      $tpercent = ($ttime_elt*100.0)/($ttime);
    }
    printf ("\n\tTotal Time Spent in Element Loops:\t%10.4f (%10.2f%)","$ttime_elt","$tpercent");
#                             evaluate time per iteration
    my $ttime_iterative = $ttime/$niterations;
#   print "\n\tTotal Time Spent in Element Loops  : $ttime_iterative \n";
    printf ("\n\tAverage Time For Each Iteration:\t%10.4f\n","$ttime_iterative");
  }
}


#                             stop script since checking is now done
if ($resflag == 1 )
{
  print "\n\nScanning output files only was requested - now stopping\n" ;
  exit 3 ;
}

#---------------------------------------------------------------------
# now sort the stored list of nodes/elements to remove duplicates
#---------------------------------------------------------------------

for (my $imode=0; $imode<$maxcol; $imode++)
{
#
  if ($debug == 1)
  {
    print "\n IMODE: $imode";
  }
  if ($nselected[$imode] > 0) 
  {
#                             set first sorted element number
    $selected_sorted[$imode][0] = $selected[$imode][0];
#-----------------------------loop over number of unsorted selected 
#                             nodes/elements
    for (my $unsorted=0; $unsorted <$nselected[$imode]; $unsorted++)
    {
      my $foundit = 0;
#-----------------------------loop over the total number of sorted 
#                             selected nodes/elements so far
      for (my $sorted=0; $sorted <$nselected_sorted[$imode]; $sorted++)
      {
#                             ...check whether current unsorted node 
#                                has already been stored in the sorted 
#                                list
        if ($selected_sorted[$imode][$sorted] eq $selected[$imode][$unsorted])
        {
          $foundit = 1;
#
          if ($debug == 1)
          {
            print "\n found it: $selected_sorted[$imode][$sorted] - $foundit";
          }
        }
      }

      if ($foundit == 0)
      {
        $selected_sorted[$imode][$nselected_sorted[$imode]] = $selected[$imode][$unsorted];
        $nselected_sorted[$imode]++;
#
        if ($debug == 1)
        {
          print "\n adding to sorted list: $selected_sorted[$imode][$nselected_sorted[$imode]] - $foundit";
        }
      }
    }
  }
  else
  {
    $nselected_sorted[$imode]=0;
  }
}

#---------------------------------------------------------------------
# print a summary list of the number of sorted nodes/elements 
# associated with each of the warning/error messages searched for
#---------------------------------------------------------------------
print "\n\t    Summary of Output Check After Sorting:\n";
#                             nodes separating
print "\n\tTotal Number of Separating Nodes Found: $nselected_sorted[0] \n";
#                             insert node problem found
print "\tTotal Number of INSERT problem Nodes Found: $nselected_sorted[1] \n";
#                             contact node sliding along segment
print "\tTotal Number of Nodes Sliding/Released Along Segments or Hitting Concave Edges: $nselected_sorted[2] \n";
#                             contact node belonging to more than 1 body
print "\tTotal Number of Contact Nodes Belonging To More Than 1 Body: $nselected_sorted[3] \n";
#                             contact node constraint conflict
print "\tTotal Number of Nodes With Constraint Conflicts: $nselected_sorted[4] \n";
#                             inside out elements
print "\tTotal Number of Inside Out Element Found: $nselected_sorted[5] \n";
#                             displacement convergence nodes
print "\tTotal Number of Displacement Convergence Nodes Found: $nselected_sorted[6] \n";
#                             residual convergence nodes
print "\tTotal Number of Residual Convergence Nodes Found: $nselected_sorted[7] \n";
#                             contact with nurbs
print "\tTotal Number of Touching Nodes Found: $nselected_sorted[8] \n";
#                             bad beam section
print "\tTotal Number of Elements Having a Bad Beam Section: $nselected_sorted[9] \n";
#                             bad iterative contact projection
print "\tTotal Number of Nodes with Bad Iterative Contact Projection: $nselected_sorted[10] \n";
#                             bad iterative penetration check (displacement)
print "\tTotal Number of Iterative Penetration Checks (displacement): $nselected_sorted[11] \n";
#                             bad iterative penetration check (penetration)
print "\tTotal Number of Iterative Penetration Checks (penetration): $nselected_sorted[12] \n";
#                             number of nodes joined to a node 
print "\tTotal Number of Nodes Joined to a Node Checks: $nselected_sorted[13] \n";
#                             projection for contact node failed 
print "\tTotal Projection for Contact Node Failed Checks: $nselected_sorted[14] \n";
#                             bad rigid body orientation
print "\tTotal Number of Bad Rigid Body Orientation Checks: $nselected_sorted[15] \n";
#                             node separated 5 times and will be skipped 
print "\tTotal Number of Nodes Separating 5 times Checks: $nselected_sorted[16] \n";
#                             incorrect degenerated hex elements
print "\tTotal Number of Incorrect Degenerated Hex Elements: $nselected[17] \n";
#                             total number of element assemblies
print "\tTotal Number of Element Assemblies: $nselected[18] \n";
#                             total number of matrix solutions
print "\tTotal Number of Matrix Solutions: $nselected[19] \n";
#                             total number of remeshes
print "\tTotal Number of Global Remeshes: $nselected_sorted[21] \n";
#                             axisymmetric element has negative radius
print "\tTotal Number of Axisymmetric Elements with Negative Radius: $nselected_sorted[22] \n";
#                             bad iterative penetration check (penetration)
print "\tTotal Number of Iterative Penetration Checks (penetration)(bad): $nselected_sorted[23] \n";
#                             zero length element
print "\tTotal Number of Zero Length Element Checks: $nselected_sorted[24] \n";
#                             debug tying messages
print "\tTotal Number of Inserted nodes: $nselected_sorted[25] \n";

#---------------------------------------------------------------------
# print general command to mentat proc file
#---------------------------------------------------------------------
if( $guiflag == 1)
{
#                             turn off echoes
  print {$DATA} "*command_group_begin\n";
  print {$DATA} "*set_proc_echo off\n";
  print {$DATA} "*py_echo off\n";

#-----------------------------loop over each set of element/node lists 
#                             and write commands to the session file 
#                             to create a SET/GROUP
  for (my $imode=0; $imode<$maxcol; $imode++)
  {
#                             extract number of items for this set of 
#                             messages
    my $nmode_items = $nselected_sorted[$imode];
#                             don't process the timing data
    if( $nmode_items >0 and ($imode != 18 and $imode != 19 and $imode != 20 and $imode != 21 ))
    {
#                             remove any previously created set
      print {$DATA} "*remove_set_entries\n";
      print {$DATA} $messages[$imode], "\n";
      print {$DATA} "all_existing\n";
#                             appropriate mentat command to select 
#                             elements
      if( $imode == 5 or $imode == 9 or $imode == 17 or $imode == 22 or $imode == 24)
      {
#                             elements directly associated with this set of 
#                             messages
        print {$DATA} "*select_clear\n";
        print {$DATA} "*select_elements\n";
      }
#                             appropriate mentat command to select 
#                             surfaces
      elsif( $imode == 15)
      {
#                             surfaces associated with this set of 
#                             messages
        print {$DATA} "*select_clear\n";
        print {$DATA} "*select_faces\n";
      }
#                             write debug tying matrices to external file
      elsif( $imode == 25)
      {
        for (my $itie1=0; $itie1<$nmode_items; $itie1++)
        {
#                             print inserted node to the external tying file
#         print {$TYING} "$selected_sorted[$imode][$itie1] \n";
#
          for (my $itie2=0; $itie2<=$nmode_items; $itie2++)
          {
            print "$itie1: $selected_sorted[$imode][$itie1] \n";
            print "$itie2: $tying[0][$itie2] \n";
#
            print "$tying[0][$itie2] $tying[1][$itie2] $tying[2][$itie2] $tying[3][$itie2] $tying[4][$itie2] \n";

            if( $selected_sorted[$imode][$itie1] == $tying[0][$itie2])
            {
#                             print host nodes to the external tying file
              print {$TYING} "$tying[0][$itie2] $tying[1][$itie2] $tying[2][$itie2] $tying[3][$itie2] $tying[4][$itie2] \n";
            }
          }
        }
      }
      else
      {
#                             nodes were selected with this set of 
#                             messages, so select the elements 
#                             associated with these nodes instead
        print {$DATA} "*select_clear\n";
        print {$DATA} "*select_elements_nodes\n";
      }
      for (my $nelts=0; $nelts<$nmode_items; $nelts++)
      {
#                             print list of nodes/elements to results 
#                             proc file
        print {$DATA} $selected_sorted[$imode][$nelts],"\n";
      }
#                             print mentat command to proc file
      print {$DATA} "# | End of List\n";
#                             store the selected elements into a
#                             temporary group
      print {$DATA} "*store_elements ", $messages[$imode], "\n";
      print {$DATA} "all_selected\n";
    }
  }

  print {$DATA} "*command_group_end\n";
}
#---------------------------------------------------------------------
# print general command to patran session file
#---------------------------------------------------------------------
else
{
#                             fit view
  print {$DATA} "gu_fit_view(  )\n";
#-----------------------------loop over each set of element/node lists 
#                             and write commands to the session file 
#                             to create a SET/GROUP
  for (my $imode=0; $imode<$maxcol; $imode++)
  {
#                             extract number of items for this set of 
#                             messages
    my $nmode_items = $nselected_sorted[$imode];
#                             don't do messages without node or elements lists (CHANGE)
    if( $nmode_items >0 and ($imode != 18 and $imode != 19 and $imode != 20 and $imode != 21 ))
    {
#                             remove any previously created set
      print {$DATA} "sys_poll_option( 2 )\n";
      print {$DATA} "bv_group_clear(\"", $messages[$imode],"\" )\n";
      print {$DATA} "sys_poll_option( 0 )\n";
#-----------------------------appropriate patran command to select 
#                             elements directly (CHANGE)
      if( $imode == 5 or $imode == 9 or $imode == 17 or $imode == 22 )
      {
#                             elements associated with this set of 
#                             messages
        print {$DATA} "sys_poll_option( 2 )\n";
        print {$DATA} "ga_group_create( \"",$messages[$imode],"\" )\n";
        print {$DATA} "ga_group_entity_add( \"",$messages[$imode],"\",  @ \n";
        print {$DATA} "\"Elm ";
      }
      else
      {
#                             nodes were selected with this set of 
#                             messages, so select the elements 
#                             associated with these nodes instead
        print {$DATA} "STRING _elem_list[VIRTUAL]\n";
        print {$DATA} "list_create_elem_ass_node( 0, \"Node ";
      }
#----------------------------print list of elements to results 
#                             session file
      for (my $nelts=0; $nelts<$nmode_items; $nelts++)
      {
        print {$DATA} $selected_sorted[$imode][$nelts]," //@ \n";
      }
#-----------------------------commands to finish off the element lists (CHANGE)
      if( $imode == 5 or $imode == 9 or $imode == 17 or $imode == 22 )
      {
        print {$DATA} "\") \n";
        print {$DATA} "sys_poll_option( 0 ) \n";
      }
      else
      {
        print {$DATA} "\", \"lista\", _elem_list )\n";
        print {$DATA} "sys_poll_option( 0 ) \n";
#
        print {$DATA} "sys_poll_option( 2 )\n";
        print {$DATA} "ga_group_create( \"",$messages[$imode],"\" )\n";
        print {$DATA} "ga_group_entity_add( \"",$messages[$imode],"\", _elem_list) \n";
      }
    }
  }
}
#-----------------------------print main header
  print "\n\n\n-----------------------------------------\n";
  print "------- OUTPUT File Check END -----------\n";
  print "-----------------------------------------\n\n";
#                             close mentat proc file
close($DATA);

#                             sound a bell on finish
#print "\a"


# Perl trim function to remove whitespace from the start and end of the string
sub trim($)
{
	my $string = shift;
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	return $string;
}
# Left trim function to remove leading whitespace
sub ltrim($)
{
	my $string = shift;
	$string =~ s/^\s+//;
	return $string;
}
# Right trim function to remove trailing whitespace
sub rtrim($)
{
	my $string = shift;
	$string =~ s/\s+$//;
	return $string;
}
