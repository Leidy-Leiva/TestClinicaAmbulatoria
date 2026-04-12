from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from agentPrincipal import agente_alertas
from agentPrincipal import agente_datos
from agentPrincipal import agente_analytics
from agentPrincipal import agente_reporte

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    # model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_orquestador",
    description="Orquestador de cierre de turno para clínica Centro Médico Norte",
    instruction="""
Eres el orquestador del cierre de turno. DEBES ejecutar los 4 subagentes en este EXACTO orden:

1. agente_alertas → Obtiene alertas sanitarias (NO clima)
2. agente_datos → Obtiene datos clínicos (atenciones, recetas, pacientes)
3. agente_analytics → Obtiene métricas (ocupación, stock)
4. agente_reporte → Genera y guarda el reporte final en /workspace/cierre_YYYY-MM-DD.md

FLUJO OBLIGATORIO:
- Primero transfiere a agente_alertas
- Cuando agente_alertas termine, transfiere a agente_datos
- Cuando agente_datos termine, transfiere a agente_analytics
- Cuando agente_analytics termine, transfiere a agente_reporte
- Cuando agente_reporte termine, devuelve el resultado final

 IMPORTANTE: No debes terminar hasta que agente_reporte haya guardado el archivo.""",
    sub_agents=[
        agente_alertas.sub_agent_alertas,
        agente_datos.sub_agent_crud,
        agente_analytics.sub_agent_analytics,
        agente_reporte.sub_agent_reporte
    ]
)
