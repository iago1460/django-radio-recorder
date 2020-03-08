FROM python:3.7.6-buster

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -yq --fix-missing \
    jack-capture \
    lame \
    alsa-utils \
    vorbis-tools \
    netcat \
    && apt-get clean

RUN pip3 install --upgrade pip setuptools virtualenv

COPY ./requirements*.txt /

ARG requirements=requirements.txt
RUN pip3 install -r /$requirements

COPY ./radioco_recorder/ /workdir/radioco_recorder/
WORKDIR /workdir/

ENTRYPOINT [ "python3", "-m", "radioco_recorder", "--output",  "/output", "--tmp", "/tmp"]
