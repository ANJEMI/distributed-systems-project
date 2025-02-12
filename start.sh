#!/bin/bash

# Colors
RESET="\033[0m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BLUE="\033[94m"

ROCKET="🚀"
CHECK_MARK="✅"
WARNING="🚧"
CRASH="❌"
SHELL=""

NUM_SERVERS=1
NUM_CLIENTS=2

# Check status function
check_status() {
    if [ $? -ne 0 ]; then
        echo -e "${RED}${WARNING} Error occurred during the last operation.${RESET}"
        exit 1
    fi
}

stop_existing_container() {
    local container_name=$1

    if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
        echo -e "${YELLOW}${WARNING} Container $container_name already exists. Stopping and removing it...${RESET}"
        docker stop "$container_name" >/dev/null 2>&1
        docker rm "$container_name" >/dev/null 2>&1
        check_status
    fi
}

stop_containers_using_network() {
    local network_name=$1
    local containers=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$network_name")

    if [ -n "$containers" ]; then
        echo -e "${YELLOW}Stopping containers using network $network_name: $containers${RESET}"
        for container in $containers; do
            docker stop "$container"
            check_status
        done
    fi
}

create_network() {
    local network_name=$1
    local subnet=$2

    if docker network ls | grep -q "$network_name"; then
        echo -e "${WARNING} ${YELLOW}Network $network_name already exists. Removing it...${RESET}"
        stop_containers_using_network "$network_name"
        docker network rm "$network_name"
        check_status
    fi

    docker network create "$network_name" --subnet "$subnet"
    check_status
}

identify_terminal() {
    # in case of using another terminal this function must be modified
    if command -v kitty &> /dev/null; then
        SHELL="kitty"
    elif command -v gnome-terminal &> /dev/null; then
        SHELL="gnome-terminal"
    else
        echo -e "${CRASH} ${RED}Neither kitty nor gnome-terminal was found. You must modify identify_terminal() manually.${RESET}"
        exit 1
    fi
}

# Create the networks
echo -e "${BLUE}${ROCKET} Creating networks...${RESET}"
create_network "bitclients" "10.0.10.0/24"
create_network "bitservers" "10.0.11.0/24"

# Set up the router
echo -e "${BLUE}${ROCKET} Setting up router...${RESET}"
docker build -t router -f src/router/router.Dockerfile .
check_status
docker run -itd --rm --name router router
check_status
docker network connect --ip 10.0.10.254 bitclients router
check_status
docker network connect --ip 10.0.11.254 bitservers router
check_status

# Set up client and server
echo -e "${BLUE}${ROCKET} Building client and server images...${RESET}"
docker build -t bitserver -f server.dockerfile .
check_status
docker build -t bitclient -f client.dockerfile .
check_status

# Identify Shell to run the docker comands
identify_terminal

# uncomment later
# Run server
# echo -e "${BLUE}${ROCKET} Running server...${RESET}"
# for ((i=1; i<=NUM_SERVERS; i++)); do
#     server_name="bitserver$i"
#     stop_existing_container "$server_name"
#     $SHELL --title "Server #$i" -- bash -c "echo 'This is server #$i' && docker run --rm --privileged -it --name $server_name --cap-add NET_ADMIN --network bitservers bitserver; exec bash" &
#     check_status
# done

# # Run clients
# echo -e "${BLUE}${ROCKET} Running clients...${RESET}"
# for ((i=1; i<=NUM_CLIENTS; i++)); do
#     client_name="bitclient$i"
#     stop_existing_container "$client_name"
#     $SHELL --title "Client #$i" -- bash -c "echo 'This is client #$i' && docker run --rm --privileged -it --name $client_name --cap-add NET_ADMIN --network bitclients bitclient; exec bash" &
#     check_status
# done

# Run server
echo -e "${BLUE}${ROCKET} Running server...${RESET}"
for ((i=1; i<=NUM_SERVERS; i++)); do
    server_name="bitserver$i"
    stop_existing_container "$server_name"
    $SHELL --title "Server #$i" -- bash -c "echo 'This is server #$i' && docker run --privileged -it --name $server_name --cap-add NET_ADMIN --network bitservers \
        -v $(pwd)/src/tracker:/app/tracker \
        -v $(pwd)/src/common:/app/common \
        -v $(pwd)/src/__init__.py:/app/__init__.py \
        -v $(pwd)/src/tracker/main.py:/app/main.py bitserver; exec zsh" &
    check_status
done

# Run clients
echo -e "${BLUE}${ROCKET} Running clients...${RESET}"
for ((i=1; i<=NUM_CLIENTS; i++)); do
    client_name="bitclient$i"
    stop_existing_container "$client_name"
    $SHELL --title "Client #$i" -- bash -c "echo 'This is client #$i' && docker run --privileged -it --name $client_name --cap-add NET_ADMIN --network bitclients \
        -v $(pwd)/src/client:/app/client \
        -v $(pwd)/src/torrents:/app/torrents \
        -v $(pwd)/src/common:/app/common \
        -v $(pwd)/src/__init__.py:/app/__init__.py \
        -v $(pwd)/src/client/main.py:/app/main.py bitclient; exec zsh" &
    check_status
done


echo -e "${GREEN}${CHECK_MARK} Setup complete! You can run everything now.${RESET}"
