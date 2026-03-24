Windturbinen-Bericht Generator
==============================

Beschreibung:
-------------
Dieses kleine Programm erstellt PDF-Berichte über die erzeugte Energie
einer Windturbine basierend auf Wetterdaten (real oder simuliert).

Funktionen:
-----------
- Eingabe der Stadt
- Auswahl des Zeitraums: Heute, 3 Tage, 5 Tage
- Berechnung der erzeugten Energie basierend auf Windgeschwindigkeit, Luftdichte etc.
- Speicherung des Berichts als PDF in der Unterordner "WindReports"
- Automatische Erstellung des Ordners "WindReports", falls er nicht existiert
- Mehrseitige PDF, wenn die Daten nicht auf eine Seite passen
- Nutzung von simulierten Daten, falls API-Daten nicht verfügbar sind

Installation und Start:
----------------------
1. Stelle sicher, dass Python 3.x installiert ist
2. Installiere die benötigten Pakete:
   pip install requests matplotlib
3. Öffne die Datei main.pyw per Doppelklick, kein Konsolenfenster wird angezeigt
4. Gib die Stadt ein und wähle den Zeitraum aus
5. Klicke auf "PDF Bericht erstellen"
6. Die PDF wird automatisch in WindReports gespeichert und geöffnet

Hinweise:
---------
- Falls OpenWeatherMap API nicht erreichbar ist, werden Zufallsdaten genutzt
- Die PDF-Datei wird benannt nach Stadt und Zeitraum, z.B. berlin_3_Tage_20260323_1425.pdf
- Nur deutsche Sprache unterstützt

Windturbinen-Parameter:
-----------------------
- Rotorradius: 50 m
- Wirkungsgrad (Cp): 0.45
- Startgeschwindigkeit (Cut-in): 3 m/s
- Nennwindgeschwindigkeit (Rated): 12 m/s
- Abschaltgeschwindigkeit (Cut-off): 25 m/s
- Maximale Leistung: 3 MW