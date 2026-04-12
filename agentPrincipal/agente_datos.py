from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp",
    )
)

sub_agent_crud = LlmAgent(
    # model="gemini-2.5-flash",
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_datos",
    description="Especialista en base de datos clínica",
    instruction="""
Eres un agente encargado de obtener datos clínicos del turno.

Debes OBLIGATORIAMENTE:
1. Llamar a list_atenciones(limit=1000)
2. Llamar a list_recetas(limit=1000)
3. Llamar a list_pacientes(limit=1000)

Luego devuelve:
- total de pacientes atendidos
- lista de diagnósticos
- medicamentos utilizados

NO uses transfer_to_agent. NO generes reportes.
Simplemente obtén los datos y devuélvelos.""",
    tools=[crud_toolset],
)
