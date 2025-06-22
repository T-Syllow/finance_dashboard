# 📊 Finance Dashboard – Installationsanleitung

Dieses Dashboard visualisiert Unternehmens- und Branchendaten für den Datensatz https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets  
Es dient als Analysetool für Märkte und Unternehmen in den USA.
Folge dieser Anleitung, um das Projekt lokal zum Laufen zu bringen.

---

## 🚀 Schnellstart

### 1. Repository klonen

```bash
git clone <REPO-URL>
cd finance_dashboard
```

### 2. Virtuelle Umgebung (venv) erstellen und starten

**(empfohlen, um Abhängigkeiten sauber zu halten)**

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Falls keine `requirements.txt` vorhanden ist, installiere die wichtigsten Pakete manuell:

```bash
pip install dash dash-bootstrap-components pandas plotly duckdb pyarrow fastparquet
```

### 4. Daten vorbereiten
- Installiere den Datensatz unter https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets und lege die Dateien in den Ordner finance_dashboard/newData

- Führe die Datei cleanData.py aus: (ersetze wenn notwendig den Pfad zur transactions_data.csv)
```bash
python3 cleanData.py
```
!! Beachte: dies kann ein paar Minuten dauern. (Großer Datensatz!)

- Führe die Datei to_parquet.py aus: (ersetze wenn notwendig den Pfad zur cleaned_transaction_data.csv)
```bash
python3 to_parquet.py
```
Erwartetes Verhalten: im Ordner parquet_data entsteht eine "cleaned_transactions_data.parquet" und eine "gesamt_ausgaben_pro_client.parquet" Datei.

- Führe die Datei prerender.py aus: (ersetze wenn notwendig den Pfad zur cleand_transaction_data.parquet)
```bash
python3 prerender.py
```
Erwartetes Verhalten: im Ordner parquet_data entstehen transactions_YYYY_MM.parquet Dateien für jeden Monat und Jahr des Datensatzes.

### 5. Dashboard starten

```bash
python app.py
```

Das Dashboard ist dann erreichbar unter:  
[http://127.0.0.1:8050](http://127.0.0.1:8050)

---

## ⚙️ Hinweise

- **Python 3.8+** wird empfohlen.
- Für große Datenmengen wird ausreichend RAM benötigt.
- Die wichtigsten Einstellungen (z.B. Datenpfade) findest du in `app.py` und `prerender.py`.

---

## 🛠️ Nützliche Kommandos

- Virtuelle Umgebung verlassen:  
  ```bash
  deactivate
  ```
- Abhängigkeiten exportieren:  
  ```bash
  pip freeze > requirements.txt
  ```
