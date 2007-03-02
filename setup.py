#!/usr/bin/python

from tracnav import __version__ as VERSION
from setuptools import setup

# workaround for a setuptools bug: sdist doesn't honor package_data
from setuptools.command.sdist import sdist as _sdist
import glob, os

class mysdist(_sdist):

    def make_distribution(self):
        # add the package_data files to self.filelist
        for key, globs in self.distribution.package_data.iteritems(): 
            for pattern in globs:
                self.filelist.extend(glob.glob(os.path.join(key, pattern)))
        _sdist.make_distribution(self)


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
    cmdclass = { 'sdist' : mysdist }
)
