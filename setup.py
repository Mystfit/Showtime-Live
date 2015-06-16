import os
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='Showtime-Live',
      version='1.1',
      description='Showtime Bridge for Ableton Live.',
      long_description=read('README.md'),
      author='Byron Mallett',
      author_email='byronated@gmail.com',
      url='http://github.com/Mystfit/Showtime-Live',
      scripts=['scripts/LiveShowtimeClient.py'],
      license='MIT',
      install_requires=["Showtime-Python", "rtmidi_python", "Pyro<=3.16"],
      packages=find_packages()
      )
