#!python
import Queue
import os
import time
import threading
from optparse import OptionParser

import tkFileDialog
import tkSimpleDialog
from Tkinter import *

import rpyc
from rpyc.core import SlaveService
from rpyc.utils.server import ThreadedServer
from rpyc.utils.classic import DEFAULT_SERVER_PORT, DEFAULT_SERVER_SSL_PORT
from rpyc.utils.helpers import classpartial

import scriptinstaller
import showtime.showtime as ZST

DEFAULT_CLIENT_NAME = "LiveBridge"

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

class RPCLoop(threading.Thread):
    def __init__(self, bridge):
        threading.Thread.__init__(self)
        self.bridge = bridge
        self.setDaemon(True)

    def run(self):
        self.bridge.start()


class LiveZSTService(rpyc.Service):
    def __init__(self, client):
        self.zst_client = client

    def exposed_get_client(self):
        return self.zst_client

    def exposed_get_module(self):
        return ZST

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
        self.installScriptsBtn = Button(self, text="Install Live scripts", command=self.install_scripts_pressed)
        self.installScriptsBtn.grid(row=1, column=1, sticky=(N, E, W), padx=2, pady=2)
        self.customPathInstallScriptsBtn = Button(self, text="Install Live scripts to custom location", command=self.open_custom_install_dialog)
        self.customPathInstallScriptsBtn.grid(row=2, column=1, sticky=(N, E, W), padx=2, pady=2)

        # Server list
        Label(self, text="Discovered servers").grid(row=3, column=0, sticky=E, padx=2, pady=2)
        self.serverListVar = StringVar(self)
        self.serverListVar.set("No servers found") 
        self.serverList = Listbox(self, selectmode=SINGLE, height=4, listvariable="a b c")
        self.serverList.grid(row=3, column=1, sticky=(E, W), padx=2, pady=2)
        self.serverList.bind('<<ListboxSelect>>', self.click_serverlist)

        # Server address
        Label(self, text="Server address").grid(row=4, column=0, sticky=E, padx=2, pady=2)
        self.serverAddressVar = StringVar(self)
        self.serverAddressEntry = Entry(self, textvariable=self.serverAddressVar)
        self.serverAddressEntry.grid(sticky=(N, E, W), row=4, column=1, padx=2, pady=2)
        
        # Client options
        Label(self, text="Client name").grid(row=5, column=0, sticky=E, padx=2, pady=2)
        self.clientNameVar = StringVar(self, DEFAULT_CLIENT_NAME)
        self.clientNameEntry = Entry(self, textvariable=self.clientNameVar)
        self.clientNameEntry.grid(row=5, column=1, sticky=(N, E, W), padx=2, pady=2)

        # Connection button
        self.connectBtn = Button(self, text='Connect', command=self.connectBtn_pressed)
        self.connectBtn.grid(row=6, column=1, sticky=(N, E, W), pady=4)

        # Server log
        self.output = Text(self)
        self.output.grid(row=7, column=0, columnspan=2, rowspan=5, padx=2, pady=2, sticky=(N, E, S, W))
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
        if self.serverAddressVar.get():
            self.client.get_root().set_name(self.clientNameVar.get())
            self.client.join(self.serverAddressVar.get())
        else:
            print("No server address specified.")

    def install_scripts_pressed(self):
        scriptinstaller.install_midi_remote_scripts()
        scriptinstaller.install_dependencies()

    def refresh_discovered_servers(self, client):
        self.serverListVar.set('')
        self.serverList.delete(0, END)
        servers = client.get_discovered_servers()
        if servers:
            self.serverList.config(state=NORMAL)
            if not self.serverListVar.get():
                self.select_server(servers[0].name)
        else:
            self.serverListVar.set("No servers found") 
            self.serverList.config(state=DISABLED)
        for server in servers:
            self.serverList.insert(END, server.name)

    def click_serverlist(self, event):
        selected_index = self.serverList.curselection()
        if not selected_index:
            return
        server_name = self.serverList.get(self.serverList.curselection())
        if server_name:
            self.select_server(server_name)

    def select_server(self, server_name):
        self.serverListVar.set(server_name)
        server = self.client.get_discovered_server(server_name)
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

        self.entry.insert(0, 'C:\\ProgramData\\Ableton\\')
        self.browseBtn = Button(master, text="Browse", command=self.askdirectory)
        self.browseBtn.grid(row=1, column=1, sticky=W)
        return self.entry  # initial focus

    def askdirectory(self):
        """Returns a selected directory name."""
        options = {
            'initialdir': 'C:\\ProgramData\\Ableton\'',
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
        path = scriptinstaller.ableton_resource_dir(os.path.normpath(self.entry.get()))
        scriptinstaller.install_dependencies([path])
        scriptinstaller.install_midi_remote_scripts([path])

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
        if not options.useCLI:
            self.create_gui()

        # Create client
        self.create_client()
        self.create_bridge()
        self.gui.register_client(self.client)

        # Check if midi remote scripts are installed correctly
        live_resource_dirs = scriptinstaller.find_ableton_resource_dirs()
        success = True

        if options.installScripts:
            scriptinstaller.install_midi_remote_scripts(options.liveCustomFolder)

        if not options.useCLI:
            # Redirect stdout to GUI log
            sys.stdout = self.gui
            sys.stderr = self.gui
            self.gui.update()

        print("Checking if Ableton Live is installed.")
        print("Found {} instance{} of Ableton Live.".format(len(live_resource_dirs), "s" if len(live_resource_dirs) > 1 else ""))
        for path in live_resource_dirs:
            script_path = os.path.join(path, "MIDI Remote Scripts", "Showtime")
            if not os.path.isdir(script_path):
                success = False
                print("Showtime-Live scripts not installed in {}.".format(script_path))

        if success:
            print("Showtime-Live scripts found.")
        else:
            print("Some local Ableton Live installations do not have the Showtime-Live Midi Remote Scripts installed.")
            print("Either click the \"Install Scripts\" button or restart with the command line flag --install.")

        # Enter into the idle loop to handle messages
        try:
            if not options.useCLI:
                self.gui.after(50, self.gui.write_log)
                self.gui.mainloop()
            else:
                while 1:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")

    def __del__(self):
        if(hasattr(self, "server")):
            self.server.destroy()

        self.client_loop.stop()
        self.client.destroy()

    def create_client(self):
        self.client = ZST.ShowtimeClient()
        self.client.init(DEFAULT_CLIENT_NAME, True)
        self.connection_CB = ConnectionCallbacks(self.gui)
        self.client.add_connection_adaptor(self.connection_CB)
        self.client_loop = EventLoop(self.client)
        self.client_loop.start()

    def create_gui(self):
        self.root = Tk()
        self.gui = Display(self.root)

    def create_bridge(self):
        service = classpartial(LiveZSTService, self.client)
        self.bridge = ThreadedServer(service, port=DEFAULT_SERVER_PORT, protocol_config={
            'allow_public_attrs': True
        })
        self.bridge_loop = RPCLoop(self.bridge)
        self.bridge_loop.start()
        print("RPyC server available at localhost:{}".format(DEFAULT_SERVER_PORT))


def main():
    ShowtimeLiveBridgeClient()


if __name__ == "__main__":
    main()