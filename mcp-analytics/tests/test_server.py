import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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


class TestFechas:
    def test_get_hoy_formato(self):
        fecha = get_hoy()
        assert len(fecha) == 10
        assert fecha[4] == "-"
        assert fecha[7] == "-"

    def test_get_manana_formato(self):
        fecha = get_manana()
        assert len(fecha) == 10
        assert fecha[4] == "-"


class TestOcupacion:
    @patch('server.get_connection')
    def test_porcentaje_ocupacion_vacio(self, mock_conn):
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: 0 if key == "total" else 0
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 0}
        
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value.fetchone.return_value = {"total": 0}
        
        result = porcentaje_ocupacion("2026-04-09")
        
        assert "fecha" in result
        assert "turnos_totales" in result
        assert "porcentaje_ocupacion" in result


class TestStock:
    @patch('server.get_connection')
    def test_proyectar_stock_manana_vacio(self, mock_conn):
        mock_conn.return_value.__enter__ = Mock(return_value=mock_conn.return_value)
        mock_conn.return_value.__exit__ = Mock(return_value=False)
        mock_conn.return_value.execute.return_value.fetchall.return_value = []
        
        result = proyectar_stock_manana()
        
        assert "fecha_hoy" in result
        assert "fecha_proyeccion" in result
        assert "alertas" in result
        assert result["total_medicamentos"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])