"""
MCP Analytics Server para Clínica Ambulatoria
Calcula métricas de ocupación y proyectar stock de medicamentos.
"""

import os
import platform
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from fastmcp import FastMCP

if platform.system() == "Windows":
    DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp-crud", "data", "crud.db")
else:
    DEFAULT_DB_PATH = "/data/crud.db"

DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)

mcp = FastMCP(
    name="clinica-analytics-mcp",
    instructions=(
        "Servidor MCP de análisis para clínica ambulatoria. "
        "Proporciona métricas de ocupación de turnos y proyecciones de stock de medicamentos. "
        "Usa las herramientas disponibles para obtener analytics en tiempo real."
    ),
)


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


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def get_hoy() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_manana() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


@mcp.tool()
def porcentaje_ocupacion(
    fecha: Optional[str] = None,
    clinica_id: Optional[int] = None,
) -> dict:
    """
    Calcula el porcentaje de ocupación de turnos para una fecha específica.
    Usa pacientes únicos vs capacidad máxima de la clínica.

    Args:
        fecha: Fecha a analizar (YYYY-MM-DD). Por defecto, hoy.
        clinica_id: ID de la clínica para filtrar (opcional).

    Returns:
        Porcentaje de ocupación, turnos totales, pacientes únicos, capacidad.
    """
    if fecha is None:
        fecha = get_hoy()

    with get_connection() as conn:
        base_query = "SELECT COUNT(*) as total FROM turnos WHERE fecha = ?"
        params = [fecha]

        if clinica_id is not None:
            base_query += " AND clinica_id = ?"
            params.append(clinica_id)

        total_turnos = conn.execute(base_query, params).fetchone()["total"]

        pacientes_unicos = conn.execute(
            f"SELECT COUNT(DISTINCT paciente_id) as total FROM turnos WHERE fecha = ?" + 
            (" AND clinica_id = ?" if clinica_id else ""),
            params
        ).fetchone()["total"]

        capacidad = 10
        if clinica_id:
            cap_row = conn.execute(
                "SELECT cantidad_pacientes_maximo FROM clinicas WHERE id = ?", 
                [clinica_id]
            ).fetchone()
            if cap_row:
                capacidad = cap_row["cantidad_pacientes_maximo"]

    porcentaje = round((pacientes_unicos / capacidad * 100), 2) if capacidad > 0 else 0
    nivel = "BAJO" if porcentaje < 30 else "NORMAL" if porcentaje < 70 else "ALTO" if porcentaje < 90 else "CRITICO"

    return {
        "fecha": fecha,
        "clinica_id": clinica_id,
        "capacidad": capacidad,
        "pacientes_unicos": pacientes_unicos,
        "turnos_totales": total_turnos,
        "porcentaje_ocupacion": porcentaje,
        "nivel_ocupacion": nivel,
    }


@mcp.tool()
def ocupacion_por_clinica(fecha: Optional[str] = None) -> dict:
    """
    Calcula el porcentaje de ocupación por clínica para una fecha.

    Args:
        fecha: Fecha a analizar (YYYY-MM-DD). Por defecto, hoy.

    Returns:
        Lista de clínicas con su porcentaje de ocupación.
    """
    if fecha is None:
        fecha = get_hoy()

    with get_connection() as conn:
        clinicas = conn.execute("SELECT id, nombre FROM clinicas").fetchall()

        resultados = []
        for clinica in clinicas:
            total = conn.execute(
                "SELECT COUNT(*) as total FROM turnos WHERE fecha = ? AND clinica_id = ?",
                (fecha, clinica["id"])
            ).fetchone()["total"]

            ocup = conn.execute(
                """SELECT COUNT(*) as ocup FROM turnos 
                   WHERE fecha = ? AND clinica_id = ? AND estado != 'cancelado'""",
                (fecha, clinica["id"])
            ).fetchone()["ocup"]

            pct = round((ocup / total * 100), 2) if total > 0 else 0
            resultados.append({
                "clinica_id": clinica["id"],
                "clinica_nombre": clinica["nombre"],
                "turnos_totales": total,
                "turnos_ocupados": ocup,
                "porcentaje_ocupacion": pct,
            })

        resultados.sort(key=lambda x: x["porcentaje_ocupacion"], reverse=True)

    return {
        "fecha": fecha,
        "total_clinicas": len(resultados),
        "ocupacion_por_clinica": resultados,
    }


@mcp.tool()
def proyectar_stock_manana() -> dict:
    """
    Proyecta el stock de medicamentos para el día siguiente.

    Calcula el consumo estimado basado en el promedio de los últimos 7 días
    y lo compara con el stock actual para el día de mañana.

    Returns:
        Stock actual, consumo proyectado, stock proyectado, alertas de stock bajo.
    """
    fecha_hoy = get_hoy()
    fecha_manana = get_manana()

    fecha_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    with get_connection() as conn:
        medicamentos = conn.execute("SELECT * FROM medicamentos ORDER BY id").fetchall()

        resultados = []
        alertas = []

        for med in medicamentos:
            consumo_total = conn.execute("""
                SELECT COALESCE(SUM(r.cantidad), 0) as total
                FROM recetas r
                JOIN atenciones a ON r.atencion_id = a.id
                WHERE r.medicamento_id = ? AND a.created_at >= ? AND a.created_at < ?
            """, (med["id"], fecha_inicio, fecha_hoy)).fetchone()["total"]

            consumo_promedio_diario = round(consumo_total / 7, 2)

            stock_actual = med["stock_actual"]
            stock_minimo = med["stock_minimo"]
            stock_proyectado = stock_actual - consumo_promedio_diario

            estado = "ok"
            if stock_proyectado <= 0:
                estado = "sin_stock"
                alertas.append({
                    "medicamento_id": med["id"],
                    "medicamento_nombre": med["nombre"],
                    "stock_actual": stock_actual,
                    "consumo_proyectado": consumo_promedio_diario,
                    "stock_proyectado": stock_proyectado,
                    "alerta": "Sin stock mañana",
                })
            elif stock_proyectado <= stock_minimo:
                estado = "bajo_stock"
                alertas.append({
                    "medicamento_id": med["id"],
                    "medicamento_nombre": med["nombre"],
                    "stock_actual": stock_actual,
                    "consumo_proyectado": consumo_promedio_diario,
                    "stock_proyectado": round(stock_proyectado, 2),
                    "stock_minimo": stock_minimo,
                    "alerta": "Stock bajo mañana",
                })

            resultados.append({
                "medicamento_id": med["id"],
                "medicamento_nombre": med["nombre"],
                "principio_activo": med["principio_activo"],
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
                "consumo_promedio_7dias": consumo_promedio_diario,
                "stock_proyectado_manana": round(stock_proyectado, 2),
                "estado": estado,
            })

        resultados.sort(key=lambda x: x["stock_proyectado_manana"])

    return {
        "fecha_hoy": fecha_hoy,
        "fecha_proyeccion": fecha_manana,
        "periodo_consumo_dias": 7,
        "total_medicamentos": len(resultados),
        "alertas_stock": len(alertas),
        "medicamentos": resultados,
        "alertas": alertas,
    }


@mcp.tool()
def tendencia_ocupacion(dias: int = 7) -> dict:
    """
    Calcula la tendencia de ocupación de los últimos N días.

    Args:
        dias: Número de días hacia atrás a analizar (default: 7).

    Returns:
        Lista diaria con porcentaje de ocupación.
    """
    if dias < 1 or dias > 30:
        raise ValueError("El número de días debe estar entre 1 y 30.")

    fecha_fin = get_hoy()
    fecha_inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

    with get_connection() as conn:
        resultados = []
        fecha_actual = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")

        while fecha_actual <= fecha_fin_dt:
            fecha_str = fecha_actual.strftime("%Y-%m-%d")

            total = conn.execute(
                "SELECT COUNT(*) as total FROM turnos WHERE fecha = ?",
                (fecha_str,)
            ).fetchone()["total"]

            ocup = conn.execute(
                """SELECT COUNT(*) as ocup FROM turnos 
                   WHERE fecha = ? AND estado != 'cancelado'""",
                (fecha_str,)
            ).fetchone()["ocup"]

            pct = round((ocup / total * 100), 2) if total > 0 else 0

            resultados.append({
                "fecha": fecha_str,
                "turnos_totales": total,
                "turnos_ocupados": ocup,
                "porcentaje_ocupacion": pct,
            })

            fecha_actual += timedelta(days=1)

    promedio = round(sum(r["porcentaje_ocupacion"] for r in resultados) / len(resultados), 2) if resultados else 0

    return {
        "dias_analizados": dias,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "promedio_ocupacion": promedio,
        "tendencia": resultados,
    }


@mcp.tool()
def metricas_clinica(
    clinica_id: Optional[int] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
) -> dict:
    """
    Métricas generales de la clínica.

    Args:
        clinica_id: ID de la clínica (opcional).
        fecha_inicio: Fecha inicial (YYYY-MM-DD). Por defecto, 30 días atrás.
        fecha_fin: Fecha final (YYYY-MM-DD). Por defecto, hoy.

    Returns:
        Métricas completas de turnos, atenciones y stock.
    """
    if fecha_fin is None:
        fecha_fin = get_hoy()
    if fecha_inicio is None:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    with get_connection() as conn:
        params_turnos = [fecha_inicio, fecha_fin]
        if clinica_id:
            params_turnos.append(clinica_id)

        turnos_total = conn.execute(
            "SELECT COUNT(*) as total FROM turnos WHERE fecha >= ? AND fecha <= ?" + (" AND clinica_id = ?" if clinica_id else ""),
            params_turnos
        ).fetchone()["total"]

        turnos_ocupados = conn.execute(
            "SELECT COUNT(*) as total FROM turnos WHERE fecha >= ? AND fecha <= ? AND estado != 'cancelado'" + (" AND clinica_id = ?" if clinica_id else ""),
            params_turnos
        ).fetchone()["total"]

        atenciones = conn.execute(
            "SELECT COUNT(*) as total FROM atenciones WHERE created_at >= ? AND created_at <= ?",
            [fecha_inicio, fecha_fin]
        ).fetchone()["total"]

        promedio_diario = round(turnos_ocupados / 30, 2) if turnos_ocupados > 0 else 0

        medicamentos_bajo_stock = conn.execute(
            "SELECT COUNT(*) as total FROM medicamentos WHERE stock_actual <= stock_minimo"
        ).fetchone()["total"]

        total_medicamentos = conn.execute(
            "SELECT COUNT(*) as total FROM medicamentos"
        ).fetchone()["total"]

        stock_total = conn.execute(
            "SELECT COALESCE(SUM(stock_actual), 0) as total FROM medicamentos"
        ).fetchone()["total"]

    return {
        "clinica_id": clinica_id,
        "periodo": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
        "turnos": {
            "total": turnos_total,
            "ocupados": turnos_ocupados,
            "disponibles": turnos_total - turnos_ocupados,
            "promedio_diario": promedio_diario,
            "porcentaje_ocupacion": round((turnos_ocupados / turnos_total * 100), 2) if turnos_total > 0 else 0,
        },
        "atenciones": {"total": atenciones},
        "medicamentos": {
            "total": total_medicamentos,
            "bajo_stock": medicamentos_bajo_stock,
            "stock_total_unidades": stock_total,
        },
    }


@mcp.tool()
def ranking_medicamentos(limit: int = 10) -> dict:
    """
    Ranking de medicamentos más consumidos en los últimos 30 días.

    Args:
        limit: Número de medicamentos a incluir (default: 10).

    Returns:
        Lista de medicamentos ordenados por consumo.
    """
    fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    with get_connection() as conn:
        resultados = conn.execute("""
            SELECT m.id, m.nombre, m.principio_activo, m.stock_actual,
                   COALESCE(SUM(r.cantidad), 0) as consumo_total
            FROM medicamentos m
            LEFT JOIN recetas r ON m.id = r.medicamento_id
            LEFT JOIN atenciones a ON r.atencion_id = a.id AND a.created_at >= ?
            GROUP BY m.id
            ORDER BY consumo_total DESC
            LIMIT ?
        """, (fecha_inicio, limit)).fetchall()

    return {
        "periodo": f"Últimos 30 días desde {fecha_inicio}",
        "total_resultados": len(resultados),
        "medicamentos": [row_to_dict(r) for r in resultados],
    }


# ── Recursos MCP ───────────────────────────────────────────────────────────────

@mcp.resource("analytics://ocupacion-hoy")
def resource_ocupacion_hoy() -> str:
    """Porcentaje de ocupación de hoy."""
    datos = porcentaje_ocupacion()
    return (
        f"Ocupación de turnos - {datos['fecha']}\n"
        f"Total: {datos['turnos_totales']} | "
        f"Ocupados: {datos['turnos_ocupados']} | "
        f"Disponibles: {datos['turnos_disponibles']}\n"
        f"Porcentaje: {datos['porcentaje_ocupacion']}%"
    )


@mcp.resource("analytics://stock-manana")
def resource_stock_manana() -> str:
    """Proyección de stock para mañana."""
    datos = proyectar_stock_manana()
    lines = [f"Proyección de stock para {datos['fecha_proyeccion']}"]
    lines.append("=" * 50)

    if datos["alertas"]:
        lines.append(f"ALERTAS: {datos['alertas_stock']} medicamentos")
        for alerta in datos["alertas"][:5]:
            lines.append(f"  - {alerta['medicamento_nombre']}: {alerta['alerta']}")
    else:
        lines.append("Sin alertas de stock")

    return "\n".join(lines)


@mcp.resource("analytics://metricas")
def resource_metricas() -> str:
    """Métricas generales de la clínica."""
    datos = metricas_clinica()
    return (
        f"Metricas Clinica (ultimos 30 dias)\n"
        f"Turnos: {datos['turnos']['total']} ({datos['turnos']['porcentaje_ocupacion']}% ocupacion)\n"
        f"Atenciones: {datos['atenciones']['total']}\n"
        f"Medicamentos: {datos['medicamentos']['total']} total, "
        f"{datos['medicamentos']['bajo_stock']} bajo stock"
    )


# ── Prompts MCP ───────────────────────────────────────────────────────────────

@mcp.prompt()
def analytics_guide() -> str:
    """Guía de uso del servidor de análisis."""
    return """
Eres un asistente de analisis para una clinica ambulatoria.

Herramientas disponibles:

📊 OCUPACION
- porcentaje_ocupacion(fecha, clinica_id)     → % ocupacion para una fecha
- ocupacion_por_clinica(fecha)                → % ocupacion por clinica
- tendencia_ocupacion(dias)                   → Tendencia ultimos N dias

📦 STOCK DE MEDICAMENTOS
- proyectar_stock_manana()                     → Proyeccion para manana
- ranking_medicamentos(limit)                 → Top medicamentos consumidos

📈 METRICAS GENERALES
- metricas_clinica(clinica_id, inicio, fin)   → Metricas completas

Recursos:
- analytics://ocupacion-hoy    → Resumen de ocupacion hoy
- analytics://stock-manana     → Alertas de stock para manana
- analytics://metricas         → Metricas generales

Usa estas herramientas para proporcionar insights utiles sobre la operacion de la clinica.
"""


# ── Punto de entrada ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)