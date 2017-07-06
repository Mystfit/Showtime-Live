from setuptools import setup, find_packages
import glob
import os
import platform
from shutil import copytree, rmtree, ignore_patterns


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

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
    scriptspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "MidiRemoteScripts")

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


def install_showtime_package(custom_install_path=None):
    try:
        import showtime
    except ImportError as e:
        print("Couldn't import Showtime python egg. Skipping egg installation.")
        return

    scriptspath = os.path.dirname(showtime.__file__)

    liveinstallations = []
    if custom_install_path:
        liveinstallations = [os.path.join(custom_install_path, "Resources")]
    else:
        liveinstallations = find_ableton_dirs()

    for path in liveinstallations:
        installpath = os.path.join(path, "Python", "site-packages", os.path.basename(scriptspath))

        try:
            rmtree(installpath)
        except OSError:
            pass

        print("Installing Showtime python library to %s" % installpath)
        copytree(scriptspath, installpath, ignore=ignore_patterns('*.pyc', 'tmp*'))

install_midi_remote_scripts()
install_showtime_package()

platform_options = None
if platform.system() == 'Darwin':
      platform_options = dict(
         setup_requires=['py2app'],
         app=['Showtime_Live/ShowtimeLiveServer.py'],
         options=dict(py2app=dict(argv_emulation=True))
      )

setup(name='Showtime-Live',
      version='1.5.1',
      description='Showtime Bridge for Ableton Live.',
      long_description=read('README.md'),
      author='Byron Mallett',
      author_email='byronated@gmail.com',
      url='http://github.com/Mystfit/Showtime-Live',
      scripts=['scripts/ShowtimeLiveServer.py'],
      license='MIT',
      install_requires=["rtmidi"],
      packages=find_packages(),
      **platform_options
      )
