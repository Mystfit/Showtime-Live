from setuptools import setup, find_packages
# import py2exe

setup(name='Showtime-Live',
      version='1.0',
      description='Showtime Bridge for Ableton Live.',
      author='Byron Mallett',
      author_email='byronated@gmail.com',
      url='http://github.com/Mystfit/Showtime-Live',
      scripts = [
        'Showtime_Live/LiveShowtimeClient.py'
    	],
      license='MIT',
      install_requires=["Showtime-Python", "rtmidi_python", "Pyro<=3.16"],
      packages=find_packages()
      )
