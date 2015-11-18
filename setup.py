import os, platform, glob
from shutil import copytree, rmtree, ignore_patterns
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def install_midi_remote_scripts():
      installpath = ""
      liveinstallations = None

      scriptspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Showtime_Live", "Midi_Remote_Scripts", "ShowtimeBridge")

      if platform.system() == "Windows":
            liveinstallations = glob.glob(os.path.abspath(os.path.join(os.getenv("PROGRAMDATA"), "Ableton", "Live*")) + "*")
            liveinstallations = [os.path.join(path, "Resources", "MIDI Remote Scripts", "ShowtimeBridge") for path in liveinstallations]

      elif platform.system() == "Darwin":
            liveinstallations = glob.glob(os.path.abspath(os.path.join(os.path.sep, "Applications", "Ableton Live")) + "*")
            liveinstallations = [os.path.join(path, "Contents", "App-Resources", "MIDI Remote Scripts", "ShowtimeBridge") for path in liveinstallations]

      if len(liveinstallations) > 0:
            for path in liveinstallations:
                  try:
                        rmtree(path)
                  except:
                        pass

                  print("Installing midi remote scripts to {0}".format(path))
                  copytree(scriptspath, path, ignore=ignore_patterns('*.pyc', 'tmp*'))
      else:
            print("No Ableton Live installations detected.")

setup(name='Showtime-Live',
      version='1.3',
      description='Showtime Bridge for Ableton Live.',
      long_description=read('README.md'),
      author='Byron Mallett',
      author_email='byronated@gmail.com',
      url='http://github.com/Mystfit/Showtime-Live',
      scripts=['scripts/LiveShowtimeClient.py'],
      license='MIT',
      install_requires=["Showtime-Python", "rtmidi_python", "zeroconf"],
      packages=find_packages()
      )

install_midi_remote_scripts()
