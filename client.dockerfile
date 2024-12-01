FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src/client /app/client
COPY src/torrents /app/torrents
COPY src/common /app/common
COPY src/__init__.py /app/
COPY src/client/main.py /app/

CMD ["/bin/sh"]