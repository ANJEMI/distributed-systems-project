FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src/client /app/client
COPY src/torrents /app/torrents
COPY src/common /app/common
COPY src/__init__.py /app/
COPY src/client/main.py /app/

EXPOSE 6881

RUN chmod +x /app/client/client_config_route.sh
RUN ./app/client/client_config_route.sh

CMD ["/bin/sh"]
