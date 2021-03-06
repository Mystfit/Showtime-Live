#!python
import Queue
import glob
import os
import platform
import time
import tkFileDialog
import tkSimpleDialog
from Tkinter import *
from optparse import OptionParser
from shutil import copytree, rmtree, ignore_patterns

import zmq
from Showtime.zst_method import ZstMethod

from Showtime_Live.LiveRouter import LiveRouter
from Showtime_Live.MidiRouter import MidiRouter
from Showtime_Live.Midi_Remote_Scripts.ShowtimeBridge.Logger import Log


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
    scriptspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Midi_Remote_Scripts", "ShowtimeBridge")

    liveinstallations = []
    if custom_install_path:
        liveinstallations = [os.path.join(custom_install_path, "Resources")]
    else:
        liveinstallations = find_ableton_dirs()

    for path in liveinstallations:
        installpath = os.path.join(path, "MIDI Remote Scripts", "ShowtimeBridge")

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

        self.showtimeRouter = None
        self.midiRouter = None

        parent.minsize(width=800, height=600)
        parent.title("Showtime-Live Server")

        self.pack(fill=BOTH, expand=YES)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, pad=7)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(5, pad=7)

        # Connection status
        self.connectionStatusLabel = StringVar(self)
        self.connectionStatusLabel.set("Disconnected")
        Label(self, text="Live status:").grid(row=0, column=0, sticky=E, padx=2, pady=4)
        Label(self, text="", textvariable=self.connectionStatusLabel).grid(row=0, column=1, sticky=W, padx=2, pady=4)

        # Install script buttons
        self.installScriptsBtn = Button(self, text="Install Live scripts", command=install_midi_remote_scripts)
        self.installScriptsBtn.grid(row=1, column=0, sticky=(N, E, W), padx=2, pady=2)

        self.customPathInstallScriptsBtn = Button(self, text="Install Live scripts to custom location",
                                                  command=self.open_custom_install_dialog)
        self.customPathInstallScriptsBtn.grid(row=2, column=0, sticky=(N, E, W), padx=2, pady=2)

        # Server log
        self.consoleLabel = Label(self, text="Server Log")
        self.consoleLabel.grid(row=4, column=0, sticky=W, padx=2, pady=2)
        self.output = Text(self)
        self.output.grid(row=5, column=0, columnspan=2, rowspan=5, padx=2, pady=2, sticky=(N, E, S, W))
        sys.stdout = self
        self.consoleQueue = Queue.Queue()

        scrollbar = Scrollbar(self)
        scrollbar.grid(row=5, column=1, rowspan=5, sticky=(N, E, S), pady=2)
        self.output.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output.yview)

        # Logging buttons
        self.logNetworkVar = IntVar(self)
        self.logNetworkVar.set(Log.useNetworkLogging == 1)
        self.logNetworkVar.trace('w', self.lognetwork_changed)
        self.logNetworkButton = Checkbutton(self, text="Log network connections", variable=self.logNetworkVar)
        self.logNetworkButton.grid(row=10, column=0, sticky=(S, W), padx=2, pady=2)

        self.logShowtimeVar = IntVar(self)
        self.logShowtimeVar.set(1)
        self.logShowtimeVar.trace('w', self.logshowtime_changed)
        self.logShowtimeButton = Checkbutton(self, text="Log Showtime messages", variable=self.logShowtimeVar)
        self.logShowtimeButton.config(state="disabled")
        self.logShowtimeButton.grid(row=11, column=0, sticky=(S, W), padx=2, pady=2)

        Label(self, text="Logging level").grid(row=12, column=0, sticky=(S, W), padx=2, pady=2)
        self.logTypeVar = StringVar(self)
        self.logTypeVar.set(Log.titles[Log.level])
        self.logTypeVar.trace('w', self.logtype_changed)
        self.logLevelOptions = OptionMenu(self, self.logTypeVar,
                                          Log.titles[Log.LOG_INFO],
                                          Log.titles[Log.LOG_WARN],
                                          Log.titles[Log.LOG_ERRORS])
        self.logLevelOptions.grid(row=13, column=0, sticky=(S, E, W), padx=2, pady=2)

        # Midi UI
        self.midiPortVar = None
        self.midiPortOptions = None

    def set_showtime_router(self, showtimerouter):
        self.showtimeRouter = showtimerouter
        self.showtimeRouter.clientConnectedCallback = self.connectionstatus_changed

    def create_midi_loopback_options(self, midirouter):
        self.midiRouter = midirouter

        Label(self, text="MIDI Loopback Port").grid(row=3, column=0, sticky=(N, E), padx=2, pady=2)
        self.midiPortVar = StringVar(self)
        self.midiPortVar.trace('w', self.midiport_changed)

        ports = self.midiRouter.midi_out.ports
        loopmidiports = [port for port in ports if "loopmidi" in port.lower()]
        if len(loopmidiports) > 0:
            self.midiPortVar.set(loopmidiports[0])

        self.midiPortOptions = OptionMenu(self, self.midiPortVar, *ports)
        self.midiPortOptions.grid(row=3, column=1, sticky=(N, W), padx=2, pady=2)

    def connectionstatus_changed(self, *args):
        text = "Connected" if self.showtimeRouter.clientConnected else "Disconnected"
        print("\nAbleton Live connection status: %s\n\n" % text)
        self.connectionStatusLabel.set(text)

    def midiport_changed(self, *args):
        if hasattr(self, "midiRouter"):
            ports = self.midiRouter.midi_out.ports
            if len(ports) > 0:
                portindex = int(ports.index(self.midiPortVar.get()))
                self.midiRouter.close()
                self.midiRouter = MidiRouter(portindex)

    def logtype_changed(self, *args):
        Log.set_log_level(Log.log_level_from_name(self.logTypeVar.get()))

    def lognetwork_changed(self, *args):
        Log.set_log_network(self.logNetworkVar.get() == 1)

    def logshowtime_changed(self, *args):
        pass

    def open_custom_install_dialog(self):
        LiveScriptInstallDialog(self)

    def write(self, txt):
        self.consoleQueue.put(txt)

    def write_log(self):
        while self.consoleQueue.qsize():
            try:
                self.output.insert(END, str(self.consoleQueue.get(0)))
                self.output.see(END)
            except Queue.Empty:
                pass
        self.after(50, self.write_log)


class LiveScriptInstallDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent):
        tkSimpleDialog.Dialog.__init__(self, parent)
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
        parser.add_option("-s", "--stagehost", action="store", dest="stageaddress", type="string",
                          help="IP address of the Showtime stage.", default=None)
        parser.add_option("-p", "--stageport", action="store", dest="stageport", type="string",
                          help="Port of the Showtime stage", default="6000")
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

        # Logging options
        if options.verbose:
            Log.set_log_level(Log.LOG_INFO)
        else:
            Log.set_log_level(Log.LOG_WARN)
        Log.set_log_network(True)

        # Create GUI
        gui = None
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
            print("Some local Ableton Live installations do not have the Showtime-Live Midi Remote Scripts installed.")
            print("Either click the \"Install Scripts\" button or restart with the command line flag --install.")

        if options.installScripts:
            install_midi_remote_scripts(options.liveCustomFolder)

        if not options.useCLI:
            gui.update()

        # Set up MIDI router
        print("\n-------------------------------------")
        print("Starting MIDI clock")
        self.midiRouter = MidiRouter(options.midiportindex)

        if platform.system() == "Windows":
            gui.create_midi_loopback_options(self.midiRouter)

        if options.listmidiports:
            midirouter = MidiRouter(None)
            print("\n-------------------------------------")
            print("Available MIDI ports:")
            midirouter.list_midi_ports()
            sys.exit(0)

        if not options.useCLI:
            gui.update()

        # Set up network router
        print("\n-------------------------------------")
        print("Starting Showtime-Live Server")
        stageaddress = options.stageaddress
        if stageaddress:
            stageaddress += ":" + str(options.stageport)

        self.showtimeRouter = None
        try:
            self.showtimeRouter = LiveRouter(stageaddress)
            if not options.useCLI:
                gui.set_showtime_router(self.showtimeRouter)

            self.showtimeRouter.start()
            print("Server running!")
            print("-------------------------------------\n")
        except zmq.error.ZMQError, e:
            if str(e) == "Address in use":
                Log.error("Could not create Showtime node. Address already in use.\n")
                Log.error("Close any ShowtimeLive servers on this machine and try re-launching the server.")
        except Exception, e:
            Log.error("Could not start LiveRouter. General Error: %s" % e)

        if self.midiRouter.is_midi_active():
            self.showtimeRouter.node.request_register_method(
                    "play_note",
                    ZstMethod.WRITE,
                    {
                        "trackindex": None,
                        "note": None,
                        "state": None,
                        "velocity": None
                    },
                    self.midiRouter.play_midi_note)

        if not options.useCLI:
            gui.update()

        # Enter into the idle loop to handle messages
        try:
            if options.useCLI:
                while 1:
                    time.sleep(1)
            else:
                gui.after(50, gui.write_log)
                gui.mainloop()

        except KeyboardInterrupt:
            print "\nExiting..."
            if self.showtimeRouter:
                self.showtimeRouter.stop()
            self.midiRouter.close()


def main():
    ShowtimeLiveServer()


if __name__ == "__main__":
    main()
