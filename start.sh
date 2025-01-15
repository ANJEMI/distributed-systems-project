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

# Run server
echo -e "${BLUE}${ROCKET} Running server...${RESET}"
for ((i=1; i<=NUM_SERVERS; i++)); do
    $SHELL bash -c "echo 'This is the server #$i' && docker run --rm -it --name bitserver$i --cap-add NET_ADMIN --network bitservers bitserver" &
    check_status
done

# Run clients
echo -e "${BLUE}${ROCKET} Running clients...${RESET}"
for ((i=1; i<=NUM_CLIENTS; i++)); do
    $SHELL bash -c "echo 'This is client #$i' && docker run --rm -it --name bitclient$i --cap-add NET_ADMIN --network bitclients bitclient" &
    check_status
done

echo -e "${GREEN}${CHECK_MARK} Setup complete! You can run everything now${RESET}"
