from setuptools import setup, find_packages
import glob
import os
import platform

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

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
      install_requires=["Showtime-Python", "rtmidi", "zeroconf"],
      packages=find_packages(),
      **platform_options
      )
