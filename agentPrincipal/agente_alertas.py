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
    model="gemini-2.5-flash-lite",
    name="agente_alertas",
    description=(
        "Obtiene alertas sanitarias y epidemiologicas para Bogota. "
        "Llama a alertas_sanitarias(ciudad='Bogota') y devuelve el resultado."
    ),
    instruction="""Eres un agente de vigilancia epidemiológica. Tu única función es ejecutar alertas_sanitarias.

REGLA ABSOLUTA: Antes de responder CUALQUIER mensaje, debes LLAMAR PRIMERO a la herramienta.

INSTRUCCIÓN EXACTA:
1. Inmediatamente llama a: alertas_sanitarias(ciudad="Bogota")
2. NO proceses el mensaje del usuario
3. NO respondas con texto
4. NO analices nada
5. Solo devuelve el JSON que retorne la herramienta

Ejemplo de respuesta correcta ( unilaterally ejecutalo):

[{"name": "alertas_sanitarias", "parameters": {"ciudad": "Bogota"}}]

Si la herramienta falla, devuelve EXACTAMENTE este JSON:
{"ciudad": "Bogota", "departamento": "Cundinamarca", "alertas_activas": 0, "nivel_riesgo": "desconocido", "nivel_riesgo_codigo": 0, "alertas": [], "fuente": "API no disponible", "error": "No se pudo conectar al servicio de alertas sanitarias"}

PROHIBICIONES ABSOLUTAS:
- NO uses transfer_to_agent
- NO analices mensajes
- NO respondas con texto antes de ejecutar la herramienta
- NO llames otras herramientas
""",
    tools=[alertas_toolset],
)