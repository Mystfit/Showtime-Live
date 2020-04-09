#!python
import Queue
import glob
import os
import platform
import time
import threading
import tkFileDialog
import tkSimpleDialog
from Tkinter import *
from optparse import OptionParser
from shutil import copytree, rmtree, ignore_patterns

import showtime.showtime as ZST


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
        installpath = os.path.join(path, "MIDI Remote Scripts", "Showtime")

        try:
            rmtree(installpath)
        except OSError:
            pass

        print("Installing MIDI remote scripts to %s" % installpath)
        copytree(scriptspath, installpath, ignore=ignore_patterns('*.pyc', 'tmp*'))


class ConnectionCallbacks(ZST.ZstConnectionAdaptor):
    def __init__(self, client_gui):
        ZST.ZstConnectionAdaptor.__init__(self)
        self.gui = client_gui

    def on_connected_to_stage(self, client, server):
        print("Connected to server: {}".format(server.address))

    def on_disconnected_from_stage(self, client, server):
        print("Disconnected from server: {}".format(server.name))

    def on_server_discovered(self, client, server):
        print("Received server beacon: {}".format(server.name))
        self.gui.refresh_discovered_servers(client)

    def on_server_lost(self, client, server):
        print("Lost server beacon: {}".format(server.name))
        self.gui.refresh_discovered_servers(client)

    def on_synchronised_with_stage(self, client, server):
        pass


class EventLoop(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        self.setDaemon(True)
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            self.client.poll_once()
            time.sleep(1)

# UI
# -------------------
class Display(Frame):
    def __init__(self, parent=0):
        Frame.__init__(self, parent)

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
        Label(self, text="Live status").grid(row=0, column=0, sticky=E, padx=2, pady=4)
        Label(self, text="", textvariable=self.connectionStatusLabel).grid(row=0, column=1, sticky=W, padx=2, pady=4)

        # Install script buttons
        Label(self, text="Script installation").grid(row=1, column=0, sticky=E, padx=2, pady=4)
        self.installScriptsBtn = Button(self, text="Install Live scripts", command=install_midi_remote_scripts)
        self.installScriptsBtn.grid(row=1, column=1, sticky=(N, E, W), padx=2, pady=2)
        self.customPathInstallScriptsBtn = Button(self, text="Install Live scripts to custom location", command=self.open_custom_install_dialog)
        self.customPathInstallScriptsBtn.grid(row=2, column=1, sticky=(N, E, W), padx=2, pady=2)

        # Server list
        Label(self, text="Discovered servers").grid(row=3, column=0, sticky=E, padx=2, pady=2)
        self.serverListVar = StringVar(self)
        self.serverListVar.set("No servers found") 
        self.serverListOptions = OptionMenu(self, self.serverListVar, "")
        self.serverListOptions.config(state=DISABLED)
        self.serverListOptions.grid(row=3, column=1, sticky=(E, W), padx=2, pady=2)
        Label(self, text="Server address").grid(row=4, column=0, sticky=E, padx=2, pady=2)
        self.serverAddressVar = StringVar(self)
        self.serverAddressEntry = Entry(self, textvariable=self.serverAddressVar)
        self.serverAddressEntry.grid(sticky=(N, E, W), row=4, column=1, padx=2, pady=2)
        self.connectBtn = Button(self, text='Connect', command=self.connectBtn_pressed)
        self.connectBtn.grid(row=5, column=1, sticky=(N, E, W), pady=4)

        # Server log
        self.output = Text(self)
        self.output.grid(row=7, column=0, columnspan=2, rowspan=5, padx=2, pady=2, sticky=(N, E, S, W))
        sys.stdout = self
        sys.stderr = self
        self.consoleQueue = Queue.Queue()

        scrollbar = Scrollbar(self)
        scrollbar.grid(row=7, column=1, rowspan=5, sticky=(N, E, S), pady=2)
        self.output.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output.yview)
 
        # Midi UI
        self.midiPortVar = None
        self.midiPortOptions = None

    def register_client(self, client):
        self.client = client

    def connectBtn_pressed(self):
        self.client.join(self.serverAddressVar.get())

    def refresh_discovered_servers(self, client):
        self.serverListVar.set('')
        self.serverListOptions["menu"].delete(0, END)
        servers = client.get_discovered_servers()
        if servers:
            self.serverListOptions.config(state=NORMAL)
            if not self.serverListVar.get():
                self.select_server(servers[0])
        else:
            self.serverListVar.set("No servers found") 
            self.serverListOptions.config(state=DISABLED)
        for server in servers:
            self.serverListOptions["menu"].add_command(label=server.name, command=lambda value=server: self.select_server(server))


    def select_server(self, server):
        self.serverListVar.set(server.name)
        self.serverAddressVar.set(server.address)

    def create_midi_loopback_options(self, midirouter):
        Label(self, text="MIDI Loopback Port").grid(row=4, column=0, sticky=(E), padx=2, pady=2)
        self.midiPortVar = StringVar(self)
        self.midiPortVar.trace('w', self.midiport_changed)
        ports = ["None"]
        loopmidiports = [port for port in ports if "loopmidi" in port.lower()]
        if len(loopmidiports) > 0:
            self.midiPortVar.set(loopmidiports[0])

        self.midiPortOptions = OptionMenu(self, self.midiPortVar, *ports)
        self.midiPortOptions.grid(row=4, column=1, sticky=(S, E, W), padx=2, pady=2)

    def connectionstatus_changed(self, *args):
        text = "Insert connection status text here"
        print("\nAbleton Live connection status: %s\n\n" % text)
        self.connectionStatusLabel.set(text)

    def midiport_changed(self, *args):
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

        self.entry.insert(0, 'C:\\ProgramData\Ableton\Live 10.x.x')
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
class ShowtimeLiveBridgeClient:
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

        # Create GUI
        self.gui = None
        if not options.useCLI:
            root = Tk()
            self.gui = Display(root)

        # Create client
        self.create_client()
        self.gui.register_client(self.client)

        # Check if midi remote scripts are installed correctly
        installed_midi_remote_scripts = find_ableton_dirs()
        success = True

        print("\n-------------------------------------")
        print("Checking if Ableton Live is installed")
        print("Found %s instances of Ableton Live." % len(installed_midi_remote_scripts))
        for path in installed_midi_remote_scripts:
            script_path = os.path.join(path, "MIDI Remote Scripts", "Showtime")
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
            self.gui.update()

        # Enter into the idle loop to handle messages
        try:
            if options.useCLI:
                while 1:
                    time.sleep(1)
            else:
                self.gui.after(50, self.gui.write_log)
                self.gui.mainloop()

        except KeyboardInterrupt:
            print("\nExiting...")

    def __del__(self):
        if(hasattr(self, "server")):
            self.server.destroy()

        self.event_loop.stop()
        self.client.destroy()

    def create_client(self):
        self.client = ZST.ShowtimeClient()
        self.client.init("LiveBridge", True)
        self.connection_CB = ConnectionCallbacks(self.gui)
        self.client.add_connection_adaptor(self.connection_CB)

        # Set up event loop
        self.event_loop = EventLoop(self.client)
        self.event_loop.start()

        return self.client

def main():
    ShowtimeLiveBridgeClient()


if __name__ == "__main__":
    main()