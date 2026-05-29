def generate_yandex_maps(lat: float, lon: float, zoom: int = 17) -> str:
    return f"https://yandex.ru/maps/?ll={lon},{lat}&z={zoom}"

def generate_yandex_panoramas(lat: float, lon: float) -> str:
    return f"https://yandex.ru/maps/?ll={lon},{lat}&panorama[point]={lon},{lat}"

def generate_2gis(lat: float, lon: float, zoom: int = 17) -> str:
    return f"https://2gis.ru/geo/{lon},{lat}?m={lon},{lat}/{zoom}"

def generate_google_maps(lat: float, lon: float, zoom: int = 17) -> str:
    return f"https://www.google.com/maps/@{lat},{lon},{zoom}z/data=!3m1!1e3"

def generate_all_links(lat: float, lon: float) -> dict:
    return {
        "Yandex Maps": generate_yandex_maps(lat, lon),
        "Yandex Panoramas": generate_yandex_panoramas(lat, lon),
        "2GIS": generate_2gis(lat, lon),
        "Google Satellite": generate_google_maps(lat, lon)
    }
