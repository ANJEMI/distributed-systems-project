from client.client import Client
import sys

def main():
    client_id = int(input("Por favor introduzca id del cliente: "))
    client = Client(client_id=client_id)
    client.Run()

if __name__ == "__main__":
    main()
