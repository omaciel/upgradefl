#!/usr/bin/env python
# vim: ts=4 sw=4 expandtab ai
# -*- encoding: utf-8 -*-

import pygtk
pygtk.require('2.0')
import gtk
import subprocess

"""
Copyright (c) 2010, Og Maciel <ogmaciel@gnome.org>

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.
    * Neither the name of the Og Maciel nor the names of its contributors may be used to
      endorse or promote products derived from this software without specific prior written
      permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
“AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

INFOTEXT = """
<b>Updates to Foresight are now available.</b>\n
For a variety of technical reasons, the update process
is temporarily more complex than usual.  After this
update process is complete,your update process will
return to normal.\n\n
In order to complete this update process, you should
first close running programs.
"""

(STEP1, STEP2, STEP3) = range(3)
COMMAND1 = "sudo conary update conary --resolve"
COMMAND2 = "sudo conary updateall"
COMMANDR3= "sudo conary migrate group-gnome-dist"

class UpgradeSystem(object):

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def __init__(self):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_resizable(False)
        self.window.set_urgency_hint(True)

        self.window.set_title("Foresight Upgrade Helper")
        self.window.set_icon_name(gtk.STOCK_DIALOG_ERROR)

        #self.window.set_size_request(500, 200)

        self.window.connect("delete_event", self.delete_event)

        self.create_widgets()
        self.window.show_all()

    def create_widgets(self):
        topContainer = gtk.HBox(homogeneous=False, spacing=2)
        buttonsContainer = gtk.VBox(homogeneous=False, spacing=2)

        self.stepOneButton = gtk.Button("Update Conary")
        self.stepOneButton.set_tooltip_text("Step 1")
        self.stepOneButton.idx = STEP1

        self.stepTwoButton = gtk.Button("Update All")
        self.stepTwoButton.set_tooltip_text("Step 2")
        self.stepTwoButton.set_sensitive(False)
        self.stepTwoButton.idx = STEP2

        self.stepThreeButton = gtk.Button("Migrate Packages")
        self.stepThreeButton.set_tooltip_text("Step 3")
        self.stepThreeButton.set_sensitive(False)
        self.stepThreeButton.idx = STEP3

        self.stepOneButton.connect("clicked", self.button_clicked)
        self.stepTwoButton.connect("clicked", self.button_clicked)
        self.stepThreeButton.connect("clicked", self.button_clicked)

        self.infoLabel = gtk.Label()
        self.infoLabel.set_markup(INFOTEXT)
        self.infoLabel.set_line_wrap(True)

        # Add buttons to container
        buttonsContainer.pack_start(self.stepOneButton, expand=True, fill=True, padding=2)
        buttonsContainer.pack_start(self.stepTwoButton, expand=True, fill=True, padding=2)
        buttonsContainer.pack_start(self.stepThreeButton, expand=True, fill=True, padding=2)

        topContainer.pack_start(buttonsContainer, expand=True, fill=True, padding=2)
        topContainer.pack_start(self.infoLabel, expand=True, fill=True, padding=2)
        self.window.add(topContainer)

    def button_clicked(self, button):
        #TODO: We could get fancy and check the return code of the process and determine whether to continue.
        if button.idx == STEP1:
            self.run_conary(COMMAND1)
            self.stepOneButton.set_sensitive(False)
            self.stepTwoButton.set_sensitive(True)
            self.stepThreeButton.set_sensitive(False)
        elif button.idx == STEP2:
            self.run_conary(COMMAND2)
            self.stepOneButton.set_sensitive(False)
            self.stepTwoButton.set_sensitive(False)
            self.stepThreeButton.set_sensitive(True)
        else:
            self.run_conary(COMMAND2)
            self.stepOneButton.set_sensitive(True)
            self.stepTwoButton.set_sensitive(False)
            self.stepThreeButton.set_sensitive(False)

        #TODO: Maybe we want to notify the user of completion and close the window?

    def run_conary(self, command):
        print "--command='%s'; echo ''; echo 'Press Enter to close window'; read" % command
        pid = subprocess.Popen(args=[
            "gnome-terminal", '--command="%s"; echo ""; echo "Press Enter to close window"; read' % command]).pid

def main():
    gtk.main()

if __name__ == "__main__":
    example = UpgradeSystem()
    main()
