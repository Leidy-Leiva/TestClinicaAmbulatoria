"""
MCP CRUD Server usando FastMCP + SQLite
Proporciona herramientas para gestionar una base de datos de clínica ambulatoria.
"""

import sqlite3
import os
import platform
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP

if platform.system() == "Windows":
    DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "crud.db")
else:
    DEFAULT_DB_PATH = "/data/crud.db"

DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)

mcp = FastMCP(
    name="clinica-mcp",
    instructions=(
        "Servidor MCP para gestionar la base de datos de clínica ambulatoria. "
        "Tablas disponibles: clinicas, turnos, pacientes, atenciones, medicamentos, recetas. "
        "Usa las herramientas disponibles para realizar operaciones CRUD y consultas."
    ),
)


# ── Helpers de base de datos ───────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
        except PermissionError:
            raise RuntimeError(f"No hay permisos para crear el directorio: {db_dir}")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        return conn
    except sqlite3.OperationalError as e:
        raise RuntimeError(f"No se puede abrir la base de datos en {DB_PATH}: {e}")


def init_db() -> None:
    """Crea las tablas si no existen."""
    with get_connection() as conn:
           
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clinicas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                direccion TEXT,
                telefono TEXT,
                email TEXT,
                ciudad TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                cantidad_pacientes_maximo INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                documento TEXT UNIQUE,
                fecha_nacimiento DATE,
                genero TEXT,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                ciudad TEXT,
                eps TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS medicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                documento TEXT UNIQUE,
                especialidad TEXT,
                telefono TEXT,
                email TEXT,
                clinica_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clinica_id) REFERENCES clinicas(id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                medico_id INTEGER,
                clinica_id INTEGER,
                fecha DATE NOT NULL,
                hora TIME,
                tipo_atencion TEXT,
                motivo TEXT,
                estado TEXT DEFAULT 'programado',
                prioridad INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                FOREIGN KEY (medico_id) REFERENCES medicos(id),
                FOREIGN KEY (clinica_id) REFERENCES clinicas(id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS atenciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turno_id INTEGER NOT NULL,
                paciente_id INTEGER NOT NULL,
                medico_id INTEGER,
                diagnostico TEXT,
                sintomas TEXT,
                tratamiento TEXT,
                observaciones TEXT,
                estado TEXT DEFAULT 'atendido',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (turno_id) REFERENCES turnos(id),
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                FOREIGN KEY (medico_id) REFERENCES medicos(id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS medicamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                principio_activo TEXT,
                presentacion TEXT,
                descripcion TEXT,
                stock_actual INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 10,
                precio_unitario REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recetas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atencion_id INTEGER NOT NULL,
                paciente_id INTEGER NOT NULL,
                medicamento_id INTEGER NOT NULL,
                cantidad INTEGER DEFAULT 1,
                dosis TEXT,
                frecuencia TEXT,
                duracion TEXT,
                instrucciones TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (atencion_id) REFERENCES atenciones(id),
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id)
            )
        """)

        conn.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ── Herramientas MCP: Clínicas ─────────────────────────────────────────────────

@mcp.tool()
def create_clinica(
    nombre: str,
    direccion: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    ciudad: Optional[str] = None,
) -> dict:
    """Crea una nueva clínica."""
    if not nombre.strip():
        raise ValueError("El nombre de la clínica no puede estar vacío.")

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO clinicas (nombre, direccion, telefono, email, ciudad)
               VALUES (?, ?, ?, ?, ?)""",
            (nombre.strip(), direccion, telefono, email, ciudad),
        )
        conn.commit()
        clinica = conn.execute(
            "SELECT * FROM clinicas WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_dict(clinica)


@mcp.tool()
def list_clinicas(
    nombre: Optional[str] = None,
    ciudad: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista clínicas con filtros."""
    query = "SELECT * FROM clinicas WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM clinicas WHERE 1=1"
    params = []

    if nombre:
        query += " AND nombre LIKE ?"
        count_query += " AND nombre LIKE ?"
        params.append(f"%{nombre.strip()}%")
    if ciudad:
        query += " AND ciudad LIKE ?"
        count_query += " AND ciudad LIKE ?"
        params.append(f"%{ciudad.strip()}%")

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": total}


@mcp.tool()
def get_clinica(clinica_id: int) -> dict:
    """Obtiene una clínica por ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM clinicas WHERE id = ?", (clinica_id,)).fetchone()

    if row is None:
        raise ValueError(f"Clínica con id={clinica_id} no encontrada.")
    return row_to_dict(row)


@mcp.tool()
def update_clinica(
    clinica_id: int,
    nombre: Optional[str] = None,
    direccion: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    ciudad: Optional[str] = None,
) -> dict:
    """Actualiza una clínica."""
    fields = {}
    if nombre is not None:
        if not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        fields["nombre"] = nombre.strip()
    if direccion is not None:
        fields["direccion"] = direccion
    if telefono is not None:
        fields["telefono"] = telefono
    if email is not None:
        fields["email"] = email
    if ciudad is not None:
        fields["ciudad"] = ciudad

    if not fields:
        raise ValueError("Debes proporcionar al menos un campo para actualizar.")

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [clinica_id]

    with get_connection() as conn:
        affected = conn.execute(f"UPDATE clinicas SET {set_clause} WHERE id = ?", values).rowcount
        conn.commit()
        if affected == 0:
            raise ValueError(f"Clínica con id={clinica_id} no encontrada.")
        row = conn.execute("SELECT * FROM clinicas WHERE id = ?", (clinica_id,)).fetchone()

    return row_to_dict(row)


@mcp.tool()
def delete_clinica(clinica_id: int) -> dict:
    """Elimina una clínica."""
    with get_connection() as conn:
        affected = conn.execute("DELETE FROM clinicas WHERE id = ?", (clinica_id,)).rowcount
        conn.commit()

    if affected == 0:
        raise ValueError(f"Clínica con id={clinica_id} no encontrada.")

    return {"deleted": True, "clinica_id": clinica_id}

@mcp.tool()
def create_paciente(
    nombre: str,
    documento: Optional[str] = None,
    fecha_nacimiento: Optional[str] = None,
    genero: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    direccion: Optional[str] = None,
    ciudad: Optional[str] = None,
    eps: Optional[str] = None,
) -> dict:
    """
    Crea un nuevo paciente en la base de datos.

    Args:
        nombre: Nombre completo del paciente (requerido).
        documento: Número de documento de identidad (opcional).
        fecha_nacimiento: Fecha de nacimiento (YYYY-MM-DD) (opcional).
        genero: Género del paciente (opcional).
        telefono: Teléfono de contacto (opcional).
        email: Correo electrónico (opcional).
        direccion: Dirección de residencia (opcional).
        ciudad: Ciudad de residencia (opcional).
        eps: EPS o aseguradora de salud (opcional).

    Returns:
        El paciente recién creado con su id asignado.
    """
    if not nombre.strip():
        raise ValueError("El nombre del paciente no puede estar vacío.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pacientes (nombre, documento, fecha_nacimiento, genero, 
                                   telefono, email, direccion, ciudad, eps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (nombre.strip(), documento, fecha_nacimiento, genero, 
             telefono, email, direccion, ciudad, eps),
        )
        conn.commit()
        paciente = conn.execute(
            "SELECT * FROM pacientes WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_dict(paciente)


@mcp.tool()
def list_pacientes(
    nombre: Optional[str] = None,
    documento: Optional[str] = None,
    ciudad: Optional[str] = None,
    eps: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    Lista pacientes con filtros opcionales.

    Args:
        nombre: Filtra por nombre (opcional).
        documento: Filtra por documento (opcional).
        ciudad: Filtra por ciudad (opcional).
        eps: Filtra por EPS (opcional).
        limit: Máximo de resultados (default: 50).
        offset: Desplazamiento para paginación (default: 0).

    Returns:
        Diccionario con 'items' (lista) y 'total' (conteo total).
    """
    query = "SELECT * FROM pacientes WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM pacientes WHERE 1=1"
    params: list = []

    if nombre:
        query += " AND nombre LIKE ?"
        count_query += " AND nombre LIKE ?"
        params.append(f"%{nombre.strip()}%")
    if documento:
        query += " AND documento LIKE ?"
        count_query += " AND documento LIKE ?"
        params.append(f"%{documento.strip()}%")
    if ciudad:
        query += " AND ciudad LIKE ?"
        count_query += " AND ciudad LIKE ?"
        params.append(f"%{ciudad.strip()}%")
    if eps:
        query += " AND eps LIKE ?"
        count_query += " AND eps LIKE ?"
        params.append(f"%{eps.strip()}%")

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": total}


@mcp.tool()
def get_paciente(paciente_id: int) -> dict:
    """
    Obtiene un paciente por su ID.

    Args:
        paciente_id: ID del paciente.

    Returns:
        Datos completos del paciente.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
        ).fetchone()

    if row is None:
        raise ValueError(f"Paciente con id={paciente_id} no encontrado.")
    return row_to_dict(row)


@mcp.tool()
def update_paciente(
    paciente_id: int,
    nombre: Optional[str] = None,
    documento: Optional[str] = None,
    fecha_nacimiento: Optional[str] = None,
    genero: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    direccion: Optional[str] = None,
    ciudad: Optional[str] = None,
    eps: Optional[str] = None,
) -> dict:
    """
    Actualiza uno o más campos de un paciente existente.

    Args:
        paciente_id: ID del paciente a actualizar.
        nombre: Nuevo nombre (opcional).
        documento: Nuevo documento (opcional).
        fecha_nacimiento: Nueva fecha de nacimiento (opcional).
        genero: Nuevo género (opcional).
        telefono: Nuevo teléfono (opcional).
        email: Nuevo email (opcional).
        direccion: Nueva dirección (opcional).
        ciudad: Nueva ciudad (opcional).
        eps: Nueva EPS (opcional).

    Returns:
        El paciente actualizado.
    """
    fields: dict = {}
    if nombre is not None:
        if not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        fields["nombre"] = nombre.strip()
    if documento is not None:
        fields["documento"] = documento
    if fecha_nacimiento is not None:
        fields["fecha_nacimiento"] = fecha_nacimiento
    if genero is not None:
        fields["genero"] = genero
    if telefono is not None:
        fields["telefono"] = telefono
    if email is not None:
        fields["email"] = email
    if direccion is not None:
        fields["direccion"] = direccion
    if ciudad is not None:
        fields["ciudad"] = ciudad
    if eps is not None:
        fields["eps"] = eps

    if not fields:
        raise ValueError("Debes proporcionar al menos un campo para actualizar.")

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [paciente_id]

    with get_connection() as conn:
        affected = conn.execute(
            f"UPDATE pacientes SET {set_clause} WHERE id = ?", values
        ).rowcount
        conn.commit()

        if affected == 0:
            raise ValueError(f"Paciente con id={paciente_id} no encontrado.")

        row = conn.execute(
            "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
        ).fetchone()

    return row_to_dict(row)


@mcp.tool()
def delete_paciente(paciente_id: int) -> dict:
    """
    Elimina un paciente de la base de datos.

    Args:
        paciente_id: ID del paciente a eliminar.

    Returns:
        Mensaje de confirmación con el id eliminado.
    """
    with get_connection() as conn:
        affected = conn.execute(
            "DELETE FROM pacientes WHERE id = ?", (paciente_id,)
        ).rowcount
        conn.commit()

    if affected == 0:
        raise ValueError(f"Paciente con id={paciente_id} no encontrado.")

    return {"deleted": True, "paciente_id": paciente_id}


@mcp.tool()
def buscar_pacientes(query: str, limit: int = 20) -> dict:
    """
    Busca pacientes cuyo nombre, documento o EPS contengan el texto indicado.

    Args:
        query: Texto a buscar.
        limit: Máximo de resultados (default: 20).

    Returns:
        Lista de pacientes coincidentes y total.
    """
    pattern = f"%{query.strip()}%"
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM pacientes
            WHERE nombre LIKE ? OR documento LIKE ? OR eps LIKE ? OR ciudad LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (pattern, pattern, pattern, pattern, limit),
        ).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": len(rows)}


# ── Herramientas MCP: Turnos ────────────────────────────────────────────────────

@mcp.tool()
def create_turno(
    paciente_id: int,
    clinica_id: int,
    fecha: str,
    hora: Optional[str] = None,
    motivo: Optional[str] = None,
    tipo_atencion: Optional[str] = None,
    prioridad: int = 1,
    medico_id: Optional[int] = None,
) -> dict:
    """Crea un nuevo turno."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO turnos (paciente_id, clinica_id, medico_id, fecha, hora, 
               tipo_atencion, motivo, prioridad, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'programado')""",
            (paciente_id, clinica_id, medico_id, fecha, hora, tipo_atencion, motivo, prioridad),
        )
        conn.commit()
        turno = conn.execute(
            "SELECT * FROM turnos WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_dict(turno)


@mcp.tool()
def list_turnos(
    paciente_id: Optional[int] = None,
    clinica_id: Optional[int] = None,
    medico_id: Optional[int] = None,
    estado: Optional[str] = None,
    fecha: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista turnos con filtros."""
    query = "SELECT * FROM turnos WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM turnos WHERE 1=1"
    params = []

    if paciente_id:
        query += " AND paciente_id = ?"
        count_query += " AND paciente_id = ?"
        params.append(paciente_id)
    if clinica_id:
        query += " AND clinica_id = ?"
        count_query += " AND clinica_id = ?"
        params.append(clinica_id)
    if medico_id:
        query += " AND medico_id = ?"
        count_query += " AND medico_id = ?"
        params.append(medico_id)
    if estado:
        query += " AND estado = ?"
        count_query += " AND estado = ?"
        params.append(estado)
    if fecha:
        query += " AND fecha = ?"
        count_query += " AND fecha = ?"
        params.append(fecha)

    query += " ORDER BY fecha DESC, hora DESC LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": total}


@mcp.tool()
def get_turno(turno_id: int) -> dict:
    """Obtiene un turno por ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM turnos WHERE id = ?", (turno_id,)).fetchone()

    if row is None:
        raise ValueError(f"Turno con id={turno_id} no encontrado.")
    return row_to_dict(row)


@mcp.tool()
def update_turno(
    turno_id: int,
    estado: Optional[str] = None,
    hora: Optional[str] = None,
    motivo: Optional[str] = None,
    prioridad: Optional[int] = None,
) -> dict:
    """Actualiza un turno."""
    fields = {}
    if estado is not None:
        fields["estado"] = estado
    if hora is not None:
        fields["hora"] = hora
    if motivo is not None:
        fields["motivo"] = motivo
    if prioridad is not None:
        fields["prioridad"] = prioridad

    if not fields:
        raise ValueError("Debes proporcionar al menos un campo para actualizar.")

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [turno_id]

    with get_connection() as conn:
        affected = conn.execute(f"UPDATE turnos SET {set_clause} WHERE id = ?", values).rowcount
        conn.commit()
        if affected == 0:
            raise ValueError(f"Turno con id={turno_id} no encontrado.")
        row = conn.execute("SELECT * FROM turnos WHERE id = ?", (turno_id,)).fetchone()

    return row_to_dict(row)


@mcp.tool()
def delete_turno(turno_id: int) -> dict:
    """Elimina un turno."""
    with get_connection() as conn:
        affected = conn.execute("DELETE FROM turnos WHERE id = ?", (turno_id,)).rowcount
        conn.commit()

    if affected == 0:
        raise ValueError(f"Turno con id={turno_id} no encontrado.")

    return {"deleted": True, "turno_id": turno_id}


# ── Herramientas MCP: Atenciones ─────────────────────────────────────────────────

@mcp.tool()
def create_atencion(
    turno_id: int,
    paciente_id: int,
    diagnostico: Optional[str] = None,
    sintomas: Optional[str] = None,
    tratamiento: Optional[str] = None,
    observaciones: Optional[str] = None,
    medico_id: Optional[int] = None,
) -> dict:
    """Crea una nueva atención."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO atenciones (turno_id, paciente_id, medico_id, diagnostico, 
               sintomas, tratamiento, observaciones, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'atendido')""",
            (turno_id, paciente_id, medico_id, diagnostico, sintomas, tratamiento, observaciones),
        )
        conn.commit()
        atencion = conn.execute(
            "SELECT * FROM atenciones WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_dict(atencion)


@mcp.tool()
def list_atenciones(
    paciente_id: Optional[int] = None,
    medico_id: Optional[int] = None,
    estado: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista atenciones con filtros."""
    query = "SELECT * FROM atenciones WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM atenciones WHERE 1=1"
    params = []

    if paciente_id:
        query += " AND paciente_id = ?"
        count_query += " AND paciente_id = ?"
        params.append(paciente_id)
    if medico_id:
        query += " AND medico_id = ?"
        count_query += " AND medico_id = ?"
        params.append(medico_id)
    if estado:
        query += " AND estado = ?"
        count_query += " AND estado = ?"
        params.append(estado)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": total}


@mcp.tool()
def get_atencion(atencion_id: int) -> dict:
    """Obtiene una atención por ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM atenciones WHERE id = ?", (atencion_id,)).fetchone()

    if row is None:
        raise ValueError(f"Atención con id={atencion_id} no encontrada.")
    return row_to_dict(row)


@mcp.tool()
def update_atencion(
    atencion_id: int,
    diagnostico: Optional[str] = None,
    sintomas: Optional[str] = None,
    tratamiento: Optional[str] = None,
    observaciones: Optional[str] = None,
    estado: Optional[str] = None,
) -> dict:
    """Actualiza una atención."""
    fields = {}
    if diagnostico is not None:
        fields["diagnostico"] = diagnostico
    if sintomas is not None:
        fields["sintomas"] = sintomas
    if tratamiento is not None:
        fields["tratamiento"] = tratamiento
    if observaciones is not None:
        fields["observaciones"] = observaciones
    if estado is not None:
        fields["estado"] = estado

    if not fields:
        raise ValueError("Debes proporcionar al menos un campo para actualizar.")

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [atencion_id]

    with get_connection() as conn:
        affected = conn.execute(f"UPDATE atenciones SET {set_clause} WHERE id = ?", values).rowcount
        conn.commit()
        if affected == 0:
            raise ValueError(f"Atención con id={atencion_id} no encontrada.")
        row = conn.execute("SELECT * FROM atenciones WHERE id = ?", (atencion_id,)).fetchone()

    return row_to_dict(row)


# ── Herramientas MCP: Medicamentos ─────────────────────────────────────────────

@mcp.tool()
def create_medicamento(
    nombre: str,
    principio_activo: Optional[str] = None,
    presentacion: Optional[str] = None,
    descripcion: Optional[str] = None,
    stock_actual: int = 0,
    stock_minimo: int = 10,
    precio_unitario: float = 0,
) -> dict:
    """Crea un nuevo medicamento."""
    if not nombre.strip():
        raise ValueError("El nombre del medicamento no puede estar vacío.")

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO medicamentos (nombre, principio_activo, presentacion, 
               descripcion, stock_actual, stock_minimo, precio_unitario)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre.strip(), principio_activo, presentacion, descripcion, 
             stock_actual, stock_minimo, precio_unitario),
        )
        conn.commit()
        medicamento = conn.execute(
            "SELECT * FROM medicamentos WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_dict(medicamento)


@mcp.tool()
def list_medicamentos(
    nombre: Optional[str] = None,
    principio_activo: Optional[str] = None,
    low_stock: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista medicamentos con filtros."""
    query = "SELECT * FROM medicamentos WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM medicamentos WHERE 1=1"
    params = []

    if nombre:
        query += " AND nombre LIKE ?"
        count_query += " AND nombre LIKE ?"
        params.append(f"%{nombre.strip()}%")
    if principio_activo:
        query += " AND principio_activo LIKE ?"
        count_query += " AND principio_activo LIKE ?"
        params.append(f"%{principio_activo.strip()}%")
    if low_stock:
        query += " AND stock_actual <= stock_minimo"
        count_query += " AND stock_actual <= stock_minimo"

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": total}


@mcp.tool()
def get_medicamento(medicamento_id: int) -> dict:
    """Obtiene un medicamento por ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM medicamentos WHERE id = ?", (medicamento_id,)).fetchone()

    if row is None:
        raise ValueError(f"Medicamento con id={medicamento_id} no encontrado.")
    return row_to_dict(row)


@mcp.tool()
def update_medicamento(
    medicamento_id: int,
    nombre: Optional[str] = None,
    principio_activo: Optional[str] = None,
    presentacion: Optional[str] = None,
    descripcion: Optional[str] = None,
    stock_actual: Optional[int] = None,
    stock_minimo: Optional[int] = None,
    precio_unitario: Optional[float] = None,
) -> dict:
    """Actualiza un medicamento."""
    fields = {}
    if nombre is not None:
        if not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        fields["nombre"] = nombre.strip()
    if principio_activo is not None:
        fields["principio_activo"] = principio_activo
    if presentacion is not None:
        fields["presentacion"] = presentacion
    if descripcion is not None:
        fields["descripcion"] = descripcion
    if stock_actual is not None:
        if stock_actual < 0:
            raise ValueError("El stock no puede ser negativo.")
        fields["stock_actual"] = stock_actual
    if stock_minimo is not None:
        if stock_minimo < 0:
            raise ValueError("El stock mínimo no puede ser negativo.")
        fields["stock_minimo"] = stock_minimo
    if precio_unitario is not None:
        if precio_unitario < 0:
            raise ValueError("El precio no puede ser negativo.")
        fields["precio_unitario"] = precio_unitario

    if not fields:
        raise ValueError("Debes proporcionar al menos un campo para actualizar.")

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [medicamento_id]

    with get_connection() as conn:
        affected = conn.execute(f"UPDATE medicamentos SET {set_clause} WHERE id = ?", values).rowcount
        conn.commit()
        if affected == 0:
            raise ValueError(f"Medicamento con id={medicamento_id} no encontrado.")
        row = conn.execute("SELECT * FROM medicamentos WHERE id = ?", (medicamento_id,)).fetchone()

    return row_to_dict(row)


@mcp.tool()
def delete_medicamento(medicamento_id: int) -> dict:
    """Elimina un medicamento."""
    with get_connection() as conn:
        affected = conn.execute("DELETE FROM medicamentos WHERE id = ?", (medicamento_id,)).rowcount
        conn.commit()

    if affected == 0:
        raise ValueError(f"Medicamento con id={medicamento_id} no encontrado.")

    return {"deleted": True, "medicamento_id": medicamento_id}


# ── Herramientas MCP: Recetas ───────────────────────────────────────────────────

@mcp.tool()
def create_receta(
    atencion_id: int,
    paciente_id: int,
    medicamento_id: int,
    cantidad: int = 1,
    dosis: Optional[str] = None,
    frecuencia: Optional[str] = None,
    duracion: Optional[str] = None,
    instrucciones: Optional[str] = None,
) -> dict:
    """Crea una nueva receta."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO recetas (atencion_id, paciente_id, medicamento_id, cantidad, 
               dosis, frecuencia, duracion, instrucciones)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (atencion_id, paciente_id, medicamento_id, cantidad, 
             dosis, frecuencia, duracion, instrucciones),
        )
        conn.commit()
        receta = conn.execute(
            "SELECT * FROM recetas WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_dict(receta)


@mcp.tool()
def list_recetas(
    paciente_id: Optional[int] = None,
    atencion_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista recetas con filtros."""
    query = "SELECT * FROM recetas WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM recetas WHERE 1=1"
    params = []

    if paciente_id:
        query += " AND paciente_id = ?"
        count_query += " AND paciente_id = ?"
        params.append(paciente_id)
    if atencion_id:
        query += " AND atencion_id = ?"
        count_query += " AND atencion_id = ?"
        params.append(atencion_id)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": total}


@mcp.tool()
def get_receta(receta_id: int) -> dict:
    """Obtiene una receta por ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM recetas WHERE id = ?", (receta_id,)).fetchone()

    if row is None:
        raise ValueError(f"Receta con id={receta_id} no encontrada.")
    return row_to_dict(row)


# ── Herramientas MCP: Médicos ───────────────────────────────────────────────────

@mcp.tool()
def create_medico(
    nombre: str,
    documento: Optional[str] = None,
    especialidad: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    clinica_id: Optional[int] = None,
) -> dict:
    """Crea un nuevo médico."""
    if not nombre.strip():
        raise ValueError("El nombre del médico no puede estar vacío.")

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO medicos (nombre, documento, especialidad, telefono, email, clinica_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nombre.strip(), documento, especialidad, telefono, email, clinica_id),
        )
        conn.commit()
        medico = conn.execute(
            "SELECT * FROM medicos WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return row_to_dict(medico)


@mcp.tool()
def list_medicos(
    nombre: Optional[str] = None,
    especialidad: Optional[str] = None,
    clinica_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista médicos con filtros."""
    query = "SELECT * FROM medicos WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM medicos WHERE 1=1"
    params = []

    if nombre:
        query += " AND nombre LIKE ?"
        count_query += " AND nombre LIKE ?"
        params.append(f"%{nombre.strip()}%")
    if especialidad:
        query += " AND especialidad LIKE ?"
        count_query += " AND especialidad LIKE ?"
        params.append(f"%{especialidad.strip()}%")
    if clinica_id:
        query += " AND clinica_id = ?"
        count_query += " AND clinica_id = ?"
        params.append(clinica_id)

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    return {"items": [row_to_dict(r) for r in rows], "total": total}


@mcp.tool()
def get_medico(medico_id: int) -> dict:
    """Obtiene un médico por ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM medicos WHERE id = ?", (medico_id,)).fetchone()

    if row is None:
        raise ValueError(f"Médico con id={medico_id} no encontrado.")
    return row_to_dict(row)


@mcp.tool()
def update_medico(
    medico_id: int,
    nombre: Optional[str] = None,
    documento: Optional[str] = None,
    especialidad: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    clinica_id: Optional[int] = None,
) -> dict:
    """Actualiza un médico."""
    fields = {}
    if nombre is not None:
        if not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        fields["nombre"] = nombre.strip()
    if documento is not None:
        fields["documento"] = documento
    if especialidad is not None:
        fields["especialidad"] = especialidad
    if telefono is not None:
        fields["telefono"] = telefono
    if email is not None:
        fields["email"] = email
    if clinica_id is not None:
        fields["clinica_id"] = clinica_id

    if not fields:
        raise ValueError("Debes proporcionar al menos un campo para actualizar.")

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [medico_id]

    with get_connection() as conn:
        affected = conn.execute(f"UPDATE medicos SET {set_clause} WHERE id = ?", values).rowcount
        conn.commit()
        if affected == 0:
            raise ValueError(f"Médico con id={medico_id} no encontrado.")
        row = conn.execute("SELECT * FROM medicos WHERE id = ?", (medico_id,)).fetchone()

    return row_to_dict(row)


@mcp.tool()
def delete_medico(medico_id: int) -> dict:
    """Elimina un médico."""
    with get_connection() as conn:
        affected = conn.execute("DELETE FROM medicos WHERE id = ?", (medico_id,)).rowcount
        conn.commit()

    if affected == 0:
        raise ValueError(f"Médico con id={medico_id} no encontrado.")

    return {"deleted": True, "medico_id": medico_id}


# ── Herramientas MCP: Estadísticas ───────────────────────────────────────────────

@mcp.tool()
def get_clinica_stats() -> dict:
    """Devuelve estadísticas generales de la clínica."""
    with get_connection() as conn:
        pacientes = conn.execute("SELECT COUNT(*) as total FROM pacientes").fetchone()
        clinicas = conn.execute("SELECT COUNT(*) as total FROM clinicas").fetchone()
        medicos = conn.execute("SELECT COUNT(*) as total FROM medicos").fetchone()
        turnos = conn.execute("SELECT COUNT(*) as total FROM turnos").fetchone()
        atenciones = conn.execute("SELECT COUNT(*) as total FROM atenciones").fetchone()
        
        turnos_estado = conn.execute(
            "SELECT estado, COUNT(*) as total FROM turnos GROUP BY estado"
        ).fetchall()
        
        medicamentos_stock = conn.execute(
            """SELECT COUNT(*) as total FROM medicamentos 
               WHERE stock_actual <= stock_minimo"""
        ).fetchone()

    return {
        "total_pacientes": pacientes["total"],
        "total_clinicas": clinicas["total"],
        "total_medicos": medicos["total"],
        "total_turnos": turnos["total"],
        "total_atenciones": atenciones["total"],
        "turnos_por_estado": [row_to_dict(r) for r in turnos_estado],
        "medicamentos_bajo_stock": medicamentos_stock["total"],
    }

# ── Recursos MCP ───────────────────────────────────────────────────────────────

@mcp.resource("clinica://pacientes")
def resource_all_pacientes() -> str:
    """Listado rápido de todos los pacientes como texto."""
    with get_connection() as conn:
        rows = conn.execute("SELECT id, nombre, documento, telefono, eps FROM pacientes ORDER BY id").fetchall()
    if not rows:
        return "No hay pacientes registrados."
    lines = ["ID | Nombre | Documento | Teléfono | EPS"]
    lines.append("-" * 70)
    for r in rows:
        doc = r['documento'] or "-"
        tel = r['telefono'] or "-"
        eps = r['eps'] or "-"
        lines.append(f"{r['id']} | {r['nombre'][:30]} | {doc} | {tel} | {eps}")
    return "\n".join(lines)


@mcp.resource("clinica://pacientes/{paciente_id}")
def resource_paciente(paciente_id: str) -> str:
    """Detalle de un paciente por ID."""
    try:
        pid = int(paciente_id)
    except ValueError:
        return f"ID inválido: {paciente_id}"

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM pacientes WHERE id = ?", (pid,)).fetchone()

    if not row:
        return f"Paciente {paciente_id} no encontrado."

    d = row_to_dict(row)
    return "\n".join(f"{k}: {v}" for k, v in d.items())


@mcp.resource("clinica://turnos")
def resource_all_turnos() -> str:
    """Listado rápido de todos los turnos."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT t.id, t.fecha, t.hora, t.estado, p.nombre as paciente, c.nombre as clinica
            FROM turnos t
            LEFT JOIN pacientes p ON t.paciente_id = p.id
            LEFT JOIN clinicas c ON t.clinica_id = c.id
            ORDER BY t.fecha DESC, t.hora DESC
            LIMIT 20
        """).fetchall()
    if not rows:
        return "No hay turnos registrados."
    lines = ["ID | Fecha | Hora | Estado | Paciente | Clínica"]
    lines.append("-" * 80)
    for r in rows:
        lines.append(f"{r['id']} | {r['fecha']} | {r['hora'] or '-'} | {r['estado']} | {r['paciente'][:20]} | {r['clinica'][:20]}")
    return "\n".join(lines)


@mcp.resource("clinica://medicamentos")
def resource_all_medicamentos() -> str:
    """Listado rápido de todos los medicamentos."""
    with get_connection() as conn:
        rows = conn.execute("SELECT id, nombre, principio_activo, stock_actual, stock_minimo FROM medicamentos ORDER BY id").fetchall()
    if not rows:
        return "No hay medicamentos registrados."
    lines = ["ID | Nombre | Principio Activo | Stock | Stock Mín"]
    lines.append("-" * 70)
    for r in rows:
        lines.append(f"{r['id']} | {r['nombre'][:25]} | {r['principio_activo'][:20] or '-'} | {r['stock_actual']} | {r['stock_minimo']}")
    return "\n".join(lines)


# ── Prompts MCP ────────────────────────────────────────────────────────────────

@mcp.prompt()
def clinica_guide() -> str:
    """Guía rápida de uso del servidor de clínica ambulatoria."""
    return """
Eres un asistente que gestiona una clínica ambulatoria a través de un servidor MCP.

Herramientas disponibles:

🏥 CLÍNICAS
- create_clinica   → Agregar una clínica nueva
- list_clinicas    → Listar con filtros
- get_clinica      → Ver detalle por ID
- update_clinica   → Modificar campos
- delete_clinica   → Eliminar una clínica

👤 PACIENTES
- create_paciente  → Agregar un paciente nuevo
- list_pacientes   → Listar con filtros (nombre, documento, ciudad, EPS)
- get_paciente     → Ver detalle por ID
- update_paciente  → Modificar campos
- delete_paciente  → Eliminar un paciente
- buscar_pacientes → Buscar por nombre, documento, EPS o ciudad

👨‍⚕️ MÉDICOS
- create_medico    → Agregar un médico nuevo
- list_medicos     → Listar con filtros
- get_medico       → Ver detalle por ID
- update_medico    → Modificar campos
- delete_medico    → Eliminar un médico

📅 TURNOS
- create_turno     → Crear un turno
- list_turnos      → Listar con filtros
- get_turno        → Ver detalle por ID
- update_turno     → Modificar estado, hora, motivo
- delete_turno     → Eliminar un turno

🏥 ATENCIONES
- create_atencion   → Registrar una atención
- list_atenciones  → Listar con filtros
- get_atencion     → Ver detalle por ID
- update_atencion  → Modificar diagnóstico, síntomas, tratamiento

💊 MEDICAMENTOS
- create_medicamento  → Agregar un medicamento
- list_medicamentos  → Listar con filtros (stock bajo)
- get_medicamento    → Ver detalle por ID
- update_medicamento → Modificar stock, precio
- delete_medicamento → Eliminar un medicamento

📝 RECETAS
- create_receta    → Crear una receta
- list_recetas     → Listar con filtros
- get_receta       → Ver detalle por ID

📊 ESTADÍSTICAS
- get_clinica_stats → Ver estadísticas generales

Recursos disponibles:
- clinica://pacientes       → Vista de todos los pacientes
- clinica://pacientes/{id}  → Detalle de un paciente
- clinica://turnos          → Vista de turnos recientes
- clinica://medicamentos    → Vista de medicamentos

Siempre confirma las operaciones destructivas antes de ejecutarlas.
"""


# ── Punto de entrada ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
