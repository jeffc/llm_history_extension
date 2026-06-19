# LLM History & Entity ID Extension

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badgelink.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jeffc&repository=llm_history_extension&category=integration)

A Home Assistant custom integration that enhances the Large Language Model (LLM) Assist API with dynamic state history queries and entity ID matching capabilities.

## Features

1. **Entity ID Exposure**:
   Injects the `entity_id` directly into the exposed entity metadata lists sent to LLMs (both in the static prompt context and the `GetLiveContext` tool). This allows the LLM to refer to entities by their exact `entity_id` rather than relying on loose name matching.
   
2. **`GetHistory` Tool**:
   Registers a new native LLM tool that allows LLMs to query the state history of one or more exposed entities over a specified period. The tool formats changes compactly as YAML with human-readable timestamps adjusted to your local timezone.

---

## Installation

### Method 1: HACS (Recommended)

1. Click the button below to add this repository directly to HACS:
   
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badgelink.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jeffc&repository=llm_history_extension&category=integration)
   
2. Or go to **HACS** -> **Integrations**, click the three dots in the top right, select **Custom repositories**, and add:
   * **Repository**: `https://github.com/jeffc/llm_history_extension`
   * **Category**: `Integration`
3. Click **Download** on the integration card.
4. Restart Home Assistant.

### Method 2: Manual

1. Download the source code.
2. Copy the `custom_components/llm_history_extension` directory into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration & Setup

Once installed, you can set up the integration either through the Home Assistant user interface or via your `configuration.yaml` file.

### Method 1: Via the User Interface (Recommended)

1. Navigate to **Settings** -> **Devices & Services** in Home Assistant.
2. Click **+ Add Integration** in the bottom right.
3. Search for **LLM History & Entity ID Extension** and select it.
4. Confirm the installation. No extra options are required!

### Method 2: Via `configuration.yaml`

Simply add the integration's domain to your `configuration.yaml` file:

```yaml
llm_history_extension:
```

After adding the configuration line, restart Home Assistant to load the integration.

The integration will automatically run its setup, apply the patches to the Assist API in memory, and register the `GetHistory` tool.

---

## Technical Details

This integration operates by hot-patching core LLM helpers at runtime:
* Overrides `llm._get_exposed_entities` to map `entity_id` values to LLM contexts.
* Intercepts `llm.AssistAPI._async_get_tools` to register the `GetHistory` tool dynamically when exposed entities are present.
