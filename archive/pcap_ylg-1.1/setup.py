#!/usr/bin/env python

PKG_NAME = 'pcap_ylg'
PKG_VERS = '1.1'

import sys

from distutils.core import setup, Command
from distutils.extension import Extension

from pydoc import cli

class DocGen(Command):
    description = 'generate html documentation with '
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
    
class PyDocGen(DocGen):
    description = DocGen.description + "`pydoc'"
    
    def run(self):
        sys.argv = ['pydoc', '-w', 'pcap']
        cli()
CMDCLASS = {'doc': PyDocGen}

try:
    from epydoc.cli import cli as ecli

    class EPyDocGen(DocGen):
        description = DocGen.description + "`epydoc'"
        
        def run(self):
            sys.argv = ['epydoc', '--html', 'pcap']
            ecli()
    CMDCLASS['edoc'] = EPyDocGen
except ImportError:
    pass

import os, platform

DEFINE_MACROS, OS = [], platform.system()
if OS == 'Linux':
    DEFINE_MACROS.append(('OS_LINUX', '1'))
elif OS == 'FreeBSD':
    DEFINE_MACROS.append(('OS_FREEBSD', '1'))

setup(
    name=PKG_NAME,
    version=PKG_VERS,
    description='PCAP library wrapper',
    long_description='see file README.txt',
    url='http://www.pps.univ-paris-diderot.fr/~ylg/python/',
    author='Yves Legrandgerard',
    author_email='ylg@pps.jussieu.fr',
    license='DWTFYWT',
    platforms=['Linux', 'FreeBSD'],
    ext_modules=[Extension('pcap', ['pcap.c'],
                           define_macros=DEFINE_MACROS, libraries=['pcap'])
                 ],
    cmdclass=CMDCLASS
)
