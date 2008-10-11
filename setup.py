#!/usr/bin/python

from tracnav import __version__ as VERSION
from setuptools import setup

setup(
    name = 'TracNav',
    version = VERSION,
    packages = ['tracnav'],
    package_data = { 'tracnav': ['htdocs/css/*.css'] },
    author = 'Bernhard Haumacher',
    author_email = 'haui@haumacher.de',
    maintainer = 'Thomas Moschny',
    maintainer_email = 'moschny@ipd.uni-karlsruhe.de',
    url = 'http://svn.ipd.uka.de/trac/javaparty/wiki/TracNav',
    description = 'The Navigation Bar for Trac',
    entry_points={'trac.plugins': ['TracNav = tracnav.tracnav']},
    keywords = 'trac toc',
    license = 'GPL',
)
