FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src/tracker /app/tracker
COPY src/common /app/common
COPY src/__init__.py /app/
COPY src/tracker/main.py /app/

EXPOSE 5000

CMD ["/bin/sh"]
