
from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

weather_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8002/mcp",
    )
)


sub_agent_alertas = LlmAgent(
    # model="gemini-2.5-flash",
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_alertas",
    description="Especialista en contexto sanitario externo",
    instruction="""
Eres un agente especializado en alertas sanitarias y epidemiológicas.

Tu única tarea OBLIGATORIA es:
1. LLAMAR A LA HERRAMIENTA alertas_sanitarias(ciudad="Bogotá") - NO clima_actual
2. Devolver el resultado tal cual

Si no existe la herramienta alertas_sanitarias, devuelve: "No disponible"

NO uses transfer_to_agent. NO generes textos. Solo llama a la herramienta.""",
    tools=[weather_toolset],
)

