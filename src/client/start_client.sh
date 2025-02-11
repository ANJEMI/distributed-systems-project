#!/bin/sh
chmod +x /app/client/client_config_route.sh
/app/client/client_config_route.sh

# for developing
python main.py

exec /bin/sh
