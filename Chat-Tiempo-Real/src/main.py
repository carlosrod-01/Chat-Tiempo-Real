import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 5000
clientes = {}
salas = {"general": set()}
bloqueo = threading.Lock()


def servidor():
    server = socket.socket()
    server.bind((HOST, PORT))
    server.listen()
    print("Servidor de chat iniciado...")

    while True:
        conexion, direccion = server.accept()
        threading.Thread(
            target=gestionar_cliente,
            args=(conexion,),
            daemon=True
        ).start()


def gestionar_cliente(conexion):
    usuario = conexion.recv(1024).decode().strip()

    with bloqueo:
        clientes[usuario] = conexion
        salas["general"].add(usuario)

    conexion.send("Conectado a la sala general\n".encode())
    enviar_sala("general", f"{usuario} se ha conectado")

    while True:
        try:
            mensaje = conexion.recv(1024).decode().strip()

            if not mensaje or mensaje == "/salir":
                break

            if mensaje == "/usuarios":
                lista = ", ".join(clientes.keys())
                conexion.send(f"Conectados: {lista}\n".encode())

            elif mensaje.startswith("/privado "):
                partes = mensaje.split(" ", 2)
                if len(partes) == 3:
                    destino, texto = partes[1], partes[2]
                    if destino in clientes:
                        clientes[destino].send(
                            f"[Privado de {usuario}] {texto}\n".encode()
                        )

            elif mensaje.startswith("/sala "):
                nombre = mensaje.split(" ", 1)[1]
                with bloqueo:
                    salas.setdefault(nombre, set()).add(usuario)
                conexion.send(f"Ahora estás en {nombre}\n".encode())

            else:
                with open("data/conversaciones.txt", "a", encoding="utf-8") as archivo:
                    archivo.write(f"{usuario}: {mensaje}\n")
                enviar_sala("general", f"{usuario}: {mensaje}")

        except:
            break

    with bloqueo:
        clientes.pop(usuario, None)
        for sala in salas.values():
            sala.discard(usuario)

    conexion.close()
    enviar_sala("general", f"{usuario} ha salido")


def enviar_sala(nombre, mensaje):
    with bloqueo:
        usuarios = list(salas.get(nombre, set()))
        conexiones = [clientes[u] for u in usuarios if u in clientes]

    for conexion in conexiones:
        try:
            conexion.send((mensaje + "\n").encode())
        except:
            pass


def cliente():
    usuario = input("Tu nombre: ")
    conexion = socket.socket()
    conexion.connect((HOST, PORT))
    conexion.send(usuario.encode())

    def recibir():
        while True:
            try:
                mensaje = conexion.recv(1024).decode()
                if not mensaje:
                    break
                print(mensaje, end="")
            except:
                break

    threading.Thread(target=recibir, daemon=True).start()

    print("Escribe /usuarios, /privado usuario mensaje o /salir")

    while True:
        mensaje = input()
        conexion.send(mensaje.encode())
        if mensaje == "/salir":
            break

    conexion.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "servidor":
        servidor()
    else:
        cliente()


        