
User 1 Plugin

This is a sample plugin to demonstrate Mentat's plugin framework. It executes a procedure file named **user1_plugin.proc**, which in turn changes to dark theme.

Summary

It is possible to customize Marc Mentat GUI with new user-defined options in different ways and locations, such as in the Menu Bar, Toolbar, and Main Menu (Page Tab). Furthermore, the execution of procedure and python files can also be automated with user-defined buttons and popmenus.

Description

In order to do this, it is necessary to edit some ASCII installation files of Marc Mentat with a text editor. These files are generally in .xml and .ms format. In most cases, no recompile is needed by Marc Mentat to apply effects on the new configuration.

The installation files are usually found in the directory where Marc Mentat has been installed, depending on the specific version. By default *<Mentat\_Installation\_Dir>* is in *C:\\Program Files\\MSC.Software\\Marc\\20xx\\mentat20xx\\* .

Only in case the new user-defined options trigger a pop menu dialog box, then a .ms file should be created and edited accordingly. All files should be saved in the same folder where the .xml file resides. 

Before editing the installation files, it is strongly recommended that backup files are copied in case they are needed to be restored.

Make sure the attached files are downloaded and saved in the *<Mentat\_Installation\_Dir>\menus\* folder. For example: *C:\\Program Files\\MSC.Software\\Marc\\20xx\\mentat20xx\\menus\\* .

*Customizing the Menu Bar*
Edit the *menubar.xml* file located in *<Mentat\\_Installation\\_Dir>\menus\\*. Below is an example of a portion of the text code to be appended at the end of the file for the creation of a new menu bar named Utilities User 1:



```xml 

 </menu>

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
…
    </toolbar>

    <toolbar name="User 1 Toolbar">
      <exec title="User 1 Toolbar"
            tooltip="Execute Procedure File user1_tb.proc"
            command='*exec_procedure "<Mentat_Installation_Dir>\menus\user1_tb.proc"'/>
    </toolbar>
    
  </top>
…
…

</toolbars>

```

*Customizing the Main Menu (Page Tabs)*
Edit the *main.xml* file located in *<Mentat\_Installation\_Dir>\menus\*. Below is an example of a portion of the text code to be appended at the end of the file for the creation of a new Main Menu Page named User 1, which in turn executes the same procedure code of the sample toolbar, or a python code that prints a test output in the Marc Mentat Dialog Window. The <Mentat\_Installation\_Dir> path should be updated accordingly in the .xml code file:

```xml 
…
…
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

</main>


```


Alternatively, for customizing the Toolbar or Menu Bar, the user can also create user plugins in a similar fashion. Attached is a user1\_plugin.zip example to be unzipped and saved in the plugins directory. This plugin changes the GUI to dark theme. The plugin directory where the customizing files should be stored can be found in *<Mentat\_Installation\_Dir>\plugins\*. Care should be taken when using this alternate method with user plugins, since the files names for each plugin ([*plugin.ms*](http://plugin.ms/), *menubar.xml*, and *toolbars.xml*) should not be modified to work properly.

For further information about user plugins, please refer to the Mentat User’s Guide -> Basics of Mentat -> Mechanics of Mentat -> User Plugins.
