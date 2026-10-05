#!/usr/bin/env python3
"""
===============================================================================
SERVIDOR DE CHAT MULTIUSUARIO (TCP Sockets & Multithreading)
===============================================================================
Materia: Redes de Datos - Licenciatura en Sistemas de Información
Ejercicio 1: Aplicación de Chat Servidor Centralizado

Descripción:
Este script implementa un servidor TCP concurrente capaz de gestionar múltiples
clientes en tiempo real. Utiliza la librería estándar 'socket' para las
comunicaciones de red y 'threading' para atender a cada cliente de manera paralela.

Conceptos Clave de Python y Sockets explicados:
- socket.AF_INET: Familia de direcciones IPv4.
- socket.SOCK_STREAM: Protocolo TCP (orientado a conexión, confiable).
- bind((host, port)): Asocia el socket a una IP y puerto específicos.
- listen(): Coloca el socket en modo de escucha para aceptar conexiones entrantes.
- accept(): Bloquea hasta que llega un cliente. Retorna (socket_cliente, direccion).
- threading.Thread: Permite ejecutar funciones concurrentemente en hilos separados.
- threading.Lock: Sincroniza el acceso a variables compartidas entre hilos (hilo-seguro).
===============================================================================
"""

import socket
import threading
import sys

# =============================================================================
# CONFIGURACIÓN POR DEFECTO
# =============================================================================
DEFAULT_HOST = "127.0.0.1"  # Localhost (para pruebas en la misma máquina)
DEFAULT_PORT = 4000         # Puerto por defecto solicitado por el trabajo práctico
BUFFER_SIZE = 1024          # Tamaño máximo del búfer de lectura en bytes (1 KB)
ENCODING = "utf-8"          # Codificación de caracteres para enviar/recibir texto

# Estructuras globales sincronizadas
# clientes_conectados guardará pares { socket_cliente: nombre_usuario }
clientes_conectados = {}
# lock_clientes asegura que múltiples hilos no modifiquen el diccionario al mismo tiempo
lock_clientes = threading.Lock()


def transmitir_mensaje(mensaje: str, cliente_emisor_socket=None):
    """
    Retransmite un mensaje de texto codificado a los clientes conectados.
    
    Parámetros:
    - mensaje: El texto que se enviará.
    - cliente_emisor_socket: El socket del cliente que originó el mensaje.
      Si se especifica, el mensaje se envía a TODOS LOS DEMÁS clientes (no al emisor).
      Si es None, se transmite a absolutamente TODOS los clientes (mensajes del servidor).
    """
    # Asegurar que el mensaje termina en salto de línea '\n' para lectores basados en líneas (ej. BufferedReader de Java)
    if not mensaje.endswith("\n"):
        mensaje += "\n"
        
    mensaje_bytes = mensaje.encode(ENCODING)
    
    # Adquirimos el candado (Lock) para leer el diccionario de clientes de forma segura
    with lock_clientes:
        # Copiamos la lista de sockets activos para iterar de manera segura
        sockets_activos = list(clientes_conectados.keys())
    
    for sock in sockets_activos:
        # Si el socket es diferente al emisor, le enviamos el mensaje
        if sock != cliente_emisor_socket:
            try:
                # sendall garantiza que se envíen todos los bytes o lance una excepción
                sock.sendall(mensaje_bytes)
            except Exception as error:
                print(f"[ERROR] No se pudo enviar mensaje a un cliente: {error}")


def manejar_cliente(cliente_socket: socket.socket, cliente_direccion: tuple):
    """
    Función ejecutada en un hilo independiente para CADA cliente conectado.
    Maneja la recepción del nombre de usuario, el bucle de mensajes y la desconexión.
    """
    print(f"[NUEVA CONEXIÓN] Cliente conectado desde {cliente_direccion[0]}:{cliente_direccion[1]}")
    
    nombre_usuario = ""
    try:
        # 1. RECEPCIÓN DEL NOMBRE DE USUARIO
        # El cliente debe enviar su nombre de usuario inmediatamente después de conectarse
        datos_iniciales = cliente_socket.recv(BUFFER_SIZE)
        if not datos_iniciales:
            # Si el cliente cierra la conexión antes de enviar el nombre
            cliente_socket.close()
            return

        nombre_usuario = datos_iniciales.decode(ENCODING).strip()
        
        # Validar si el nombre está vacío
        if not nombre_usuario:
            nombre_usuario = f"Usuario_{cliente_direccion[1]}"

        # Registrar el cliente en nuestra estructura compartida (con Lock)
        with lock_clientes:
            clientes_conectados[cliente_socket] = nombre_usuario

        print(f"[REGISTRO] {cliente_direccion} se identificó como '{nombre_usuario}'")
        
        # Notificar a todos los demás usuarios que un nuevo participante ha ingresado
        transmitir_mensaje(f"[SERVIDOR] {nombre_usuario} se ha unido al chat.", cliente_emisor_socket=cliente_socket)
        
        # Confirmación de bienvenida al nuevo cliente
        mensaje_bienvenida = (
            f"[SERVIDOR] Bienvenida/o al chat, {nombre_usuario}!\n"
            f"[SERVIDOR] Comandos disponibles: '/listar' (ver conectados), '/quitar' (desconectarse).\n"
        )
        cliente_socket.sendall(mensaje_bienvenida.encode(ENCODING))

        # 2. BUCLE PRINCIPAL DE RECEPCIÓN DE MENSAJES
        while True:
            # recv es una llamada bloqueante: espera a que el cliente envíe datos
            datos = cliente_socket.recv(BUFFER_SIZE)
            
            # Si datos es un bytes vacío b'', significa que el cliente cerró el socket de forma limpia
            if not datos:
                break
                
            mensaje = datos.decode(ENCODING).strip()
            
            # --- MANEJO DE COMANDOS ESPECIALES ---
            if mensaje == "/quitar":
                # El cliente solicitó explícitamente desconectarse
                print(f"[COMANDO /quitar] {nombre_usuario} solicitó desconexión.")
                break
                
            elif mensaje == "/listar":
                # El cliente solicita ver la lista de todos los usuarios conectados
                with lock_clientes:
                    lista_usuarios = list(clientes_conectados.values())
                
                respuesta = f"[SERVIDOR] Usuarios conectados ({len(lista_usuarios)}): " + ", ".join(lista_usuarios) + "\n"
                cliente_socket.sendall(respuesta.encode(ENCODING))
                
            elif mensaje:
                # Es un mensaje de chat normal -> Retransmitirlo a todos los demás clientes
                mensaje_formateado = f"[{nombre_usuario}]: {mensaje}"
                print(f"[CHAT] {mensaje_formateado}")
                transmitir_mensaje(mensaje_formateado, cliente_emisor_socket=cliente_socket)

    except (ConnectionResetError, ConnectionAbortedError, socket.error) as e:
        # Excepciones típicas cuando un cliente cierra abruptamente su consola/programa
        print(f"[DESCONEXIÓN ABRUPTA] Conexión perdida con {nombre_usuario or cliente_direccion}: {e}")
    except Exception as e:
        print(f"[ERROR INESPERADO] Error con el cliente {nombre_usuario or cliente_direccion}: {e}")
    finally:
        # 3. LIMPIEZA Y DESCONEXIÓN DEL CLIENTE
        # Este bloque 'finally' SIEMPRE se ejecuta, garantizando que liberemos los recursos
        with lock_clientes:
            if cliente_socket in clientes_conectados:
                del clientes_conectados[cliente_socket]
        
        try:
            cliente_socket.close()
        except Exception:
            pass

        if nombre_usuario:
            print(f"[DESCONEXIÓN] {nombre_usuario} se ha desconectado.")
            # Notificar a los demás que el usuario abandonó la sala
            transmitir_mensaje(f"[SERVIDOR] {nombre_usuario} ha salido del chat.")


def iniciar_servidor(host: str, puerto: int):
    """
    Crea el socket del servidor, lo vincula a la IP y Puerto,
    y entra en un bucle infinito aceptando clientes entrantes.
    """
    # Creación del socket TCP: AF_INET (IPv4), SOCK_STREAM (TCP)
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # SOL_SOCKET y SO_REUSEADDR permiten reutilizar el puerto inmediatamente si se reinicia el servidor
    servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Asociar el socket con la dirección IP y Puerto especificados
        servidor_socket.bind((host, puerto))
    except Exception as error:
        print(f"[ERROR CRÍTICO] No se pudo vincular el servidor a {host}:{puerto}. Error: {error}")
        print("[SUGERENCIA] Verifica si el puerto ya está en uso por otro programa.")
        sys.exit(1)

    # Configurar el socket para escuchar conexiones. El argumento indica el límite de cola de conexiones entrantes
    servidor_socket.listen(5)
    print("=" * 70)
    print(f" SERVIDOR DE CHAT INICIADO CORRECTAMENTE")
    print(f" Escuchando en IP: {host} | Puerto: {puerto}")
    print(f" Presiona Ctrl + C para detener el servidor")
    print("=" * 70)

    try:
        while True:
            # accept() bloquea la ejecución hasta que llega una nueva conexión entrante
            cliente_socket, cliente_direccion = servidor_socket.accept()
            
            # Para cada cliente aceptado, creamos un nuevo hilo (Thread)
            # target: función a ejecutar en paralelo
            # args: argumentos de la función (socket del cliente y tupla de dirección)
            # daemon=True: hace que el hilo se destruya si la aplicación principal finaliza
            hilo_cliente = threading.Thread(
                target=manejar_cliente,
                args=(cliente_socket, cliente_direccion),
                daemon=True
            )
            hilo_cliente.start()
            
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Apagando el servidor por solicitud del usuario (Ctrl+C)...")
    finally:
        # Cierre ordenado de todas las conexiones activas
        with lock_clientes:
            for sock in list(clientes_conectados.keys()):
                try:
                    sock.sendall("[SERVIDOR] El servidor se está apagando. Conexión cerrada.\n".encode(ENCODING))
                    sock.close()
                except Exception:
                    pass
            clientes_conectados.clear()
            
        servidor_socket.close()
        print("[SERVIDOR] Servidor detenido correctamente.")


if __name__ == "__main__":
    # Permite pasar la IP y el Puerto como argumentos desde la línea de comandos
    # Ejemplo de uso: python servidor.py 127.0.0.1 4000
    host = DEFAULT_HOST
    puerto = DEFAULT_PORT

    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            puerto = int(sys.argv[2])
        except ValueError:
            print(f"[ADVERTENCIA] Puerto inválido '{sys.argv[2]}'. Usando puerto por defecto {DEFAULT_PORT}.")

    iniciar_servidor(host, puerto)
