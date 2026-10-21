"""
Servicio web de una taquilla (HTTP, JSON).

Antes (practica 4): un servidor de sockets que leia un numero con recv().
Ahora: la misma logica de negocio (taquilla.py) encapsulada como SERVICIO WEB
con dos operaciones expuestas por HTTP:

    GET  /boletos   -> consulta cuantos boletos quedan        (no modifica nada)
    POST /comprar   -> intenta comprar {"cantidad": N}         (modifica el inventario)
    GET  /salud     -> indica que el servicio esta vivo        (para detectar caidas)

Codigos HTTP usados (el "protocolo" que antes inventabamos con texto):
    200 OK        compra exitosa / consulta correcta
    400 Bad Req.  la peticion esta mal formada (cantidad no valida)
    409 Conflict  la peticion es valida, pero el inventario no alcanza

Uso:
    python servicio_taquilla.py <puerto> <nombre> <boletos> [ventanillas]
    python servicio_taquilla.py 5001 Taquilla-A 8
"""

import sys
import threading
import time

from flask import Flask, jsonify, request

from taquilla import Taquilla


def crear_app(nombre, boletos, max_ventanillas):
    app = Flask(nombre)
    taquilla = Taquilla(boletos)
    ventanillas = threading.Semaphore(max_ventanillas)  # igual que en la practica 3

    @app.get("/salud")
    def salud():
        return jsonify({"taquilla": nombre, "estado": "activa"})

    @app.get("/boletos")
    def consultar():
        return jsonify({"taquilla": nombre,
                        "disponibles": taquilla.boletos_disponibles})

    @app.post("/comprar")
    def comprar():
        datos = request.get_json(silent=True) or {}
        cantidad = datos.get("cantidad")
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
            return jsonify({"exito": False, "taquilla": nombre,
                            "mensaje": "Envia JSON con 'cantidad' entero mayor a 0."}), 400

        id_cliente = request.headers.get("X-Cliente-Id", "anonimo")

        with ventanillas:          # limita atenciones simultaneas
            time.sleep(0.3)        # tiempo de atencion en ventanilla
            exito, restantes = taquilla.comprar(f"{id_cliente}@{nombre}", cantidad)

        cuerpo = {"exito": exito, "taquilla": nombre,
                  "cantidad": cantidad, "restantes": restantes}
        if exito:
            cuerpo["mensaje"] = f"Compra exitosa en {nombre}."
            return jsonify(cuerpo), 200
        cuerpo["mensaje"] = f"{nombre} no tiene {cantidad} boleto(s) disponibles."
        return jsonify(cuerpo), 409

    return app


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python servicio_taquilla.py <puerto> <nombre> <boletos> [ventanillas]")
        sys.exit(1)
    puerto = int(sys.argv[1])
    nombre = sys.argv[2]
    boletos = int(sys.argv[3])
    ventanillas = int(sys.argv[4]) if len(sys.argv) > 4 else 3

    print(f"[{nombre}] servicio web con {boletos} boletos y {ventanillas} ventanillas")
    crear_app(nombre, boletos, ventanillas).run(
        host="127.0.0.1", port=puerto, threaded=True)
