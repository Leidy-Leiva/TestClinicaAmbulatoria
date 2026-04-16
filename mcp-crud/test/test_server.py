"""
Tests unitarios para el servidor MCP CRUD de Clínica.
Ejecutar con: pytest mcp-crud/test/test_server.py -v
"""

import os
import sys
import tempfile
import pytest

tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp.close()
os.environ["DB_PATH"] = tmp.name

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import server as srv
import importlib
importlib.reload(srv)

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
    create_medico,
    list_medicos,
    get_medico,
    update_medico,
    delete_medico,
    create_turno,
    list_turnos,
    get_turno,
    update_turno,
    delete_turno,
    create_atencion,
    list_atenciones,
    get_atencion,
    create_medicamento,
    list_medicamentos,
    get_medicamento,
    update_medicamento,
    delete_medicamento,
    get_clinica_stats,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    with srv.get_connection() as conn:
        conn.execute("DELETE FROM recetas")
        conn.execute("DELETE FROM atenciones")
        conn.execute("DELETE FROM turnos")
        conn.execute("DELETE FROM medicos")
        conn.execute("DELETE FROM pacientes")
        conn.execute("DELETE FROM medicamentos")
        conn.execute("DELETE FROM clinicas")
        conn.commit()
    yield


# ── CLÍNICAS ─────────────────────────────────────────────────────────────────────

def test_create_clinica_basic():
    c = create_clinica(nombre="Clínica Central", ciudad="Bogotá")
    assert c["id"] is not None
    assert c["nombre"] == "Clínica Central"
    assert c["ciudad"] == "Bogotá"


def test_create_clinica_empty_name():
    with pytest.raises(ValueError, match="vacío"):
        create_clinica(nombre="  ")


def test_list_clinicas_empty():
    result = list_clinicas()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_clinicas_with_data():
    create_clinica(nombre="Clínica A", ciudad="Bogotá")
    create_clinica(nombre="Clínica B", ciudad="Medellín")
    result = list_clinicas()
    assert result["total"] == 2


def test_list_clinicas_filter_ciudad():
    create_clinica(nombre="Clínica A", ciudad="Bogotá")
    create_clinica(nombre="Clínica B", ciudad="Medellín")
    result = list_clinicas(ciudad="Bogotá")
    assert result["total"] == 1
    assert result["items"][0]["ciudad"] == "Bogotá"


def test_get_clinica_found():
    created = create_clinica(nombre="Clínica Test")
    fetched = get_clinica(created["id"])
    assert fetched["nombre"] == "Clínica Test"


def test_get_clinica_not_found():
    with pytest.raises(ValueError, match="no encontrada"):
        get_clinica(99999)


def test_update_clinica():
    c = create_clinica(nombre="Old Name", ciudad="Bogotá")
    updated = update_clinica(c["id"], ciudad="Medellín")
    assert updated["ciudad"] == "Medellín"
    assert updated["nombre"] == "Old Name"


def test_update_clinica_no_fields():
    c = create_clinica(nombre="Test")
    with pytest.raises(ValueError, match="al menos un campo"):
        update_clinica(c["id"])


def test_delete_clinica():
    c = create_clinica(nombre="To Delete")
    result = delete_clinica(c["id"])
    assert result["deleted"] is True
    with pytest.raises(ValueError):
        get_clinica(c["id"])


def test_delete_clinica_not_found():
    with pytest.raises(ValueError, match="no encontrada"):
        delete_clinica(99999)


# ── PACIENTES ────────────────────────────────────────────────────────────────────

def test_create_paciente_basic():
    p = create_paciente(nombre="Juan Pérez", documento="12345678", eps="Sura")
    assert p["id"] is not None
    assert p["nombre"] == "Juan Pérez"
    assert p["documento"] == "12345678"
    assert p["eps"] == "Sura"


def test_create_paciente_empty_name():
    with pytest.raises(ValueError, match="vacío"):
        create_paciente(nombre="  ")


def test_create_paciente_defaults():
    p = create_paciente(nombre="Pedro")
    assert p["genero"] is None
    assert p["eps"] is None


def test_list_pacientes_empty():
    result = list_pacientes()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_pacientes_with_data():
    create_paciente(nombre="Paciente A", eps="Sura")
    create_paciente(nombre="Paciente B", eps="Sanitas")
    result = list_pacientes()
    assert result["total"] == 2


def test_list_pacientes_filter_eps():
    create_paciente(nombre="A", eps="Sura")
    create_paciente(nombre="B", eps="Sanitas")
    result = list_pacientes(eps="Sura")
    assert result["total"] == 1
    assert result["items"][0]["eps"] == "Sura"


def test_get_paciente_found():
    created = create_paciente(nombre="Carlos Gómez", documento="98765432")
    fetched = get_paciente(created["id"])
    assert fetched["nombre"] == "Carlos Gómez"


def test_get_paciente_not_found():
    with pytest.raises(ValueError, match="no encontrado"):
        get_paciente(99999)


def test_update_paciente():
    p = create_paciente(nombre="Old Name", eps="Sura")
    updated = update_paciente(p["id"], eps="Sanitas")
    assert updated["eps"] == "Sanitas"


def test_update_paciente_multiple_fields():
    p = create_paciente(nombre="Test", telefono="3000000000")
    updated = update_paciente(p["id"], telefono="3100000000", ciudad="Bogotá")
    assert updated["telefono"] == "3100000000"
    assert updated["ciudad"] == "Bogotá"


def test_delete_paciente():
    p = create_paciente(nombre="To Delete")
    result = delete_paciente(p["id"])
    assert result["deleted"] is True
    with pytest.raises(ValueError):
        get_paciente(p["id"])


def test_buscar_pacientes_by_nombre():
    create_paciente(nombre="María García", eps="Sura")
    create_paciente(nombre="María López", eps="Sanitas")
    create_paciente(nombre="Pedro Gómez", eps="Sura")
    result = buscar_pacientes("María")
    assert result["total"] == 2


def test_buscar_pacientes_by_eps():
    create_paciente(nombre="A", eps="Sura")
    create_paciente(nombre="B", eps="Sanitas")
    result = buscar_pacientes("Sura")
    assert result["total"] == 1


# ── MÉDICOS ───────────────────���─��───────────────────────────────────────────

def test_create_medico_basic():
    m = create_medico(nombre="Dr. Smith", especialidad="Cardiología", documento="med001")
    assert m["id"] is not None
    assert m["nombre"] == "Dr. Smith"
    assert m["especialidad"] == "Cardiología"


def test_create_medico_empty_name():
    with pytest.raises(ValueError, match="vacío"):
        create_medico(nombre="  ")


def test_list_medicos_empty():
    result = list_medicos()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_medicos_with_data():
    create_medico(nombre="Dr. A", especialidad="Cardiología")
    create_medico(nombre="Dr. B", especialidad="Pediatría")
    result = list_medicos()
    assert result["total"] == 2


def test_list_medicos_filter_especialidad():
    create_medico(nombre="Dr. A", especialidad="Cardiología")
    create_medico(nombre="Dr. B", especialidad="Pediatría")
    result = list_medicos(especialidad="Cardiología")
    assert result["total"] == 1
    assert result["items"][0]["especialidad"] == "Cardiología"


def test_get_medico_found():
    created = create_medico(nombre="Dr. Test", especialidad="Cirugía")
    fetched = get_medico(created["id"])
    assert fetched["nombre"] == "Dr. Test"


def test_update_medico():
    m = create_medico(nombre="Dr. Old", especialidad="Medicina General")
    updated = update_medico(m["id"], especialidad="Cirugía")
    assert updated["especialidad"] == "Cirugía"


def test_delete_medico():
    m = create_medico(nombre="Dr. To Delete")
    result = delete_medico(m["id"])
    assert result["deleted"] is True
    with pytest.raises(ValueError):
        get_medico(m["id"])


# ── TURNOS ─────────────────────────────────────────────────────────────────────

def test_create_turno():
    c = create_clinica(nombre="Clínica Test")
    p = create_paciente(nombre="Paciente Test")
    t = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20", hora="10:00")
    assert t["id"] is not None
    assert t["fecha"] == "2026-04-20"
    assert t["hora"] == "10:00"
    assert t["estado"] == "programado"


def test_list_turnos_empty():
    result = list_turnos()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_turnos_with_data():
    c = create_clinica(nombre="Clínica Test")
    p = create_paciente(nombre="Paciente Test")
    create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-21")
    result = list_turnos()
    assert result["total"] == 2


def test_list_turnos_filter_estado():
    c = create_clinica(nombre="C")
    p = create_paciente(nombre="P")
    t1 = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    update_turno(t1["id"], estado="cancelado")
    t2 = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-21")
    result = list_turnos(estado="cancelado")
    assert result["total"] == 1


def test_get_turno_found():
    c = create_clinica(nombre="C")
    p = create_paciente(nombre="P")
    created = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    fetched = get_turno(created["id"])
    assert fetched["id"] == created["id"]


def test_update_turno():
    c = create_clinica(nombre="C")
    p = create_paciente(nombre="P")
    t = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    updated = update_turno(t["id"], estado="cancelado")
    assert updated["estado"] == "cancelado"


def test_delete_turno():
    c = create_clinica(nombre="C")
    p = create_paciente(nombre="P")
    t = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    result = delete_turno(t["id"])
    assert result["deleted"] is True


# ── ATENCIONES ─────────────────────────────────────────────────────────────────────

def test_create_atencion():
    c = create_clinica(nombre="C")
    p = create_paciente(nombre="P")
    m = create_medico(nombre="Dr. M")
    t = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    a = create_atencion(turno_id=t["id"], paciente_id=p["id"], medico_id=m["id"], diagnostico="Gripe")
    assert a["id"] is not None
    assert a["diagnostico"] == "Gripe"
    assert a["estado"] == "atendido"


def test_list_atenciones_empty():
    result = list_atenciones()
    assert result["items"] == []
    assert result["total"] == 0


def test_get_atencion_found():
    c = create_clinica(nombre="C")
    p = create_paciente(nombre="P")
    t = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    created = create_atencion(turno_id=t["id"], paciente_id=p["id"], diagnostico="Prueba")
    fetched = get_atencion(created["id"])
    assert fetched["diagnostico"] == "Prueba"


# ── MEDICAMENTOS ────────────────────────────────────────────────────────────────

def test_create_medicamento_basic():
    m = create_medicamento(nombre="Acetaminofén", principio_activo="Paracetamol", stock_actual=100, stock_minimo=50)
    assert m["id"] is not None
    assert m["nombre"] == "Acetaminofén"
    assert m["stock_actual"] == 100


def test_create_medicamento_empty_name():
    with pytest.raises(ValueError, match="vacío"):
        create_medicamento(nombre="  ")


def test_list_medicamentos_empty():
    result = list_medicamentos()
    assert result["items"] == []
    assert result["total"] == 0


def test_list_medicamentos_with_data():
    create_medicamento(nombre="Medicamento A", stock_actual=10, stock_minimo=20)
    create_medicamento(nombre="Medicamento B", stock_actual=50, stock_minimo=10)
    result = list_medicamentos()
    assert result["total"] == 2


def test_list_medicamentos_low_stock():
    create_medicamento(nombre="A", stock_actual=5, stock_minimo=20)
    create_medicamento(nombre="B", stock_actual=50, stock_minimo=10)
    result = list_medicamentos(low_stock=True)
    assert result["total"] == 1


def test_get_medicamento_found():
    created = create_medicamento(nombre="Test Med")
    fetched = get_medicamento(created["id"])
    assert fetched["nombre"] == "Test Med"


def test_update_medicamento():
    m = create_medicamento(nombre="Med", stock_actual=10)
    updated = update_medicamento(m["id"], stock_actual=50)
    assert updated["stock_actual"] == 50


def test_delete_medicamento():
    m = create_medicamento(nombre="To Delete")
    result = delete_medicamento(m["id"])
    assert result["deleted"] is True


# ── ESTADÍSTICAS ─────────────────────────────────────────────────────────────────

def test_get_clinica_stats_empty():
    stats = get_clinica_stats()
    assert stats["total_pacientes"] == 0
    assert stats["total_clinicas"] == 0
    assert stats["total_medicos"] == 0
    assert stats["total_turnos"] == 0


def test_get_clinica_stats_with_data():
    c = create_clinica(nombre="C")
    p = create_paciente(nombre="P")
    m = create_medico(nombre="Dr. M")
    t = create_turno(paciente_id=p["id"], clinica_id=c["id"], fecha="2026-04-20")
    stats = get_clinica_stats()
    assert stats["total_clinicas"] == 1
    assert stats["total_pacientes"] == 1
    assert stats["total_medicos"] == 1
    assert stats["total_turnos"] == 1