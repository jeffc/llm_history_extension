"""LLM History and Entity ID Extension integration."""

import logging
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from functools import partial
from typing import Any
import voluptuous as vol

from homeassistant.components.homeassistant import async_should_expose
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, llm
from homeassistant.util import dt as dt_util, yaml as yaml_util

_LOGGER = logging.getLogger(__name__)

DOMAIN = "llm_history_extension"


class CustomGetHistoryTool(llm.Tool):
    """Custom history tool injected into Assist API."""

    name = "GetHistory"
    description = (
        "Retrieves the state history for one or more entities over a specified period. "
        "Returns state changes with human-readable timestamps in the local timezone."
    )
    parameters = vol.Schema(
        {
            vol.Required(
                "entity_ids",
                description="The entity ID or list of entity IDs to query the history for.",
            ): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(
                "start_time",
                description="The start time of the history query in ISO 8601 format (e.g. 2026-06-18T20:00:00Z). Defaults to 24 hours ago.",
            ): cv.datetime,
            vol.Optional(
                "end_time",
                description="The end time of the history query in ISO 8601 format (e.g. 2026-06-18T21:00:00Z). Defaults to now.",
            ): cv.datetime,
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        """Call the tool."""
        from homeassistant.components.recorder import get_instance, history  # noqa: PLC0415

        try:
            recorder_instance = get_instance(hass)
        except KeyError:
            return {"success": False, "error": "Recorder integration is not configured or loaded"}

        args = self.parameters(tool_input.tool_args)
        entity_ids = args["entity_ids"]

        if llm_context.assistant is None:
            return {"success": False, "error": "No assistant configured"}

        for entity_id in entity_ids:
            if not async_should_expose(hass, llm_context.assistant, entity_id):
                return {"success": False, "error": f"Entity {entity_id} is not exposed to the LLM assistant"}

        end_time = args.get("end_time") or dt_util.utcnow()
        start_time = args.get("start_time") or (end_time - timedelta(days=1))

        try:
            historical_states = await recorder_instance.async_add_executor_job(
                partial(
                    history.get_significant_states,
                    hass,
                    start_time,
                    end_time,
                    entity_ids=entity_ids,
                    include_start_time_state=True,
                    significant_changes_only=False,
                    minimal_response=False,
                )
            )
        except Exception as err:
            return {"success": False, "error": f"Failed to retrieve history: {err}"}

        interesting_attributes = {
            "temperature",
            "current_temperature",
            "temperature_unit",
            "brightness",
            "humidity",
            "unit_of_measurement",
            "device_class",
            "current_position",
            "percentage",
            "volume_level",
            "media_title",
            "media_artist",
            "media_album_name",
        }

        result_dict = {}
        for entity_id, states in historical_states.items():
            entity_history = []
            for state in states:
                entry = {
                    "timestamp": dt_util.as_local(state.last_updated).strftime("%Y-%m-%d %H:%M:%S"),
                    "state": state.state,
                }
                for attr in interesting_attributes:
                    if attr in state.attributes:
                        val = state.attributes[attr]
                        if isinstance(val, (Enum, Decimal, int)):
                            entry[attr] = str(val)
                        else:
                            entry[attr] = val
                entity_history.append(entry)
            result_dict[entity_id] = entity_history

        if not result_dict:
            return {"success": True, "result": "No history found for the requested entities in the specified period."}

        return {
            "success": True,
            "result": yaml_util.dump(result_dict),
        }


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the LLM extension integration and apply patches."""
    _LOGGER.info("Applying dynamic patches for LLM History and Entity ID Extension")

    # 1. Patch entity list serialization to include entity_id
    original_get_exposed_entities = llm._get_exposed_entities

    @callback
    def custom_get_exposed_entities(hass: HomeAssistant, assistant: str, include_state: bool = True):
        data = original_get_exposed_entities(hass, assistant, include_state)
        # Inject entity_id into the serialized info dict for each exposed entity
        if "entities" in data:
            for entity_id, info in data["entities"].items():
                info["entity_id"] = entity_id
        if "script" in data:
            for script_id, info in data["script"].items():
                info["entity_id"] = script_id
        if "calendar" in data:
            for calendar_id, info in data["calendar"].items():
                info["entity_id"] = calendar_id
        return data

    llm._get_exposed_entities = custom_get_exposed_entities

    # 2. Patch the built-in AssistAPI to register CustomGetHistoryTool
    original_get_tools = llm.AssistAPI._async_get_tools

    @callback
    def custom_get_tools(self, llm_context: llm.LLMContext, exposed_entities: dict | None) -> list[llm.Tool]:
        tools = original_get_tools(self, llm_context, exposed_entities)
        if exposed_entities and exposed_entities.get("entities"):
            tools.append(CustomGetHistoryTool())
        return tools

    llm.AssistAPI._async_get_tools = custom_get_tools

    return True
