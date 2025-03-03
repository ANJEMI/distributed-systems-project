#!/bin/sh
chmod +x /app/client/client_config_route.sh
/app/client/client_config_route.sh

# for developing
tmux new -s client_session -d
tmux send-keys -t client_session 'python main.py' C-m 
tmux attach -t client_session

exec /bin/sh
