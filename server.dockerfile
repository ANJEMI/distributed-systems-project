FROM python:3.10-alpine

# OPTIONAL 
RUN apk add --no-cache vim ranger tmux

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src/tracker /app/tracker
COPY src/common /app/common
COPY src/__init__.py /app/
COPY src/tracker/main.py /app/

EXPOSE 8080

COPY src/tracker/start_server.sh /app/start_server.sh
RUN chmod +x /app/start_server.sh
ENTRYPOINT ["/app/start_server.sh"]

