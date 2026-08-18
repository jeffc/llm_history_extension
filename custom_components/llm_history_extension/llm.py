"""LLM platform for LLM History & Entity ID Extension."""

from homeassistant.components.llm import LLMTools
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.llm import LLM_API_ASSIST, LLMContext

from . import CustomGetHistoryTool


@callback
def async_get_tools(
    hass: HomeAssistant, llm_context: LLMContext, api_id: str
) -> LLMTools | None:
    """Return LLM tools."""
    if api_id != LLM_API_ASSIST:
        return None

    try:
        from homeassistant.components.homeassistant.llm import async_get_exposed_entities
        exposed_entities = async_get_exposed_entities(hass, llm_context.assistant)
    except (ImportError, AttributeError):
        exposed_entities = None

    if not exposed_entities:
        return None

    return LLMTools(tools=[CustomGetHistoryTool()])
