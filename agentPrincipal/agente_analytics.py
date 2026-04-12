from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from datetime import datetime

analytics_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
    )
)

HOY = datetime.now().strftime("%Y-%m-%d")

sub_agent_analytics = LlmAgent(
    # model="gemini-2.5-flash",
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_analytics",
    description="Especialista en métricas",
    instruction=f"""
Eres un agente de análisis clínico.

Debes OBLIGATORIAMENTE:
1. Llamar a porcentaje_ocupacion(fecha="{HOY}")
2. Llamar a proyectar_stock_manana()

Luego devuelve:
- porcentaje de ocupación
- estado del stock (normal, bajo, crítico)
- proyección para mañana

NO uses transfer_to_agent. NO generes reportes.""",
    tools=[analytics_toolset],
)

