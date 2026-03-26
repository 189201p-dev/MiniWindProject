import requests
from datetime import datetime, timedelta, timezone
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import math
import os
import random
import sys

# ====== EINSTELLUNGEN ======
API_KEY = "f87b00c85ff05f451f2e6974191cee9a"

# Windturbinen-Parameter
RADIUS = 50.0  # m
C_P = 0.45
INTERVAL_HOURS = 3  # Stunden pro Vorhersage-Schritt
CUT_IN = 3
RATED_SPEED = 12
CUT_OFF = 25
MAX_POWER = 3_000_000  # Watt

# ====== LUFTDICHTE ======
def air_density(temp_c, humidity, pressure_hpa):
    """
    Berechnet die Luftdichte ρ [kg/m³] unter Berücksichtigung von Temperatur, Luftfeuchtigkeit und Druck.
    temp_c: Temperatur in Grad Celsius
    humidity: relative Luftfeuchtigkeit in %
    pressure_hpa: Luftdruck in hPa
    """
    T = temp_c + 273.15  # Temperatur in Kelvin
    phi = humidity / 100.0  # relative Luftfeuchtigkeit in Bruch
    P = pressure_hpa * 100  # Druck von hPa zu Pa umrechnen
    p_sat = 610.78 * math.exp(17.27 * temp_c / (temp_c + 237.3))  # Sättigungsdampfdruck
    p_v = phi * p_sat  # Partialdruck des Wasserdampfs
    p_d = P - p_v      # Partialdruck der trockenen Luft
    return p_d / (287.05 * T) + p_v / (461.5 * T)  # Luftdichte ρ berechnen

# ====== WETTERDATEN ======
def get_weather(city):
    try:
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
        geo_data = requests.get(geo_url).json()
        if not geo_data:
            raise Exception("Stadt nicht gefunden")
        lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
        data = requests.get(url).json()
        if 'list' not in data:
            raise Exception("API-Fehler")
        tz_offset = data['city']['timezone']
        result = []
        for entry in data['list']:
            dt = datetime.fromtimestamp(entry['dt'], tz=timezone.utc) + timedelta(seconds=tz_offset)
            temp = entry['main']['temp']
            humidity = entry['main']['humidity']
            pressure = entry['main']['pressure']
            wind = entry['wind']['speed']
            rho = air_density(temp, humidity, pressure)
            result.append({'dt': dt, 'wind': wind, 'rho': rho, 'temp': temp, 'humidity': humidity})
        return result, False
    except Exception as e:
        messagebox.showwarning("Warnung", f"Wetterdaten nicht verfügbar, generiere Zufallsdaten.\n{e}")
        fake_data = []
        now = datetime.now()
        for i in range(40):
            dt = now + timedelta(hours=3*i)
            wind = random.uniform(3,15)
            temp = random.uniform(-5,25)
            humidity = random.randint(20,90)
            pressure = random.randint(980,1050)
            rho = air_density(temp, humidity, pressure)
            fake_data.append({'dt': dt, 'wind': wind, 'rho': rho, 'temp': temp, 'humidity': humidity})
        return fake_data, True

# ====== PERIODENFILTER ======
def filter_period(data, period):
    if period == "Heute":
        return data[:8]
    elif period == "3 Tage":
        return data[:24]
    elif period == "5 Tage":
        return data[:40]
    return data

# ====== LEISTUNG ======
def calculate_power(v, rho, area):
    """
    Berechnet die Leistung einer Windturbine [Watt] basierend auf Windgeschwindigkeit v [m/s],
    Luftdichte rho [kg/m³] und Rotorfläche area [m²].
    Berücksichtigt Cut-in, Rated und Cut-off Geschwindigkeiten sowie maximale Leistung.
    """
    if v < CUT_IN or v > CUT_OFF:
        return 0  # Kein Betrieb unter Cut-in oder über Cut-off
    elif v <= RATED_SPEED:
        # Leistung proportional zu v³ im Bereich unter Nennwindgeschwindigkeit
        return 0.5 * rho * area * C_P * v**3
    else:
        # Leistung ab Nennwindgeschwindigkeit konstant (Rated Power), max. MAX_POWER
        rated_power = 0.5 * rho * area * C_P * RATED_SPEED**3
        return min(rated_power, MAX_POWER)

# ====== PDF BERICHT ======
def generate_pdf(city, period, data, times, energy, total_energy, fake=False):
    # Bestimmt das Basisverzeichnis neben der exe oder dem Skript
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    save_path = os.path.join(base_path, "WindReports")
    os.makedirs(save_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_formatted = city.strip().capitalize()
    period_formatted = period.replace(" ","_")
    filename = os.path.join(save_path, f"{city_formatted}_{period_formatted}_{timestamp}.pdf")

    with PdfPages(filename) as pdf:
        # Seite 1: Textbericht
        fig1 = plt.figure(figsize=(12,8))
        plt.axis('off')
        text = (
            "BERICHT WINDENERGIE\n\n"
            f"Stadt: {city_formatted}\nPeriode: {period}\n"
            f"Datenquelle: {'Simuliert' if fake else 'Real'}\n\n"
            "Windturbinen-Parameter:\n"
            f"- Rotorradius: {RADIUS} m\n"
            f"- Wirkungsgrad (Cp): {C_P}\n"
            f"- Startgeschwindigkeit (Cut-in): {CUT_IN} m/s\n"
            f"- Nennwindgeschwindigkeit (Rated): {RATED_SPEED} m/s\n"
            f"- Abschaltgeschwindigkeit (Cut-off): {CUT_OFF} m/s\n"
            f"- Maximale Leistung: {MAX_POWER/1_000_000} MW\n\n"
            f"Gesamtenergie: {round(total_energy,2)} kWh"
        )
        plt.text(0.05,0.5,text, fontsize=12)
        pdf.savefig(fig1)
        plt.close()

        # Seite 2: Graph
        fig2 = plt.figure(figsize=(12,8))
        plt.plot(times, energy, marker='o')
        plt.title("Erzeugte Energie (kWh)")
        plt.xlabel("Zeit")
        plt.ylabel("kWh")
        plt.grid(True)
        pdf.savefig(fig2)
        plt.close()

        # Seiten 3+: Wetterdaten Tabelle
        rows_per_page = 25
        for start in range(0, len(data), rows_per_page):
            fig3 = plt.figure(figsize=(12,10))
            plt.axis('off')
            table_data = []
            for d, e in zip(data[start:start+rows_per_page], energy[start:start+rows_per_page]):
                table_data.append([
                    d['dt'].strftime("%d-%m %H:%M"),
                    round(d['wind'],1),
                    round(d['temp'],1),
                    d['humidity'],
                    round(e,2)
                ])
            columns = ["Zeit", "Wind m/s", "Temp °C", "Luftfeuchtigkeit %", "kWh"]
            table = plt.table(cellText=table_data, colLabels=columns, loc='center')
            table.scale(1,1.5)
            pdf.savefig(fig3)
            plt.close()

    os.startfile(filename)
    messagebox.showinfo("Fertig", f"PDF Bericht erstellt:\n{filename}")

# ====== HAUPTFUNKTION ======
def calculate_energy():
    city = city_entry.get().strip()
    period = period_var.get()
    if not city:
        messagebox.showerror("Fehler", "Bitte Stadt eingeben")
        return
    data, fake = get_weather(city)
    if not data:
        return
    data = filter_period(data, period)
    area = math.pi * RADIUS**2
    times = []
    energy = []
    total_energy = 0
    for d in data:
        P = calculate_power(d['wind'], d['rho'], area)
        E = P * INTERVAL_HOURS / 1000
        total_energy += E
        times.append(d['dt'])
        energy.append(E)
    generate_pdf(city, period, data, times, energy, total_energy, fake=fake)

# ====== GUI ======
root = tk.Tk()
root.title("Windturbinen-Bericht Generator")

tk.Label(root, text="Stadt:").grid(row=0, column=0, padx=5, pady=5)
city_entry = tk.Entry(root)
city_entry.insert(0, "Berlin")
city_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Periode:").grid(row=1, column=0, padx=5, pady=5)
period_var = tk.StringVar(value="Heute")
ttk.Combobox(root, textvariable=period_var,
             values=["Heute","3 Tage","5 Tage"],
             state="readonly").grid(row=1, column=1, padx=5, pady=5)

tk.Button(root, text="PDF Bericht erstellen", command=calculate_energy)\
    .grid(row=2, column=0, columnspan=2, pady=10)

root.mainloop()
