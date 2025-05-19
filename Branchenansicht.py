import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Branchen aus externer JSON-Datei laden
with open("mcc_codes.json", "r") as f:
    mcc_codes = json.load(f)

branchen_liste = list(mcc_codes.values())    #


months = pd.date_range(end=datetime.today(), periods=36, freq='ME')
data = pd.DataFrame({
    'Datum': months,
    'VW': np.cumsum(np.random.randn(36) * 10 + 50),
    'Porsche': np.cumsum(np.random.randn(36) * 10 + 45),
    'Daimler': np.cumsum(np.random.randn(36) * 10 + 40)
})

data.set_index('Datum', inplace=True)

# KPIs (mit Datei verbinden!)
kpis = ["+7%", "35 Mio €"] + ["KPI"] * 4

# Layout (ändern - entsprechend anpassen 142)
with st.container():
    col1, col2 = st.columns([1, 2])

    with col1:
        selected_branche = st.selectbox("Branche wählen", options=branchen_liste)

        rows = 3
        cols = 2
        for i in range(0, len(kpis), cols):
            kpi_row = st.columns(cols)
            for j in range(cols):
                if i + j < len(kpis):
                    with kpi_row[j]:
                        st.markdown(
                            f"""
                            <div style='padding:20px; margin:5px; background-color:#f0f2f6; border-radius:10px; border:1px solid #d3d3d3; text-align:center;'>
                                <strong>{kpis[i + j]}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    with col2:

        # Zeitraum wählen 
        zeitraum = st.selectbox("Zeitraum wählen", options=["6 Monate", "1 Jahr", "2 Jahre", "3 Jahre"])

        zeitraum_map = {
            "6 Monate": 6,
            "1 Jahr": 12,
            "2 Jahre": 24,
            "3 Jahre": 36
        }

        selected_period = zeitraum_map[zeitraum]
        filtered_data = data[-selected_period:]

        # Plot
        fig, ax = plt.subplots(figsize=(8, 4))
        filtered_data.plot(ax=ax)
        ax.set_title("Umsatzentwicklung")
        ax.set_ylabel("Umsatz")
        ax.set_xlabel("Monat")
        st.pyplot(fig)

    # Persona (noch einbinden!)
    st.markdown("#### Persona ")
    col1, col2, col3 = st.columns(3)
    col1.markdown("**Einkommen Ø:**")
    col2.markdown("**Alter:**")
    col3.markdown("**Credit Score:**")

    st.markdown("**Kaufverhalten:** bezahlt mit…")



