FROM rasa/rasa

WORKDIR /app

COPY data/ ./data
COPY tests ./tests
COPY config.yml ./
COPY credentials.yml ./
COPY domain.yml ./
COPY endpoints.yml ./

RUN rasa train

EXPOSE 5005

CMD ["run"]