"""
Agente Alertas - Obtiene alertas sanitarias y epidemiológicas.
MCP: weather-colombia-mcp (http://localhost:8002/mcp)
Herramienta: alertas_sanitarias(ciudad="Bogota")

CORRECCIÓN v2:
- Prompt imperativo e incondicional: llama alertas_sanitarias SIEMPRE,
  independientemente del mensaje recibido (el SequentialAgent pasa el
  mensaje original del usuario, no uno específico para este agente).
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

alertas_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8002/mcp",
    )
)

sub_agent_alertas = LlmAgent(
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_alertas",
    description=(
        "Obtiene alertas sanitarias y epidemiologicas para Bogota. "
        "Llama a alertas_sanitarias(ciudad='Bogota') y devuelve el resultado."
    ),
    instruction="""Eres un agente de vigilancia epidemiologica. Tu unica funcion es llamar a la herramienta alertas_sanitarias.

ACCION OBLIGATORIA E INCONDICIONAL:
Sin importar el mensaje que recibas, SIEMPRE debes:
1. Llamar a: alertas_sanitarias(ciudad="Bogota")
2. Devolver el resultado JSON completo que retorne la herramienta.

NO analices el mensaje. NO preguntes. NO expliques. Solo llama a alertas_sanitarias y devuelve el resultado.

Si la herramienta falla o da error, devuelve este JSON exacto:
{"ciudad": "Bogota", "departamento": "Cundinamarca", "alertas_activas": 0, "nivel_riesgo": "desconocido", "nivel_riesgo_codigo": 0, "alertas": [], "fuente": "API no disponible", "error": "No se pudo conectar al servicio de alertas sanitarias"}

PROHIBIDO:
- Usar transfer_to_agent
- Llamar cualquier otra herramienta (clima_actual, pronostico_diario, calidad_aire)
- Responder sin haber llamado alertas_sanitarias primero
""",
    tools=[alertas_toolset],
)