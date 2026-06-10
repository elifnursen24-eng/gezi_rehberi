from deep_translator import GoogleTranslator
import os
import requests
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(
    page_title="NomadAI Gezi Rehberi",
    page_icon="🌍",
    layout="wide"
)

load_dotenv()

STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")
TOKEN = os.getenv("STRAPI_API_TOKEN")

headers = {"Authorization": f"Bearer {TOKEN}"}

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
.hero h1 {
    font-size: 48px;
    margin-bottom: 10px;
}
.hero p {
    font-size: 19px;
    color: #e5e7eb;
}
.metric-card {
    background-color: #020617;
    border: 1px solid #334155;
    padding: 20px;
    border-radius: 18px;
    text-align: center;
}
.metric-card h3 {
    font-size: 28px;
    margin: 0;
    color: #38bdf8;
}
.metric-card p {
    color: #cbd5e1;
    margin: 0;
}
.place-card {
    background-color: #020617;
    border: 1px solid #334155;
    border-radius: 22px;
    padding: 18px;
    margin-bottom: 28px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.place-title {
    font-size: 28px;
    font-weight: 800;
    color: #f8fafc;
}
.rating {
    display: inline-block;
    background-color: #facc15;
    color: #111827;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    margin: 8px 0 12px 0;
}
.desc {
    color: #d1d5db;
    font-size: 16px;
    line-height: 1.6;
}
.footer {
    text-align: center;
    color: #94a3b8;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)


def get_data(endpoint):
    response = requests.get(
        f"{STRAPI_URL}/api/{endpoint}?populate=*",
        headers=headers
    )
    response.raise_for_status()
    return response.json()["data"]


def get_image_url(cover_image):
    if not cover_image:
        return None

    if isinstance(cover_image, list):
        if len(cover_image) == 0:
            return None
        cover_image = cover_image[0]

    if isinstance(cover_image, dict):
        url = cover_image.get("url")
        if url:
            return STRAPI_URL + url if url.startswith("/") else url

    return None


def get_description(description, language):
    if not description:
        return ""

    if language == "English":
        try:
            return GoogleTranslator(source="tr", target="en").translate(description)
        except:
            return "Translation error."

    return description


st.markdown("""
<div class="hero">
    <h1>🌍 NomadAI Gezi Rehberi</h1>
    <p>YZ destekli, çok dilli ve dinamik şehir keşif platformu.</p>
</div>
""", unsafe_allow_html=True)

language = st.radio(
    "🌐 Dil seç",
    ["Türkçe", "English"],
    horizontal=True
)

cities = get_data("cities")
places = get_data("places")

total_cities = len(cities)
total_places = len(places)

ratings = [place.get("rating") for place in places if place.get("rating")]
average_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{total_cities}</h3>
        <p>Şehir</p>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{total_places}</h3>
        <p>Mekan</p>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{average_rating}</h3>
        <p>Ortalama Puan</p>
    </div>
    """, unsafe_allow_html=True)

st.write("")

if not cities:
    st.warning("Henüz şehir yok.")
else:
    city_names = [city.get("name", "İsimsiz şehir") for city in cities]

    filter_col1, filter_col2 = st.columns([1, 2])

    with filter_col1:
        selected_city = st.selectbox("📍 Şehir seç", city_names)

    with filter_col2:
        search_text = st.text_input("🔎 Mekan ara", placeholder="Örn: Louvre, Katedral, Tak...")

    selected_places = []

    for place in places:
        city = place.get("city")

        if isinstance(city, list):
            city = city[0] if city else None

        if city and city.get("name") == selected_city:
            if search_text.lower() in place.get("name", "").lower():
                selected_places.append(place)

    st.subheader(f"✨ {selected_city} Keşif Rehberi")

    if not selected_places:
        st.info("Bu filtreye uygun mekan bulunamadı.")
    else:
        for place in selected_places:
            image_url = get_image_url(place.get("cover_image"))

            st.markdown('<div class="place-card">', unsafe_allow_html=True)

            col_img, col_text = st.columns([1.1, 1.9])

            with col_img:
                if image_url:
                    st.image(image_url, use_container_width=True)
                else:
                    st.warning("Görsel bulunamadı.")

            with col_text:
                st.markdown(
                    f"<div class='place-title'>{place.get('name', 'İsimsiz mekan')}</div>",
                    unsafe_allow_html=True
                )

                rating = place.get("rating")
                if rating:
                    st.markdown(
                        f"<div class='rating'>⭐ {rating} / 5</div>",
                        unsafe_allow_html=True
                    )

                description = get_description(place.get("description"), language)

                if description:
                    st.markdown(
                        f"<div class='desc'>{description}</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    <p>YZ Destekli Gezi Rehberi Sistemi • Strapi + Python + Streamlit</p>
</div>
""", unsafe_allow_html=True)