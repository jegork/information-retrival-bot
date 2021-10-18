FROM python:3.7-slim as base
WORKDIR /app
COPY main.py .
COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]