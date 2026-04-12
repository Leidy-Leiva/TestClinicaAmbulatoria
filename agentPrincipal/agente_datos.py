"""
Agente Datos - Obtiene datos clínicos del turno.
MCP: crud-mcp (http://localhost:8000/mcp)

Herramientas reales disponibles en crud-mcp:
  - get_clinica_stats()          → estadísticas generales (total pacientes, atenciones, turnos)
  - list_turnos(fecha, estado)   → turnos del día filtrados por fecha/estado
  - list_atenciones()            → atenciones registradas con diagnósticos
  - list_medicamentos()          → stock de medicamentos
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from datetime import date

crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp",
    )
)

HOY = date.today().isoformat()

sub_agent_crud = LlmAgent(
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_datos",
    description=(
        "Obtiene datos clínicos del turno: estadísticas, atenciones, diagnósticos y stock de medicamentos. "
        "Usa las herramientas del CRUD MCP."
    ),
    instruction=f"""
Eres un agente encargado de recolectar los datos clínicos del turno del día {HOY}.

Ejecuta EXACTAMENTE estas herramientas en orden:

1. get_clinica_stats()
   → Devuelve estadísticas generales: total_pacientes, total_atenciones, total_turnos, turnos_por_estado, medicamentos_bajo_stock

2. list_turnos(fecha="{HOY}", limit=50)
   → Devuelve todos los turnos del día de hoy con su estado (programado/atendido/cancelado)

3. list_atenciones(limit=50)
   → Devuelve las atenciones del día con diagnósticos y tratamientos

4. list_medicamentos(limit=50)
   → Devuelve el inventario completo de medicamentos con stock_actual y stock_minimo

Después de ejecutar las 4 herramientas, construye y devuelve un JSON con esta estructura:
{{
  "fecha": "{HOY}",
  "estadisticas": <resultado completo de get_clinica_stats>,
  "turnos_hoy": <resultado completo de list_turnos>,
  "atenciones": <resultado completo de list_atenciones>,
  "medicamentos_stock": <resultado completo de list_medicamentos>
}}

REGLAS ESTRICTAS:
- NO uses transfer_to_agent bajo ninguna circunstancia.
- NO uses herramientas que no existen como get_resumen_turno o get_medicamentos_usados.
- NO generes datos inventados.
- Si una herramienta falla, incluye {{"error": "descripcion del error"}} en ese campo del JSON.
- Si no hay atenciones, devuelve el JSON con arrays vacíos pero NO falles.
- Responde ÚNICAMENTE con el JSON resultado, sin texto adicional.
""",
    tools=[crud_toolset],
)