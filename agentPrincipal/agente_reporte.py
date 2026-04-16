"""
Agente Reporte - Genera el reporte final de cierre de turno.
MCP: filesystem-mcp, crud-mcp, analytics-mcp
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from datetime import datetime, date

filesystem_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url="http://localhost:8003/mcp")
)
crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url="http://localhost:8000/mcp")
)
analytics_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url="http://localhost:8001/mcp")
)

HOY = date.today().isoformat()
HORA_ACTUAL = datetime.now().strftime("%H:%M")

sub_agent_reporte = LlmAgent(
    model="gemini-2.5-flash-lite",
    name="agente_reporte",
    description=("Genera y guarda reporte de cierre de turno."),
    instruction=f"""
Eres un agente que debe generar Y GUARDAR el reporte de cierre de turno.

El NOMBRE de la clínica viene en el mensaje del usuario.

PASO 1: OBTENER DATOS (ejecuta en orden)
1. list_clinicas(nombre=[NOMBRE_DE_LA_CLINICA], limit=1) → obtener clinica_id
2. list_turnos(fecha="{HOY}", clinica_id=[CLINICA_ID], limit=50)
3. list_atenciones(fecha="{HOY}", clinica_id=[CLINICA_ID], limit=100)
4. list_medicamentos(limit=50)
5. proyectar_stock_manana()
6. porcentaje_ocupacion(fecha="{HOY}", clinica_id=[CLINICA_ID])

PASO 2: GENERAR REPORTE EXACTO - USA ESTA PLANTILLA TAL CUAL:

# Cierre de Turno - [NOMBRE_DE_LA_CLINICA]
**Fecha:** {HOY}
**Hora de cierre:** {HORA_ACTUAL}
**Generado por:** Sistema Automatico de Cierre de Turno 

---

## Resumen del Turno
- Total turnos del dia: [numero total de turnos]
- Turnos atendidos: [numero de turnos con estado='atendido']
- Pacientes atendidos: [numero de pacientes unicos con atencion]
- Porcentaje de ocupacion: [numero]%
- Nivel de ocupacion: [BAJO/NORMAL/ALTO/CRITICO]

---

## Estado del Inventario de Medicamentos
**Estado general:** [OK/BAJO STOCK/CRITICO]

Medicamentos Criticos (stock = 0): [lista de nombres o 'Ninguno']

Medicamentos con Stock Bajo (stock <= stock_minimo): [lista de nombres o 'Ninguno']

---

## Proyeccion para Manana
[lista de medicamentos que estaran sin stock o bajos manana, o 'No se proyectan alertas para manana']

---

## Metricas de Ocupacion
- Total turnos registrados: [numero]
- Turnos atendidos hoy: [numero]
- Porcentaje de ocupacion: [numero]%
- Total atenciones registradas: [numero]

---

## Alertas Sanitarias - [NOMBRE_CIUDAD]
**Nivel de riesgo:** [nivel]
**Alertas activas:** [numero]

[descripcion de alertas]

---

## Recomendaciones Automaticas
- Verificar y completar registros de atenciones del turno
- Entregar informe al jefe de turno entrante

---

*Reporte generado automaticamente - Sistema de Cierre de Turno*
*[NOMBRE_DE_LA_CLINICA] | {HOY} | {HORA_ACTUAL}*

PASO 3: GUARDAR CON write_file
- path: "cierre_{HOY}.md"
- content: [EL REPORTE COMPLETO TAL CUAL]
- overwrite: true
""",
    tools=[filesystem_toolset, crud_toolset, analytics_toolset],
)
