import pandas as pd
import re
import os

# --- Zu reinigende Dateien ---
files = [
    ("./newData/cards_data.csv", "./newData/cleaned_cards_data.csv"),
    ("./newData/users_data.csv", "./newData/cleaned_users_data.csv"),
    ("./newData/transactions_data.csv", "./newData/cleaned_transactions_data.csv"),
]

# --- Datums und Uhrzeit Check ---
def is_date_or_time(value):
    value = str(value).strip()
    date_patterns = [
        r"\d{1,2}\.\d{1,2}\.\d{2,4}",     # 12.05.2023 oder 1.1.23
        r"\d{4}-\d{1,2}-\d{1,2}",         # 2023-05-12
        r"\d{1,2}:\d{2}(:\d{2})?",        # 14:30 oder 14:30:00
        r"\d{1,2}/\d{4}",                 # 06/2025
    ]
    return any(re.fullmatch(p, value) for p in date_patterns)

# --- Extract unit ---
def get_unit(value):
    if is_date_or_time(value):
        return ''
    value_str = str(value).strip()
    match = re.search(r'^[-+]?[\s]*([$€a-zA-Z%]+)?\s*[\d\.,]+\s*([$€a-zA-Z%]+)?$', value_str)
    if match:
        groups = match.groups()
        for g in groups:
            if g and re.match(r'[$€a-zA-Z%]+', g):
                return g
    return ''

# --- Units entfernen aber "-" behalten ---
def remove_unit_and_sign(value):
    value_str = str(value).strip()

    if is_date_or_time(value_str):
        return value  # Datum/Uhrzeit bleibt

    # Entferne führende oder folgende Einheiten
    value_no_unit = re.sub(r'(^[\s]*[-+]?[\$€a-zA-Z%]+[\s]*)|([\s]*[\$€a-zA-Z%]+[\s]*$)', '', value_str)

    # '+' entfernen
    if value_no_unit.startswith('+'):
        value_no_unit = value_no_unit[1:]

    try:
        return float(value_no_unit.replace(",", "."))  # Komma zu Punkt
    except ValueError:
        return value  # Falls Umwandlung fehlschlägt

# --- Hauptschleife für alle Dateien ---
for input_path, output_path in files:
    if not os.path.exists(input_path):
        print(f"Datei nicht gefunden: {input_path}")
        continue

    print(f"\nBearbeite Datei: {input_path}")
    data = pd.read_csv(input_path, sep=",", encoding="utf8")
    found_units = {}

    for column in data.columns:
        units = set()
        for value in data[column][1:]:  # erste Zeile überspringen
            unit = get_unit(value)
            if unit:
                units.add(unit)

        if len(units) == 1:
            found_unit = units.pop()
            found_units[column] = found_unit
            print(f"Einheit in Spalte '{column}': '{found_unit}'")
            data[column] = data[column].apply(remove_unit_and_sign)
        elif len(units) > 1:
            print("Mehr als eine Einheit in Spalte " + column + ":")
            print(units)
        else:
            print("Keine Einheit gefunden in Spalte " + column + ".")

    # --- Speichere bereinigte CSV ---
    data.to_csv(output_path, index=False, encoding="utf8")
    print(f"Bereinigte CSV gespeichert unter: {output_path}")