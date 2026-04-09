"""
Agente Orquestador para Cierre de Turno - Clínica Centro Médico Norte
Orquesta los MCPs disponibles para generar el cierre de turno
"""

from datetime import datetime

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams


HOY = datetime.now().strftime("%Y-%m-%d")
REPORTE = f"cierre_{HOY}_Centro_Medico_Norte.md"

crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp",
    )
)

analytics_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
    )
)

weather_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8002/mcp",
    )
)

filesystem_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8003/mcp",
    )
)

root_agent = LlmAgent(
    model=LiteLlm(model="bedrock/anthropic.claude-3-haiku-20240307-v1:0"),
    name="orquestador_cierre_turno",
    description="Orquesta MCPs para generar cierre de turno",
instruction=f"""
Eres un agente autónomo de análisis clínico.

Tu objetivo es generar el cierre del turno del día {HOY} para la clínica Centro Médico Norte.

Tienes acceso a herramientas MCP que puedes usar libremente para obtener información.

REGLAS:

- Decide qué información necesitas y cuándo obtenerla.
- Usa MCPs solo cuando sea necesario.
- No inventes datos.
- Puedes hacer múltiples llamadas a herramientas.
- No existe un orden obligatorio de ejecución.

REQUISITOS DEL RESULTADO FINAL:

El reporte debe contener (si la información está disponible):

1. Actividad clínica del día (turnos, atenciones)
2. Diagnósticos principales
3. Estado del inventario de medicamentos
4. Ocupación de la clínica
5. Proyección de stock
6. Condiciones externas relevantes (clima / alertas sanitarias)
7. Recomendaciones operativas

CONDICIÓN FINAL:

Antes de guardar el reporte, debes verificar que tienes suficiente información para cada sección.

Luego usa filesystem MCP para guardar el resultado en:
cierre_{HOY}.md
""",tools=[crud_toolset, analytics_toolset, weather_toolset, filesystem_toolset],
)