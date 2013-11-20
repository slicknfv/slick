import sys
import os
import shutil
from optparse import OptionParser

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

EXTENSION_NAME = "ndpi_cython"

parser = OptionParser()
parser.add_option("-c", "--clean",
                  dest="clean", default=True,
                  help="Clean the already compiled build.")


def clean_build():
    """Use this function to clean the previous 
    build."""
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            if (name.startswith(EXTENSION_NAME) and not(name.endswith(".pyx") or name.endswith(".pxd") or name.endswith(".py") or name.endswith("*.h") or name.endswith("*.c"))):
                os.remove(os.path.join(root, name))
        for name in dirs:
            if (name == "build"):
                shutil.rmtree(name)

def setup_dpi():
    sourcefiles = ['ndpi_reader.pyx']
    ext_modules = [Extension(EXTENSION_NAME, # Extension name
                              sourcefiles,
                              libraries = ["pcap"],
                              extra_compile_args=["-O3", "-I ./nDPI/src/include/"],
                              extra_link_args=["-L ./nDPI/src/lib/.libs/"],
                              extra_objects = ["./nDPI/src/lib/.libs/libndpi.a"],
                              )]
    setup(
        name = 'Deep Packet Inspection',
        cmdclass = {'build_ext': build_ext},
        ext_modules = ext_modules
    )

clean_build()
setup_dpi()
