FROM python:3.7

WORKDIR /app/models
RUN apt-get update
ADD "https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh" script.deb.sh
RUN bash script.deb.sh
RUN apt-get install git-lfs -y
RUN git-lfs install
RUN git clone https://huggingface.co/jegorkitskerkin/dialogpt-ir-bot

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --use-deprecated=legacy-resolver

RUN mkdir ./cache

EXPOSE 5055

CMD ["python", "-m", "rasa_sdk", "--actions", "actions"]