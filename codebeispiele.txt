import json
import csv

# Pfad zur JSON-Datei
json_datei = "/Users/nursahmisirlioglu/Desktop/Wirtschaftsprojekt/Projekt/train_fraud_labels.json"

# Pfad zur CSV-Datei
csv_pfad = "/Users/nursahmisirlioglu/Desktop/Wirtschaftsprojekt/Projekt/transactions_data.csv"


#die ersten 500 aus er csv datei 

# Die ersten 500 Zeilen lesen und ausgeben
with open(csv_pfad, mode='r', newline='') as csv_file:
    reader = csv.reader(csv_file)
    header = next(reader)  # Spaltenüberschrift lesen
    print(header)

    for i, row in enumerate(reader):
        if i >= 500:
            break
        print(row)

# JSON-Datei laden
with open(json_datei, 'r') as datei:
    daten = json.load(datei)  # ← HIER wird "daten" definiert


    # Nur die Nummern mit "Yes" sammeln und sortieren
nummern_mit_yes = []
if 'target' in daten:
    nummern_mit_yes = [nummer for nummer, wert in daten['target'].items() if wert == "nein"]
    nummern_mit_yes = sorted(nummern_mit_yes, key=int)

    # Die ersten 10 Nummern ausgeben
    #print("Die ersten 10 Nummern mit 'Yes':")
    #for nummer in nummern_mit_yes[:10]:
     #   print(nummer)
#else:
 #   print('"target" nicht in der JSON-Datei gefunden.')

# Pfad zur CSV-Datei
csv_datei = "/Users/nursahmisirlioglu/Desktop/Wirtschaftsprojekt/Projekt/reduce_transactions_data.csv"



# Die ersten 500 Zeilen der CSV-Datei lesen und ausgeben
try:
    with open(csv_datei, mode='r', newline='', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)  # Spaltenüberschrift lesen
        print("\nCSV-Datei: Zeilen mit den ersten 10 Nummern:")
        print(header)  # Spaltenüberschrift ausgeben

        for row in reader:
            if row[0] in nummern_mit_yes[:10]:  # Annahme: Nummern sind in der ersten Spalte
                print(row)

except FileNotFoundError:
    print(f"Die Datei '{csv_datei}' wurde nicht gefunden.")
except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")


# Anzahl der 'Yes'-Einträge im 'target'-Dictionary zählen
if 'target' in daten:
    anzahl_yes = sum(1 for wert in daten['target'].values() if wert == "Yes")
    print(f"Anzahl der Einträge mit 'Yes': {anzahl_yes}")
else:
    print('"target" nicht in der JSON-Datei gefunden.')


    # Nur die Nummern mit "Yes" sammeln (die ersten 10 aus csv datei#)
#nummern_mit_yes = []
#if 'target' in daten:
 #   nummern_mit_yes = [nummer for nummer, wert in daten['target'].items() if wert == "Yes"]
    
    # Sortieren (nach Zahl, nicht als Text)
  #  nummern_mit_yes = sorted(nummern_mit_yes, key=int)

    # Die ersten 10 Nummern ausgeben
   # print("Die ersten 10 Nummern mit 'Yes':")
    #for nummer in nummern_mit_yes[:10]:
     #   print(nummer)
#else:
 #   print('"target" nicht in der JSON-Datei gefunden.')

    # Nur die Nummern mit "Yes" sammeln
#if 'target' in daten:
 #   nummern_mit_yes = [nummer for nummer, wert in daten['target'].items() if wert == "Yes"]
    






  # Json Datei alle mit yes nach Nummer sortiert ausgegeben 
    
    # Sortieren (nach Zahl, nicht als Text)
    #nummern_mit_yes = sorted(nummern_mit_yes, key=int)

    #print("Sortierte Nummern mit 'Yes':")
    #for nummer in nummern_mit_yes:
     #   print(nummer)
#else:
 #   print('"target" nicht in der JSON-Datei gefunden.')

  #  for i, row in enumerate(reader):
   #     if i >= 10:
    #        break
     #   print(row)


  


    











