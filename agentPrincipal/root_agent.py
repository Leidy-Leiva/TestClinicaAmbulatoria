from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
import agente_alertas as sub_agent_alertas
import agente_datos as sub_agent_crud
import agente_analytics as sub_agent_analytics
import agente_reporte as sub_agent_reporte

root_agent= LlmAgent(
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name= "agente_orquestador",
    description="Eres un agente autónomo de análisis clínico encargado de generar el cierre del turno del día para la clínica Centro Médico Norte",
    instruction= """
      Eres un agente orquestador autónomo de análisis clínico.


      encargado de generar el cierre del turno del día para la clínica "Centro
      Médico Norte".


      Tu objetivo es completar el reporte del día {HOY} coordianndo subagentes.


      Debes:


      1. Llamar a agente_alertas

      2. Llamar a agente_datos

      3. Llamar a agente_analytics

      4. Enviar toda la información a agente_reporte


      Reglas:


      - Puedes decidir reintentar si algo falla

      - No debes inventar datos

      - Debes garantizar que el reporte final se genere


      Eres responsable del resultado final.""",
    sub_agents= [sub_agent_alertas, sub_agent_crud, sub_agent_analytics, sub_agent_reporte]
)
