# EcoBudget – WattWise AI Chatbot 🌿

A Streamlit-based AI chatbot that provides **personalized energy consumption analysis**, **electricity bill estimation**, **budget tracking**, and **eco-friendly cost optimization** — powered by **Google Gemini 2.5 Flash**.

---

## Project Overview

EcoBudget helps households understand their electricity usage and reduce costs by combining rule-based energy calculations with an LLM-powered conversational assistant. Users describe their appliances, usage patterns, income, and expenses in natural language — the chatbot handles everything else.

**Three core capabilities in one interface:**
1. **Energy Calculator** — computes monthly kWh, electricity cost, and CO₂ emissions per appliance
2. **Budget Tracker** — maps income vs. total spending (electricity + living expenses) to show real savings
3. **AI Advisor** — Gemini-powered assistant that maintains session memory and gives actionable eco tips

---

## Features

- **Natural Language Input** — describe appliances conversationally (`"My AC is 1200W for 6 hours"`)
- **Multi-turn Memory** — remembers appliances, electricity rate, income, and expenses across the conversation
- **Per-Appliance Breakdown** — monthly kWh, cost in ₹, and CO₂ footprint for every device
- **Budget Analysis** — income vs. total spend with savings calculation
- **Top Consumer Detection** — identifies the single biggest electricity drain automatically
- **Solar Sizing Suggestion** — estimates required solar system size (kW) based on usage
- **Multimodal Input Support (optional, via expander):**
  - 🎤 Upload voice notes (WAV, MP3) → Gemini transcribes and processes as text
  - 🖼️ Upload appliance photos (PNG, JPG, JPEG) → Gemini identifies appliance, typical wattage, and energy-saving tip
  - 📄 Upload bill or spec files (TXT, CSV) → Gemini extracts wattage, kWh, and cost values
- **Session Reset** — one-click new chat clears memory and conversation history

---

## Tech Stack

| Layer | Tools |
|---|---|
| Frontend / UI | Streamlit |
| LLM | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| LLM SDK | `google-generativeai` |
| Image Processing | Pillow (PIL) + Gemini Vision |
| Audio Transcription | Gemini Audio (`inline_data`) |
| Energy Calculations | Python (regex-based NLP extraction + custom formulas) |
| Language | Python 3.9+ |

---

## How It Works

### Energy Calculation Engine
- Monthly kWh   = (Wattage / 1000) × Hours/day × 30
- Monthly Cost  = kWh × ₹/kWh rate
- CO₂ Emissions = kWh × 0.82 kg CO₂/kWh
- Solar Size    = Monthly kWh / (30 days × 4 peak sun hours)
---
### Session Memory Schema
The bot maintains a persistent in-session memory dictionary injected into every Gemini prompt:
```python
memory = {
    "appliances": { "ac": {"watt": 1200, "hours": 6}, ... },
    "rate": 8.0,        # ₹/kWh
    "income": 50000,    # ₹/month
    "budget": { "rent": 12000, "groceries": 6000, ... },
    "last_energy": { "cost": ..., "kwh": ..., "co2": ... },
    "last_budget": { "base": ..., "electricity": ..., "total": ..., "savings": ... }
}
```

### Regex + LLM Hybrid Design
Appliance names, wattage, hours, electricity rate, income, and expense amounts are extracted via regex patterns. These feed deterministic energy calculations. The full memory JSON is then injected into every Gemini prompt so the LLM gives personalised advice based on actual numbers — not generic responses.

---

## Project Structure
```text
EcoBudget-WattWise/
├── ecoapp.py        # Main Streamlit application (single file)
├── requirements.txt
└── README.md
```
---

## Setup & Usage

### 1. Clone the repository
```bash
git clone https://github.com/Mitu0601/EcoBudget-WattWise.git
cd EcoBudget-WattWise
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your Gemini API key
Replace the placeholder in `ecoapp.py`:
```python
API_KEY = "your_gemini_api_key_here"
```
Or use an environment variable (recommended):
```python
import os
API_KEY = os.environ.get("GEMINI_API_KEY")
```
Get a free API key at [Google AI Studio](https://aistudio.google.com/).

### 4. Run the app
```bash
streamlit run ecoapp.py
```

---

## Requirements
- streamlit
- google-generativeai
  ---

## Example Conversation
<img width="1080" height="606" alt="image" src="https://github.com/user-attachments/assets/4629dced-b75f-4cd7-ba6f-73a09fcb654e" />
<img width="1878" height="886" alt="image" src="https://github.com/user-attachments/assets/f4acb85d-49c4-4981-81b1-565cedaa3033" />
<img width="1863" height="836" alt="image" src="https://github.com/user-attachments/assets/e8441ff4-815d-4ea1-9920-29df02cbd967" />
<img width="1855" height="818" alt="image" src="https://github.com/user-attachments/assets/4b11ce05-c79f-4fef-9e93-76b9c65ccf54" />
<img width="1391" height="808" alt="image" src="https://github.com/user-attachments/assets/ad17b5ee-ad73-4da2-a270-092d130be964" />




  
