"""
Balanceador como servicio web (punto unico de entrada HTTP, puerto 5000).

Mismas ideas de la practica 4 (round-robin con Lock, failover, complemento de
inventario), pero ahora hablando HTTP en ambos lados:
  - frente a los clientes expone el MISMO contrato que una taquilla
    (GET /boletos, POST /comprar), asi que el cliente no nota la diferencia;
  - frente a las taquillas actua como cliente HTTP (urllib).

Mapeo de resultados (codigos HTTP):
    una taquilla responde 200  -> se devuelve 200 al cliente
    una taquilla responde 409  -> se prueba la siguiente (complemento de inventario)
    una taquilla no responde   -> se prueba la siguiente (failover)
    todas dijeron 409          -> 409 al cliente
    ninguna respondio          -> 503 Service Unavailable
"""

import json
import threading
import urllib.error
import urllib.request

from flask import Flask, jsonify, request

PUERTO = 5000
TIMEOUT = 3  # segundos por llamada a una taquilla

SERVIDORES = [
    ("Taquilla-A", "http://127.0.0.1:5001"),
    ("Taquilla-B", "http://127.0.0.1:5002"),
]


class Turnos:
    """Round-robin thread-safe: el contador compartido se protege con Lock."""

    def __init__(self, n):
        self._n = n
        self._siguiente = 0
        self._candado = threading.Lock()

    def tomar(self):
        with self._candado:
            actual = self._siguiente
            self._siguiente = (self._siguiente + 1) % self._n
            return actual


turnos = Turnos(len(SERVIDORES))
app = Flask("balanceador")


def llamar(url, metodo="GET", cuerpo=None, id_cliente=None):
    """Hace una peticion HTTP a una taquilla.
    Devuelve (codigo_http, dict_json). Lanza OSError/URLError si no responde."""
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo)
    if datos is not None:
        req.add_header("Content-Type", "application/json")
    if id_cliente:
        req.add_header("X-Cliente-Id", str(id_cliente))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:   # 4xx/5xx: la taquilla SI respondio
        return e.code, json.loads(e.read().decode("utf-8"))


@app.get("/boletos")
def consultar_todo():
    detalle, total = [], 0
    for nombre, base in SERVIDORES:
        try:
            _, d = llamar(f"{base}/boletos")
            detalle.append({"taquilla": nombre, "estado": "activa",
                            "disponibles": d["disponibles"]})
            total += d["disponibles"]
        except OSError:
            detalle.append({"taquilla": nombre, "estado": "caida"})
    return jsonify({"total_disponibles": total, "taquillas": detalle})


@app.post("/comprar")
def comprar():
    datos = request.get_json(silent=True) or {}
    cantidad = datos.get("cantidad")
    if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
        return jsonify({"exito": False,
                        "mensaje": "Envia JSON con 'cantidad' entero mayor a 0."}), 400

    id_cliente = request.headers.get("X-Cliente-Id", "anonimo")
    inicio = turnos.tomar()
    print(f"[Balanceador] cliente {id_cliente} pide {cantidad}; "
          f"turno inicial: {SERVIDORES[inicio][0]}")

    hubo_rechazo = False
    for i in range(len(SERVIDORES)):
        nombre, base = SERVIDORES[(inicio + i) % len(SERVIDORES)]
        try:
            codigo, cuerpo = llamar(f"{base}/comprar", "POST",
                                    {"cantidad": cantidad}, id_cliente)
        except OSError:
            print(f"[Balanceador] {nombre} NO responde (cliente {id_cliente}) -> failover")
            continue

        if codigo == 409:
            print(f"[Balanceador] {nombre} rechazo a cliente {id_cliente} -> probando siguiente")
            hubo_rechazo = True
            continue
        return jsonify(cuerpo), codigo      # 200 (exito) o 400 (error de peticion)

    if hubo_rechazo:
        return jsonify({"exito": False, "cantidad": cantidad,
                        "mensaje": f"Ninguna taquilla disponible tiene {cantidad} boleto(s)."}), 409
    return jsonify({"exito": False,
                    "mensaje": "Servicio no disponible: ninguna taquilla respondio."}), 503


if __name__ == "__main__":
    print("Balanceador web. Taquillas configuradas:")
    for nombre, base in SERVIDORES:
        print(f"  - {nombre} en {base}")
    app.run(host="127.0.0.1", port=PUERTO, threaded=True)
