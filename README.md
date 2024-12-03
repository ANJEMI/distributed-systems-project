# BitTorrent 
Este proyecto tiene cómo objetivo la implementación de BitTorrent para la
descarga descentralizada de datos.   


## Instrucciones para levantar el entorno


Abra una terminal en la raíz del repositorio dónde deberá encontrar un archivo
`setup.sh`. Luego, ejecute el siguiente comando para darle permisos de
ejecución:

```bash
chmod +x start.sh
```

Luego ejecute el archivo
```bash
./start.sh
```

Al finalizar deberá tener el entorno listo para levantar los contenedeores de docker. 
Para ello ejecute:

```bash
docker run --rm -it --name bitserver --cap-add NET_ADMIN --network bitservers bitserver 
```

```bash
docker run --rm -it --name bitclient1 --cap-add NET_ADMIN --network bitclients bitclient
```

Estos comandos inicializaran los contenedores para emular el comportamiento de un servidor 
y un cliente respectivamente. Usted puede inicializar más clientes usando el comando anterior 
cambiando `bitclient1` por `bitclient2`, `bitclient3`, `bitclient4` ... 


Una vez dentro del los contenedores ejecutar cambiar la tabla de rutas apropiadamente y 
ejecutar el comando:

```python
python main.py
```