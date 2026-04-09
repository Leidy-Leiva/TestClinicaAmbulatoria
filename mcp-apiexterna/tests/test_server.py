"""
Tests unitarios para el servidor MCP Weather Colombia.
Ejecutar con: pytest tests/test_server.py -v

Nota: Los tests que llaman APIs externas se marcan con @pytest.mark.integration
y se pueden omitir con: pytest -m "not integration"
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from server import (
    _resolver_ciudad,
    _codigo_wmo,
    _nivel_uv,
    _calidad_aire,
    CIUDADES_COLOMBIA,
    clima_actual,
    pronostico_diario,
    pronostico_horario,
    comparar_ciudades,
    listar_ciudades,
    buscar_ciudad,
    historial_clima,
    calidad_aire,
)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def test_resolver_ciudad_exacto():
    c = _resolver_ciudad("bogota")
    assert c["nombre"] == "Bogotá"


def test_resolver_ciudad_con_tilde():
    c = _resolver_ciudad("Bogotá")
    assert c["nombre"] == "Bogotá"


def test_resolver_ciudad_parcial():
    c = _resolver_ciudad("medellin")
    assert c["nombre"] == "Medellín"


def test_resolver_ciudad_no_encontrada():
    with pytest.raises(ValueError, match="no encontrada"):
        _resolver_ciudad("Ciudad Inexistente XYZ")


def test_codigo_wmo_conocido():
    assert _codigo_wmo(0) == "Cielo despejado"
    assert _codigo_wmo(61) == "Lluvia ligera"
    assert _codigo_wmo(95) == "Tormenta eléctrica"


def test_codigo_wmo_desconocido():
    result = _codigo_wmo(999)
    assert "999" in result


def test_nivel_uv():
    assert _nivel_uv(0) == "Bajo"
    assert _nivel_uv(4) == "Moderado"
    assert _nivel_uv(7) == "Alto"
    assert _nivel_uv(9) == "Muy alto"
    assert _nivel_uv(12) == "Extremo"


def test_calidad_aire_niveles():
    assert _calidad_aire(25)  == "Buena"
    assert _calidad_aire(75)  == "Moderada"
    assert _calidad_aire(125) == "Dañina para grupos sensibles"
    assert _calidad_aire(175) == "Dañina"
    assert _calidad_aire(250) == "Muy dañina"
    assert _calidad_aire(350) == "Peligrosa"


def test_ciudades_colombia_completo():
    assert "bogota" in CIUDADES_COLOMBIA
    assert "medellin" in CIUDADES_COLOMBIA
    assert "cali" in CIUDADES_COLOMBIA
    assert "barranquilla" in CIUDADES_COLOMBIA
    assert "cartagena" in CIUDADES_COLOMBIA
    assert len(CIUDADES_COLOMBIA) >= 20


def test_ciudades_tienen_campos_requeridos():
    for key, ciudad in CIUDADES_COLOMBIA.items():
        assert "lat" in ciudad, f"{key} no tiene latitud"
        assert "lon" in ciudad, f"{key} no tiene longitud"
        assert "nombre" in ciudad, f"{key} no tiene nombre"
        assert "depto" in ciudad, f"{key} no tiene departamento"


def test_coordenadas_colombia_validas():
    """Verifica que todas las ciudades tengan coordenadas dentro de Colombia."""
    for key, c in CIUDADES_COLOMBIA.items():
        assert -5 <= c["lat"] <= 14, f"{key}: latitud fuera de rango ({c['lat']})"
        assert -83 <= c["lon"] <= -66, f"{key}: longitud fuera de rango ({c['lon']})"


# ── LISTAR CIUDADES ───────────────────────────────────────────────────────────

def test_listar_ciudades_todas():
    result = listar_ciudades()
    assert result["total"] == len(CIUDADES_COLOMBIA)
    assert len(result["ciudades"]) == len(CIUDADES_COLOMBIA)


def test_listar_ciudades_por_departamento():
    result = listar_ciudades(departamento="Antioquia")
    assert result["total"] >= 1
    for c in result["ciudades"]:
        assert "Antioquia" in c["departamento"]


def test_listar_ciudades_departamento_inexistente():
    result = listar_ciudades(departamento="Departamento Inexistente XYZ")
    assert result["total"] == 0


# ── VALIDACIONES ──────────────────────────────────────────────────────────────

def test_pronostico_diario_dias_invalidos():
    with pytest.raises(ValueError, match="entre 1 y 16"):
        pronostico_diario("bogota", dias=0)

    with pytest.raises(ValueError, match="entre 1 y 16"):
        pronostico_diario("bogota", dias=17)


def test_pronostico_horario_horas_invalidas():
    with pytest.raises(ValueError, match="entre 1 y 168"):
        pronostico_horario("bogota", horas=0)

    with pytest.raises(ValueError, match="entre 1 y 168"):
        pronostico_horario("bogota", horas=200)


def test_comparar_ciudades_vacia():
    with pytest.raises(ValueError, match="al menos una ciudad"):
        comparar_ciudades([])


def test_comparar_ciudades_excede_maximo():
    with pytest.raises(ValueError, match="Máximo 10"):
        comparar_ciudades(["bogota"] * 11)


def test_historial_clima_fechas_invalidas():
    with pytest.raises(ValueError, match="formato YYYY-MM-DD"):
        historial_clima("bogota", "01/01/2023", "31/01/2023")


def test_historial_clima_fecha_fin_antes_inicio():
    with pytest.raises(ValueError, match="posterior"):
        historial_clima("bogota", "2023-12-31", "2023-01-01")


def test_historial_clima_rango_excesivo():
    with pytest.raises(ValueError, match="365 días"):
        historial_clima("bogota", "2020-01-01", "2022-01-01")


# ── TESTS DE INTEGRACIÓN (requieren conexión a internet) ──────────────────────

@pytest.mark.integration
def test_clima_actual_bogota():
    result = clima_actual("Bogotá")
    assert result["ciudad"] == "Bogotá"
    assert isinstance(result["temperatura_c"], float)
    assert 0 <= result["humedad_pct"] <= 100
    assert result["fuente"] == "Open-Meteo"


@pytest.mark.integration
def test_clima_actual_medellin():
    result = clima_actual("Medellín")
    assert result["ciudad"] == "Medellín"
    assert result["departamento"] == "Antioquia"
    assert "descripcion" in result


@pytest.mark.integration
def test_pronostico_diario_7_dias():
    result = pronostico_diario("Cali", dias=7)
    assert result["ciudad"] == "Cali"
    assert result["dias_pronosticados"] == 7
    assert len(result["pronostico"]) == 7
    for dia in result["pronostico"]:
        assert "temp_max_c" in dia
        assert "temp_min_c" in dia
        assert "descripcion" in dia


@pytest.mark.integration
def test_pronostico_horario_24h():
    result = pronostico_horario("Barranquilla", horas=24)
    assert result["ciudad"] == "Barranquilla"
    assert result["horas_pronosticadas"] == 24


@pytest.mark.integration
def test_comparar_ciudades_principales():
    result = comparar_ciudades(["Bogotá", "Medellín", "Cali", "Barranquilla"])
    assert result["total_ciudades"] == 4
    assert result["ciudad_mas_caliente"] is not None
    assert result["ciudad_mas_fria"] is not None
    # La costa debe ser más caliente que Bogotá generalmente
    temps = {c["ciudad"]: c["temperatura_c"] for c in result["comparacion"]}
    assert temps.get("Barranquilla", 0) >= temps.get("Bogotá", 100)


@pytest.mark.integration
def test_calidad_aire_bogota():
    result = calidad_aire("Bogotá")
    assert result["ciudad"] == "Bogotá"
    assert "aqi_europeo" in result
    assert "pm2_5_ug_m3" in result
    assert "calidad" in result


@pytest.mark.integration
def test_buscar_ciudad_colombia():
    result = buscar_ciudad("Bogotá")
    assert result["total_resultados"] >= 1
    nombres = [c["nombre"] for c in result["ciudades"]]
    assert any("Bogot" in n for n in nombres)


@pytest.mark.integration
def test_historial_clima_enero_2024():
    result = historial_clima("Bogotá", "2024-01-01", "2024-01-31")
    assert result["ciudad"] == "Bogotá"
    assert result["total_dias"] == 31
    assert result["resumen"]["temp_media_periodo_c"] is not None
    # Bogotá tiene temperatura templada (aprox 13-18°C)
    assert 5 <= result["resumen"]["temp_media_periodo_c"] <= 25
