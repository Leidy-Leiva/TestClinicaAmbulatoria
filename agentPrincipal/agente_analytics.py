from distro import name
from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

analytics_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
    )
)

sub_agent_analytics= LlmAgent(
    model= LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_analytics",
    description="Especialista en métricas",
    instruction= """
  Eres un agente de análisis.

  Debes ejecutar:

  - porcentaje_ocupacion(fecha=hoy)
  - proyectar_stock_manana()

  Debes devolver:

  - porcentaje de ocupación
  - estado del stock (normal, bajo, crítico)
  - proyección para mañana

  No consultes datos clínicos.
  No generes reportes.""",
  tools=[analytics_toolset]
  )

