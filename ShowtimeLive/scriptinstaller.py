import os
import site
import platform
import glob
import importlib
from shutil import copytree, rmtree, ignore_patterns

# MIDI Remote Script installation
# -------------------------------
def find_ableton_resource_dirs():
    liveinstallations = []
    if platform.system() == "Windows":
        liveinstallations = glob.glob(os.path.abspath(os.path.join(os.getenv("PROGRAMDATA"), "Ableton", "Live*")) + "*")
    elif platform.system() == "Darwin":
        liveinstallations = glob.glob(os.path.abspath(os.path.join(os.path.sep, "Applications", "Ableton Live")) + "*")
    return [ableton_resource_dir(path) for path in liveinstallations]

def ableton_resource_dir(live_dir):
    if platform.system() == "Windows":
        return os.path.join(live_dir, "Resources")
    if platform.system() == "Darwin":
        return os.path.join(live_dir, "Contents", "App-Resources")
    raise("Only Mac and Windows supported")


def install_midi_remote_scripts(install_paths=None):
    install_paths = find_ableton_resource_dirs() if not install_paths else install_paths
    scriptspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "MidiRemoteScripts")

    for path in install_paths:
        installpath = os.path.join(path, "MIDI Remote Scripts", "ShowtimeLive")

        try:
            rmtree(installpath)
        except OSError:
            pass

        print("Installing MIDI remote scripts to %s" % installpath)
        copytree(scriptspath, installpath, ignore=ignore_patterns('*.pyc', 'tmp*'))


def install_package(package_name, install_paths):
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        print("Couldn't import package. Error: {}".format(e))
        return

    for path in install_paths:
        live_site_packages = os.path.join(path, "Python", "site-packages")
        
        # Remove existing packages
        old_packages = glob.glob(os.path.join(live_site_packages, package.__name__ + "*"))
        try:
            for old_package in old_packages:
                print("Removing old package: {0}".format(old_package))
                rmtree(old_package)
        except OSError as e:
            print("Couldn't remove old package {0}. Reason: {1}".format(old_package, e))
        pass

        # Copy packages
        print("Package path is {0}".format(package.__path__[0]))
        dest = os.path.join(live_site_packages, os.path.basename(package.__path__[0]))
        print("Installing package to {}".format(dest))
        try:
            copytree(package.__path__[0], dest, ignore=ignore_patterns('*.pyc', 'tmp*'))
        except OSError as e:
            print("Failed to copy package {} to Live's site-packages folder. Reason: {}".format(package.__name__, e))
        
        # Rename .dylib extensions to .so otherwise Live's python won't load the extensions
        for root, dirs, files in os.walk(dest):
            for file in files:
                if file.endswith(".dylib"):
                    new_name = os.path.join(root, os.path.splitext(os.path.basename(file))[0] + ".so")
                    print("Renaming {} to {}".format(os.path.join(root, file), new_name))
                    os.rename(os.path.join(root, file), new_name)

def install_dependencies(install_paths=None):
    install_paths = find_ableton_resource_dirs() if not install_paths else install_paths
    install_package("showtime", install_paths)
    install_package("rpyc", install_paths)
    install_package("plumbum", install_paths)


if __name__ == "__main__":
    install_dependencies()
    install_midi_remote_scripts()
