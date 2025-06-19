# 📊 Finance Dashboard – Installationsanleitung

Dieses Dashboard visualisiert Unternehmens- und Branchendaten für Investmententscheidungen.  
Folge dieser Anleitung, um das Projekt lokal zum Laufen zu bringen.

---

## 🚀 Schnellstart

### 1. Repository klonen

```bash
git clone <REPO-URL>
cd finance_dashboard
```

### 2. Python-Umgebung einrichten (empfohlen)

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
pip install dash dash-bootstrap-components pandas plotly duckdb
```

### 4. Daten vorbereiten

- Lege deine Parquet-Dateien im Ordner `parquet_data/` ab.
- Stelle sicher, dass die Dateien wie folgt benannt sind:
  - `transactions_YYYY_MM.parquet` (z.B. `transactions_2023_01.parquet`)
- Optional: Führe das Skript `prerender.py` aus, um die Daten vorzubereiten:

```bash
python prerender.py
```

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
- Bei Problemen prüfe die Konsolenausgabe auf Fehlermeldungen.

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

---

## 👥 Kontakt & Support

Bei Fragen oder Problemen wende dich an das Projektteam oder öffne ein Issue auf GitHub.

---

Viel Erfolg mit dem Finance Dashboard!