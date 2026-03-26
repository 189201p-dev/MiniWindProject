# Windturbinen-Bericht Generator

## Beschreibung
Dieses Programm erstellt PDF-Berichte über die erzeugte Energie einer Windturbine basierend auf Wetterdaten (real oder simuliert).  
Die Berechnung basiert auf physikalischen Modellen der Windenergie und berücksichtigt unter anderem Windgeschwindigkeit, Luftdichte sowie den Wirkungsgrad der Turbine.

Die Luftdichte wird unter Berücksichtigung von Temperatur, Luftfeuchtigkeit und Luftdruck berechnet, was eine realistischere Simulation ermöglicht.

Die Leistung der Windturbine wird mit der Standardformel der Windenergie berechnet und durch den Leistungsbeiwert (Cp) begrenzt. Dabei wird das physikalische Maximum gemäß dem Betz-Gesetz berücksichtigt.

## Funktionen
- Eingabe der Stadt  
- Auswahl des Zeitraums: Heute, 3 Tage, 5 Tage  
- Automatische Abfrage von Wetterdaten über API (OpenWeather)  
- Fallback auf realistische Zufallsdaten bei API-Fehlern  
- Berechnung der Luftdichte unter Berücksichtigung von:
  - Temperatur  
  - Luftfeuchtigkeit  
  - Luftdruck  
- Berechnung der Windleistung nach physikalischem Modell:  P=0.5⋅ρ⋅A⋅Cp​⋅v3  
- Begrenzung der Leistung durch:
  - Nennleistung (Rated Power)  
  - Cut-in / Cut-off Bedingungen  
- Berechnung der erzeugten Energie in kWh  
- Erstellung eines mehrseitigen PDF-Berichts mit:
  - Zusammenfassung  
  - Graph (Energieverlauf)  
  - Tabelle mit Wetterdaten und Energie  
- Automatische Speicherung im Ordner **WindReports**  
- Automatische Erstellung des Ordners, falls nicht vorhanden  
- Dateiname enthält Zeitraum (z.B. `Berlin_3_Tage_26-03_28-03.pdf`)  

### Optionale Datenbank-Anbindung
- Speicherung der erzeugten Berichte in einer SQLite- oder CSV-Datenbank  
- Möglichkeit, auf historische Berichte zuzugreifen (z.B. Berlin gestern vs. heute)  
- Erleichtert Analyse über mehrere Zeiträume  
- Tabellen könnten enthalten:
  - Stadt  
  - Zeitraum  
  - Datum der Erstellung  
  - Gesamtenergie (kWh)  
  - Datenquelle (Real / Simuliert)  
  - Pfad zur PDF-Datei  

## Installation und Start
1. Stelle sicher, dass Python 3.x installiert ist  
2. Installiere die benötigten Pakete:  
   ```bash
   pip install requests matplotlib
