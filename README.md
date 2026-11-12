# EGD Power Data

A Home Assistant integration for retrieving daily electricity consumption and generation data from EGD Distribuce. It uses the `egd_power_data` domain and is configured through the Home Assistant UI.

## Installation and setup

Add the integration in Home Assistant under **Settings → Devices & services → Add integration → EGD Power Data**. Enter the Client ID, Client Secret, and your consumption EAN from the Distribuce24 portal. If you have separate consumption and generation EANs, use the consumption EAN, which provides both profiles.

When migrating from the original `egdczpowerdata` integration, remove its YAML configuration (`sensor: - platform: egdczpowerdata`) and remove the old integration first. The new integration uses a different domain, so its settings are not migrated automatically. Then add EGD Power Data through the UI.

## Data updates

Consumption and generation are fetched together at setup and then once daily at 17:13 (Home Assistant's local time). The sensors show data for the previous calendar day; the date is also available in the `data_date` attribute. EGD updates meter data once per day in the afternoon; frequent polling can overload the API. Home Assistant manages updates for all entities; no status sensor or `homeassistant.update_entity` automation is needed.

The integration creates these sensors:

- **Consumption** (`ICQ2`) — daily energy drawn from the grid, read directly from the quarter-hour energy profile in kWh.
- **Generation** (`ISQ2`) — daily energy delivered to the grid, read directly from the quarter-hour energy profile in kWh.
- **Consumption covered by the leading metering point** (`ICCS`) — only for metering points sharing electricity within an apartment building. This is not the commercial/distribution sharing data shown in Distribuce24; those profiles are not exposed by the OpenAPI.

The measured period, interval minimum and maximum, record count, and reading statuses are available in each sensor's attributes. Empty profiles are shown as `unknown` rather than zero.

## Troubleshooting

When reporting an issue, include the Home Assistant logs for `custom_components.egd_power_data`. Enable debug logging for this integration to include the quarter-hour API responses. Logs may contain measured values and timestamps; metering point identifiers, access tokens, and the client secret are not logged. The integration does not write a separate `/config/egddistribuce.log` file.
