RadioCo recorder
================
RadioCo utility for recording podcasts.
This program can record live audio, it communicates with RadioCo automatically


Documentation
=============

Please head over to our `documentation <http://django-radio.readthedocs.org/>`_ for all
the details on how to install, extend and use django radio.


Installation
============

Local installation Requirements
-------------------------------

- Python 3.7
- Recording software (jack_capture / lame)

Local installation steps:

    virtualenv venv
    source venv/bin/activate

    pip install -r requirements.txt
    pip install -e .
    
    radioco-recorder --help


Docker Requirements
-------------------------------

Tweak the .env variables and then:
    
    docker-compose up --build
