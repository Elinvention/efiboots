#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='efibootmgr-gui',
      version='1.0',
      # Modules to import from other scripts:
      packages=find_packages(),
      # Executables
      scripts=["efibootmgr_gui.py"],

      data_files = [
            ('share/applications', ['efibootmgr.desktop']),
      ],
     )
