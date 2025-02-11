import logging
import json
import time
import os
from datetime import datetime
import inspect
import traceback

# Crea la carpeta 'logs' si no existe
logs_dir = "app/logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)


# Configura el manejador de archivos
log_file_name = f"my_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"


log_file_path = os.path.join(logs_dir, log_file_name)
file_handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(custom_funcName)s - %(message)s"
)
file_handler.setFormatter(formatter)

# Configura el manejador de consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Configura el logger raíz
logging.basicConfig(handlers=[file_handler, console_handler], level=logging.DEBUG)

# Define un diccionario para almacenar los logs en JSON
logs_json = {}


# Función para serializar los logs en JSON
def serialize_logs(logs_json, filename="logs_container.json"):
    full_path = os.path.join(logs_dir, filename)
    with open(full_path, "w") as f:
        json.dump(logs_json, f, indent=4)


# Crea una función para registrar mensajes con información adicional
def log_message(message, level="INFO", extra_data={}, func=None):
    """
    Registra un mensaje de log con información adicional.
    Si se proporciona 'func', se usa como nombre de la función.
    Si no, se detecta automáticamente.
    """
    # Obtiene información sobre el llamador
    caller_frame = inspect.currentframe().f_back
    caller_line = caller_frame.f_lineno

    if func is None:
        caller_method = caller_frame.f_code.co_name
    else:
        caller_method = func.__name__ if callable(func) else str(func)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": f"{message} Error: {traceback.format_exc()}",
        "extra_data": extra_data,
        "method": caller_method,
        "line": caller_line,
    }
    logs_json[time.time()] = log_entry

    # Añade el nombre del método y el número de línea al diccionario extra_data
    extra_data["custom_funcName"] = caller_method
    extra_data["line"] = caller_line

    logger = logging.getLogger(__name__)
    logger.log(logging.getLevelName(level), message, extra=extra_data)
    #serialize_logs(logs_json)

if __name__ == "__main__":
    # Ejemplo de uso
    log_message("Este es un mensaje de información desde el nivel principal.")

    # Serializa los logs en JSON cada cierto tiempo
    while True:
        serialize_logs(logs_json)
        time.sleep(30)  # Serializa cada 30 segundos
