"""
Modulo: taquilla.py
Sistemas Distribuidos

Contiene la logica de negocio del problema (inventario de boletos
protegido con Lock), separada del mecanismo de comunicacion. Esto
permite que el servidor por sockets reutilice exactamente la misma
clase que se probo en la practica con hilos simulados, sin modificar
nada de la logica de concurrencia.
"""

import threading
import time
import random


class Taquilla:
    """
    Recurso compartido: representa el inventario de boletos de un evento.
    Es el nucleo del servidor: no sabe nada de sockets ni de hilos,
    solo protege su propio estado con un Lock.
    """

    def __init__(self, boletos_totales):
        self._boletos_disponibles = boletos_totales
        self._candado = threading.Lock()  # protege el inventario

    def comprar(self, id_cliente, cantidad):
        """
        Intenta vender 'cantidad' boletos a 'id_cliente'.
        Devuelve una tupla (exito: bool, boletos_restantes: int).
        """
        with self._candado:
            # Seccion critica: solo un hilo a la vez puede leer y
            # modificar _boletos_disponibles, sin importar si la peticion
            # vino de un hilo simulado o de un cliente real por socket.
            if cantidad <= self._boletos_disponibles:
                time.sleep(random.uniform(0.05, 0.2))  # simula procesar el pago
                self._boletos_disponibles -= cantidad
                print(f"  [OK] Cliente {id_cliente}: compro {cantidad} "
                      f"boleto(s). Quedan {self._boletos_disponibles}.")
                return True, self._boletos_disponibles
            else:
                print(f"  [RECHAZADO] Cliente {id_cliente}: pidio "
                      f"{cantidad}, solo quedan "
                      f"{self._boletos_disponibles}.")
                return False, self._boletos_disponibles

    @property
    def boletos_disponibles(self):
        with self._candado:
            return self._boletos_disponibles
