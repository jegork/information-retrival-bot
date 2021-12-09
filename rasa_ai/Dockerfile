FROM rasa/rasa:2.8.15

WORKDIR /app

COPY data/ ./data
COPY tests ./tests
COPY config.yml ./
COPY credentials.yml ./
COPY domain.yml ./
COPY endpoints.yml ./
COPY endpoints.aws.yml ./
COPY connectors/* ./connectors/

RUN rasa train

EXPOSE 5005

CMD ["run"]