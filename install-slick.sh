#!/bin/sh

BASE_DIR=$PWD  # by default, we'll assume you're running it from /home/mininet/middlesox

if [ $# -gt 1 ]; then
	echo "Usage: $0 [middlesox directory]"
	exit
elif [ $# -eq 1 ]; then
	BASE_DIR=$1
fi

if [ ! -d $BASE_DIR ]; then
	echo "Sorry, but directory $BASE_DIR does not exist"
	echo "Usage: $0 [middlesox directory]"
	exit
fi

ORIG_DIR=$PWD
cd $BASE_DIR
BASE_DIR=$PWD
ARCHIVE_DIR=$BASE_DIR/archive
LIB_DIR=$BASE_DIR/lib

if [ ! -d $ARCHIVE_DIR ] || [ ! -d $LIB_DIR ]; then
	echo "The $BASE_DIR directory does not have the proper mininet and middlesox directories"
	echo "Usage: $0 [middlesox directory]"
	exit
fi

echo ""
echo ""
echo "Performing install from base directory $BASE_DIR/"


echo ""
echo ""
echo "*** Installing python-setuptools so I can easy_install..."
sudo apt-get install python-setuptools

echo ""
echo ""
echo "*** Adding support for SSHv3..."
sudo easy_install paramiko
cd $ARCHIVE_DIR/scp.py/
sudo python setup.py install

echo ""
echo ""
echo "*** Installing other dependencies"
sudo easy_install jsonpickle
sudo apt-get install python-dpkt

echo ""
echo ""
echo "*** Installing pcap (for shim)"
sudo apt-get install python-dev
sudo apt-get install libpcap-dev
cd $ARCHIVE_DIR
tar xzf pcap_ylg-1.1.tar.gz
cd $ARCHIVE_DIR/pcap_ylg-1.1/
sudo python setup.py install
cp $ARCHIVE_DIR/pcap_ylg-1.1/pcap.so $LIB_DIR


echo ""
echo ""
echo "*** Installing rpyc (for shim)"
sudo easy_install rpyc

echo ""
echo ""
echo "*** Installing scapy..."
cd $ARCHIVE_DIR
tar xzf scapy-latest.tar.gz
cd $ARCHIVE_DIR/scapy-2.1.0
sudo python setup.py install

echo "*** Installing c-algorithms for pybloomfiltermmap..."
cd $ARCHIVE_DIR
tar xzf c-algorithms-1.2.0.tar.gz
cd $ARCHIVE_DIR/c-algorithms-1.2.0
./configure
make
sudo make install
sudo ldconfig

echo ""
echo ""
echo "*** Installing pybloomfiltermmap..."
sudo easy_install pybloomfiltermmap

echo ""
echo ""
echo "*** Creating/Updating links to libraries..."
sudo ldconfig

echo ""
echo ""
echo "*** SLICK INSTALL COMPLETE ***"
echo "Please scroll up to ensure that there were no failures (this script does not yet automatically check return statuses)"
echo ""
echo "Be sure to add the following to your appropriate shell setup:"
echo "export PYTHONPATH=/home/mininet/middlesox/pox:/home/mininet/mininet:/home/mininet/pox"

cd $ORIG_DIR
