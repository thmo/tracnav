#!/usr/bin/python

from setuptools import setup

PACKAGE = 'TracNav'
VERSION = '3.90'

setup(
    name = PACKAGE,
    version = VERSION,
    packages = ['tracnav'],
    package_data = { 'tracnav': ['htdocs/css/*.css'] },
    author = 'Bernhard Haumacher, Thomas Moschny',
    url = 'http://svn.ipd.uka.de/trac/javaparty/wiki/TracNav',
    description = 'The navigation bar for Trac',
    entry_points={'trac.plugins': '%s = tracnav' % PACKAGE},
    licence = 'GPL',
)
