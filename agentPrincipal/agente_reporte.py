
from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

filesystem_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8003/mcp",
    )
)

sub_agent_reporte= LlmAgent(
    model= LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_reporte",
    description="Generador de informe final",
    instruction= """
    Eres un agente encargado de generar el reporte final en Markdown.

    Recibirás información de otros agentes:

    - datos clínicos
    - analytics
    - alertas sanitarias

    Debes construir:

    1. Resumen ejecutivo
    2. Top 3 diagnósticos
    3. Estado del inventario
    4. Ocupación
    5. Alertas sanitarias
    6. Recomendaciones

    Luego debes guardar el archivo usando:
    write_file(path="/workspace/cierre_{fecha}.md")

    Si falta información:
    - indícalo claramente
    - no falles""",
    tools=[filesystem_toolset],
)