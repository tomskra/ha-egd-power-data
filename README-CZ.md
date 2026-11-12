# EGD Power Data

Samostatná Home Assistant integrace pro načítání denní spotřeby a výroby z EGD Distribuce. Integrace používá vlastní doménu `egd_power_data` a konfiguraci přes uživatelské rozhraní.

## Instalace a nastavení

Integraci přidejte v Home Assistantu přes **Nastavení → Zařízení a služby → Přidat integraci → EGD Power Data**. Zadejte Client ID, Client Secret a spotřební EAN z portálu Distribuce24. Pokud máte spotřební i výrobní EAN, použijte spotřební EAN.

Pokud přecházíte z původní `egdczpowerdata`, nejprve odstraňte starou YAML konfiguraci z `configuration.yaml` a původní integraci. Nová integrace má vlastní doménu a nastavení se nepřenáší automaticky. Poté ji přidejte přes uživatelské rozhraní.

## Aktualizace dat

Spotřeba a výroba se načítají společně při spuštění integrace a potom jednou denně v 17:13 (místní čas Home Assistantu). Senzory zobrazují data za předchozí kalendářní den; datum najdete také v jejich atributu `data_date`. EG.D aktualizuje naměřená data jednou denně odpoledne a časté dotazování může API přetížit. Aktualizaci všech entit řídí Home Assistant; není potřeba status senzor ani automatizace `homeassistant.update_entity`.

Integrace vytváří tyto entity:

- **Spotřeba** (`ICQ2`) – denní energie odebraná ze sítě, načtená přímo z čtvrthodinového energetického profilu v kWh.
- **Výroba** (`ISQ2`) – denní energie dodaná do sítě, načtená přímo z čtvrthodinového energetického profilu v kWh.
- **Sdílená spotřeba** (`ICCS`) – dostupná pouze tehdy, pokud EG.D tento profil pro odběrné místo vrací.

Časové údaje o období, minimum a maximum čtvrthodinové hodnoty, počet záznamů a stavové kódy jsou v atributech senzorů. Prázdný profil se zobrazí jako `unknown`, nikoli jako nula.

## Problémy

Při hlášení problému přiložte záznamy z Home Assistantu pro `custom_components.egd_power_data`. Pro podrobné čtvrthodinové odpovědi API zapněte debug logování integrace. Logy mohou obsahovat naměřené hodnoty a časové značky; identifikátory odběrného místa, tokeny ani klientský secret se nezapisují. Integrace nepíše samostatný soubor `/config/egddistribuce.log`.
