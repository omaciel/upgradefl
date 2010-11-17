#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import pygtk
pygtk.require('2.0')
import gtk
import subprocess
import os
import tempfile

"""
Copyright (c) 2010, Og Maciel <ogmaciel@gnome.org>

All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name Og Maciel nor the names of other contributors may be used
      to endorse or promote products derived from this software without specific
      prior written permission.

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

INFOTEXT = """<b>Updates to Foresight are now available.</b>

For a variety of technical reasons, the update process is temporarily more      
complex than usual.  After this update process is complete,  your update        
process will return to normal.

<b>NOTE:</b>
Before attempting to complete the update process, you should close any          
running programs on your desktop.                                               
"""

CONARY_TEXT="""
First, the system software manager, Conary, needs to be updated to the latest version.  

In fact, the rest of the update process cannot continue until Conary has been updated successfully."""

UPDATEALL_TEXT = """
Second, after having updated Conary successfully, you should try updating all the installed packages on your system.

Depending on which packages you have installed in the past, the update process may fail, possibly with messages about "file conflicts" or "dependency failures"."""

MIGRATE_TEXT = """
If the update process in step 2a fails, you will need to migrate your system to its default state -- i.e. roughly the same state your system would be in if you had just installed it from a Foresight DVD.

This will remove any extra packages that you have previously installed, and you will have to add them back after this step.

<b>NOTE:</b>
The migration process should not tamper with any documents, media files or other saved data in your home folder.  But if you are the paranoid sort, now would be a good time to ensure that you have good backups of your important data/documents/media files."""

(CONARY_STEP, UPDATEALL_STEP, MIGRATE_STEP) = range(3)

## Using files allows for more control than using commands
# Set up a file to use for conary return values -- 
# gnome-terminal does not appear to make the conary exit
# status available, so we use xterm instead.
fd, CONARY_EXIT_STATUS = tempfile.mkstemp(prefix='conary_exit_status-')
conary_exit_status = os.fdopen(fd, 'r')
os.close(fd)
print "** Conary exit status lives in %s" % CONARY_EXIT_STATUS

#COMMAND1 = "sudo conary update conary --resolve"
fd, UPDATE_CONARY = tempfile.mkstemp(prefix='update_conary-')
f = os.fdopen(fd, 'w')
f.write(
'''#!/bin/sh
echo "Updating Conary...(ppid=$PPID)"
#echo "conary update conary --resolve" && sleep 3
conary update conary --resolve --verbose
rv=$?
echo "$PPID" > %s
echo "$rv" >> %s
echo ""
if [ $rv -eq 0 ]; then
  echo "** Conary updated successfully."
else
  echo "!! Conary not updated, please try again."
fi
echo ""
echo "Press <Return> to close this window."
read ANSWER
exit $rv
''' % (CONARY_EXIT_STATUS, CONARY_EXIT_STATUS))
f.close()
os.chmod(UPDATE_CONARY, 0755)
# TODO: Save a reference so that we can clean up afterwards?

#COMMAND2 = "sudo conary updateall"
fd, CONARY_UPDATEALL = tempfile.mkstemp(prefix='conary_updateall-')
f = os.fdopen(fd, 'w')
f.write('''#!/bin/sh
echo "Updating packages on the system...(ppid=$PPID)"
#echo "conary updateall" && sleep 3 && rv=1
conary updateall --verbose
rv=$?
echo "$PPID" > %s
echo "$rv" >> %s
echo ""
if [ $rv -eq 0 ]; then
  echo "** System packages updated successfully."
else
  echo "!! System packages not updated, please try again."
fi
echo ""
echo "Press <Return> to close this window."
read ANSWER
exit $rv
''' % (CONARY_EXIT_STATUS, CONARY_EXIT_STATUS))
f.close()
os.chmod(CONARY_UPDATEALL, 0755)
# TODO: Save a reference so that we can clean up afterwards?

#COMMAND3 = "sudo conary migrate group-gnome-dist"
fd, CONARY_MIGRATE = tempfile.mkstemp(prefix='conary_updateall-')
f = os.fdopen(fd, 'w')
f.write(
'''#!/bin/sh
echo "Resetting your system configuration to installation defaults...(ppid=$PPID)"
#echo "conary migrate group-gnome-dist" && sleep 3 && rv=1
conary migrate group-gnome-dist
rv=$?
echo "$PPID" > %s
echo "$rv" >> %s
echo ""
if [ $rv -eq 0 ]; then
  echo "** System successfully reset to installation defaults."
else
  echo "!! System could not be reset to installation defaults, please try again."
fi
echo ""
echo "Press <Return> to close this window."
read ANSWER
exit $rv
''' % (CONARY_EXIT_STATUS, CONARY_EXIT_STATUS))
f.close()
os.chmod(CONARY_MIGRATE, 0755)
# TODO: Save a reference so that we can clean up afterwards?

class UpgradeSystem(object):

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        #TODO: clean up?
        gtk.main_quit()
        return False

    def __init__(self):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_resizable(False)
        self.window.set_urgency_hint(True)

        self.window.set_title("Foresight Upgrade Helper")
        self.window.set_icon_name(gtk.STOCK_DIALOG_ERROR)
        self.window.set_border_width(10)

        #self.window.set_size_request(500, 200)
        
        # don't loop endlessly
        self._update_conary_tries = 0
        self._conary_updateall_tries = 0
        # if we've tried a few times, perhaps it's time to bring out
        # the big migrate hammer?
        self._max_tries = 3 

        self.window.connect("delete_event", self.delete_event)

        self.create_widgets()
        self.window.show_all()

    def create_widgets(self):

        self.updateConaryButton = gtk.Button("Update Conary Now")
        self.updateConaryButton.set_tooltip_text(
            "This will attempt to update Conary, the Foresight"
            " package manager, to the newest version available.")
        self.updateConaryButton.idx = CONARY_STEP

        self.updateallButton = gtk.Button("Update All Installed Packages")
        self.updateallButton.set_tooltip_text(
            "This will attempt to update all the packages"
            " on your system to their newest available versions.")
        self.updateallButton.set_sensitive(False)
        self.updateallButton.idx = UPDATEALL_STEP

        self.migrateButton = gtk.Button("Migrate To Default Installation")
        self.migrateButton.set_tooltip_text(
            "This will attempt to reset your system to installation defaults."
            " Only do this if the \'Update All Installed Packages\' step"
            " cannot be completed successfully.")
        self.migrateButton.set_sensitive(False)
        self.migrateButton.idx = MIGRATE_STEP

        self.updateConaryButton.connect("clicked", self.button_clicked)
        self.updateallButton.connect("clicked", self.button_clicked)
        self.migrateButton.connect("clicked", self.button_clicked)

        self.infoLabel = gtk.Label()
        self.infoLabel.set_markup(INFOTEXT)
        self.infoLabel.set_line_wrap(False)
        #self.infoLabel.set_alignment(0, 0)

        self.updateConaryLabel = gtk.Label()
        self.updateConaryLabel.set_markup(CONARY_TEXT)
        self.updateConaryLabel.set_line_wrap(True)
        self.updateConaryLabel.set_alignment(0, 0)

        self.updateallLabel = gtk.Label()
        self.updateallLabel.set_markup(UPDATEALL_TEXT)
        self.updateallLabel.set_line_wrap(True)
        self.updateallLabel.set_alignment(0, 0)

        self.migrateLabel = gtk.Label()
        self.migrateLabel.set_markup(MIGRATE_TEXT)
        self.migrateLabel.set_line_wrap(True)
        self.migrateLabel.set_alignment(0, 0)

        # Let's see if we can make the infoLabel fill the screen horizontally
        topContainer = gtk.VBox()
        #infoLabelAlign = gtk.Alignment(0,0,0,0)
        #infoLabelAlign.add(self.infoLabel)
        topContainer.pack_start(self.infoLabel, True, True, 10)

        table = gtk.Table(rows=4, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        # use xpadding=x, ypadding=y for spacing?

        self.updateConaryFrame = gtk.Frame("Step 1 - Update Conary")
        self.updateConaryFrame.add(self.updateConaryLabel)
        table.attach(self.updateConaryFrame, 0, 1, 0, 1,
                            xoptions=gtk.FILL, yoptions=gtk.FILL)
        table.attach(self.updateConaryButton, 0, 1, 1, 2, 
                            yoptions=gtk.SHRINK)
        #                    xpadding=2, ypadding=2)
        self.updateallFrame = gtk.Frame("Step 2a - Update All Installed Packages")
        self.updateallFrame.add(self.updateallLabel)
        table.attach(self.updateallFrame, 0, 1, 2, 3,
                            xoptions=gtk.FILL, yoptions=gtk.FILL) 
        #                    xpadding=10, ypadding=2)
        table.attach(self.updateallButton, 0, 1, 3, 4, 
                            yoptions=gtk.SHRINK)
        #                    xpadding=2, ypadding=2)
        self.migrateFrame = gtk.Frame("Step 2b - Migrate To Default Installation")
        self.migrateFrame.add(self.migrateLabel)
        table.attach(self.migrateFrame, 1, 2, 0, 3,
                            xoptions=gtk.FILL, yoptions=gtk.FILL)
        #                    xpadding=10, ypadding=2)
        table.attach(self.migrateButton, 1, 2, 3, 4, 
                            yoptions=gtk.SHRINK)
        #                    xpadding=2, ypadding=10)
        topContainer.pack_start(table, False, False, 0)
        self.window.add(topContainer)

    def button_clicked(self, button):
        if button.idx == CONARY_STEP:
            retval = self.run_conary(UPDATE_CONARY)
            self._update_conary_tries += 1
            if(retval != 0): 
                #TODO: Ask the user to check his internet connection?
                self.updateConaryButton.set_sensitive(True)
                self.updateallButton.set_sensitive(False)
                self.migrateButton.set_sensitive(False)
                # We need the newest conary for the rest to work.
            else: 
                # Conary updated, move on to the next step
                self.updateConaryButton.set_sensitive(False)
                self.updateallButton.set_sensitive(True)
                self.migrateButton.set_sensitive(False)
        elif button.idx == UPDATEALL_STEP:
            retval = self.run_conary(CONARY_UPDATEALL)
            self._conary_updateall_tries += 1
            if(retval != 0):
                if(self._conary_updateall_tries < self._max_tries):
                    # just try again
                    self.updateConaryButton.set_sensitive(False)
                    self.updateallButton.set_sensitive(True)
                    self.migrateButton.set_sensitive(False)
                else: 
                    # All right, no luck; let the user try the big hammer!
                    self.updateConaryButton.set_sensitive(False)
                    self.updateallButton.set_sensitive(True)
                    self.migrateButton.set_sensitive(True)
            else: 
                # if the updateall ran without issues, we're all done!
                self.updateConaryButton.set_sensitive(False)
                self.updateallButton.set_sensitive(False)
                self.migrateButton.set_sensitive(False)
                #TODO: open update complete dialog box and quit
        else:
            #TODO: What do we do if migrating fails? Try again?
            self.updateConaryButton.set_sensitive(False)
            self.updateallButton.set_sensitive(False)
            self.migrateButton.set_sensitive(False)
            retval = self.run_conary(CONARY_MIGRATE)
            if (retval != 0):
                # Just keep trying?
                self.migrateButton.set_sensitive(True)
            else:
                # At least the migrate worked
                self.migrateButton.set_sensitive(False)

        #TODO: Maybe we want to notify the user of completion and close the window?

    def run_conary(self, command):
        #TODO: If xterm doesn't exist, try gnome-terminal?
        ppid=None
        conary_exit_status = None
        try:
            cmd_line = ["/usr/bin/xterm", "-fg", "grey", 
                        "-bg", "black", "-fn", "9x15",
                        "-e", command]
            p = subprocess.Popen(cmd_line)
            print "** %s is executed by %s (ppid %s)" \
                % (command, cmd_line[0], p.pid)
            rv = p.wait() # The idea is to block here.
            with open(CONARY_EXIT_STATUS, 'r') as f:
                f.flush()
                ppid = int(f.readline().strip())
                conary_exit_status = int(f.readline().strip())
                assert (ppid == p.pid)
                print "** Conary exit status file is in sync with current Conary process(%i)." \
                    % p.pid
        except OSError as (errno, strerror):
            print "Executing \'%s\'" % " ".join(cmd_line)
            print "failed with the following error:"
            print "  OS error({0}): {1}".format(errno, strerror)
            conary_exit_status = errno
        except IOError as (errno, strerror):
            print "!! I/O error({0}): {1}".format(errno, strerror)
        except ValueError:
            print "!! Couldn't parse Conary exit status file (ppid=%s, conary_exit_status=%s)" \
                % (ppid, conary_exit_status)
        except AssertionError:
            print "!! Conary exit status file is not in sync with current Conary process."
            print "   (current ppid=%i, ppid from file=%i, conary_exit_status from file=%s)" % (p.pid, ppid, conary_exit_status)
            # Might be 0 if the prior conary operation completed succesfully.
            conary_exit_status = -1
        except e: #FIXME: This might be a Java idiom ...
            print e
        else:
            print "** Process %i returned with status %i" \
                % (p.pid, conary_exit_status)
        finally:
            if (conary_exit_status == None):
                conary_exit_status = -1
        # wait for and check the return value of the conary operation
        return conary_exit_status

    def main(self):
        gtk.main()

if __name__ == "__main__":
    app = UpgradeSystem()
    app.main()
