"""
Lanza varios clientes HTTP simultaneos (cada uno en su hilo) contra el balanceador.
Equivalente web de cliente_multiple.py de la practica anterior.
"""

import threading

from cliente_http import peticion

SOLICITUDES = [2, 3, 1, 2, 3, 1, 2, 3]


def cliente(id_cliente, cantidad):
    codigo, cuerpo = peticion("/comprar", "POST", {"cantidad": cantidad}, id_cliente)
    print(f"Cliente {id_cliente} (pidio {cantidad}): HTTP {codigo} - {cuerpo['mensaje']}")


if __name__ == "__main__":
    hilos = [threading.Thread(target=cliente, args=(i, c))
             for i, c in enumerate(SOLICITUDES, start=1)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
