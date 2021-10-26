# syntax=docker/dockerfile:1
FROM python:3.7


WORKDIR /app/models
ADD "https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh" script.deb.sh
RUN bash script.deb.sh
RUN apt-get install git-lfs
RUN git-lfs install
#RUN git clone https://huggingface.co/microsoft/DialoGPT-medium
RUN git clone https://huggingface.co/jegorkitskerkin/dialogpt-twitter-ubuntu


WORKDIR /app
COPY __init__.py actions/__init__.py
COPY actions.py actions/actions.py
#COPY housing.db actions/housing.db
COPY requirements.txt .

USER root
RUN mkdir ./cache
RUN --mount=type=cache,target=/root/.cache \
pip install -r requirements.txt --use-deprecated=legacy-resolver

RUN rasa telemetry disable

EXPOSE 5055

CMD ["rasa", "run", "actions"]