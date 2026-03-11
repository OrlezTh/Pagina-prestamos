import json
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from twilio.rest import Client

#TWILIO
TWILIO_ACCOUNT_SID = 'x' #con la x reemplaza con tu SID real de Twilio
TWILIO_AUTH_TOKEN = 'x' #con la x reemplaza con tu token real
TWILIO_WHATSAPP_FROM = 'whatsapp:+x' #con la x reemplaza con tu número de WhatsApp de Twilio (ej: 'whatsapp:+1234567890')
MI_WHATSAPP = 'whatsapp:+x' #con la x reemplaza con tu número de WhatsApp personal (ej: 'whatsapp:+0987654321')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = FastAPI()


DATOS_CLIENTES = "datos.json"
DATOS_PRESTAMOS = "cuotas.json"


def leer_json(archivo):
    if not os.path.exists(archivo):
        return []
    try: 
        with open(archivo, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def guardar_json(archivo, datos):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# Notificaciones:
def enviar_alertas_vencimiento():
    """Escanea los préstamos y envía WhatsApp si alguno vence mañana."""
    clientes = leer_json(DATOS_CLIENTES)
    prestamos = leer_json(DATOS_PRESTAMOS)
    
    nombres_dict = {c['id']: c['nombre'] for c in clientes if isinstance(c, dict)}
    
    # Calculamos la fecha de mañana
    manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for p in prestamos:
        if not isinstance(p, dict): continue
        nombre_c = nombres_dict.get(p['id_cliente'], "Desconocido")
        
        for cuota in p['plan_pagos']:
            if cuota['vencimiento'] == manana and cuota['estado'] == "Pendiente":
                mensaje = (f"🔔 *RECORDATORIO DE COBRO*\n\n"
                           f"Mañana vence la cuota {cuota['nro_cuota']} de *{nombre_c}*.\n"
                           f"💰 Monto a cobrar: ${cuota['monto_a_pagar']:,.0f}")
                
                twilio_client.messages.create(
                    body=mensaje,
                    from_=TWILIO_WHATSAPP_FROM,
                    to=MI_WHATSAPP
                )

#RUTAS DEL SERVIDOR 

@app.get("/a", response_class=HTMLResponse)
def inicio():
    clientes = leer_json(DATOS_CLIENTES)
    prestamos = leer_json(DATOS_PRESTAMOS)
    
    nombres_dict = {c['id']: c['nombre'] for c in clientes if isinstance(c, dict)}

    estilo = """ 
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #e0e0e0; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 12px; }
        h1 { color: #bb86fc; text-align: center; }
        .form-group { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 30px; }
        input, select, button { padding: 12px; background: #2c2c2c; color: white; border: 1px solid #444; border-radius: 6px; }
        button { background-color: #bb86fc; color: #121212; font-weight: bold; cursor: pointer; border: none; grid-column: span 2; }

        details { background: #252525; margin-bottom: 10px; border-radius: 8px; overflow: hidden; border: 1px solid #333; }
        summary { 
            padding: 15px; 
            cursor: pointer; 
            font-weight: bold; 
            list-style: none; 
            display: grid; 
            grid-template-columns: 1fr 1fr 1fr; /* 3 COLUMNAS PARA CENTRAR */
            align-items: center; 
        }
        summary:hover { background: #2d2d2d; }
        summary::-webkit-details-marker { display: none; }
        
        .text-center { text-align: center; }
        .text-right { text-align: right; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background-color: #3700b3; color: white; padding: 10px; font-size: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #333; font-size: 14px; }
        .sub-table { width: 95%; margin: 10px auto; background: #1a1a1a; }
        
        .pago { color: #03dac6; } .pendiente { color: #ffb74d; } .no-pago { color: #cf6679; }
        .client-name { color: #bb86fc; }
        .badge { background: #3700b3; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
    </style>
    
    <script>
    function mascaraMoneda(i) {
        let cursor = i.selectionStart;
        let valorViejo = i.value;
        let v = i.value.replace(/\\D/g, "");
        v = v.replace(/(\\d)(?=(\\d{3})+(?!\\d))/g, "$1.");
        let valorNuevo = v ? "$" + v : "";
        i.value = valorNuevo;
        if (valorNuevo.length > valorViejo.length && valorViejo !== "") {
            cursor += (valorNuevo.length - valorViejo.length);
        }
        i.setSelectionRange(cursor, cursor);
    }
    </script>
    """

    formulario = f"""
    <div class="container">
        <h1>PRESTAMOS 2026</h1>
        <form action="/registrar_web" method="post" class="form-group">  
            <input type="text" name="nombre" placeholder="Nombre del Cliente" required>
            <input type="text" name="prestado" placeholder="Monto Prestado ($)" oninput="mascaraMoneda(this)" required>
            <input type="text" name="monto_cuota" placeholder="Monto Cuota ($)" oninput="mascaraMoneda(this)" required>
            <select name="cant_cuotas">
                <option value="1">1 Cuota</option>
                <option value="2">2 Cuotas</option>
                <option value="3">3 Cuotas</option>
                <option value="4">4 Cuotas</option>
                <option value="5">5 Cuotas</option>
                <option value="6">6 Cuotas</option>
                <option value="7">7 Cuotas</option>
                <option value="8">8 Cuotas</option>
                <option value="9">9 Cuotas</option>
                <option value="10">10 Cuotas</option>
            </select>
            <div style="display: flex; flex-direction: column; align-items: right; margin: 0px 0;">
                
                <input type="date" id="fecha_prestamo" name="userdate" required>
            </div>

            <button type="submit">GENERAR PRÉSTAMO</button>
        </form>
    """

    acordeon = ""
    for p in prestamos:
        if not isinstance(p, dict): continue
        nombre_c = nombres_dict.get(p['id_cliente'], f"ID: {p['id_cliente']}")
        
        filas_cuotas = ""
        for c in p['plan_pagos']:
            clase = c['estado'].lower().replace(" ", "-")
            filas_cuotas += f"""
                <tr>
                    <td>{c['nro_cuota']}</td>
                    <td>{c['vencimiento']}</td>
                    <td>${c['monto_a_pagar']:,.0f}</td>
                    <td class="{clase}">{c['estado']}</td>
                </tr>
            """

        acordeon += f"""
        <details>
            <summary>
                <span class="client-name">{nombre_c}</span>
                <span class="text-center">Prestamo de: <b>${p['Prestado']:,.0f}</b></span>
                <div class="text-right">
                    <span class="badge">{p['cantidad_cuotas_mes']} cuotas</span>
                </div>
            </summary>
            <table class="sub-table">
                <thead>
                    <tr><th>Nº</th><th>Vencimiento</th><th>Monto</th><th>Estado</th></tr>
                </thead>
                <tbody>
                    {filas_cuotas}
                </tbody>
            </table>
        </details>
        """

    if not acordeon:
        acordeon = "<p style='text-align:center;'>No hay registros actuales.</p>"

    return estilo + formulario + acordeon + "</div>"

@app.post("/registrar_web")#el button type="submit" de la variable formulario es lo que dispara la funcion
def registrar_web(# aca definicmos que interceptara registar_web donde en la variable formulario se dijo que se usara esto:
    nombre: str = Form(...), #gracias al "<form action="/registrar_web" method="post" class="form-group">"  
    prestado: str = Form(...), 
    monto_cuota: str = Form(...), #cuando se aprete el boton submit, post buscara estas variables en el formulario y las pasara a esta funcion
    cant_cuotas: int = Form(...),
    userdate: str = Form(...) # Esta es la fecha del input, se pone string porque viene en formato "YYYY-MM-DD" y lo convertiremos a datetime dentro de la función(def registrar_web)donde guardamos estas variables
):
    clientes = leer_json(DATOS_CLIENTES)#leemos los datos actuales de clientes y prestamos para agregar el nuevo registro sin perder los anteriores
    prestamos = leer_json(DATOS_PRESTAMOS)
    
    p_limpio = float(prestado.replace("$", "").replace(".", ""))#limpiamos el string del input para convertirlo a float, eliminando el simbolo de pesos y los puntos de miles
    c_limpia = float(monto_cuota.replace("$", "").replace(".", ""))#limpiamos el string del input para convertirlo a float, eliminando el simbolo de pesos y los puntos de miles
    
    # 1. Convertir el string del input a un objeto datetime
    # El formato del input type="date" es siempre YYYY-MM-DD
    fecha_base = datetime.strptime(userdate, "%Y-%m-%d") # Convertimos el string a datetime para usarlo como base de las fechas de vencimiento de las cuotas
    
    nuevo_id = len(clientes) + 1# Generamos un nuevo ID basado en la cantidad actual de clientes, esto asegura que cada cliente tenga un ID único y secuencial
    clientes.append({"id": nuevo_id, "nombre": nombre, "idcuota": nuevo_id})# Agregamos el nuevo cliente a la lista de clientes, usando el nuevo ID generado y el nombre proporcionado en el formulario
    
    plan = []#creamos una lista vacia para agregar despues cada cuota, dentro se guradara en formato json, y dentro sus datos de cada cuota por separado
    # 2. Usar fecha_base en lugar de datetime.now()
    for i in range(1, cant_cuotas + 1):
        # 1. Calculamos el mes y año teóricos
        mes_total = fecha_base.month + i
        
        # 2. Ajustamos el año si el mes pasa de 12
        # (mes_total - 1) // 12 nos dice cuántos años sumar
        anio_nuevo = fecha_base.year + (mes_total - 1) // 12
        
        # 3. Ajustamos el mes para que sea del 1 al 12
        mes_nuevo = (mes_total - 1) % 12 + 1
        
        # 4. Mantenemos el MISMO día original
        dia_original = fecha_base.day
        
        # NOTA: Esto funciona perfecto para días del 1 al 28 (como el día 3).
        # Si tu fecha base fuera un 31, esto daría error en meses cortos (como febrero).
        # Para evitar errores simples, usamos un try/except por si acaso cae en un día inválido (ej: 30 de febrero).
        try:
            vencimiento_date = fecha_base.replace(year=anio_nuevo, month=mes_nuevo, day=dia_original)
        except ValueError:
            # Si el día no existe en ese mes (ej: 31 de febrero), tomamos el día 28 como "parche" rápido
            vencimiento_date = fecha_base.replace(year=anio_nuevo, month=mes_nuevo, day=28)

        vencimiento = vencimiento_date.strftime("%Y-%m-%d")
        
        plan.append({
            "nro_cuota": i, 
            "vencimiento": vencimiento, 
            "monto_a_pagar": c_limpia, 
            "estado": "Pendiente", 
            "recargo_por_atraso": 0
        })

    
    prestamos.append({ 
        "id_prestamo": nuevo_id,
        "id_cliente": nuevo_id,
        "Prestado": p_limpio,
        "cantidad_cuotas_mes": cant_cuotas,
        "monto_fijo_cuota": c_limpia,
        "plan_pagos": plan
    })
    
    guardar_json(DATOS_CLIENTES, clientes)
    guardar_json(DATOS_PRESTAMOS, prestamos)
    
    return HTMLResponse(content="<script>window.location.href='/a';</script>")

if __name__ == "__main__":
    import uvicorn
    # Chequeamos vencimientos al arrancar
    enviar_alertas_vencimiento()
    uvicorn.run(app, host="0.0.0.0", port=8000)