"""
MCP Weather Server — Colombia
Consume la API de Open-Meteo (gratuita, sin API key) y opcionalmente
OpenWeatherMap para datos del clima en ciudades colombianas.
"""

import os
import httpx
from datetime import datetime, timezone
from typing import Optional
from fastmcp import FastMCP

# ── Configuración ──────────────────────────────────────────────────────────────
OWM_API_KEY = os.getenv("OWM_API_KEY", "")          # opcional
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))

# Endpoints
OPEN_METEO_FORECAST   = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE    = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_AIR        = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPEN_METEO_GEO        = "https://geocoding-api.open-meteo.com/v1/search"
OWM_CURRENT           = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST          = "https://api.openweathermap.org/data/2.5/forecast"

mcp = FastMCP(
    name="weather-colombia-mcp",
    instructions=(
        "Servidor MCP para consultar el clima en Colombia. "
        "Usa Open-Meteo (gratuito, sin API key) para pronósticos, "
        "historial y calidad del aire. "
        "Puedes consultar por nombre de ciudad o coordenadas. "
        "Ciudades disponibles: Bogotá, Medellín, Cali, Barranquilla, "
        "Cartagena, Bucaramanga, Pereira, Manizales, Santa Marta, Cúcuta y más."
    ),
)

# ── Ciudades colombianas precargadas ──────────────────────────────────────────
CIUDADES_COLOMBIA: dict[str, dict] = {
    "bogota":        {"lat": 4.7110,  "lon": -74.0721, "nombre": "Bogotá",        "depto": "Cundinamarca"},
    "medellin":      {"lat": 6.2442,  "lon": -75.5812, "nombre": "Medellín",      "depto": "Antioquia"},
    "cali":          {"lat": 3.4516,  "lon": -76.5320, "nombre": "Cali",          "depto": "Valle del Cauca"},
    "barranquilla":  {"lat": 10.9685, "lon": -74.7813, "nombre": "Barranquilla",  "depto": "Atlántico"},
    "cartagena":     {"lat": 10.3910, "lon": -75.4794, "nombre": "Cartagena",     "depto": "Bolívar"},
    "bucaramanga":   {"lat": 7.1193,  "lon": -73.1227, "nombre": "Bucaramanga",   "depto": "Santander"},
    "pereira":       {"lat": 4.8133,  "lon": -75.6961, "nombre": "Pereira",       "depto": "Risaralda"},
    "manizales":     {"lat": 5.0703,  "lon": -75.5138, "nombre": "Manizales",     "depto": "Caldas"},
    "santa_marta":   {"lat": 11.2408, "lon": -74.1990, "nombre": "Santa Marta",   "depto": "Magdalena"},
    "cucuta":        {"lat": 7.8939,  "lon": -72.5078, "nombre": "Cúcuta",        "depto": "Norte de Santander"},
    "ibague":        {"lat": 4.4389,  "lon": -75.2322, "nombre": "Ibagué",        "depto": "Tolima"},
    "villavicencio": {"lat": 4.1420,  "lon": -73.6266, "nombre": "Villavicencio", "depto": "Meta"},
    "pasto":         {"lat": 1.2136,  "lon": -77.2811, "nombre": "Pasto",         "depto": "Nariño"},
    "armenia":       {"lat": 4.5339,  "lon": -75.6811, "nombre": "Armenia",       "depto": "Quindío"},
    "monteria":      {"lat": 8.7575,  "lon": -75.8851, "nombre": "Montería",      "depto": "Córdoba"},
    "sincelejo":     {"lat": 9.3047,  "lon": -75.3978, "nombre": "Sincelejo",     "depto": "Sucre"},
    "valledupar":    {"lat": 10.4631, "lon": -73.2532, "nombre": "Valledupar",    "depto": "Cesar"},
    "neiva":         {"lat": 2.9273,  "lon": -75.2819, "nombre": "Neiva",         "depto": "Huila"},
    "popayan":       {"lat": 2.4419,  "lon": -76.6061, "nombre": "Popayán",       "depto": "Cauca"},
    "tunja":         {"lat": 5.5353,  "lon": -73.3678, "nombre": "Tunja",         "depto": "Boyacá"},
    "leticia":       {"lat": -4.2153, "lon": -69.9406, "nombre": "Leticia",       "depto": "Amazonas"},
    "san_andres":    {"lat": 12.5847, "lon": -81.7006, "nombre": "San Andrés",    "depto": "Archipiélago"},
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_client() -> httpx.Client:
    return httpx.Client(timeout=HTTP_TIMEOUT)


def _resolver_ciudad(ciudad: str) -> dict:
    """Busca una ciudad en el catálogo colombiano por nombre (fuzzy)."""
    key = ciudad.lower().strip()
    key = key.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    key = key.replace(" ", "_")

    if key in CIUDADES_COLOMBIA:
        return CIUDADES_COLOMBIA[key]

    # Búsqueda parcial
    for k, v in CIUDADES_COLOMBIA.items():
        if key in k or key in v["nombre"].lower():
            return v

    raise ValueError(
        f"Ciudad '{ciudad}' no encontrada. Ciudades disponibles: "
        + ", ".join(c["nombre"] for c in CIUDADES_COLOMBIA.values())
    )


def _codigo_wmo(code: int) -> str:
    """Traduce el código WMO de clima a texto en español."""
    tabla = {
        0: "Cielo despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado",
        3: "Nublado", 45: "Niebla", 48: "Niebla con escarcha",
        51: "Llovizna ligera", 53: "Llovizna moderada", 55: "Llovizna densa",
        61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia fuerte",
        71: "Nevada ligera", 73: "Nevada moderada", 75: "Nevada fuerte",
        80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos fuertes",
        95: "Tormenta eléctrica", 96: "Tormenta con granizo ligero",
        99: "Tormenta con granizo fuerte",
    }
    return tabla.get(code, f"Código WMO {code}")


def _nivel_uv(uv: float) -> str:
    if uv < 3:   return "Bajo"
    if uv < 6:   return "Moderado"
    if uv < 8:   return "Alto"
    if uv < 11:  return "Muy alto"
    return "Extremo"


def _calidad_aire(aqi: int) -> str:
    if aqi <= 50:  return "Buena"
    if aqi <= 100: return "Moderada"
    if aqi <= 150: return "Dañina para grupos sensibles"
    if aqi <= 200: return "Dañina"
    if aqi <= 300: return "Muy dañina"
    return "Peligrosa"


# ── Herramientas MCP ───────────────────────────────────────────────────────────

@mcp.tool()
def clima_actual(ciudad: str) -> dict:
    """
    Obtiene el clima actual de una ciudad colombiana.
    Incluye temperatura, sensación térmica, humedad, viento,
    precipitación, nubosidad, presión e índice UV.

    Args:
        ciudad: Nombre de la ciudad colombiana (ej: 'Bogotá', 'Medellín', 'Cali').

    Returns:
        Condiciones meteorológicas actuales.
    """
    c = _resolver_ciudad(ciudad)

    params = {
        "latitude": c["lat"],
        "longitude": c["lon"],
        "current": [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "precipitation", "weather_code", "cloud_cover", "pressure_msl",
            "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
            "uv_index", "is_day",
        ],
        "timezone": "America/Bogota",
        "wind_speed_unit": "kmh",
    }

    with _get_client() as client:
        resp = client.get(OPEN_METEO_FORECAST, params=params)
        resp.raise_for_status()
        data = resp.json()

    cur = data["current"]
    uv  = cur.get("uv_index", 0)

    return {
        "ciudad": c["nombre"],
        "departamento": c["depto"],
        "coordenadas": {"lat": c["lat"], "lon": c["lon"]},
        "hora_local": cur["time"],
        "temperatura_c": cur["temperature_2m"],
        "sensacion_termica_c": cur["apparent_temperature"],
        "humedad_pct": cur["relative_humidity_2m"],
        "descripcion": _codigo_wmo(cur["weather_code"]),
        "precipitacion_mm": cur["precipitation"],
        "nubosidad_pct": cur["cloud_cover"],
        "presion_hpa": cur["pressure_msl"],
        "viento_kmh": cur["wind_speed_10m"],
        "direccion_viento_grados": cur["wind_direction_10m"],
        "rachas_viento_kmh": cur["wind_gusts_10m"],
        "indice_uv": uv,
        "nivel_uv": _nivel_uv(uv),
        "es_de_dia": bool(cur["is_day"]),
        "fuente": "Open-Meteo",
    }


@mcp.tool()
def pronostico_diario(ciudad: str, dias: int = 7) -> dict:
    """
    Pronóstico del tiempo día a día para una ciudad colombiana.

    Args:
        ciudad: Nombre de la ciudad colombiana.
        dias: Número de días a pronosticar, entre 1 y 16 (default: 7).

    Returns:
        Pronóstico diario con temperatura máx/mín, lluvia, UV y descripción.
    """
    if not 1 <= dias <= 16:
        raise ValueError("El número de días debe estar entre 1 y 16.")

    c = _resolver_ciudad(ciudad)

    params = {
        "latitude": c["lat"],
        "longitude": c["lon"],
        "daily": [
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "apparent_temperature_max", "apparent_temperature_min",
            "precipitation_sum", "precipitation_probability_max",
            "wind_speed_10m_max", "wind_gusts_10m_max",
            "uv_index_max", "sunrise", "sunset",
        ],
        "timezone": "America/Bogota",
        "forecast_days": dias,
        "wind_speed_unit": "kmh",
    }

    with _get_client() as client:
        resp = client.get(OPEN_METEO_FORECAST, params=params)
        resp.raise_for_status()
        data = resp.json()

    daily = data["daily"]
    dias_data = []
    for i, fecha in enumerate(daily["time"]):
        uv = daily["uv_index_max"][i] or 0
        dias_data.append({
            "fecha": fecha,
            "descripcion": _codigo_wmo(daily["weather_code"][i]),
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "sensacion_max_c": daily["apparent_temperature_max"][i],
            "sensacion_min_c": daily["apparent_temperature_min"][i],
            "precipitacion_mm": daily["precipitation_sum"][i],
            "prob_lluvia_pct": daily["precipitation_probability_max"][i],
            "viento_max_kmh": daily["wind_speed_10m_max"][i],
            "rachas_max_kmh": daily["wind_gusts_10m_max"][i],
            "uv_max": uv,
            "nivel_uv": _nivel_uv(uv),
            "amanecer": daily["sunrise"][i],
            "atardecer": daily["sunset"][i],
        })

    return {
        "ciudad": c["nombre"],
        "departamento": c["depto"],
        "dias_pronosticados": len(dias_data),
        "pronostico": dias_data,
        "fuente": "Open-Meteo",
    }


@mcp.tool()
def pronostico_horario(ciudad: str, horas: int = 24) -> dict:
    """
    Pronóstico hora a hora para una ciudad colombiana.

    Args:
        ciudad: Nombre de la ciudad colombiana.
        horas: Número de horas a pronosticar, entre 1 y 168 (default: 24).

    Returns:
        Pronóstico horario con temperatura, lluvia, viento y humedad.
    """
    if not 1 <= horas <= 168:
        raise ValueError("El número de horas debe estar entre 1 y 168.")

    c = _resolver_ciudad(ciudad)

    params = {
        "latitude": c["lat"],
        "longitude": c["lon"],
        "hourly": [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "precipitation_probability", "precipitation", "weather_code",
            "wind_speed_10m", "wind_direction_10m", "uv_index", "is_day",
        ],
        "timezone": "America/Bogota",
        "forecast_days": max(1, (horas // 24) + 1),
        "wind_speed_unit": "kmh",
    }

    with _get_client() as client:
        resp = client.get(OPEN_METEO_FORECAST, params=params)
        resp.raise_for_status()
        data = resp.json()

    hourly = data["hourly"]
    horas_data = []
    for i in range(min(horas, len(hourly["time"]))):
        uv = hourly["uv_index"][i] or 0
        horas_data.append({
            "hora": hourly["time"][i],
            "temperatura_c": hourly["temperature_2m"][i],
            "sensacion_c": hourly["apparent_temperature"][i],
            "humedad_pct": hourly["relative_humidity_2m"][i],
            "descripcion": _codigo_wmo(hourly["weather_code"][i]),
            "prob_lluvia_pct": hourly["precipitation_probability"][i],
            "precipitacion_mm": hourly["precipitation"][i],
            "viento_kmh": hourly["wind_speed_10m"][i],
            "direccion_viento": hourly["wind_direction_10m"][i],
            "uv": uv,
            "nivel_uv": _nivel_uv(uv),
            "es_de_dia": bool(hourly["is_day"][i]),
        })

    return {
        "ciudad": c["nombre"],
        "departamento": c["depto"],
        "horas_pronosticadas": len(horas_data),
        "pronostico": horas_data,
        "fuente": "Open-Meteo",
    }


@mcp.tool()
def calidad_aire(ciudad: str) -> dict:
    """
    Obtiene la calidad del aire actual y pronóstico para una ciudad colombiana.
    Incluye PM2.5, PM10, ozono, NO2 e índice AQI europeo.

    Args:
        ciudad: Nombre de la ciudad colombiana.

    Returns:
        Índices de calidad del aire y contaminantes principales.
    """
    c = _resolver_ciudad(ciudad)

    params = {
        "latitude": c["lat"],
        "longitude": c["lon"],
        "current": [
            "pm2_5", "pm10", "carbon_monoxide", "nitrogen_dioxide",
            "ozone", "european_aqi",
        ],
        "hourly": ["pm2_5", "pm10", "european_aqi"],
        "timezone": "America/Bogota",
        "forecast_days": 1,
    }

    with _get_client() as client:
        resp = client.get(OPEN_METEO_AIR, params=params)
        resp.raise_for_status()
        data = resp.json()

    cur = data["current"]
    aqi = cur.get("european_aqi") or 0

    return {
        "ciudad": c["nombre"],
        "departamento": c["depto"],
        "hora_local": cur["time"],
        "aqi_europeo": aqi,
        "calidad": _calidad_aire(aqi),
        "pm2_5_ug_m3": cur.get("pm2_5"),
        "pm10_ug_m3": cur.get("pm10"),
        "monoxido_carbono_ug_m3": cur.get("carbon_monoxide"),
        "dioxido_nitrogeno_ug_m3": cur.get("nitrogen_dioxide"),
        "ozono_ug_m3": cur.get("ozone"),
        "fuente": "Open-Meteo CAMS",
    }


@mcp.tool()
def historial_clima(ciudad: str, fecha_inicio: str, fecha_fin: str) -> dict:
    """
    Consulta el historial climático de una ciudad colombiana.

    Args:
        ciudad: Nombre de la ciudad colombiana.
        fecha_inicio: Fecha de inicio en formato YYYY-MM-DD (desde 1940).
        fecha_fin: Fecha de fin en formato YYYY-MM-DD.

    Returns:
        Datos históricos diarios de temperatura, lluvia y viento.
    """
    c = _resolver_ciudad(ciudad)

    # Validar fechas
    try:
        dt_ini = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Las fechas deben tener formato YYYY-MM-DD.")

    if dt_fin < dt_ini:
        raise ValueError("La fecha de fin debe ser posterior a la de inicio.")

    dias = (dt_fin - dt_ini).days
    if dias > 365:
        raise ValueError("El rango máximo es de 365 días por consulta.")

    params = {
        "latitude": c["lat"],
        "longitude": c["lon"],
        "start_date": fecha_inicio,
        "end_date": fecha_fin,
        "daily": [
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "temperature_2m_mean", "precipitation_sum",
            "wind_speed_10m_max", "shortwave_radiation_sum",
        ],
        "timezone": "America/Bogota",
        "wind_speed_unit": "kmh",
    }

    with _get_client() as client:
        resp = client.get(OPEN_METEO_ARCHIVE, params=params)
        resp.raise_for_status()
        data = resp.json()

    daily = data["daily"]
    registros = []
    for i, fecha in enumerate(daily["time"]):
        registros.append({
            "fecha": fecha,
            "descripcion": _codigo_wmo(daily["weather_code"][i]),
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "temp_media_c": daily["temperature_2m_mean"][i],
            "precipitacion_mm": daily["precipitation_sum"][i],
            "viento_max_kmh": daily["wind_speed_10m_max"][i],
            "radiacion_mj_m2": daily["shortwave_radiation_sum"][i],
        })

    temps = [r["temp_media_c"] for r in registros if r["temp_media_c"] is not None]
    lluvias = [r["precipitacion_mm"] for r in registros if r["precipitacion_mm"] is not None]

    return {
        "ciudad": c["nombre"],
        "departamento": c["depto"],
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_dias": len(registros),
        "resumen": {
            "temp_media_periodo_c": round(sum(temps) / len(temps), 1) if temps else None,
            "temp_max_periodo_c": max(temps) if temps else None,
            "temp_min_periodo_c": min(temps) if temps else None,
            "precipitacion_total_mm": round(sum(lluvias), 1) if lluvias else None,
        },
        "registros": registros,
        "fuente": "Open-Meteo ERA5 Archive",
    }


@mcp.tool()
def comparar_ciudades(ciudades: list[str]) -> dict:
    """
    Compara el clima actual entre varias ciudades colombianas.

    Args:
        ciudades: Lista de nombres de ciudades colombianas (máximo 10).

    Returns:
        Tabla comparativa con temperatura, lluvia, viento y descripción.
    """
    if not ciudades:
        raise ValueError("Debes proporcionar al menos una ciudad.")
    if len(ciudades) > 10:
        raise ValueError("Máximo 10 ciudades por comparación.")

    resultados = []
    errores = []

    for nombre in ciudades:
        try:
            datos = clima_actual(nombre)
            resultados.append({
                "ciudad": datos["ciudad"],
                "departamento": datos["departamento"],
                "temperatura_c": datos["temperatura_c"],
                "sensacion_termica_c": datos["sensacion_termica_c"],
                "humedad_pct": datos["humedad_pct"],
                "descripcion": datos["descripcion"],
                "precipitacion_mm": datos["precipitacion_mm"],
                "viento_kmh": datos["viento_kmh"],
                "indice_uv": datos["indice_uv"],
                "nivel_uv": datos["nivel_uv"],
            })
        except Exception as e:
            errores.append({"ciudad": nombre, "error": str(e)})

    # Ordenar por temperatura
    resultados.sort(key=lambda x: x["temperatura_c"], reverse=True)

    return {
        "total_ciudades": len(resultados),
        "comparacion": resultados,
        "errores": errores,
        "ciudad_mas_caliente": resultados[0]["ciudad"] if resultados else None,
        "ciudad_mas_fria": resultados[-1]["ciudad"] if resultados else None,
        "fuente": "Open-Meteo",
    }


@mcp.tool()
def buscar_ciudad(nombre: str) -> dict:
    """
    Busca una ciudad colombiana o mundial por nombre usando la API de geocodificación.

    Args:
        nombre: Nombre de la ciudad a buscar.

    Returns:
        Lista de ciudades encontradas con sus coordenadas.
    """
    params = {
        "name": nombre,
        "count": 10,
        "language": "es",
        "format": "json",
        "countryCode": "CO",  # Filtrar por Colombia
    }

    with _get_client() as client:
        resp = client.get(OPEN_METEO_GEO, params=params)
        resp.raise_for_status()
        data = resp.json()

    resultados = data.get("results", [])
    ciudades = []
    for r in resultados:
        ciudades.append({
            "nombre": r.get("name"),
            "departamento": r.get("admin1"),
            "municipio": r.get("admin2"),
            "pais": r.get("country"),
            "latitud": r.get("latitude"),
            "longitud": r.get("longitude"),
            "elevacion_m": r.get("elevation"),
            "poblacion": r.get("population"),
        })

    return {
        "busqueda": nombre,
        "total_resultados": len(ciudades),
        "ciudades": ciudades,
        "fuente": "Open-Meteo Geocoding",
    }


@mcp.tool()
def clima_por_coordenadas(latitud: float, longitud: float, nombre_lugar: Optional[str] = None) -> dict:
    """
    Obtiene el clima actual para cualquier coordenada geográfica en Colombia.

    Args:
        latitud: Latitud en grados decimales (Colombia: -4 a 13).
        longitud: Longitud en grados decimales (Colombia: -82 a -66).
        nombre_lugar: Nombre opcional del lugar para identificar el resultado.

    Returns:
        Condiciones meteorológicas actuales para las coordenadas.
    """
    if not (-5 <= latitud <= 14 and -83 <= longitud <= -66):
        raise ValueError(
            "Las coordenadas parecen estar fuera de Colombia. "
            "Latitud: -4 a 13, Longitud: -82 a -67."
        )

    params = {
        "latitude": latitud,
        "longitude": longitud,
        "current": [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "precipitation", "weather_code", "cloud_cover", "pressure_msl",
            "wind_speed_10m", "wind_direction_10m", "uv_index", "is_day",
        ],
        "timezone": "America/Bogota",
        "wind_speed_unit": "kmh",
    }

    with _get_client() as client:
        resp = client.get(OPEN_METEO_FORECAST, params=params)
        resp.raise_for_status()
        data = resp.json()

    cur = data["current"]
    uv = cur.get("uv_index", 0)

    return {
        "lugar": nombre_lugar or f"Coordenadas ({latitud}, {longitud})",
        "latitud": latitud,
        "longitud": longitud,
        "hora_local": cur["time"],
        "temperatura_c": cur["temperature_2m"],
        "sensacion_termica_c": cur["apparent_temperature"],
        "humedad_pct": cur["relative_humidity_2m"],
        "descripcion": _codigo_wmo(cur["weather_code"]),
        "precipitacion_mm": cur["precipitation"],
        "nubosidad_pct": cur["cloud_cover"],
        "presion_hpa": cur["pressure_msl"],
        "viento_kmh": cur["wind_speed_10m"],
        "indice_uv": uv,
        "nivel_uv": _nivel_uv(uv),
        "es_de_dia": bool(cur["is_day"]),
        "fuente": "Open-Meteo",
    }


@mcp.tool()
def listar_ciudades(departamento: Optional[str] = None) -> dict:
    """
    Lista todas las ciudades colombianas disponibles en el servidor.

    Args:
        departamento: Filtra por departamento (opcional, ej: 'Antioquia').

    Returns:
        Lista de ciudades con sus coordenadas y departamentos.
    """
    ciudades = list(CIUDADES_COLOMBIA.values())

    if departamento:
        dep = departamento.lower()
        ciudades = [
            c for c in ciudades
            if dep in c["depto"].lower()
        ]

    return {
        "total": len(ciudades),
        "filtro_departamento": departamento,
        "ciudades": [
            {
                "nombre": c["nombre"],
                "departamento": c["depto"],
                "latitud": c["lat"],
                "longitud": c["lon"],
            }
            for c in ciudades
        ],
    }


# ── Recursos MCP ───────────────────────────────────────────────────────────────

@mcp.resource("weather://colombia/ciudades")
def resource_ciudades() -> str:
    """Lista rápida de todas las ciudades disponibles."""
    lines = ["🇨🇴 Ciudades colombianas disponibles", "=" * 40]
    for c in CIUDADES_COLOMBIA.values():
        lines.append(f"• {c['nombre']} ({c['depto']}) — {c['lat']}, {c['lon']}")
    return "\n".join(lines)


@mcp.resource("weather://colombia/{ciudad}")
def resource_clima_ciudad(ciudad: str) -> str:
    """Clima actual de una ciudad como recurso de texto."""
    try:
        d = clima_actual(ciudad)
        return (
            f"🌤️ {d['ciudad']}, {d['departamento']}\n"
            f"Hora: {d['hora_local']}\n"
            f"Temperatura: {d['temperatura_c']}°C (sensación {d['sensacion_termica_c']}°C)\n"
            f"Condición: {d['descripcion']}\n"
            f"Humedad: {d['humedad_pct']}%\n"
            f"Viento: {d['viento_kmh']} km/h\n"
            f"Lluvia: {d['precipitacion_mm']} mm\n"
            f"UV: {d['indice_uv']} ({d['nivel_uv']})\n"
        )
    except Exception as e:
        return f"Error obteniendo clima para '{ciudad}': {e}"


# ── Prompts MCP ────────────────────────────────────────────────────────────────

@mcp.prompt()
def weather_guide() -> str:
    """Guía de uso del servidor de clima para Colombia."""
    return """
Eres un asistente meteorológico especializado en Colombia.
Tienes acceso a datos del clima en tiempo real vía Open-Meteo (sin API key).

Herramientas disponibles:

🌡️ CLIMA ACTUAL
- clima_actual(ciudad)              → Temperatura, humedad, viento, UV, etc.
- clima_por_coordenadas(lat, lon)   → Clima para cualquier punto del país

📅 PRONÓSTICOS
- pronostico_diario(ciudad, dias)   → Hasta 16 días, día a día
- pronostico_horario(ciudad, horas) → Hasta 168 horas, hora a hora

🌍 COMPARACIÓN Y BÚSQUEDA
- comparar_ciudades([...])          → Compara clima entre varias ciudades
- buscar_ciudad(nombre)             → Geocodificación de cualquier lugar
- listar_ciudades(departamento)     → Lista de ciudades disponibles

🌫️ CALIDAD DEL AIRE
- calidad_aire(ciudad)              → PM2.5, PM10, ozono, AQI europeo

📊 HISTORIAL
- historial_clima(ciudad, ini, fin) → Datos históricos desde 1940

Ciudades principales:
Bogotá, Medellín, Cali, Barranquilla, Cartagena, Bucaramanga,
Pereira, Manizales, Santa Marta, Cúcuta, Ibagué, Villavicencio,
Pasto, Armenia, Montería, Valledupar, Neiva, Popayán, Tunja,
Leticia, San Andrés.

Recursos:
- weather://colombia/ciudades     → Lista completa de ciudades
- weather://colombia/{ciudad}     → Resumen del clima de una ciudad

Fuente: Open-Meteo (datos en tiempo real, sin API key)
"""


# ── Punto de entrada ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8002)
