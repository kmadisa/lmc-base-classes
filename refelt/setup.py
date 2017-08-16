#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the RefA project
#
#
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.

import os
import sys
from setuptools import setup, find_packages

setup_dir = os.path.dirname(os.path.abspath(__file__))

# make sure we use latest info from local code
sys.path.insert(0, setup_dir)

readme_filename = os.path.join(setup_dir, 'README.rst')
with open(readme_filename) as file:
    long_description = file.read()

release_filename = os.path.join(setup_dir, 'release.py')
exec(open(release_filename).read())

setup(name=name,
      version=version,
      description='An SKA Refence Element (Ref)',
      author="MeerKAT CAM Team",
      author_email="cam atska.ac.za",
      packages=find_packages(),  #pack
      include_package_data=True,
      entry_points={'console_scripts':[
          'RefMaster = refelt.RefMaster:main',
          'RefA = refelt.RefA:main',
          'RefAchild = refelt.RefAchild:main',
          'RefB = refelt.RefB:main',
          'RefBchild = refelt.RefBchild:main',
          'Rack = refelt.Rack:main',
          'Server = refelt.Server:main',
          'Switch = refelt.Switch:main',
          'PDU = refelt.PDU:main',
          'FileLogger = refelt.FileLogger:main',
          'RefTelState = refelt.RefTelState:main',
          'RefAlarms = refelt.RefAlarms:main',
          ]},
      url='http://ska.ac.za/',
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "License :: Other/Proprietary License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Scientific/Engineering :: Astronomy"],
      platforms="All Platforms",
      setup_requires=[],
      install_requires=[],
      tests_require=[
          "nose",
          "coverage",
          "nosexcover",
          "unittest2"
      ],
      keywords="generic element ref elt lmc ska",
      test_suite="nose.collector",
      zip_safe=False)