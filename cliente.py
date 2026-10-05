#!/usr/bin/env python3
"""
===============================================================================
CLIENTE DE CHAT MULTIUSUARIO (TCP Sockets & Multithreading)
===============================================================================
Materia: Redes de Datos - Licenciatura en Sistemas de Información
Ejercicio 1: Aplicación de Chat Cliente

Descripción:
Este script implementa el cliente TCP del chat. Se conecta al servidor central,
envía el nombre de usuario e inicia dos hilos de ejecución:
1. Un hilo secundario (Escucha): Espera y muestra continuamente los mensajes
   recibidos desde el servidor en tiempo real.
2. El hilo principal (Envío): Lee la entrada de texto del usuario por consola (input)
   y transmite los mensajes o comandos al servidor.

Comandos especiales admitidos:
- /listar: Solicita la lista de usuarios actualmente conectados al chat.
- /quitar: Se desconecta limpiamente del servidor y finaliza la aplicación.

Ejecución de múltiples clientes con el mismo código:
Para simular 2, 3 o más usuarios interactuando simultáneamente:
1. Abre múltiples ventanas o pestañas de la consola/terminal.
2. En cada terminal ejecuta: python cliente.py
3. Ingresa un nombre de usuario distinto en cada terminal.
===============================================================================
"""

import socket
import threading
import sys

# =============================================================================
# CONFIGURACIÓN POR DEFECTO
# =============================================================================
DEFAULT_HOST = "127.0.0.1"  # IP del servidor (localhost por defecto)
DEFAULT_PORT = 4000         # Puerto por defecto del servidor
BUFFER_SIZE = 1024          # Tamaño de búfer para recibir mensajes
ENCODING = "utf-8"          # Codificación de texto UTF-8

# Variable global para controlar la ejecución de los hilos de manera limpia
ejecutando = True


def recibir_mensajes(cliente_socket: socket.socket):
    """
    Función que se ejecuta en un hilo secundario de escucha continua.
    Recibe datos entrantes del servidor mediante recv() y los imprime en la pantalla.
    """
    global ejecutando
    
    while ejecutando:
        try:
            # recv() bloquea el hilo hasta recibir datos desde el servidor
            datos = cliente_socket.recv(BUFFER_SIZE)
            
            if not datos:
                # Si los datos devueltos están vacíos (b''), el servidor ha cerrado la conexión
                if ejecutando:
                    print("\n[DESCONECTADO] El servidor ha cerrado la conexión.")
                ejecutando = False
                break
                
            # Decodificar de bytes a texto y mostrar en consola
            mensaje_recibido = datos.decode(ENCODING)
            
            # Imprimir el mensaje recibido directamente en pantalla
            print(f"{mensaje_recibido}")

        except (ConnectionResetError, ConnectionAbortedError, socket.error):
            if ejecutando:
                print("\n[ERROR] Se ha perdido la conexión con el servidor.")
            ejecutando = False
            break
        except Exception as error:
            if ejecutando:
                print(f"\n[ERROR EN RECEPCIÓN] {error}")
            ejecutando = False
            break


def iniciar_cliente(host: str, puerto: int, nombre_usuario: str = None):
    """
    Conecta al cliente con el servidor TCP, envía el nombre de usuario e inicia los hilos.
    """
    global ejecutando

    # 1. SOLICITAR NOMBRE DE USUARIO SI NO FUE PROVISTO COMO ARGUMENTO
    if not nombre_usuario:
        while True:
            nombre_usuario = input("Ingresa tu nombre de usuario para el chat: ").strip()
            if nombre_usuario:
                break
            print("[ADVERTENCIA] El nombre de usuario no puede estar vacío.")

    # 2. CREACIÓN DEL SOCKET Y CONEXIÓN AL SERVIDOR
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    print(f"[CONECTANDO] Intentando conectar a {host}:{puerto}...")
    try:
        # connect() establece la conexión TCP de tres vías (3-way handshake) con el servidor
        cliente_socket.connect((host, puerto))
        print("[CONECTADO] ¡Conexión establecida exitosamente con el servidor!")
    except Exception as error:
        print(f"[ERROR DE CONEXIÓN] No se pudo conectar al servidor en {host}:{puerto}.")
        print(f"Detalle del error: {error}")
        print("Asegúrate de que el servidor esté en ejecución y que la IP/Puerto sean correctos.")
        return

    try:
        # 3. ENVIAR NOMBRE DE USUARIO AL SERVIDOR
        # Inmediatamente al conectar, enviamos nuestro nombre de usuario codificado a bytes
        cliente_socket.sendall(nombre_usuario.encode(ENCODING))

        # 4. INICIAR HILO SECUNDARIO PARA RECEPCIÓN EN TIEMPO REAL
        # Este hilo escuchará constantemente los mensajes que envíen otros usuarios o el servidor
        hilo_escucha = threading.Thread(
            target=recibir_mensajes,
            args=(cliente_socket,),
            daemon=True
        )
        hilo_escucha.start()

        # 5. BUCLE PRINCIPAL DEL HILO DE ENVÍO (Lectura de consola / input)
        print("\n--- INICIO DE INTERACCIÓN DE CHAT ---")
        print("Escribe tus mensajes a continuación. Usa Ctrl+C para salir.\n")

        while ejecutando:
            try:
                # input() detiene la ejecución a la espera de que el usuario escriba algo
                mensaje = input("> ").strip()
                
                if not ejecutando:
                    break

                if not mensaje:
                    continue

                # Si el usuario escribe /quitar, enviamos el comando al servidor y salimos
                if mensaje == "/quitar":
                    cliente_socket.sendall(mensaje.encode(ENCODING))
                    print("[DESCONEXIÓN] Saliendo del chat...")
                    ejecutando = False
                    break
                
                # Enviar el mensaje normal o comando al servidor
                cliente_socket.sendall(mensaje.encode(ENCODING))

            except (KeyboardInterrupt, EOFError):
                print("\n[CANCELADO] Solicitada interrupción por teclado.")
                try:
                    cliente_socket.sendall("/quitar".encode(ENCODING))
                except Exception:
                    pass
                ejecutando = False
                break
            except Exception as error:
                print(f"[ERROR EN ENVÍO] Ocurrió un error enviando el mensaje: {error}")
                ejecutando = False
                break

    finally:
        # 6. LIMPIEZA Y CIERRE DEL SOCKET
        ejecutando = False
        try:
            cliente_socket.close()
        except Exception:
            pass
        print("[FIN] Cliente finalizado.")


if __name__ == "__main__":
    # Permite pasar la IP, el Puerto y opcionalmente el Nombre de Usuario por consola
    # Ejemplos de uso:
    #   python cliente.py
    #   python cliente.py 127.0.0.1 4000
    #   python cliente.py 127.0.0.1 4000 Juan
    host = DEFAULT_HOST
    puerto = DEFAULT_PORT
    usuario = None

    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            puerto = int(sys.argv[2])
        except ValueError:
            print(f"[ADVERTENCIA] Puerto inválido '{sys.argv[2]}'. Usando puerto por defecto {DEFAULT_PORT}.")
    if len(sys.argv) >= 4:
        usuario = sys.argv[3]

    iniciar_cliente(host, puerto, usuario)
