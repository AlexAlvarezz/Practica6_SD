"""
Cliente HTTP de linea de comandos.

    python cliente_http.py consultar       -> GET  /boletos
    python cliente_http.py comprar 2       -> POST /comprar  {"cantidad": 2}
"""

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5000"


def peticion(ruta, metodo="GET", cuerpo=None, id_cliente=None):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo)
    if datos is not None:
        req.add_header("Content-Type", "application/json")
    if id_cliente:
        req.add_header("X-Cliente-Id", str(id_cliente))
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "consultar":
        codigo, cuerpo = peticion("/boletos")
    elif len(sys.argv) >= 3 and sys.argv[1] == "comprar":
        codigo, cuerpo = peticion("/comprar", "POST",
                                  {"cantidad": int(sys.argv[2])}, "cli")
    else:
        print("Uso: python cliente_http.py consultar | comprar <cantidad>")
        sys.exit(1)
    print(codigo, json.dumps(cuerpo, ensure_ascii=False))
