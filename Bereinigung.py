import json
import csv

# Pfade
json_datei = "/Users/nursahmisirlioglu/Desktop/Wirtschaftsprojekt/Projekt/train_fraud_labels.json"
csv_pfad = "/Users/nursahmisirlioglu/Desktop/Wirtschaftsprojekt/Projekt/transactions_data.csv"
csv_ausgabe_pfad = "/Users/nursahmisirlioglu/Desktop/Wirtschaftsprojekt/Projekt/transactions_data_gefiltert.csv"

# 1. JSON laden und alle IDs mit "ja" sammeln
with open(json_datei, 'r') as datei:
    daten = json.load(datei)

ids_ja = set()
if 'target' in daten:
    ids_ja = {nummer for nummer, wert in daten['target'].items() if wert.lower() == "yes"}
    print(f"Anzahl der 'ja'-IDs in JSON: {len(ids_ja)}")
else:
    print('"target" nicht in der JSON-Datei gefunden.')

# 2. CSV lesen und Zeilen filtern
#    Annahme: Die erste Spalte (index 0) der CSV enthält die IDs, die mit JSON übereinstimmen
gefilterte_zeilen = []

with open(csv_pfad, mode='r', newline='') as csv_file:
    reader = csv.reader(csv_file)
    header = next(reader)
    gefilterte_zeilen.append(header)  # Header mitnehmen

    for row in reader:
        # Prüfen, ob die ID (erste Spalte) NICHT in ids_ja ist
        # Wenn ja, diese Zeile überspringen (also entfernen)
        if row[0] not in ids_ja:
            gefilterte_zeilen.append(row)

print(f"Anzahl der Zeilen nach Filterung: {len(gefilterte_zeilen) - 1}")  # ohne Header

# 3. Gefilterte CSV-Daten speichern
with open(csv_ausgabe_pfad, mode='w', newline='') as csv_out:
    writer = csv.writer(csv_out)
    writer.writerows(gefilterte_zeilen)

print(f"Gefilterte CSV wurde gespeichert unter: {csv_ausgabe_pfad}")




  
    

    










#git pull (immer am anfang!!!!!)

#git add .
#git commit -m "befehl- was gemacht"
#git push (ende)
