# EGD Power Data

Samostatná Home Assistant integrace pro načítání denní spotřeby a výroby z EGD Distribuce. Konfigurace probíhá výhradně přes uživatelské rozhraní.

Přidejte ji v **Nastavení → Zařízení a služby → Přidat integraci → EGD Power Data**. Zadejte Client ID, Client Secret a spotřební EAN z portálu Distribuce24. Při přechodu ze staré integrace nejprve odstraňte její YAML konfiguraci `sensor: - platform: egdczpowerdata`; nastavení se nepřenáší automaticky.

Spotřeba (`ICC1`) a výroba (`ISC1`) se načítají společně jednou za hodinu. Status senzor ani automatizace pro ruční aktualizaci nejsou potřeba.
