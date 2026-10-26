# EGD Power Data

Samostatná Home Assistant integrace pro načítání denní spotřeby a výroby z EGD Distribuce. Integrace používá vlastní doménu `egd_power_data` a konfiguraci přes uživatelské rozhraní.

## Instalace a nastavení

Integraci přidejte v Home Assistantu přes **Nastavení → Zařízení a služby → Přidat integraci → EGD Power Data**. Zadejte Client ID, Client Secret a spotřební EAN z portálu Distribuce24. Pokud máte spotřební i výrobní EAN, použijte spotřební EAN.

Pokud přecházíte z původní `egdczpowerdata`, nejprve odstraňte starou YAML konfiguraci z `configuration.yaml` a původní integraci. Nová integrace má vlastní doménu a nastavení se nepřenáší automaticky. Poté ji přidejte přes uživatelské rozhraní.

## Aktualizace dat

Spotřeba a výroba se načítají společně jedním aktualizačním cyklem, standardně jednou za hodinu. Aktualizaci obou entit řídí Home Assistant; není potřeba status senzor ani automatizace `homeassistant.update_entity`.

Integrace vytváří dvě entity:

- **Spotřeba** (`ICC1`) – denní spotřeba za předchozí den.
- **Výroba** (`ISC1`) – denní výroba za předchozí den.

Časové údaje o načteném období jsou dostupné v atributech senzorů.

## Problémy

Při hlášení problému přiložte záznamy z Home Assistantu pro `custom_components.egd_power_data`. Integrace nepíše samostatný soubor `/config/egddistribuce.log` a nezapisuje přístupové tokeny ani klientský secret do logu.
