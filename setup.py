#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='efiboots',
      version='1.0',
      # Modules to import from other scripts:
      packages=find_packages(),
      py_modules=['efiboots'],
      # Executables
      scripts=["efiboots"],

      data_files = [
            ('share/applications', ['efiboots.desktop']),
      ],
     )
