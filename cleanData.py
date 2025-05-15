import pandas as pd
import re

# --- Read in data --- man muss nur Dateinamen ändern
input_path = "C:/Users/skugl/Documents/HFT/WIP2/finance_dashboard/user_data.csv"
output_path = "C:/Users/skugl/Documents/HFT/WIP2/finance_dashboard/cleaned_user_data.csv"

transaction_data = pd.read_csv(input_path, sep=",", encoding="utf8")

# --- Check if value looks like a date or time ---
def is_date_or_time(value):
    value = str(value).strip()
    date_patterns = [
        r"\d{1,2}\.\d{1,2}\.\d{2,4}",     # z. B. 12.05.2023 oder 1.1.23
        r"\d{4}-\d{1,2}-\d{1,2}",         # z. B. 2023-05-12
        r"\d{1,2}:\d{2}(:\d{2})?",        # z. B. 14:30 oder 14:30:00
    ]
    return any(re.fullmatch(p, value) for p in date_patterns)

# --- Extract unit (either at start or end) ---
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

# --- Remove unit and '+' sign (but keep '-') ---
def remove_unit_and_sign(value):
    value_str = str(value).strip()

    if is_date_or_time(value_str):
        return value  # Datum/Uhrzeit bleibt

    # Entferne führende oder folgende Einheiten inkl. optionalem Vorzeichen
    value_no_unit = re.sub(r'(^[\s]*[-+]?[\$€a-zA-Z%]+[\s]*)|([\s]*[\$€a-zA-Z%]+[\s]*$)', '', value_str)

    # '+' entfernen, '-' beibehalten
    if value_no_unit.startswith('+'):
        value_no_unit = value_no_unit[1:]

    try:
        return float(value_no_unit.replace(",", "."))  # Komma zu Punkt
    except ValueError:
        return value  # Falls Umwandlung fehlschlägt

# --- Spaltenverarbeitung ---
found_units = {}

for column in transaction_data.columns:
    units = set()
    for value in transaction_data[column][1:]:  # erste Zeile überspringen
        unit = get_unit(value)
        if unit:
            units.add(unit)

    if len(units) == 1:
        found_unit = units.pop()
        found_units[column] = found_unit
        print(f"Einheit in Spalte '{column}': '{found_unit}'")
        transaction_data[column] = transaction_data[column].apply(remove_unit_and_sign)
    elif len(units) > 1:
        print("Mehr als eine Einheit in Spalte " + column + ":")
        print(units)
    else:
        print("Keine Einheit gefunden in Spalte " + column + ".")

# --- Dropdown-Spalten (z. B. für x-/y-Achsen) ---
column_titles_with_num = list(found_units.keys())

# --- Speichere bereinigte CSV ---
transaction_data.to_csv(output_path, index=False, encoding="utf8")
print(f"Bereinigte CSV gespeichert unter: {output_path}")