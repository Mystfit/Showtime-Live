#!python
import glob
import os
import platform
import time
from MidiScreamer import MidiScreamer

try: 
    # Python 3
    from tkinter import filedialog
    from tkinter import simpledialog
    from tkinter import *
except ImportError:
    # Python 2
    import tkFileDialog as filedialog
    import tkSimpleDialog as simpledialog
    from Tkinter import *
from optparse import OptionParser
from shutil import copytree, rmtree, ignore_patterns

# MIDI Remote Script installation
# -------------------------------
def find_ableton_dirs():
    liveinstallations = []
    if platform.system() == "Windows":
        liveinstallations = glob.glob(os.path.abspath(os.path.join(os.getenv("PROGRAMDATA"), "Ableton", "Live*")) + "*")
        liveinstallations = [os.path.join(path, "Resources") for path in liveinstallations]

    elif platform.system() == "Darwin":
        liveinstallations = glob.glob(os.path.abspath(os.path.join(os.path.sep, "Applications", "Ableton Live")) + "*")
        liveinstallations = [os.path.join(path, "Contents", "App-Resources") for path in liveinstallations]

    return liveinstallations


def install_midi_remote_scripts(custom_install_path=None):
    scriptspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "MidiRemoteScripts")

    liveinstallations = []
    if custom_install_path:
        liveinstallations = [os.path.join(custom_install_path, "Resources")]
    else:
        liveinstallations = find_ableton_dirs()

    for path in liveinstallations:
        installpath = os.path.join(path, "MIDI Remote Scripts", "ShowtimeBridge")
        print(scriptspath)
        print(installpath)
        try:
            rmtree(installpath)
        except OSError:
            pass

        print("Installing MIDI remote scripts to %s" % installpath)
        copytree(scriptspath, installpath, ignore=ignore_patterns('*.pyc', 'tmp*'))


# UI
# -------------------
class Display(Frame):
    def __init__(self, parent=0):
        Frame.__init__(self, parent)

        self.midiScreamer = None

        parent.minsize(width=800, height=600)
        parent.title("Showtime-Live Server")

        self.pack(fill=BOTH, expand=YES)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, pad=7)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, pad=7)

        # Install script buttons
        self.installScriptsBtn = Button(self, text="Install Live scripts", command=install_midi_remote_scripts)
        self.installScriptsBtn.grid(row=1, column=0, sticky=(N, E, W), padx=2, pady=2)

        self.customPathInstallScriptsBtn = Button(self, text="Install Live scripts to custom location",
                                                  command=self.open_custom_install_dialog)
        self.customPathInstallScriptsBtn.grid(row=2, column=0, sticky=(N, E, W), padx=2, pady=2)

        # Midi UI
        self.midiPortVar = None
        self.midiPortOptions = None

    def create_midi_loopback_options(self, midiscreamer):
        self.midiScreamer = midiscreamer

        Label(self, text="MIDI Loopback Port").grid(row=3, column=0, sticky=(N, E), padx=2, pady=2)
        self.midiPortVar = StringVar(self)
        self.midiPortVar.trace('w', self.midiport_changed)

        ports = self.midiScreamer.midi_out.ports
        loopmidiports = [port for port in ports if "loopmidi" in port.lower()]
        if len(loopmidiports) > 0:
            self.midiPortVar.set(loopmidiports[0])

        self.midiPortOptions = OptionMenu(self, self.midiPortVar, *ports)
        self.midiPortOptions.grid(row=3, column=1, sticky=(N, W), padx=2, pady=2)

    def midiport_changed(self, *args):
        if hasattr(self, "midiScreamer"):
            ports = self.midiScreamer.midi_out.ports
            if len(ports) > 0:
                portindex = int(ports.index(self.midiPortVar.get()))
                self.midiScreamer.close()
                self.midiScreamer = MidiScreamer(portindex)

    def open_custom_install_dialog(self):
        LiveScriptInstallDialog(self)


class LiveScriptInstallDialog(simpledialog.Dialog):
    def __init__(self, parent):
        simpledialog.Dialog.__init__(self, parent)
        self.entry = None
        self.browseBtn = None

    def body(self, master):
        master.pack(fill=BOTH, expand=YES)
        self.resizable(width=TRUE, height=FALSE)
        self.minsize(width=320, height=50)

        Label(master, text="Ableton Live Directory:").grid(row=0, column=0, sticky=W)
        self.entry = Entry(master, width=35)
        self.entry.grid(row=0, column=1, sticky=(E, W), padx=2)
        self.grid_columnconfigure(1, weight=1)

        self.entry.insert(0, 'C:\\ProgramData\Ableton\Live 9.x.x')
        self.browseBtn = Button(master, text="Browse", command=self.askdirectory)
        self.browseBtn.grid(row=1, column=1, sticky=W)
        return self.entry  # initial focus

    def askdirectory(self):
        """Returns a selected directory name."""
        options = {
            'initialdir': 'C:\\ProgramData\Ableton\'',
            'mustexist': False,
            'parent': self,
            'title': 'Ableton Live Directory'
        }
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
class ShowtimeLiveServer:
    def __init__(self):
        # Options parser
        parser = OptionParser()
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)
        parser.add_option("-c", "--cli", action="store_true", dest="useCLI",
                          help="Run server in Command Line Interface mode.", default=False)
        parser.add_option("-m", "--midiportindex", action="store", dest="midiportindex", type="int",
                          help="Midi loopback port to use. Windows only, make sure loopMidi is running first!",
                          default=None)
        parser.add_option("--listmidiports", action="store_true", dest="listmidiports",
                          help="List the available midi ports on the system.", default=False)
        parser.add_option("--install", action="store_true", dest="installScripts",
                          help="Install MIDI remote scripts for all found copies of Ableton Live.", default=False)
        parser.add_option("--install-dir", action="store_true", dest="liveCustomFolder",
                          help="Ableton Live directory to install MIDI remote scripts to.",
                          default=None)

        (options, args) = parser.parse_args()

        # Create GUI
        gui = None
        if not options.useCLI:
            root = Tk()
            gui = Display(root)

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
            print("Some local Ableton Live installations do not have the Showtime-Live Midi Remote Scripts installed.")
            print("Either click the \"Install Scripts\" button or restart with the command line flag --install.")

        if options.installScripts:
            install_midi_remote_scripts(options.liveCustomFolder)

        if not options.useCLI:
            gui.update()

        # Set up MIDI router
        print("\n-------------------------------------")
        print("Starting MIDI clock")
        self.midiScreamer = MidiScreamer(options.midiportindex)

        if platform.system() == "Windows":
            gui.create_midi_loopback_options(self.midiScreamer)

        if options.listmidiports:
            midiscreamer = MidiScreamer(None)
            print("\n-------------------------------------")
            print("Available MIDI ports:")
            midiscreamer.list_midi_ports()
            sys.exit(0)

        if not options.useCLI:
            gui.update()


        # Enter into the idle loop to handle messages
        try:
            if options.useCLI:
                while 1:
                    time.sleep(1)
            else:
                gui.mainloop()

        except KeyboardInterrupt:
            print("\nExiting...")
            self.midiScreamer.close()


def main():
    ShowtimeLiveServer()


if __name__ == "__main__":
    main()
