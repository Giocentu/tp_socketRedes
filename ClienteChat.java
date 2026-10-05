import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Scanner;

/**
 * ===============================================================================
 * CLIENTE DE CHAT EN JAVA (Sockets TCP & Multithreading)
 * ===============================================================================
 * Materia: Redes de Datos - Licenciatura en Sistemas de Información
 * Ejercicio 2 - Opción 1: Nuevo Cliente de Chat en Lenguaje Diferente (Java)
 * 
 * Descripción:
 * Este programa implementa un cliente de chat en Java capaz de comunicarse
 * con el servidor de chat desarrollado en Python (servidor.py). Demuestra la
 * INTEROPERABILIDAD entre distintas tecnologías utilizando el protocolo TCP.
 * 
 * Conceptos clave explicados:
 * - java.net.Socket: Clase nativa de Java para establecer conexiones TCP.
 * - BufferedReader / PrintWriter: Manejo eficiente de flujos de texto de I/O.
 * - StandardCharsets.UTF_8: Garantiza la decodificación correcta de caracteres entre Java y Python.
 * - Thread (Hilo de Escucha): Permite recibir mensajes en tiempo real sin bloquear la entrada de texto por teclado.
 * ===============================================================================
 */
public class ClienteChat {

    // Valores por defecto para la conexión
    private static final String DEFAULT_HOST = "127.0.0.1";
    private static final int DEFAULT_PORT = 4000;
    
    // Flag para controlar la ejecución limpia de los hilos
    private static volatile boolean ejecutando = true;

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        String host = DEFAULT_HOST;
        int puerto = DEFAULT_PORT;
        String nombreUsuario = null;

        // 1. LECTURA DE PARÁMETROS DESDE LÍNEA DE COMANDOS O INTERACTIVOS
        if (args.length >= 1) {
            host = args[0];
        }
        if (args.length >= 2) {
            try {
                puerto = Integer.parseInt(args[1]);
            } catch (NumberFormatException e) {
                System.out.println("[ADVERTENCIA] Puerto inválido '" + args[1] + "'. Usando puerto por defecto " + DEFAULT_PORT);
            }
        }
        if (args.length >= 3) {
            nombreUsuario = args[2];
        }

        System.out.println("=================================================================");
        System.out.println(" CLIENTE DE CHAT EN JAVA (Ejercicio 2 - Interoperabilidad)");
        System.out.println("=================================================================");

        // Si no se pasaron parámetros por línea de comandos, solicitarlos al usuario
        if (args.length == 0) {
            System.out.print("Ingresa la IP del servidor (Presiona Enter para " + DEFAULT_HOST + "): ");
            String inputHost = scanner.nextLine().trim();
            if (!inputHost.isEmpty()) {
                host = inputHost;
            }

            System.out.print("Ingresa el Puerto del servidor (Presiona Enter para " + DEFAULT_PORT + "): ");
            String inputPuerto = scanner.nextLine().trim();
            if (!inputPuerto.isEmpty()) {
                try {
                    puerto = Integer.parseInt(inputPuerto);
                } catch (NumberFormatException e) {
                    System.out.println("[ADVERTENCIA] Puerto no válido. Usando " + DEFAULT_PORT);
                }
            }
        }

        if (nombreUsuario == null || nombreUsuario.isEmpty()) {
            while (true) {
                System.out.print("Ingresa tu nombre de usuario para el chat: ");
                nombreUsuario = scanner.nextLine().trim();
                if (!nombreUsuario.isEmpty()) {
                    break;
                }
                System.out.println("[ADVERTENCIA] El nombre de usuario no puede estar vacío.");
            }
        }

        // 2. ESTABLECER CONEXIÓN CON EL SERVIDOR TCP (PYTHON)
        System.out.println("\n[CONECTANDO] Conectando a " + host + ":" + puerto + "...");
        
        try (Socket socket = new Socket(host, puerto)) {
            // Confirmación explícita requerida por la consigna del Ejercicio 2
            System.out.println("[ÉXITO] ¡Conexión establecida exitosamente con el servidor!");

            // Canales de entrada (recepción) y salida (envío) configurados explícitamente en UTF-8
            BufferedReader entradaRed = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            PrintWriter salidaRed = new PrintWriter(
                    new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8), true);

            // 3. ENVIAR NOMBRE DE USUARIO AL SERVIDOR
            salidaRed.println(nombreUsuario);

            // 4. CREAR E INICIAR HILO SECUNDARIO PARA RECEPCIÓN EN TIEMPO REAL
            Thread hiloEscucha = new Thread(() -> {
                try {
                    String mensajeServidor;
                    // readLine() se bloquea hasta recibir una línea de texto completa desde la red
                    while (ejecutando && (mensajeServidor = entradaRed.readLine()) != null) {
                        System.out.println(mensajeServidor);
                    }
                } catch (IOException e) {
                    if (ejecutando) {
                        System.out.println("\n[DESCONECTADO] Se ha perdido la conexión con el servidor.");
                    }
                } finally {
                    ejecutando = false;
                }
            });
            // Marcamos el hilo como daemon para que no impida la salida del programa
            hiloEscucha.setDaemon(true);
            hiloEscucha.start();

            // 5. BUCLE PRINCIPAL DEL HILO DE ENVÍO (Entrada por consola)
            System.out.println("\n--- INICIO DE INTERACCIÓN DE CHAT (JAVA) ---");
            System.out.println("Escribe tus mensajes a continuación. Usa '/quitar' o Ctrl+C para salir.\n");

            while (ejecutando) {
                System.out.print("> ");
                if (!scanner.hasNextLine()) {
                    break;
                }
                String mensaje = scanner.nextLine().trim();

                if (!ejecutando) {
                    break;
                }

                if (mensaje.isEmpty()) {
                    continue;
                }

                // Transmitir mensaje o comando al servidor de Python
                salidaRed.println(mensaje);

                if (mensaje.equalsIgnoreCase("/quitar")) {
                    System.out.println("[DESCONEXIÓN] Saliendo del chat...");
                    ejecutando = false;
                    break;
                }
            }

        } catch (IOException e) {
            System.out.println("\n[ERROR DE CONEXIÓN] No se pudo conectar al servidor en " + host + ":" + puerto);
            System.out.println("Detalle del error: " + e.getMessage());
            System.out.println("Asegúrate de que 'servidor.py' esté corriendo en esa IP y Puerto.");
        } finally {
            ejecutando = false;
            System.out.println("[FIN] Cliente Java finalizado.");
        }
    }
}
