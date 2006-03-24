#!/usr/bin/python

from setuptools import setup
from tracnav.tracnav import __version__ as version

setup(
    name = 'TracNav',
    version = version,
    packages = ['tracnav'],
    package_data = { 'tracnav': ['htdocs/css/*.css'] },
    author = 'Bernhard Haumacher',
    author_email = 'haui@haumacher.de',
    maintainer = 'Thomas Moschny',
    maintainer_email = 'moschny@ipd.uni-karlsruhe.de',
    url = 'http://svn.ipd.uka.de/trac/javaparty/wiki/TracNav',
    description = 'The navigation bar for Trac',
    entry_points={'trac.plugins': 'TracNav = tracnav'},
    keywords = 'trac toc',
    license = 'GPL',
)
