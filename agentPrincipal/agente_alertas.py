
from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

weather_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8002/mcp",
    )
)


sub_agent_alertas= LlmAgent(
    model= LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_alertas",
    description="Especialista en contexto sanitario externo",
    instruction= """
      Eres un agente especializado en consultar alertas sanitarias y
      epidemiológicas.


      Tu única responsabilidad es:


      1. Consultar alertas usando:
        alertas_sanitarias(ciudad="Bogotá")

      2. Interpretar el resultado y devolver:

      - nivel de riesgo

      - lista de alertas

      - recomendaciones clave


      NO generes reportes completos.

      NO consultes otras herramientas""",
      tools=[weather_toolset],

)

