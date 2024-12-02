#!/bin/bash

# Definición de colores
RESET="\033[0m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BLUE="\033[94m"

# Emojis
ROCKET="🚀"
CHECK_MARK="✅"
WARNING="⚠️"

# Función para verificar el estado de salida
check_status() {
    if [ $? -ne 0 ]; then
        echo -e "${RED}${WARNING} Error occurred during the last operation.${RESET}"
        exit 1
    fi
}

# Crear redes
echo -e "${BLUE}${ROCKET} Creating networks...${RESET}"
docker network create bitclients --subnet 10.0.10.0/24
check_status
docker network create bitservers --subnet 10.0.11.0/24
check_status

# Configurar el router
echo -e "${BLUE}${ROCKET} Setting up router...${RESET}"
docker build -t router -f src/router/router.Dockerfile .
check_status
docker run -itd --rm --name router router
check_status
docker network connect --ip 10.0.10.254 bitclients router
check_status
docker network connect --ip 10.0.11.254 bitservers router
check_status

# Configurar cliente y servidor
echo -e "${BLUE}${ROCKET} Building client and server images...${RESET}"
docker build -t bitserver -f server.dockerfile .
check_status
docker build -t bitclient -f client.dockerfile .
check_status

# Ejecutar servidor
echo -e "${BLUE}${ROCKET} Running server...${RESET}"
docker run --rm -it --name bitserver1 --cap-add NET_ADMIN --network bitservers bitserver
check_status

# Ejecutar cliente
echo -e "${BLUE}${ROCKET} Running clients...${RESET}"
docker run --rm -it --name bitclient1 --cap-add NET_ADMIN --network bitclients bitclient
check_status
docker run --rm -it --name bitclient2 --cap-add NET_ADMIN --network bitclients bitclient
check_status

echo -e "${GREEN}${CHECK_MARK} Setup complete!${RESET}"
