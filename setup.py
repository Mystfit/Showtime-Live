from setuptools import setup, find_packages
import glob
import os
import platform
from shutil import rmtree, ignore_patterns, copyfile
from distutils.dir_util import copy_tree

setup(
  name          = 'ShowtimeLive',
  version       = '1.0.0',
  author        = "Byron Mallett",
  author_email  = "byronated@gmail.com",
  description   = """Ableton Live bindings for Showtime""",
  url = "https://github.com/mystfit/Showtime-Live",
  packages = find_packages(),
  install_requires = ['rpyc', 'defusedxml', 'showtimepython']
)
