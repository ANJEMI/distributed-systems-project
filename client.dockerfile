FROM python:3.10-alpine

# OPTIONAL 
RUN apk add --no-cache ranger
RUN apk add --no-cache vim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src/client /app/client
COPY src/torrents /app/torrents
COPY src/common /app/common
COPY src/__init__.py /app/
COPY src/client/main.py /app/

EXPOSE 6881

COPY src/client/start_client.sh /app/start_client.sh
RUN chmod +x /app/start_client.sh
ENTRYPOINT ["/app/start_client.sh"]
