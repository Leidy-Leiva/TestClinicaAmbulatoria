"""
Tests unitarios para el servidor MCP CRUD.
Ejecutar con: pytest test/test_server.py -v
"""

import os
import sys
import tempfile
import sqlite3
import pytest

tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp.close()
os.environ["DB_PATH"] = tmp.name

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from server import (
    init_db,
    create_clinica,
    list_clinicas,
    get_clinica,
    update_clinica,
    delete_clinica,
    create_paciente,
    list_pacientes,
    get_paciente,
    update_paciente,
    delete_paciente,
    buscar_pacientes,
    create_medicamento,
    list_medicamentos,
    get_medicamento,
    update_medicamento,
    delete_medicamento,
    create_turno,
    list_turnos,
    get_turno,
    delete_turno,
    create_atencion,
    list_atenciones,
    get_atencion,
    get_clinica_stats,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    with sqlite3.connect(tmp.name) as conn:
        conn.execute("DELETE FROM clinicas")
        conn.execute("DELETE FROM pacientes")
        conn.execute("DELETE FROM medicos")
        conn.execute("DELETE FROM turnos")
        conn.execute("DELETE FROM atenciones")
        conn.execute("DELETE FROM medicamentos")
        conn.execute("DELETE FROM recetas")
        conn.commit()
    yield


# ── CLÍNICAS: CREATE ───────────────────────────────────────────────────────────────

def test_create_clinica_basic():
    c = create_clinica(nombre="Clinica Central", direccion="Calle 10 #20-30", ciudad="Bogotá")
    assert c["id"] is not None
    assert c["nombre"] == "Clinica Central"
    assert c["ciudad"] == "Bogotá"


def test_create_clinica_defaults():
    c = create_clinica(nombre="Clinica Norte")
    assert c["direccion"] is None
    assert c["telefono"] is None


def test_create_clinica_empty_name():
    with pytest.raises(ValueError, match="vacío"):
        create_clinica(nombre="  ")


# ── CLÍNICAS: READ ───────────────────────────────────────────────────────────────

def test_get_clinica_found():
    created = create_clinica(nombre="Clinica Ejemplo")
    fetched = get_clinica(created["id"])
    assert fetched["nombre"] == "Clinica Ejemplo"


def test_get_clinica_not_found():
    with pytest.raises(ValueError, match="no encontrada"):
        get_clinica(99999)


def test_list_clinicas_empty():
    result = list_clinicas()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_clinicas_with_data():
    create_clinica(nombre="A")
    create_clinica(nombre="B")
    result = list_clinicas()
    assert result["total"] == 2


def test_list_clinicas_filter_ciudad():
    create_clinica(nombre="A", ciudad="Bogotá")
    create_clinica(nombre="B", ciudad="Medellín")
    result = list_clinicas(ciudad="Bogotá")
    assert result["total"] == 1


# ── CLÍNICAS: UPDATE ──────────────────────────────────────────────────────────���────

def test_update_clinica_nombre():
    c = create_clinica(nombre="Old Name")
    updated = update_clinica(c["id"], nombre="New Name")
    assert updated["nombre"] == "New Name"


def test_update_clinica_multiple_fields():
    c = create_clinica(nombre="X")
    updated = update_clinica(c["id"], direccion="New Address", telefono="3000000")
    assert updated["direccion"] == "New Address"
    assert updated["telefono"] == "3000000"


def test_update_clinica_not_found():
    with pytest.raises(ValueError, match="no encontrada"):
        update_clinica(99999, nombre="Ghost")


def test_update_clinica_no_fields():
    c = create_clinica(nombre="X")
    with pytest.raises(ValueError, match="al menos un campo"):
        update_clinica(c["id"])


def test_update_clinica_empty_name():
    c = create_clinica(nombre="X")
    with pytest.raises(ValueError, match="vacío"):
        update_clinica(c["id"], nombre="")


# ── CLÍNICAS: DELETE ───────────────────────────────────────────────────────────────

def test_delete_clinica():
    c = create_clinica(nombre="Temp")
    result = delete_clinica(c["id"])
    assert result["deleted"] is True
    with pytest.raises(ValueError):
        get_clinica(c["id"])


def test_delete_clinica_not_found():
    with pytest.raises(ValueError, match="no encontrada"):
        delete_clinica(99999)


# ── PACIENTES: CREATE ─────────────────────────────────────────────────────────────

def test_create_paciente_basic():
    p = create_paciente(nombre="Juan Pérez", documento="12345678", eps="Sanitas")
    assert p["id"] is not None
    assert p["nombre"] == "Juan Pérez"
    assert p["eps"] == "Sanitas"


def test_create_paciente_empty_name():
    with pytest.raises(ValueError, match="vacío"):
        create_paciente(nombre="  ")


# ── PACIENTES: READ ───────────────────────────────────────────────────────────────

def test_get_paciente_found():
    created = create_paciente(nombre="Test Patient")
    fetched = get_paciente(created["id"])
    assert fetched["nombre"] == "Test Patient"


def test_get_paciente_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        get_paciente(99999)


def test_list_pacientes_empty():
    result = list_pacientes()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_pacientes_with_data():
    create_paciente(nombre="A", documento="1")
    create_paciente(nombre="B", documento="2")
    result = list_pacientes()
    assert result["total"] == 2


# ── PACIENTES: UPDATE ───────────────────────────────────────────────────────────────

def test_update_paciente():
    p = create_paciente(nombre="Old")
    updated = update_paciente(p["id"], nombre="New")
    assert updated["nombre"] == "New"


def test_update_paciente_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        update_paciente(99999, nombre="Ghost")


def test_update_paciente_no_fields():
    p = create_paciente(nombre="X")
    with pytest.raises(ValueError, match="al menos un campo"):
        update_paciente(p["id"])


# ── PACIENTES: DELETE ───────────────────────────────────────────────────────

def test_delete_paciente():
    p = create_paciente(nombre="Temp")
    result = delete_paciente(p["id"])
    assert result["deleted"] is True
    with pytest.raises(ValueError):
        get_paciente(p["id"])


def test_delete_paciente_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        delete_paciente(99999)


# ── SEARCH ────────────────────────────────────────────────────────────────

def test_buscar_pacientes_by_nombre():
    create_paciente(nombre="Carlos García", documento="111")
    create_paciente(nombre="Ana López", documento="222")
    result = buscar_pacientes("Carlos")
    assert result["total"] >= 1


def test_buscar_pacientes_by_eps():
    create_paciente(nombre="A", eps="EPS1")
    create_paciente(nombre="B", eps="EPS2")
    result = buscar_pacientes("EPS1")
    assert result["total"] >= 1


# ── MEDICAMENTOS: CREATE ────────────────────────────────────────────────

def test_create_medicamento_basic():
    m = create_medicamento(nombre="Acetaminophen", principio_activo="Paracetamol", stock_actual=100)
    assert m["id"] is not None
    assert m["nombre"] == "Acetaminophen"
    assert m["stock_actual"] == 100


def test_create_medicamento_empty_name():
    with pytest.raises(ValueError, match="vacío"):
        create_medicamento(nombre="  ")


# ── MEDICAMENTOS: READ ────────────────────────────────────────────────

def test_get_medicamento_found():
    created = create_medicamento(nombre="Test Med")
    fetched = get_medicamento(created["id"])
    assert fetched["nombre"] == "Test Med"


def test_get_medicamento_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        get_medicamento(99999)


def test_list_medicamentos_with_data():
    create_medicamento(nombre="A")
    create_medicamento(nombre="B")
    result = list_medicamentos()
    assert result["total"] == 2


def test_list_medicamentos_low_stock():
    create_medicamento(nombre="Low Stock", stock_actual=5, stock_minimo=10)
    create_medicamento(nombre="Normal", stock_actual=50, stock_minimo=10)
    result = list_medicamentos(low_stock=True)
    assert result["total"] == 1


# ── MEDICAMENTOS: UPDATE ──────────────────────────────────────────────

def test_update_medicamento():
    m = create_medicamento(nombre="X", stock_actual=10)
    updated = update_medicamento(m["id"], stock_actual=20)
    assert updated["stock_actual"] == 20


def test_update_medicamento_negative_stock():
    m = create_medicamento(nombre="X")
    with pytest.raises(ValueError, match="negativo"):
        update_medicamento(m["id"], stock_actual=-5)


def test_update_medicamento_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        update_medicamento(99999, nombre="Ghost")


# ── MEDICAMENTOS: DELETE ───────────────────────────────────────────────

def test_delete_medicamento():
    m = create_medicamento(nombre="Temp")
    result = delete_medicamento(m["id"])
    assert result["deleted"] is True


def test_delete_medicamento_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        delete_medicamento(99999)


# ── ESTADÍSTICAS ────────────────────────────────────────────────────────

def test_get_clinica_stats_empty():
    stats = get_clinica_stats()
    assert stats["total_pacientes"] == 0
    assert stats["total_clinicas"] == 0


def test_get_clinica_stats_with_data():
    create_clinica(nombre="C1")
    create_paciente(nombre="P1")
    create_medicamento(nombre="M1", stock_actual=10)
    stats = get_clinica_stats()
    assert stats["total_clinicas"] == 1
    assert stats["total_pacientes"] == 1


# ── SEGURIDAD: INYECCIÓN SQL ─────────────────────────────────────────────

def test_sql_injection_search_prevented():
    create_paciente(nombre="Test Patient", documento="123", eps="EPS Test")
    result = buscar_pacientes("'; DROP TABLE pacientes; --")
    assert result["items"] == []
    verify_pacientes_table_exists()


def test_sql_injection_in_name_field_prevented():
    with pytest.raises(ValueError, match="vacío"):
        create_paciente(nombre="'; DROP TABLE pacientes; --")


def test_sql_injection_like_pattern_prevented():
    create_paciente(nombre="Normal Patient", documento="1")
    result = buscar_pacientes("%' OR '1'='1")
    assert result["total"] == 0


def test_sql_injection_union_attempt_prevented():
    result = buscar_pacientes("1' UNION SELECT password FROM users--")
    assert result["items"] == []


def test_sql_no_eval_safe():
    result = buscar_pacientes("eval(base64_decode('a'))")
    assert result["items"] == []


def verify_pacientes_table_exists():
    with sqlite3.connect(tmp.name) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='pacientes'"
        ).fetchone()
    assert cursor is not None, "Table pacientes was dropped!"


# ── ERRORES: CASOS ESPECIALES ────────────────────────────────────────

def test_create_clinica_duplicate_name():
    create_clinica(nombre="Unique Clinica")
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
        create_clinica(nombre="Unique Clinica")


def test_list_clinicas_pagination():
    for i in range(15):
        create_clinica(nombre=f"C{i}")
    result = list_clinicas(limit=5, offset=10)
    assert result["total"] == 15
    assert len(result["items"]) == 5


def test_list_clinicas_invalid_limit():
    with pytest.raises(ValueError):
        list_clinicas(limit=-1)