================
RadioCo recorder
================
**A recorder program**.

This program communicates with RadioCo

Main Program
============

https://github.com/iago1460/django-radio

Website
-------

http://radioco.org/


Installation
============

Requirements
------------

- Python 2.7



In the project folder.

Optional, but recommended steps to install virtualenv::
	
	sudo apt-get install python-virtualenv
	virtualenv .
 	source bin/activate
 
Install requirements::

	sudo apt-get install python-dev
	pip install -r requirements.txt

Install arecorder and oggenc::

    sudo apt-get install alsa-utils
    sudo apt-get install vorbis-tools

Usage
-----

run command::
	
	python main.py
