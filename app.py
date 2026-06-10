from deep_translator import GoogleTranslator
import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")
TOKEN = os.getenv("STRAPI_API_TOKEN")

headers = {}

# ---------------- UI ----------------
st.set_page_config(
    page_title="NomadAI Gezi Rehberi",
    page_icon="🌍",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #111827 50%, #1e293b 100%);
    color: white;
}
.hero {
    padding: 45px;
    border-radius: 25px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    margin-bottom: 30px;
}
.hero h1 { font-size: 48px; }
.hero p { font-size: 19px; color: #e5e7eb; }

.metric-card {
    background-color: #020617;
    border: 1px solid #334155;
    padding: 20px;
    border-radius: 18px;
    text-align: center;
}

.place-card {
    background-color: #020617;
    border: 1px solid #334155;
    border-radius: 22px;
    padding: 18px;
    margin-bottom: 28px;
}

.place-title {
    font-size: 26px;
    font-weight: 800;
}
.rating {
    background-color: #facc15;
    padding: 6px 12px;
    border-radius: 999px;
    color: black;
    display: inline-block;
}
.desc {
    color: #d1d5db;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA ----------------
def get_data(endpoint):
    try:
        response = requests.get(
            f"{STRAPI_URL}/api/{endpoint}?populate=*"
        )
        return response.json().get("data", [])
    except:
        return []

def get_image_url(cover):
    if isinstance(cover, dict):
        url = cover.get("url")
        if url:
            return STRAPI_URL + url
    return None

def get_text(desc, lang):
    if not desc:
        return ""
    if lang == "English":
        try:
            return GoogleTranslator(source="tr", target="en").translate(desc)
        except:
            return desc
    return desc

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
    <h1>🌍 NomadAI Gezi Rehberi</h1>
    <p>AI destekli gezi keşif platformu</p>
</div>
""", unsafe_allow_html=True)

language = st.radio("Dil seç", ["Türkçe", "English"], horizontal=True)

# ---------------- FIXED DATA PARSE ----------------
raw_cities = get_data("cities")
raw_places = get_data("places")

cities = [c["attributes"] for c in raw_cities]
places = [p["attributes"] for p in raw_places]

# ---------------- METRICS ----------------
st.columns(3)
st.write(f"Şehir: {len(cities)} | Mekan: {len(places)}")

# ---------------- UI ----------------
if not cities:
    st.warning("Şehir yok")
else:
    city_names = [c.get("name", "No Name") for c in cities]

    selected_city = st.selectbox("Şehir seç", city_names)
    search = st.text_input("Ara")

    filtered = []

    for p in places:
        city = p.get("city")
        if isinstance(city, dict):
            city_name = city.get("name")
        else:
            city_name = None

        if city_name == selected_city:
            if search.lower() in p.get("name", "").lower():
                filtered.append(p)

    for p in filtered:
        st.markdown("----")

        st.subheader(p.get("name"))
        st.write(p.get("rating"))

        desc = get_text(p.get("description"), language)
        st.write(desc)

        img = get_image_url(p.get("cover_image"))
        if img:
            st.image(img)