
"""
==========================================================
GANADOSALUD AI - ACTIVIDAD 8
TEST DE PREDICCIONES Y MONITORIZACIÓN
==========================================================

Objetivo:
- Enviar 10 perfiles sanos por cada perfil diferente.
- Alternar los perfiles diferentes entre Enfermo y Observación.
- Registrar las predicciones reales del Random Forest.
- Medir la latencia de las solicitudes HTTP.
- Generar tráfico para Prometheus y Grafana.

IMPORTANTE:
Los perfiles son simulaciones de prueba.
El diagnóstico real de la API lo determina el modelo.
"""

import json
import random
import time
import urllib.request
import urllib.error

from collections import Counter


# ========================================================
# CONFIGURACIÓN GENERAL
# ========================================================

URL = "http://localhost:8000/predict"

NUMERO_CICLOS = 100
SANOS_POR_CICLO = 3

PAUSA_SEGUNDOS = 0.2
TIMEOUT_SEGUNDOS = 10

# Semilla para reproducir las variaciones de los datos
random.seed(42)


# ========================================================
# PERFILES SIMULADOS
# ========================================================

PERFILES = {
    "Sano": {
        "alimento_consumido_kg": 18.0,
        "pasos_por_dia": 7500,
        "horas_de_reposo": 7.5,
        "temperatura_corp_c": 38.5,
        "nivel_actividad": "Alto",
    },

    "Observación": {
        "alimento_consumido_kg": 12.0,
        "pasos_por_dia": 4200,
        "horas_de_reposo": 10.0,
        "temperatura_corp_c": 39.4,
        "nivel_actividad": "Moderado",
    },

    "Enfermo": {
        "alimento_consumido_kg": 5.0,
        "pasos_por_dia": 1000,
        "horas_de_reposo": 15.0,
        "temperatura_corp_c": 40.7,
        "nivel_actividad": "Bajo",
    },
}


# ========================================================
# GENERACIÓN DE DATOS
# ========================================================

def generar_datos(perfil, numero):

    datos = PERFILES[perfil].copy()

    # Variaciones controladas en cada animal
    datos["alimento_consumido_kg"] = round(
        max(
            0,
            datos["alimento_consumido_kg"]
            + random.uniform(-1, 1)
        ),
        2
    )

    datos["pasos_por_dia"] = max(
        0,
        datos["pasos_por_dia"]
        + random.randint(-200, 200)
    )

    datos["horas_de_reposo"] = round(
        min(
            24,
            max(
                0,
                datos["horas_de_reposo"]
                + random.uniform(-0.5, 0.5)
            )
        ),
        2
    )

    datos["temperatura_corp_c"] = round(
        datos["temperatura_corp_c"]
        + random.uniform(-0.2, 0.2),
        2
    )

    datos["animal_id"] = f"VACA_{numero:03d}"

    datos["dia"] = (numero % 30) + 1

    return datos


# ========================================================
# GENERAR SECUENCIA 10 SANOS + 1 DIFERENTE
# ========================================================

def generar_secuencia():

    secuencia = []

    for ciclo in range(NUMERO_CICLOS):

        secuencia.extend(
            ["Sano"] * SANOS_POR_CICLO
        )

        if ciclo % 2 == 0:
            secuencia.append("Enfermo")
        else:
            secuencia.append("Observación")

    return secuencia


# ========================================================
# ENVIAR PREDICCIÓN
# ========================================================

def enviar_prediccion(datos):

    solicitud = urllib.request.Request(
        URL,
        data=json.dumps(datos).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    inicio = time.perf_counter()

    with urllib.request.urlopen(
        solicitud,
        timeout=TIMEOUT_SEGUNDOS
    ) as respuesta:

        resultado = json.loads(
            respuesta.read().decode("utf-8")
        )

        duracion = time.perf_counter() - inicio

        return {
            "codigo_http": respuesta.status,
            "latencia": duracion,
            "diagnostico": resultado["prediccion"],
            "probabilidades": resultado.get(
                "probabilidades",
                {}
            ),
        }


# ========================================================
# PRUEBA PRINCIPAL
# ========================================================

def ejecutar_test():

    secuencia = generar_secuencia()

    total_solicitudes = len(secuencia)

    resultados = Counter()
    perfiles_enviados = Counter()
    comparaciones = Counter()

    latencias = []

    errores = 0

    print("=" * 78)
    print("GANADOSALUD AI - TEST DE PREDICCIONES")
    print("=" * 78)

    print(f"Total de solicitudes: {total_solicitudes}")
    print(f"Ciclos: {NUMERO_CICLOS}")
    print(f"Sanos por ciclo: {SANOS_POR_CICLO}")

    print("\nDistribución programada:")

    for perfil in [
        "Sano",
        "Enfermo",
        "Observación"
    ]:
        print(
            f"  {perfil}: {secuencia.count(perfil)}"
        )

    print("\nIniciando predicciones...\n")

    # ----------------------------------------------------
    # Ejecutar las solicitudes
    # ----------------------------------------------------

    for numero, perfil_esperado in enumerate(
        secuencia,
        start=1
    ):

        datos = generar_datos(
            perfil_esperado,
            numero
        )

        perfiles_enviados[perfil_esperado] += 1

        try:

            respuesta = enviar_prediccion(datos)

            diagnostico_real = respuesta["diagnostico"]
            latencia = respuesta["latencia"]
            codigo_http = respuesta["codigo_http"]

            resultados[diagnostico_real] += 1

            comparaciones[
                (perfil_esperado, diagnostico_real)
            ] += 1

            latencias.append(latencia)

            # Marcar los casos especiales
            indicador = (
                "***"
                if perfil_esperado != "Sano"
                else "   "
            )

            print(
                f"{indicador} "
                f"{numero:03d}/{total_solicitudes} | "
                f"Animal: {datos['animal_id']} | "
                f"Perfil: {perfil_esperado:12s} | "
                f"Predicción: {diagnostico_real:12s} | "
                f"HTTP: {codigo_http} | "
                f"Latencia: {latencia:.3f}s",
                flush=True
            )

        except urllib.error.HTTPError as error:

            errores += 1

            print(
                f"ERROR HTTP | "
                f"Animal: {datos['animal_id']} | "
                f"Código: {error.code}",
                flush=True
            )

        except (
            urllib.error.URLError,
            TimeoutError
        ) as error:

            errores += 1

            print(
                f"ERROR CONEXIÓN | "
                f"Animal: {datos['animal_id']} | "
                f"{error}",
                flush=True
            )

        time.sleep(PAUSA_SEGUNDOS)

    # ====================================================
    # RESUMEN FINAL
    # ====================================================

    print("\n" + "=" * 78)
    print("RESUMEN FINAL DE LA PRUEBA")
    print("=" * 78)

    print("\n1. PERFILES SIMULADOS ENVIADOS")

    for perfil in [
        "Sano",
        "Enfermo",
        "Observación"
    ]:

        print(
            f"  {perfil:12s}: "
            f"{perfiles_enviados[perfil]}"
        )

    print("\n2. DIAGNÓSTICOS REALES DEL MODELO")

    for diagnostico in [
        "Sano",
        "Enfermo",
        "Observación"
    ]:

        print(
            f"  {diagnostico:12s}: "
            f"{resultados[diagnostico]}"
        )

    print("\n3. COMPARACIÓN POR PERFIL")

    for perfil in [
        "Sano",
        "Enfermo",
        "Observación"
    ]:

        print(f"\n  Perfil enviado: {perfil}")

        for diagnostico in [
            "Sano",
            "Enfermo",
            "Observación"
        ]:

            cantidad = comparaciones[
                (perfil, diagnostico)
            ]

            print(
                f"    Predicho como "
                f"{diagnostico:12s}: {cantidad}"
            )

    print("\n4. MÉTRICAS HTTP")

    print(
        f"  Solicitudes programadas: "
        f"{total_solicitudes}"
    )

    print(
        f"  Predicciones exitosas: "
        f"{sum(resultados.values())}"
    )

    print(
        f"  Errores: {errores}"
    )

    if latencias:

        promedio = sum(latencias) / len(latencias)

        print(
            f"  Latencia promedio: "
            f"{promedio:.3f} segundos"
        )

        print(
            f"  Latencia mínima: "
            f"{min(latencias):.3f} segundos"
        )

        print(
            f"  Latencia máxima: "
            f"{max(latencias):.3f} segundos"
        )

    print("\n" + "=" * 78)
    print("PRUEBA FINALIZADA")
    print("=" * 78)

    print("\nMonitorización:")
    print("Grafana: http://localhost:3001")
    print("Prometheus: http://localhost:9090")
    print("Alertmanager: http://localhost:9093")


# ========================================================
# PUNTO DE ENTRADA
# ========================================================

if __name__ == "__main__":
    ejecutar_test()
