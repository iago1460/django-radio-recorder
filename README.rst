================
RadioCo recorder
================
**A recorder program**.

This program can record live audio, it communicates with RadioCo automatically


Documentation
=============

Please head over to our `documentation <http://django-radio.readthedocs.org/>`_ for all
the details on how to install, extend and use django radio.


Installation
============

Requirements
------------

- Python 2.7


In the project folder.

Optional, but recommended steps to install virtualenv::
	
	sudo apt-get install python-virtualenv
	virtualenv venv
 	source venv/bin/activate
 
Install requirements::

	sudo apt-get install python-dev
	pip install -r requirements.txt

Install arecorder and oggenc if you use default recording settings::

    sudo apt-get install alsa-utils vorbis-tools

Usage
-----

run command::
	
	python main.py
