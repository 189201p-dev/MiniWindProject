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
import sqlite3

# ====== EINSTELLUNGEN ======
API_KEY = "f87b00c85ff05f451f2e6974191cee9a"

RADIUS = 50.0
C_P = 0.45
INTERVAL_HOURS = 3
CUT_IN = 3
RATED_SPEED = 12
CUT_OFF = 25
MAX_POWER = 3_000_000

# ====== DATENBANK ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "wind_data.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER,
    period TEXT,
    filename TEXT,
    generated_at DATETIME,
    start_dt DATETIME,
    end_dt DATETIME
)
""")

conn.commit()

# ====== LUFTDICHTE ======
def air_density(temp_c, humidity, pressure_hpa):
    T = temp_c + 273.15  # Temperatur in Kelvin
    phi = humidity / 100.0  # relative Luftfeuchtigkeit
    P = pressure_hpa * 100  # Druck in Pascal
    p_sat = 610.78 * math.exp(17.27 * temp_c / (temp_c + 237.3))
    p_v = phi * p_sat  # Dampfdruck
    p_d = P - p_v      # trockene Luft
    return p_d / (287.05 * T) + p_v / (461.5 * T)

# ====== LEISTUNG ======
def calculate_power(v, rho, area):
    if v < CUT_IN or v > CUT_OFF:
        return 0
    elif v <= RATED_SPEED:
        return 0.5 * rho * area * C_P * v**3
    else:
        rated_power = 0.5 * rho * area * C_P * RATED_SPEED**3
        return min(rated_power, MAX_POWER)

# ====== WETTERDATEN ======
def get_weather(city):
    try:
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
        geo_data = requests.get(geo_url).json()
        lat, lon = geo_data[0]['lat'], geo_data[0]['lon']

        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
        data = requests.get(url).json()

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

    except Exception:
        messagebox.showwarning("Warnung", "API nicht verfügbar → Zufallsdaten werden verwendet")
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

# ====== PDF ======
def generate_pdf(city, period, data, times, energy, total_energy, fake=False):
    base_path = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(base_path, "WindReports")
    os.makedirs(save_path, exist_ok=True)

    start_date = data[0]['dt'].strftime("%d-%m")
    end_date = data[-1]['dt'].strftime("%d-%m")

    filename = os.path.join(
        save_path,
        f"{city.capitalize()}_{period.replace(' ','_')}_{start_date}_{end_date}.pdf"
    )

    with PdfPages(filename) as pdf:

        # Seite 1: Vollständiger Bericht
        fig1 = plt.figure(figsize=(12,8))
        plt.axis('off')

        text = (
            "BERICHT WINDENERGIE\n\n"
            f"Stadt: {city}\n"
            f"Periode: {period}\n"
            f"Datenquelle: {'Simuliert' if fake else 'Real'}\n"
            f"Zeitraum: {start_date} - {end_date}\n\n"
            "Windturbinen-Parameter:\n"
            f"- Rotorradius: {RADIUS} m\n"
            f"- Wirkungsgrad (Cp): {C_P}\n"
            f"- Startgeschwindigkeit (Cut-in): {CUT_IN} m/s\n"
            f"- Nennwindgeschwindigkeit (Rated): {RATED_SPEED} m/s\n"
            f"- Abschaltgeschwindigkeit (Cut-off): {CUT_OFF} m/s\n"
            f"- Maximale Leistung: {MAX_POWER/1_000_000} MW\n\n"
            f"Gesamtenergie: {round(total_energy,2)} kWh"
        )

        plt.text(0.05, 0.5, text, fontsize=12)
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

        # Tabelle
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

    cursor.execute("INSERT OR IGNORE INTO cities (name) VALUES (?)", (city,))
    conn.commit()
    cursor.execute("SELECT id FROM cities WHERE name=?", (city,))
    city_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO reports (city_id, period, filename, generated_at, start_dt, end_dt)
        VALUES (?,?,?,?,?,?)
    """, (
        city_id,
        period,
        filename,
        datetime.now().isoformat(),
        data[0]['dt'].isoformat(),
        data[-1]['dt'].isoformat()
    ))
    conn.commit()

    messagebox.showinfo("Fertig", f"Bericht erstellt:\n{filename}")

# ====== HAUPTFUNKTION ======
def calculate_energy():
    city = city_entry.get().strip()
    period = period_var.get()

    if not city:
        messagebox.showerror("Fehler", "Bitte Stadt eingeben")
        return

    data, fake = get_weather(city)
    data = filter_period(data, period)

    area = math.pi * RADIUS**2
    total_energy = 0
    times = []
    energy = []

    for d in data:
        P = calculate_power(d['wind'], d['rho'], area)
        E = P * INTERVAL_HOURS / 1000
        total_energy += E
        times.append(d['dt'])
        energy.append(E)

    generate_pdf(city, period, data, times, energy, total_energy, fake)

# ====== GUI ======
root = tk.Tk()
root.title("Windturbinen Bericht Generator")
root.geometry("350x200")
root.resizable(False, False)

frame = tk.Frame(root, padx=15, pady=15)
frame.pack()

tk.Label(frame, text="Windenergie Bericht", font=("Arial", 14, "bold")).grid(row=0, columnspan=2, pady=10)

tk.Label(frame, text="Stadt:").grid(row=1, column=0, sticky="w")
city_entry = tk.Entry(frame)
city_entry.insert(0, "Berlin")
city_entry.grid(row=1, column=1)

tk.Label(frame, text="Zeitraum:").grid(row=2, column=0, sticky="w")
period_var = tk.StringVar(value="Heute")
ttk.Combobox(frame, textvariable=period_var,
             values=["Heute", "3 Tage", "5 Tage"],
             state="readonly").grid(row=2, column=1)

tk.Button(frame, text="Bericht erstellen", command=calculate_energy)\
    .grid(row=3, columnspan=2, pady=15)

root.mainloop()