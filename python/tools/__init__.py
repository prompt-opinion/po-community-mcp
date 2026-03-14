from mcp_instance import mcp
from tools.patient_age_tool import patient_age_tool_instance
from tools.patient_allergies_tool import patient_allergies_tool_instance
from tools.patient_id_tool import patient_id_tool_instance

for tool in [patient_age_tool_instance, patient_allergies_tool_instance, patient_id_tool_instance]:
    tool.register_tool(mcp)
