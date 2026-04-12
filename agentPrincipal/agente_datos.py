from os import name
from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
    )
)

sub_agent_crud= LlmAgent(
    model= LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_datos",
    description="Especialista en base de datos clínica",
    instruction= """
      Eres un agente encargado de obtener datos clínicos del turno.

      Debes ejecutar:

      - list_turnos(fecha=hoy)
      - list_atenciones()
      - list_medicamentos()

      Debes devolver:

      - total de pacientes atendidos
      - lista de diagnósticos
      - medicamentos utilizados

      No hagas cálculos complejos.
      No generes reportes.""",
    tools=[crud_toolset],
)
