#!/bin/sh
chmod +x /app/tracker/server_config_route.sh
/app/tracker/server_config_route.sh

# for developing
tmux new -s server_session -d
tmux send-keys -t server_session 'python main.py' C-m 
tmux attach -t server_session

exec /bin/sh
