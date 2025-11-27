import streamlit as st
import google.generativeai as genai
import re
import json
from datetime import datetime
from PIL import Image

# ---------------- CONFIG ----------------
API_KEY = "AIzaSyCH-slfJV-Xu1SiUxcnXX-Tg-o93i2w4l0"   # 🔴 PUT YOUR GEMINI KEY HERE
genai.configure(api_key=API_KEY)

CARBON_FACTOR = 0.82  # kg CO2/kWh approx

# ---------------- PAGE SETUP (dark) ----------------
st.set_page_config(page_title="EcoBudget AI", page_icon="🌿", layout="wide")

st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #050816;
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .chat-message {
        padding: 0.6rem 0.8rem;
        border-radius: 0.9rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi, I'm *EcoBudget AI* 🌿\n\n"
                "Tell me your appliances, wattage, hours, income, and rough expenses, "
                "and I'll help you understand your bill and how to reduce it."
            ),
        }
    ]

if "memory" not in st.session_state:
    st.session_state.memory = {
        "appliances": {},   # name -> {watt, hours}
        "rate": None,       # ₹/kWh
        "budget": {},       # category -> ₹
        "income": None,     # ₹
        "last_energy": {},
        "last_budget": {},
    }

memory = st.session_state.memory

# ---------------- ECO HELPERS ----------------
def extract_appliance(text: str):
    pattern = r"([A-Za-z]+)\s+(\d+)\s*W.*?(\d+)\s*hours?"
    return re.findall(pattern, text, re.IGNORECASE)

def extract_energy_simple(text: str):
    watts = re.findall(r"(\d+)\s*W", text)
    hours = re.findall(r"(\d+)\s*hours?", text)
    return watts, hours

def calc_kwh(watt, hours):
    return (watt / 1000.0) * hours * 30.0

def detect_expense(text: str):
    return re.findall(r"\b([a-zA-Z]+)\s+(\d+)\s*₹\b", text)

def get_energy_report(mem: dict):
    report = []
    for name, d in mem["appliances"].items():
        w = d["watt"]; h = d["hours"]
        kwh = calc_kwh(w, h)
        cost = kwh * mem["rate"] if mem["rate"] else 0.0
        co2 = kwh * CARBON_FACTOR
        report.append((name, w, h, kwh, cost, co2))
    return report

def get_top_consumers(mem: dict):
    return sorted(get_energy_report(mem), key=lambda x: x[3], reverse=True)

def build_auto_output(mem: dict) -> str:
    out = ""

    # Energy summary
    if mem["appliances"] and mem.get("rate"):
        report = get_energy_report(mem)
        total_cost = sum(x[4] for x in report)
        total_kwh = sum(x[3] for x in report)
        total_co2 = sum(x[5] for x in report)
        mem["last_energy"] = {"cost": total_cost, "kwh": total_kwh, "co2": total_co2}

        out += "🔋 *Energy Summary*\n"
        for n, w, h, k, c, co in report:
            out += (
                f"- *{n.capitalize()}*: {w}W × {h}h/day → "
                f"{k:.2f} kWh/month | ₹{c:.2f} | {co:.1f} kg CO₂\n"
            )
        out += f"\n🌍 Total CO₂: *{total_co2:.1f} kg/month*\n\n"

    # Budget summary
    if mem.get("income") and (mem["budget"] or mem.get("last_energy")):
        base = sum(mem["budget"].values())
        elec = mem.get("last_energy", {}).get("cost", 0.0)
        total = base + elec
        savings = mem["income"] - total
        mem["last_budget"] = {
            "base": base,
            "electricity": elec,
            "total": total,
            "savings": savings,
        }

        out += (
            "💰 *Budget Summary*\n"
            f"- Income: ₹{mem['income']}\n"
            f"- Base expenses: ₹{base}\n"
            f"- Electricity: ₹{elec:.2f}\n"
            f"- Total spending: ₹{total:.2f}\n"
            f"- Savings: ₹{savings:.2f}\n\n"
        )

        consumers = get_top_consumers(mem)
        if consumers:
            n, _, _, k, c, _ = consumers[0]
            out += (
                f"⚡ Biggest consumer: *{n.capitalize()}* "
                f"({k:.1f} kWh/month, ₹{c:.1f})\n\n"
            )

        if mem.get("last_energy"):
            monthly_kwh = mem["last_energy"]["kwh"]
            solar_kw = monthly_kwh / (30 * 4)  # rough hours of sun/day
            out += (
                "🔆 *Solar suggestion*\n"
                f"- Approx solar system size: *{solar_kw:.2f} kW*\n"
                "  (Could offset most of your monthly usage.)\n\n"
            )

        out += (
            "🌿 *Quick eco tips*\n"
            "- Keep AC at 24–26°C.\n"
            "- Use LED bulbs instead of CFL/halogen.\n"
            "- Turn devices fully off at the plug.\n"
            "- Clean fridge coils regularly.\n"
            "- Use natural daylight whenever possible.\n\n"
        )

    return out

# ---------------- FILE / IMAGE / AUDIO HELPERS ----------------
def analyze_file(uploaded):
    if uploaded is None:
        return ""
    try:
        data = uploaded.read()
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        resp = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": uploaded.type or "application/octet-stream",
                                "data": data,
                            }
                        },
                        {
                            "text": (
                                "This may be an electricity bill or appliance spec. "
                                "Briefly extract any useful wattage (W), hours/day, kWh or cost values."
                            )
                        },
                    ],
                }
            ]
        )
        return resp.text.strip()
    except Exception as e:
        return f"[File analysis error: {e}]"

def analyze_image(uploaded):
    if uploaded is None:
        return ""
    try:
        img = Image.open(uploaded)
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        resp = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "This image likely shows a household appliance. "
                                "Identify the appliance type (AC, fridge, fan, TV, etc.), "
                                "give a typical wattage range and one energy-saving tip."
                            )
                        },
                        img,
                    ],
                }
            ]
        )
        return resp.text.strip()
    except Exception as e:
        return f"[Image analysis error: {e}]"

def transcribe_audio(uploaded):
    if uploaded is None:
        return ""
    try:
        data = uploaded.read()
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        resp = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": uploaded.type or "audio/wav",
                                "data": data,
                            }
                        },
                        {
                            "text": "Transcribe this audio to plain text only. No extra explanation."
                        },
                    ],
                }
            ]
        )
        return resp.text.strip()
    except Exception as e:
        return f"[Audio error: {e}]"

# ---------------- MODEL CALL ----------------
def get_bot_reply(user_text: str, file_obj, image_obj, audio_obj) -> str:
    # attach advanced inputs as text
    if file_obj is not None:
        file_info = analyze_file(file_obj)
        if file_info:
            user_text += f"\n[Bill/spec info: {file_info}]"

    if image_obj is not None:
        img_info = analyze_image(image_obj)
        if img_info:
            user_text += f"\n[Appliance image info: {img_info}]"

    if audio_obj is not None:
        audio_text = transcribe_audio(audio_obj)
        if audio_text:
            user_text += f"\n[Voice note: {audio_text}]"

    # update memory from text
    for name, watt, hours in extract_appliance(user_text):
        memory["appliances"][name.lower()] = {"watt": int(watt), "hours": int(hours)}

    watts, hours = extract_energy_simple(user_text)
    if watts and hours and "custom" not in memory["appliances"]:
        memory["appliances"]["custom"] = {"watt": int(watts[0]), "hours": int(hours[0])}

    rate_match = re.search(r"(\d+)\s*₹?\s*/?\s*kWh", user_text)
    if rate_match:
        memory["rate"] = float(rate_match.group(1))

    income_match = re.search(r"income\s*is\s*(\d+)", user_text, re.IGNORECASE)
    if income_match:
        memory["income"] = int(income_match.group(1))

    for cat, amt in detect_expense(user_text):
        c = cat.lower()
        if c not in ["base", "total", "income", "savings", "electricity"]:
            memory["budget"][c] = int(amt)

    auto_text = build_auto_output(memory)

    system_text = (
        "You are EcoBudget AI, an eco-friendly energy & budget assistant.\n"
        "Use the MEMORY JSON to keep track of appliances, wattage, hours/day, electricity rate, "
        "income and expenses. Give clear, practical suggestions.\n\n"
        f"MEMORY JSON: {json.dumps(memory)}\n\n"
        "Now answer the user's latest message:"
    )

    model = genai.GenerativeModel("models/gemini-2.5-flash")

    try:
        resp = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {"text": system_text},
                        {"text": user_text},
                    ],
                }
            ]
        )
        llm_reply = resp.text
    except Exception as e:
        llm_reply = f"[Gemini error: {e}]"

    return (auto_text + llm_reply).strip()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("### 💬 Session")
    if st.button("🧹 New chat", use_container_width=True):
        st.session_state.messages = st.session_state.messages[:1]
        st.session_state.memory = {
            "appliances": {},
            "rate": None,
            "budget": {},
            "income": None,
            "last_energy": {},
            "last_budget": {},
        }
        st.experimental_rerun()

    st.markdown("#### Quick tips")
    st.markdown(
        "- Try: My AC is 1200W for 6 hours, fridge 150W 24 hours, fan 80W 10 hours.\n"
        "- Then: My electricity rate is 8 ₹/kWh and income is 50000.\n"
        "- Then add: rent 12000 ₹ groceries 6000 ₹ internet 999 ₹ entertainment 2500 ₹"
    )

# ---------------- MAIN CHAT UI ----------------
st.title("🌿 EcoBudget AI")


# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Optional advanced inputs (kept in an expander so UI stays clean)
with st.expander("✨ Advanced input (optional: voice, bill, image)"):
    c1, c2, c3 = st.columns(3)
    with c1:
        audio_file = st.file_uploader(
            "🎤 Voice (wav/mp3)", type=["wav", "mp3"], key="audio_upload"
        )
    with c2:
        bill_file = st.file_uploader(
            "📄 Bill / specs", type=["pdf", "txt", "docx", "csv"], key="bill_upload"
        )
    with c3:
        image_file = st.file_uploader(
            "🖼 Appliance photo", type=["png", "jpg", "jpeg"], key="image_upload"
        )

# Bottom chat input
user_input = st.chat_input("Type your message about appliances, bills or savings...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    reply = get_bot_reply(user_input, bill_file, image_file, audio_file)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)