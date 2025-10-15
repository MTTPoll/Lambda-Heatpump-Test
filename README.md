
# Lambda Heatpump Test (Home Assistant)

**Test-/Parallel-Integration** zur originalen *Lambda Heatpump* Integration – mit umschaltbarer Word-Order (Big/Little) je nach Baujahr (vor/ab 2025).

## Was ist anders?
- Beim Setup wirst du gefragt: **„Wurde das Gerät vor 2025 eingebaut?“**
  - **Ja → Big-Endian** (MSW zuerst; kompatibel mit Anlagen **vor 2025**)
  - **Nein → Little-Endian** (LSW zuerst; kompatibel mit Anlagen **ab 2025**)
- **Alle Sensoren** aus der Original-Integration sind enthalten.
- Eigene Domain: **`lambda_heatpump_test`** (überschneidet sich nicht mit der Originalen).

## Installation
### Manuell
1. ZIP herunterladen und entpacken.
2. Den Ordner `custom_components/lambda_heatpump_test` nach `<config>/custom_components/` kopieren.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → „Lambda Heatpump Test“**.
5. IP, Intervall & **vor/ab 2025** wählen.

> Du kannst die originale `lambda_heatpump` Integration parallel behalten. Diese Test-Integration verwendet eine **eigene Domain**.

## HACS
Ein HACS-Manifest (`hacs.json`) liegt bei. Für die Nutzung über HACS muss ein passendes GitHub-Repository existieren
(z. B. `route662/Lambda-Heatpump-Test`). Danach kann dieses Repo als **Custom Repository** eingebunden werden.

## Hinweise
- 32‑Bit‑Register (z. B. 1020–1023) werden abhängig von der Auswahl **Big/Little** zusammengesetzt.
- Skalierung, Präzision, `description_map` etc. stammen aus der eingebetteten Sensorliste.

## Lizenz
Siehe **LICENSE** (GPL‑3.0).
