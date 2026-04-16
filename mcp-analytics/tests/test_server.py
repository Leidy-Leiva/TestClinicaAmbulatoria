import pytest
import os
import sys
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from server import (
    get_hoy,
    get_manana,
    porcentaje_ocupacion,
    ocupacion_por_clinica,
    proyectar_stock_manana,
    tendencia_ocupacion,
    metricas_clinica,
    ranking_medicamentos,
)


class TestFechasHappyPath:
    """Casos exitosos para funciones de fecha."""

    def test_get_hoy_formato_correcto(self):
        fecha = get_hoy()
        assert len(fecha) == 10
        assert fecha[4] == "-"
        assert fecha[7] == "-"

    def test_get_hoy_retorna_fecha_actual(self):
        fecha = get_hoy()
        hoy_expected = datetime.now().strftime("%Y-%m-%d")
        assert fecha == hoy_expected

    def test_get_manana_formato_correcto(self):
        fecha = get_manana()
        assert len(fecha) == 10
        assert fecha[4] == "-"
        assert fecha[7] == "-"

    def test_get_manana_es_dia_siguiente(self):
        manana = get_manana()
        manana_expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert manana == manana_expected


class TestOcupacionHappyPath:
    """Casos exitosos para ocupación."""

    @patch("server.get_connection")
    def test_porcentaje_ocupacion_basico(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"cantidad_pacientes_maximo": 100},
            {"total": 50},
            {"total": 30},
            {"total": 15},
            {"total": 5},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        result = porcentaje_ocupacion("2026-04-13", clinica_id=1)

        assert result["fecha"] == "2026-04-13"
        assert result["clinica_id"] == 1
        assert result["capacidad_maxima"] == 100
        assert result["turnos_ocupados"] == 50
        assert result["turnos_disponibles"] == 50
        assert result["porcentaje_ocupacion"] == 50.0

    @patch("server.get_connection")
    def test_porcentaje_ocupacion_sin_turnos(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"cantidad_pacientes_maximo": 100},
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        result = porcentaje_ocupacion("2026-04-13", clinica_id=1)

        assert result["turnos_ocupados"] == 0
        assert result["porcentaje_ocupacion"] == 0

    @patch("server.get_connection")
    def test_ocupacion_por_clinica_multiple(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "nombre": "Clínica A"},
            {"id": 2, "nombre": "Clínica B"},
        ]
        mock_cursor.fetchone.side_effect = [
            {"total": 20},
            {"ocup": 15},
            {"total": 30},
            {"ocup": 20},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor
        mock_conn.return_value.cursor.return_value = mock_cursor

        result = ocupacion_por_clinica("2026-04-13")

        assert result["total_clinicas"] == 2
        assert len(result["ocupacion_por_clinica"]) == 2

    @patch("server.get_connection")
    def test_tendencia_ocupacion_7_dias(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"total": 100, "ocup": 50},
            {"total": 100, "ocup": 60},
            {"total": 100, "ocup": 55},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        result = tendencia_ocupacion(dias=7)

        assert "tendencia" in result
        assert result["dias_analizados"] == 7
        assert result["promedio_ocupacion"] > 0


class TestStockHappyPath:
    """Casos exitosos para stock de medicamentos."""

    @patch("server.get_connection")
    def test_proyectar_stock_manana_vacio(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        result = proyectar_stock_manana()

        assert "fecha_hoy" in result
        assert "fecha_proyeccion" in result
        assert result["total_medicamentos"] == 0

    @patch("server.get_connection")
    def test_ranking_medicamentos_basico(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "nombre": "Acetaminofén", "principio_activo": "Paracetamol", "stock_actual": 100, "consumo_total": 50},
            {"id": 2, "nombre": "Ibuprofeno", "principio_activo": "Ibuprofen", "stock_actual": 80, "consumo_total": 30},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        result = ranking_medicamentos(limit=10)

        assert result["total_resultados"] == 2
        assert len(result["medicamentos"]) == 2


class TestErrores:
    """Casos de error para inputs inválidos y servicios caídos."""

    def test_porcentaje_ocupacion_sin_clinica_id(self):
        with pytest.raises(ValueError, match="clinica_id es obligatorio"):
            porcentaje_ocupacion("2026-04-13")

    @patch("server.get_connection")
    def test_porcentaje_ocupacion_clinica_no_existe(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        with pytest.raises(ValueError, match="Clínica no encontrada"):
            porcentaje_ocupacion("2026-04-13", clinica_id=99999)

    def test_tendencia_ocupacion_dias_invalidos_menor(self):
        with pytest.raises(ValueError, match="entre 1 y 30"):
            tendencia_ocupacion(dias=0)

    def test_tendencia_ocupacion_dias_invalidos_mayor(self):
        with pytest.raises(ValueError, match="entre 1 y 30"):
            tendencia_ocupacion(dias=31)

    @patch("server.get_connection")
    def test_error_conexion_base_datos(self, mock_conn):
        import sqlite3
        mock_conn.side_effect = sqlite3.OperationalError("Database locked")

        with pytest.raises(RuntimeError, match="No se puede abrir la base de datos"):
            porcentaje_ocupacion("2026-04-13", clinica_id=1)


class TestSeguridad:
    """Casos de seguridad: SQL injection, path traversal, inputs maliciosos."""

    @patch("server.get_connection")
    def test_sql_injection_en_fecha(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        with pytest.raises(Exception):
            fecha_inyectada = "2026-04-13' OR '1'='1"
            porcentaje_ocupacion(fecha_inyectada, clinica_id=1)

    @patch("server.get_connection")
    def test_sql_injection_en_clinica_id(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"cantidad_pacientes_maximo": 100},
            {"total": 50},
            {"total": 30},
            {"total": 15},
            {"total": 5},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        result = porcentaje_ocupacion("2026-04-13", clinica_id="1; DROP TABLE clinicas;--")

        assert "clinica_id" in result

    @patch("server.get_connection")
    def test_caracteres_especiales_en_fecha(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"cantidad_pacientes_maximo": 100},
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        fecha_maliciosa = "../../../etc/passwd"
        result = porcentaje_ocupacion(fecha_maliciosa, clinica_id=1)

        assert "fecha" in result

    @patch("server.get_connection")
    def test_input_vacio_en_clinica(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        with pytest.raises(Exception):
            porcentaje_ocupacion("2026-04-13", clinica_id=None)

    @patch("server.get_connection")
    def test_fecha_futura_extrema(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"cantidad_pacientes_maximo": 100},
            {"total": 0},
            {"total": 0},
            {"total": 0},
            {"total": 0},
        ]
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value = mock_cursor

        result = porcentaje_ocupacion("2099-12-31", clinica_id=1)

        assert "fecha" in result
        assert result["porcentaje_ocupacion"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])