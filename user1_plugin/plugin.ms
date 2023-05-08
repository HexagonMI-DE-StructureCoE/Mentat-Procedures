popmenu user1_plugin_pm {

 text "RUN PROCEDURE FILE"
 mode permanent

 group {
  layout vbox

  frame {
   group {
    layout hbox

    button {
     size 40 20
     text "RUN PROCEDURE FILE USER 1"
     command "*exec_plugin_proc user1_plugin user1_plugin.proc"
     help "user1_plugin"
    }

   }
  }
 }
}
