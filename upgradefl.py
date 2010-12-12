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

For a variety of technical reasons, the update process is temporarily more complex than usual.  After this update process is complete, your update process will return to normal.

<b>NOTE:</b>
Before attempting to complete the update process, you should close any running programs on your desktop."""

CONARY_TEXT="""First, the system software manager, Conary, needs to be updated to the latest version.

In fact, the rest of the update process cannot continue until Conary has been updated successfully."""

UPDATEALL_TEXT = """Second, after having updated Conary successfully, you should try updating all the installed packages on your system.

Depending on which packages you have installed in the past, the update process may fail, possibly with messages about "file conflicts" or "dependency failures"."""

MIGRATE_TEXT = """If the update process in step 2a fails, you will need to migrate your system to its installation defaults -- i.e. roughly the same state your system would be in if you had just installed it from a Foresight DVD.

This will remove any extra packages that you have previously installed, and you will have to add them back after this step.

<b>NOTE:</b>
The migration process should not tamper with any documents, media files or other saved data in your home folder.  But if you are the paranoid sort, now would be a good time to ensure that you have good backups of your important data/documents/media files."""

(CONARY_STEP, UPDATEALL_STEP, MIGRATE_STEP) = range(3)

## Using shell scripts allows for more control than using commands
# Set up a file to use for capturing conary return values -- 
# neither gnome-terminal nor xterm appear to make the conary exit
# status available.
fd, CONARY_EXIT_STATUS = tempfile.mkstemp(prefix='conary_exit_status-')
os.fdopen(fd, 'r')
#os.close(fd)
print "** Conary exit status lives in %s" % CONARY_EXIT_STATUS

#COMMAND1 = "sudo conary update conary --resolve"
fd, UPDATE_CONARY = tempfile.mkstemp(prefix='update_conary-')
f = os.fdopen(fd, 'w')
f.write(
'''#!/bin/sh
echo "Updating Conary...(ppid=$PPID)"
#echo "conary update conary --resolve" && sleep 3
conary update conary --resolve --verbose --no-interactive
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

#COMMAND2 = "sudo conary updateall"
fd, CONARY_UPDATEALL = tempfile.mkstemp(prefix='conary_updateall-')
f = os.fdopen(fd, 'w')
f.write('''#!/bin/sh
echo "Updating all the installed packages on your system...(ppid=$PPID)"
#echo "conary updateall" && sleep 3 && rv=1
conary updateall --verbose --no-interactive
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

#COMMAND3 = "sudo conary migrate group-gnome-dist"
fd, CONARY_MIGRATE = tempfile.mkstemp(prefix='conary_migrate-')
f = os.fdopen(fd, 'w')
f.write(
'''#!/bin/sh
echo "Resetting your system configuration to installation defaults...(ppid=$PPID)"
#echo "conary migrate group-gnome-dist" && sleep 3 && rv=1
conary migrate group-gnome-dist --verbose --no-interactive
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

def cleanup():
    files = [ CONARY_EXIT_STATUS, UPDATE_CONARY,
              CONARY_UPDATEALL, CONARY_MIGRATE ]
    print "** Cleaning up after upgradefl.py:"
    for file in files:
        try:
            print "** Deleting %s ..." % file
            os.remove(file)
        except Exception, e:
            print "!! Could not delete file %s:" % file
            print e
    print "== Done cleaning up after upgradefl.py"

class UpgradeSystem(object):
    """
    Create an UI for controlling the upgrade process.
    """
    # close the window and quit
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def __init__(self):

        # don't loop endlessly in the updateall step.
        self._update_conary_tries = 0
        self._conary_updateall_tries = 0
        # if we've tried a few times, perhaps it's time to bring out
        # the big migrate hammer?
        self._max_tries = 3 

        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_urgency_hint(True)
        self.window.set_title("Foresight Upgrade Helper")
        self.window.set_icon_name(gtk.STOCK_DIALOG_ERROR)
        #self.window.set_border_width(0)
        self.window.set_size_request(450, 536) # 600 - 2*32
        self.window.set_resizable(True)
        self.window.connect("delete_event", self.delete_event)
        self.create_widgets()
        self.window.show_all()
    
    def create_text_frame(self, content_text, my_padding=10):
        """
        Convenience function for creating an aligned text box.
        content_text is expected to be a label.
        """
        frameVBox = gtk.VBox()
        frameHBox = gtk.HBox()
        alignment = gtk.Alignment(0.0, 0.0)
        alignment.add(content_text) # ensure proper alignment for text
        frameHBox.pack_start(alignment, expand=False, fill=False, padding=my_padding)
        frameVBox.pack_start(frameHBox, expand=True, fill=False, padding=my_padding)
        return frameVBox

    def create_text_label(self, text):
        label = gtk.Label()
        label.set_markup(text)
        label.set_line_wrap(True)
        return label

    def create_widgets(self):
        """
        Convenience UI thunk (packs the UI elements).
        """
        self.updateConaryButton = gtk.Button("Update Conary Now")
        self.updateConaryButton.set_tooltip_text(
            "This will attempt to update Conary, the Foresight"
            " system software manager, to the newest version available.")
        self.updateConaryButton.idx = CONARY_STEP

        self.updateallButton = gtk.Button("Update All Installed Packages")
        self.updateallButton.set_tooltip_text(
            "This will attempt to update all the installed packages"
            " on your system to their newest available versions.")
        self.updateallButton.set_sensitive(False)
        self.updateallButton.idx = UPDATEALL_STEP

        self.migrateButton = gtk.Button("Migrate To Installation Defaults")
        self.migrateButton.set_tooltip_text(
            "This will attempt to migrate your system to its installation defaults."
            " Only do this if the \'Update All Installed Packages\' step"
            " cannot be completed successfully even after several attempts.")
        self.migrateButton.set_sensitive(False)
        self.migrateButton.idx = MIGRATE_STEP

        self.updateConaryButton.connect("clicked", self.button_clicked)
        self.updateallButton.connect("clicked", self.button_clicked)
        self.migrateButton.connect("clicked", self.button_clicked)

        self.infoLabel = self.create_text_label(INFOTEXT)
        self.updateConaryLabel = self.create_text_label(CONARY_TEXT)
        self.updateallLabel = self.create_text_label(UPDATEALL_TEXT)
        self.migrateLabel = self.create_text_label(MIGRATE_TEXT)

        self.infoLabelFrame = self.create_text_frame(self.infoLabel)
        self.updateConaryFrame = gtk.Frame("Step 1 - Update Conary")
        self.updateConaryFrame.add(self.create_text_frame(self.updateConaryLabel))
        self.updateallFrame = gtk.Frame("Step 2a - Update All Installed Packages")
        self.updateallFrame.add(self.create_text_frame(self.updateallLabel))
        self.migrateFrame = gtk.Frame("Step 2b - Migrate To Installation Defaults")
        self.migrateFrame.add(self.create_text_frame(self.migrateLabel))

        # Let's see if we can make some vertical space between elements
        vpadding = 2
        topVBox = gtk.VBox(homogeneous=False, spacing=10)
        for element in [ self.infoLabelFrame,
                         self.updateConaryButton,
                         self.updateallFrame,
                         self.updateallButton,
                         self.migrateFrame,
                         self.migrateButton ]:
            topVBox.pack_start(element, expand=False, fill=False, padding=vpadding)
        # Why not have the first button selected by default?
        self.updateConaryButton.set_flags(gtk.CAN_DEFAULT)
        # Padding ensures that we don't pack right up against the edge of
        # the window (spacing is irrelevant due to single column layout)
        topHBox = gtk.HBox()
        topHBox.pack_start(topVBox, True, False, padding=10)

        # Always show the vertical scrollbar, but never the horizontal.
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolled_window.add_with_viewport(topHBox)
        self.window.add(scrolled_window)

    def update_done(self, text):
        """
        Present a dialog box with a message text  and an Exit button. 
        The Exit button exits the program.
        """
        dialog = gtk.Dialog(title="Foresight Upgrade Helper", 
                            parent=self.window, flags=gtk.DIALOG_MODAL)
        dialog.set_resizable(False)
        msg = self.create_text_frame(self.create_text_label(text))
        hbox = gtk.HBox()
        hbox.pack_start(msg, True, False, padding=20)
        dialog.vbox.pack_start(hbox, True, False, padding=20)
        exit_button = gtk.Button(label="Exit", stock=None)
        exit_button.connect("clicked", self.delete_event, None)
        aa_hbox = gtk.HBox()
        aa_hbox.pack_end(exit_button, True, True, padding=20)
        dialog.action_area.pack_end(aa_hbox, True, True, padding=20)
        dialog.show_all()

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
                text = """<b>Update Complete</b>

Successfully updated all installed packages.  
               
Press <i>Exit</i> to close the Foresight upgrade helper program.
"""
                self.update_done(text)
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
                text = """<b>Migration Complete</b>

Successfully migrated to installation defaults.  
               
Press <i>Exit</i> to close the Foresight upgrade helper program.
"""
                self.update_done(text)

    def run_conary(self, command):
        #TODO: If xterm doesn't exist, try gnome-terminal?
        ppid=None
        conary_exit_status = None
        try:
            cmd_line = ["/usr/bin/xterm", "-fg", "grey", "-bg", "black",
                        "-fn", "9x15", "-j", "-sb", "-rightbar", "-sl", "4096",
                        "-e", command]
            p = subprocess.Popen(cmd_line)
            print "** %s is executed by %s (ppid %s)" \
                % (command, cmd_line[0], p.pid)
            rv = p.wait() # The idea is to block the UI here...
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
            # Might be left at 0 if the prior conary operation completed succesfully.
            conary_exit_status = -1
        except Exception, e:
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
    try:
        app.main()
    except Exception, e:
        print e
    finally:
        cleanup()
