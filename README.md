# EGD Power Data

A Home Assistant integration for retrieving daily electricity consumption and generation data from EGD Distribuce. It uses the `egd_power_data` domain and is configured through the Home Assistant UI.

## Installation and setup

Add the integration in Home Assistant under **Settings → Devices & services → Add integration → EGD Power Data**. Enter the Client ID, Client Secret, and your consumption EAN from the Distribuce24 portal. If you have separate consumption and generation EANs, use the consumption EAN, which provides both profiles.

When migrating from the original `egdczpowerdata` integration, remove its YAML configuration (`sensor: - platform: egdczpowerdata`) and remove the old integration first. The new integration uses a different domain, so its settings are not migrated automatically. Then add EGD Power Data through the UI.

## Data updates

Consumption and generation are fetched together once per update cycle, every hour by default. Home Assistant manages updates for both entities; no status sensor or `homeassistant.update_entity` automation is needed.

The integration creates two sensors:

- **Consumption** (`ICC1`) — daily consumption for the previous day.
- **Generation** (`ISC1`) — daily generation for the previous day.

The measured period is available in each sensor's attributes.

## Troubleshooting

When reporting an issue, include the Home Assistant logs for `custom_components.egd_power_data`. The integration does not write a separate `/config/egddistribuce.log` file and does not log access tokens or the client secret.
