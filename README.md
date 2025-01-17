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

Este comando inicializará los contenedores para emular el comportamiento de lso servidores
y un clientes respectivamente. Usted puede inicializar más clientes y servidores modificando 
las variables `NUM_CLIENTS` y `NUM_SERVERS` respectivamente. 


Una vez dentro del los contenedores debe ejecutar el siguiente comando:

```python
python main.py
```