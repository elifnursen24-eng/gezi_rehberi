from PIL import Image
import os
import time
import tempfile
import urllib.parse
import requests
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv()

STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")
TOKEN = os.getenv("STRAPI_API_TOKEN")

CITY_ENDPOINT = "cities"
PLACE_ENDPOINT = "places"

headers_json = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

headers_auth = {
    "Authorization": f"Bearer {TOKEN}"
}

city_places = {
    "Paris": {
        "country": "France",
        "short_info": "Fransa'nın başkenti, sanat ve tarih dolu turistik bir şehirdir.",
        "places": [
            {
                "name": "Louvre Müzesi",
                "description_tr": "Louvre Müzesi, Paris'in en önemli sanat müzelerinden biridir. Mona Lisa gibi dünyaca ünlü eserlere ev sahipliği yapar.",
                "rating": 4.9
            },
            {
                "name": "Notre Dame Katedrali",
                "description_tr": "Notre Dame Katedrali, gotik mimarisiyle Paris'in en dikkat çeken tarihi yapılarından biridir.",
                "rating": 4.7
            },
            {
                "name": "Zafer Takı",
                "description_tr": "Zafer Takı, Paris'in simgesel yapılarından biridir ve Champs-Élysées Caddesi'nin sonunda yer alır.",
                "rating": 4.6
            }
        ]
    },

    "İstanbul": {
        "country": "Türkiye",
        "short_info": "İstanbul, tarihi yarımadası, boğazı ve kültürel mirasıyla dünyanın en özel şehirlerinden biridir.",
        "places": [
            {
                "name": "Ayasofya",
                "description_tr": "Ayasofya, Bizans ve Osmanlı dönemlerinden izler taşıyan, İstanbul'un en önemli tarihi yapılarından biridir.",
                "rating": 4.9
            },
            {
                "name": "Topkapı Sarayı",
                "description_tr": "Topkapı Sarayı, Osmanlı padişahlarının yaşadığı ve devletin yönetildiği önemli bir saray kompleksidir.",
                "rating": 4.8
            },
            {
                "name": "Galata Kulesi",
                "description_tr": "Galata Kulesi, İstanbul manzarasını izlemek için en popüler tarihi noktalardan biridir.",
                "rating": 4.7
            }
        ]
    },

    "Roma": {
        "country": "Italy",
        "short_info": "Roma, antik yapıları, meydanları ve tarihi atmosferiyle Avrupa'nın en önemli turizm merkezlerinden biridir.",
        "places": [
            {
                "name": "Kolezyum",
                "description_tr": "Kolezyum, Antik Roma döneminden kalan en ünlü amfitiyatrolardan biridir.",
                "rating": 4.8
            },
            {
                "name": "Trevi Çeşmesi",
                "description_tr": "Trevi Çeşmesi, Roma'nın en ünlü barok yapılarından biridir ve turistlerin en çok ziyaret ettiği noktalardandır.",
                "rating": 4.7
            },
            {
                "name": "Pantheon",
                "description_tr": "Pantheon, Roma'nın antik dönemden günümüze ulaşan en etkileyici yapılarından biridir.",
                "rating": 4.8
            }
        ]
    }
}


def make_safe_filename(text):
    safe_name = (
        text
        .replace(" ", "_")
        .replace("ü", "u")
        .replace("Ü", "U")
        .replace("ö", "o")
        .replace("Ö", "O")
        .replace("ş", "s")
        .replace("Ş", "S")
        .replace("ı", "i")
        .replace("İ", "I")
        .replace("ğ", "g")
        .replace("Ğ", "G")
        .replace("ç", "c")
        .replace("Ç", "C")
    )

    safe_name = "".join(
        char for char in safe_name
        if char.isalnum() or char in ["_", "-"]
    )

    return safe_name


def strapi_get(url):
    response = requests.get(url, headers=headers_json, timeout=60)
    response.raise_for_status()
    return response.json()


def strapi_post(url, data):
    response = requests.post(url, headers=headers_json, json=data, timeout=60)
    response.raise_for_status()
    return response.json()


def strapi_put(url, data):
    response = requests.put(url, headers=headers_json, json=data, timeout=60)
    response.raise_for_status()
    return response.json()


def get_city_document_id(city_name):
    url = f"{STRAPI_URL}/api/{CITY_ENDPOINT}?filters[name][$eq]={urllib.parse.quote(city_name)}"
    data = strapi_get(url)["data"]

    if not data:
        raise Exception(f"{city_name} şehri Strapi'de bulunamadı.")

    return data[0]["documentId"]


def get_place(place_name):
    url = f"{STRAPI_URL}/api/{PLACE_ENDPOINT}?filters[name][$eq]={urllib.parse.quote(place_name)}&populate=*"
    data = strapi_get(url)["data"]

    if not data:
        return None

    return data[0]


def translate_text(text):
    return GoogleTranslator(source="tr", target="en").translate(text)


def generate_image(place_name):
    prompt = (
        f"realistic touristic landscape photo of {place_name} in Paris, "
        f"high quality, daylight, travel guide style"
    )

    horde_headers = {
        "apikey": "0000000000",
        "Client-Agent": "gezi-rehberi-final:1.0"
    }

    payload = {
        "prompt": prompt,
        "params": {
            "width": 512,
            "height": 512,
            "steps": 20,
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": False
    }

    submit_response = requests.post(
        "https://aihorde.net/api/v2/generate/async",
        headers=horde_headers,
        json=payload,
        timeout=60
    )
    submit_response.raise_for_status()

    generation_id = submit_response.json()["id"]

    for _ in range(60):
        check_response = requests.get(
            f"https://aihorde.net/api/v2/generate/check/{generation_id}",
            headers=horde_headers,
            timeout=60
        )
        check_response.raise_for_status()

        check_data = check_response.json()

        if check_data.get("done"):
            break

        queue_position = check_data.get("queue_position", "bilinmiyor")
        wait_time = check_data.get("wait_time", "bilinmiyor")

        print(f"YZ görsel bekleniyor... sıra: {queue_position}, tahmini süre: {wait_time}")
        time.sleep(10)
    else:
        raise Exception("AI Horde görsel üretimi zaman aşımına uğradı.")

    status_response = requests.get(
        f"https://aihorde.net/api/v2/generate/status/{generation_id}",
        headers=horde_headers,
        timeout=60
    )
    status_response.raise_for_status()

    status_data = status_response.json()
    generations = status_data.get("generations", [])

    if not generations:
        raise Exception("AI Horde görsel üretmedi.")

    image_url = generations[0].get("img")

    if not image_url:
        raise Exception("AI Horde görsel linki döndürmedi.")

    image_response = requests.get(image_url, timeout=120)
    image_response.raise_for_status()

    temp_folder = tempfile.gettempdir()
    safe_name = make_safe_filename(place_name)

    raw_path = os.path.join(temp_folder, f"{safe_name}_raw.img")

    with open(raw_path, "wb") as file:
        file.write(image_response.content)

    jpeg_path = os.path.join(temp_folder, f"{safe_name}.jpg")

    image = Image.open(raw_path).convert("RGB")
    image.save(jpeg_path, "JPEG", quality=90)

    print("YZ görsel indirildi ve JPEG'e çevrildi:", jpeg_path)

    return jpeg_path


def upload_image_to_strapi(filepath):
    filename = os.path.basename(filepath)

    with open(filepath, "rb") as file:
        files = {
            "files": (filename, file, "image/jpeg")
        }

        response = requests.post(
            f"{STRAPI_URL}/api/upload",
            headers=headers_auth,
            files=files,
            timeout=120
        )

    if response.status_code >= 400:
        print("Upload hata kodu:", response.status_code)
        print("Upload cevabı:", response.text)

    response.raise_for_status()

    uploaded_file = response.json()[0]
    print("Media Library upload başarılı. ID:", uploaded_file["id"])

    return uploaded_file["id"]


def delete_uploaded_image(image_id):
    try:
        requests.delete(
            f"{STRAPI_URL}/api/upload/files/{image_id}",
            headers=headers_auth,
            timeout=60
        )
    except Exception:
        pass


def place_has_cover_image(place):
    cover_image = place.get("cover_image")

    if cover_image is None:
        return False

    if isinstance(cover_image, dict) and cover_image.get("id"):
        return True

    return False


def create_place_without_image(place, city_document_id):
    data = {
        "data": {
            "name": place["name"],
            "description": place["description_tr"],
            "rating": place["rating"],
            "city": city_document_id
        }
    }

    result = strapi_post(
        f"{STRAPI_URL}/api/{PLACE_ENDPOINT}",
        data
    )

    return result["data"]


def update_place_cover_image(place_document_id, image_id):
    data = {
        "data": {
            "cover_image": image_id
        }
    }

    return strapi_put(
        f"{STRAPI_URL}/api/{PLACE_ENDPOINT}/{place_document_id}",
        data
    )


def process_place(place, city_document_id):
    existing_place = get_place(place["name"])

    if existing_place:
        place_document_id = existing_place["documentId"]

        if place_has_cover_image(existing_place):
            print(place["name"], "zaten var ve görseli var, geçildi.")
            return

        print(place["name"], "zaten var ama görseli yok, görsel bağlanacak.")
    else:
        created_place = create_place_without_image(place, city_document_id)
        place_document_id = created_place["documentId"]
        print(place["name"], "mekan olarak oluşturuldu.")

    image_id = None

    try:
        english_description = translate_text(place["description_tr"])
        image_path = generate_image(place["name"])
        image_id = upload_image_to_strapi(image_path)
        update_place_cover_image(place_document_id, image_id)

        print(place["name"], "görseli Media Library'ye yüklendi ve mekana bağlandı.")
        print("İngilizce çeviri:", english_description)
        print("-" * 50)

    except Exception as error:
        print(place["name"], "işlenirken hata oluştu:", error)

        if image_id:
            delete_uploaded_image(image_id)
            print("Boşa yüklenen görsel silindi.")

        raise error


def create_city_if_not_exists(city_name, country, short_info):
    url = f"{STRAPI_URL}/api/{CITY_ENDPOINT}?filters[name][$eq]={urllib.parse.quote(city_name)}"
    data = strapi_get(url)["data"]

    if data:
        print(city_name, "şehri zaten var.")
        return data[0]["documentId"]

    city_data = {
        "data": {
            "name": city_name,
            "country": country,
            "short_info": short_info
        }
    }

    result = strapi_post(
        f"{STRAPI_URL}/api/{CITY_ENDPOINT}",
        city_data
    )

    print(city_name, "şehri oluşturuldu.")
    return result["data"]["documentId"]


def main():
    if not TOKEN:
        raise Exception("STRAPI_API_TOKEN .env dosyasında yok.")

    print("Strapi URL:", STRAPI_URL)

    for city_name, city_info in city_places.items():
        city_document_id = create_city_if_not_exists(
            city_name,
            city_info["country"],
            city_info["short_info"]
        )

        for place in city_info["places"]:
            process_place(place, city_document_id)


main()