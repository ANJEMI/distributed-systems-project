#!/bin/sh
chmod +x /app/tracker/server_config_route.sh
/app/tracker/server_config_route.sh

# for developing
python main.py

exec /bin/sh
