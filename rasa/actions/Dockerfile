FROM python:3.7

WORKDIR /app

COPY __init__.py actions/__init__.py
COPY actions.py actions/actions.py
COPY requirements.txt .

USER root
RUN mkdir ./cache
RUN --mount=type=cache,target=/root/.cache \
pip install -r requirements.txt
#USER 1001

EXPOSE 5055

CMD ["rasa", "run", "actions"]