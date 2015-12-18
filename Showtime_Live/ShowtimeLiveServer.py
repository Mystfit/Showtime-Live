#!python
from Tkinter import *
import tkSimpleDialog, tkFileDialog

import sys, time, os, platform, glob
from shutil import copytree, rmtree, ignore_patterns
from optparse import OptionParser

from Showtime_Live.LiveRouter import LiveRouter
from Showtime_Live.Midi_Remote_Scripts.ShowtimeBridge.Logger import Log


# MIDI Remote Script installation
# -------------------------------
def find_ableton_dirs():
    if platform.system() == "Windows":
        liveinstallations = glob.glob(os.path.abspath(os.path.join(os.getenv("PROGRAMDATA"), "Ableton", "Live*")) + "*")
        liveinstallations = [os.path.join(path, "Resources") for path in liveinstallations]

    elif platform.system() == "Darwin":
        liveinstallations = glob.glob(os.path.abspath(os.path.join(os.path.sep, "Applications", "Ableton Live")) + "*")
        liveinstallations = [os.path.join(path, "Contents", "App-Resources") for path in liveinstallations]

    return liveinstallations

def install_midi_remote_scripts(custom_install_path=None):
    installpath = ""
    scriptspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Midi_Remote_Scripts", "ShowtimeBridge")
    
    liveinstallations = None
    if custom_install_path:
        liveinstallations = [os.path.join(custom_install_path, "Resources")]
    else:
        liveinstallations = find_ableton_dirs()
    
    for path in liveinstallations:
        installpath = os.path.join(path, "MIDI Remote Scripts", "ShowtimeBridge")

        try:
            rmtree(installpath)
        except:
            pass

        print("Installing MIDI remote scripts to %s" % installpath)
        copytree(scriptspath, installpath, ignore=ignore_patterns('*.pyc', 'tmp*'))


# UI
# --------------------
class Display(Frame):
    def __init__(self,parent=0):
        Frame.__init__(self, parent)
        parent.minsize(width=800, height=600)
        parent.title("Showtime-Live Server")

        self.pack(fill=BOTH, expand=YES)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, pad=7)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, pad=7)

        # Server log
        self.consoleLabel = Label(self, text="Server Log")
        self.consoleLabel.grid(row=0, column=0, sticky=W, padx=5, pady=4)
        self.output = Text(self)
        self.output.grid(row=1, column=0, columnspan=2, rowspan=5, padx=2, pady=2, sticky=(N,E,S,W))
        sys.stdout = self

        scrollbar = Scrollbar(self)
        scrollbar.grid(row=1, column=2, rowspan=5, sticky=(N,E,S))
        # scrollbar.pack(side=RIGHT, fill=Y)
        self.output.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output.yview)

        # Install script buttons
        self.installScriptsBtn = Button(self, text="Install Scripts automatically", command=install_midi_remote_scripts)
        self.installScriptsBtn.grid(row=1, column=3, sticky=(N,E,W), padx=2, pady=2)

        self.customPathInstallScriptsBtn = Button(self, text="Install Scripts to Non-default location", command=self.open_custom_install_dialog)
        self.customPathInstallScriptsBtn.grid(row=2, column=3, sticky=(N,E,W), padx=2, pady=2)

        # Logging buttons
        self.logNetworkVar = IntVar(self)
        self.logNetworkVar.set(Log._networklogging == 1)
        self.logNetworkVar.trace('w', self.lognetwork_changed)
        self.logNetworkButton = Checkbutton(self, text="Log network connections", variable=self.logNetworkVar)
        self.logNetworkButton.grid(row=3, column=3, sticky=(S,W), padx=2, pady=2)

        self.logShowtimeVar = IntVar(self)
        self.logShowtimeVar.set(1)
        self.logShowtimeVar.trace('w', self.logshowtime_changed)
        self.logShowtimeButton = Checkbutton(self, text="Log Showtime messages", variable=self.logShowtimeVar)
        self.logShowtimeButton.config(state="disabled")
        self.logShowtimeButton.grid(row=4, column=3, sticky=(S,W), padx=2, pady=2)

        Label(self, text="Logging level").grid(row=5, column=3, sticky=(S,W), padx=2, pady=2)
        self.logTypeVar = StringVar(self)
        self.logTypeVar.set(Log.titles[Log.level])
        self.logTypeVar.trace('w', self.logtype_changed)
        self.logLevelOptions = OptionMenu(self, self.logTypeVar,
            Log.titles[Log.LOG_INFO],
            Log.titles[Log.LOG_WARN],
            Log.titles[Log.LOG_ERRORS])
        self.logLevelOptions.grid(row=6, column=3, sticky=(S,E,W), padx=2, pady=2)


    def logtype_changed(self, *args):
        Log.set_log_level(Log.log_level_from_name(self.logTypeVar.get()))

    def lognetwork_changed(self, *args):
        Log.set_log_network(self.logNetworkVar.get() == 1)

    def logshowtime_changed(self, *args):
        pass

    def open_custom_install_dialog(self):
        LiveScriptInstallDialog(self)

    def write(self, txt):
        self.output.insert(END, str(txt))
        self.output.see(END)


class LiveScriptInstallDialog(tkSimpleDialog.Dialog):
    def body(self, master):
        self.resizable(width=TRUE, height=FALSE)
        self.minsize(width=320, height=50)

        Label(master, text="Ableton Live Directory:").grid(row=0, sticky=(W))
        self.entry = Entry(master)
        self.entry.grid(row=0, column=1, sticky=(E,W))
        self.entry.insert(0, 'C:\\ProgramData\Ableton')
        self.browseBtn = Button(master, text="Browse", command=self.askdirectory)
        self.browseBtn.grid(row=0, column=2, sticky=(E))
        return self.entry # initial focus

    def askdirectory(self):
        """Returns a selected directoryname."""
        options = {}
        options['initialdir'] = self.entry.get()
        options['mustexist'] = False
        options['parent'] = self
        options['title'] = 'Ableton Live Directory'
        dirname = tkFileDialog.askdirectory(**options)
        if dirname:
            self.set_directory(dirname)

    def set_directory(self, path):
        self.entry.delete(0, END)
        self.entry.insert(0, path)

    def apply(self):
        install_midi_remote_scripts(str(self.entry.get()))

    def validate(self):
        return os.path.isdir(str(self.entry.get()))


# Server
# --------------
class ShowtimeLiveServer():
    def main(self):
        # Options parser
        parser = OptionParser()
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)
        parser.add_option("-c", "--cli", action="store_true", dest="useCLI", help="Run server in Command Line Interface mode.", default=False)
        parser.add_option("-s", "--stagehost", action="store", dest="stageaddress", type="string", help="IP address of the Showtime stage.", default=None)
        parser.add_option("-p", "--stageport", action="store", dest="stageport", type="string", help="Port of the Showtime stage", default="6000")
        parser.add_option("-m", "--midiportindex", action="store", dest="midiportindex", type="int", help="Midi loopback port to use. Windows only, make sure loopMidi is running first!", default=1)
        parser.add_option("--listmidiports", action="store_true", dest="listmidiports", help="List the available midi ports on the system.", default=False)

        (options, args) = parser.parse_args()

        if options.verbose:
            Log.set_log_level(Log.LOG_INFO)
        else:
            Log.set_log_level(Log.LOG_WARN)
        Log.set_log_network(True)

        if not options.useCLI:
            root = Tk()
            gui = Display(root)
            Log.set_logger(gui.write)



        # Check if midi remote scripts are installed correctly
        installed_midi_remote_scripts = find_ableton_dirs()
        success = True

        print("\n-------------------------------------")
        print("Checking if Ableton Live is installed")
        print("Found %s instances of Ableton Live." % len(installed_midi_remote_scripts))
        for path in installed_midi_remote_scripts:
            script_path = os.path.join(path, "MIDI Remote Scripts", "ShowtimeBridge")
            if not os.path.isdir(script_path):
                success = False
                print("Showtime-Live scripts not installed in %s" % script_path)     
        
        if success:
            print("Showtime-Live scripts already installed")
        else:
            print("Some of the discovered Ableton Live installations do not have the Showtime-Live Midi Remote Scripts installed.")
            print("Either click the \"Install Scripts\" button or restart with the command line flag --install.")
        gui.update()


        # Set up MIDI router
        if options.listmidiports:
            midiRouter = Showtime_Live.MidiRouter.MidiRouter(None)
            print("\n-------------------------------------")
            print("Available MIDI ports:")
            midiRouter.listMidiPorts()
            sys.exit(0)
        gui.update()

        print("\n-------------------------------------")
        print("Starting Showtime-Live Server")
        # Set up network router
        stageaddress = options.stageaddress
        if stageaddress:
            stageaddress += ":" + str(options.stageport)

        showtimeRouter = LiveRouter(stageaddress, options.midiportindex)
        showtimeRouter.start()
        gui.update()
        print("Server up!")
        print("-------------------------------------\n")

        # Enter into the idle loop to handle messages
        try:
            if options.useCLI:
                while 1:
                    time.sleep(1)
            else:
                gui.mainloop()
                
        except KeyboardInterrupt:
            print "\nExiting..."
            showtimeRouter.stop()


def main():
    server = ShowtimeLiveServer()
    server.main()

if __name__ == "__main__":
    main()
