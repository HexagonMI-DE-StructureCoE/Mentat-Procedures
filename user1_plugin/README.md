
## Example 1 User Plugin


It is possible to customize MSC Mentat GUI in different ways and locations, such as in the Menu Bar, Toolbar, and Main Menu (Page Tab). 

The execution of procedure and python files can also be automated with user-defined buttons and popmenus.


#### How to customize MSC Mentat
There are 2 methods:
- The new method using User Plugin
- The old method modifing the Mentat installation

#### The User Plugin Method

For customizing the Toolbar or Menu Bar, the user can create user plugins without change files in installation folder.

### Example 1 user1_plugin
**user1_plugin.proc** changes interface to dark theme.
This plugin changes the GUI to dark theme: it is a simple command recorded into a mentat procedure.

This example plugin adds an icon in the toolbar and adds an option inside the menubar

The plugin directory where the customizing files should be stored can be found in *<Mentat\_Installation\_Dir>\plugins\*. 

Care should be taken when using this alternate method with user plugins, since the files names for each plugin ([*plugin.ms*](plugin.ms), [*menubar.xml*](menubar.xml), and [*toolbars.xml*](toolbars.xml) ) should not be modified to work properly.

Please check the files in this folder to better understand how it works.


#### The Old Method

(It is deprecated nowadays.)

It is reported here because there are many examples still based on this way.

It is necessary to edit some ASCII installation files of Marc Mentat with a text editor. 
The installation files are usually found in the directory where MSC Mentat has been installed, depending on the specific version. 
By default *<Mentat\_Installation\_Dir>* is in *C:\\Program Files\\MSC.Software\\Marc\\20xx\\mentat20xx\\* .
These files are generally in .xml and .ms format. 
In most cases and in recent releases of Mentat, no recompile is needed by Marc Mentat to apply effects on the new configuration.

### MSC MENTAT SYNTAX MENU
*Customizing the Menu Bar*
Edit the *menubar.xml* file located in *<Mentat\\_Installation\\_Dir>\menus\\*. Below is an example of a portion of the text code to be appended at the end of the file for the creation of a new menu bar named Utilities User 1:



```xml 
<menubar>
 <menu title="&amp;Utilities User 1">
    <popmenu title="User-Defined Menu User 1"
             popmenu="user_defined_popmenu"
             file="user.ms"/>
  </menu>
</menubar>
```

*Customizing the Toolbar*
Edit the *toolbars.xml* file located in *<Mentat\_Installation\_Dir>\menus\*. Below is an example of a portion of the text code to be appended at the end of the file for the creation of a new top toolbar icon named User 1 Toolbar, which in turn executes a procedure file to increase the font size. The *<Mentat\_Installation\_Dir>* path should be updated accordingly in the .xml code file:

```xml 

  <toolbars>
      <toolbar name="User 1 Toolbar">
        <exec title="User 1 Toolbar"
              tooltip="Execute Procedure File user1_tb.proc"
              command='*exec_procedure "<Mentat_Installation_Dir>\menus\user1_tb.proc"'/>
      </toolbar>
  </toolbars>
```

*Customizing the Main Menu (Page Tabs)*
Edit the *main.xml* file located in *<Mentat\_Installation\_Dir>\menus\*. Below is an example of a portion of the text code to be appended at the end of the file for the creation of a new Main Menu Page named User 1, which in turn executes the same procedure code of the sample toolbar, or a python code that prints a test output in the Marc Mentat Dialog Window. The <Mentat\_Installation\_Dir> path should be updated accordingly in the .xml code file:

```xml 
  </page>
    <page title="User 1"
      name="user_1"
      >
      <!--nrows="1">-->
      <group title="Execute Files">
          <exec title="Run Procedure File #1"
            tooltip="Execute Procedure File user1_tb.proc"
            command='*exec_procedure "<Mentat_Installation_Dir>\menus\user1_tb.proc"'/>
          <exec title="Run Procedure File #2"
            tooltip="Execute Procedure File user1_mm.py"
            command='*py_file_run "<Mentat_Installation_Dir>\menus\user1_mm.py"'/>
      </group>
  </page>
```


Only in case the new user-defined options trigger a pop menu dialog box, then a .ms file should be created and edited accordingly. All files should be saved in the same folder where the .xml file resides. 

Before editing the installation files, it is strongly recommended that backup files are copied in case they are needed to be restored.

Make sure the attached files are downloaded and saved in the *<Mentat\_Installation\_Dir>\menus\* folder. For example: *C:\\Program Files\\MSC.Software\\Marc\\20xx\\mentat20xx\\menus\\* .


For further information about user plugins, please refer to the Mentat User’s Guide -> Basics of Mentat -> Mechanics of Mentat -> User Plugins.
