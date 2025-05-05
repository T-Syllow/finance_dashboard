# 📊 Projektplan – Visualisierungsdashboard für BlackRock

## 🧩 Aufgabenstellung

### 🔍 Was wird visualisiert?
Ein datengetriebenes Dashboard zur Analyse und Darstellung von Unternehmens- und Branchendaten für Investmententscheidungen im Auftrag eines BlackRock-Investmentbankers.

---

## 🧠 Geplante Features

### 🧱 Dashboard-Struktur
- Grobes Dashboard-Layout mit Navigation: **Landkarte → Branche → Unternehmen (Zoom)**
- Klare visuelle Trennung nach Unternehmen & Branche

### 📊 Visualisierungen
- Umsatzentwicklung nach Branche (Trendvisualisierung)
- Top 10 umsatzstärkste Branchen
- Balkendiagramme zu Umsatz & Wachstum
- Marktanteil pro Unternehmen (filterbar nach Zeitraum)
- Durchschnittliches Einkommen je Cluster (gering, mittel, reich)
- Vergleich Onlinekäufe vs. stationäre Käufe
- Durchschnittlicher Einkaufswert je Branche & Firma
- Geografische Lage von Händlern (für Naturkatastrophen-Risikoanalyse)
- Verhältnis zu Einwohnern pro Bundesstaat

### 🧩 Interaktionen
- Filter (Zeitraum, Branche, Unternehmen, Staaten(USA))
- Drill-Down (von Landkarte zu Branche oder Unternehmen)
- Tooltip mit Detailinfos

### 🗃️ Datenquellen
- CSV-Datei mit 13 Mio. Datensätzen (bereinigt)
- Unternehmens- und Branchendaten
- Geo-Informationen (State, Adresse)
- Transaktionsdaten (inkl. Preis, Art: online/offline)
- Käufer-Attribute (Einkommen, Debit/Credit, etc.)

### ⚙️ Datenverarbeitung
- Bereinigung (Entfernen von Fraud-Daten)
- Clustering der Userdaten nach Einkommen
- Zeitbasierte Aggregation (Monat, Quartal, Jahr)
- Kategorisierung nach Branche und Firma
- Verknüpfung mit geografischen & demografischen Daten

---

## 📌 Grobe Teilaufgaben (Pseudo-Backlog)

| Priorität | Aufgabe                               | Erledigt? |
|-----------|----------------------------------------|------------------|
| Hoch      | Datenbereinigung                       | ❌ Nein          |
| Hoch      | UI/UX-Konzept                          | ✅ Ja            |
| Hoch      | Dashboard-Layout festlegen             | ❌ Nein          |
| Mittel    | Datenanalyse & Clustering              | ❌ Nein          |
| Mittel    | Unternehmens-/Branchenansicht          | ❌ Nein          |
| Mittel    | Geovisualisierung Startseite           | ❌ Nein          |
| Niedrig   | Integration der Online-/Offline-Analyse| ❌ Nein          |
| Niedrig   | Darstellung der Kaufverhalten-Cluster  | ❌ Nein          |

---

## 🏗️ Projektinfrastruktur

- **Interne Kommunikation:** WhatsApp-Gruppe, Google Meet bei Bedarf, Vor Ort
- **Versionsverwaltung:** GitHub (inkl. Issues, Pull Requests, Branches)
- **Interne Treffen:** Wöchentlich montags, mehr bei Bedarf
- **Entwicklungsstil:** Dezentral, angelehnt an Scrum
- **Dokumentation:** 
  - Code-Kommentare

---

## 🗓️ Umsetzungsplan (zeitlich)

| Woche | Aufgaben                                                                 |
|-------|--------------------------------------------------------------------------|
| 1     | Layout fixieren, Daten bereinigen, GitHub-Konfiguration, Anforderungsdefinition |
| 2     | Beginn der Programmierung, Startseite programmiert                       |
| 3     | Weiterentwicklung, Branchenseite programmiert                            |
| 4     | Weiterentwicklung, Unternehmensseite programmiert, Erstellung von Personas(branchenbasiert) |
| 5     | Entwicklung & Korrekturlesung                                            |
| 6     | Finalisierung & Bugfixing                                                |
| 7     | Abschluss, Feinschliff, letzte Korrekturen                               |

---

## 👥 Team und Aufgabenverteilung

| Name     | Aufgaben                                              |
|----------|--------------------------------------------------------|
| Simon    | Personas schreiben, Branchenanalyse                    |
| Emir     | Unternehmensanalyse, Datenbereinigung                  |
| Nursah   | Datenbereinigung                                       |
| Chai     | Personas schreiben, Branchenanalyse, Startseite        |
| Tommy    | UI/UX Verantwortlicher, Unternehmen, Startseite, Projektmanagement |

---

## 🧠 Brainstorming-Ideen (erste Skizzen)

- Durchschnittseinkommen nach Branche
- Umsatz nach Branche (Balkendiagramm)
- Top 10 Branchen
- User-Cluster nach Einkommen (gering, mittel, reich)
- Vergleich von Clustern in Bezug auf Branchen
- Fraud-Filter in der Datenbereinigung

---

## 📦 BlackRock-Anforderungen (Zusammenfassung)

1. **Trendanalysen**: Umsatzentwicklung je Branche über Zeit
2. **Top-Unternehmen je Branche**: Umsatz, Wachstum, Marktanteil (zeitfilterbar)
3. **Käuferprofil je Branche**: Einkommen, Zahlungsmittel (Debit/Credit)
4. **Naturkatastrophen-Risiko**: Geografische Lage der Händler
5. **Relation zu Einwohnern pro Staat**
6. **Online vs. stationär**: Kaufverhalten vergleichen
7. **Durchschnittlicher Einkaufswert je Branche/Firma**
8. **Zoom-Funktion**: Von Branche auf Firmendaten

---

## 🕒 Arbeitsweise

- **Montags 09:45 – 11:15 Uhr:** Wöchentliches Code-Review & Aufgabenverteilung
- **Montags 11:30 – 13:00 Uhr:** Präsentation in der Vorlesung

