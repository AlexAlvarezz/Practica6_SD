# Taquilla - Servicios Web (Sistemas Distribuidos)

Evolucion de la practica de la taquilla: la comunicacion por **sockets** se
reemplaza por **servicios web HTTP** (metodos GET y POST, cuerpos JSON).

```
 clientes HTTP ──►  balanceador_web (5000) ──►  servicio_taquilla A (5001)
 (GET / POST)        round-robin + failover  └─►  servicio_taquilla B (5002)
```

La logica de negocio (`taquilla.py`, inventario protegido con `Lock`) **no
cambio**: solo cambio la capa de comunicacion.

## Contrato de los servicios

| Metodo | Ruta        | Cuerpo               | Respuestas                                   |
|--------|-------------|----------------------|-----------------------------------------------|
| GET    | `/boletos`  | -                    | 200 con boletos disponibles                   |
| POST   | `/comprar`  | `{"cantidad": N}`    | 200 compra ok / 409 sin inventario / 400 peticion invalida |
| GET    | `/salud`    | -                    | 200 si la taquilla esta viva (solo taquillas) |

El balanceador expone `GET /boletos` y `POST /comprar` con el mismo contrato,
y ademas responde **503** si ninguna taquilla esta disponible.

## Requisitos y ejecucion

```bash
pip install -r requirements.txt
```

Abrir 3 terminales (en Windows usar `python`, en Linux/Mac `python3`):

```bash
python servicio_taquilla.py 5001 Taquilla-A 8
python servicio_taquilla.py 5002 Taquilla-B 7
python balanceador_web.py
```

Y desde una cuarta terminal:

```bash
python cliente_http.py consultar          # GET  /boletos
python cliente_http.py comprar 2          # POST /comprar
python cliente_multiple_http.py           # 8 clientes simultaneos
```

Tambien se puede probar desde el navegador (GET): `http://127.0.0.1:5000/boletos`

## Archivos

- `taquilla.py` - logica de negocio (sin cambios respecto a practicas anteriores).
- `servicio_taquilla.py` - taquilla como servicio web (Flask) con `Semaphore` de ventanillas.
- `balanceador_web.py` - punto unico de entrada: reparto por turnos, failover y complemento de inventario.
- `cliente_http.py`, `cliente_multiple_http.py` - clientes.
