FROM python:3.11.9

WORKDIR /app

COPY . ./

RUN pip install -r requirements.txt

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "main:app"]