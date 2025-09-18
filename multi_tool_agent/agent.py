import requests
from google.adk.agents import Agent


##### DO NOT EDIT ABOVE THIS LINE #####
# Add your code here


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city using Open-Meteo API.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    pass


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    pass


root_agent = ...


##### DO NOT EDIT BELOW THIS LINE #####

_CITY_TIMEZONE_MAP = {
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "houston": "America/Chicago",
    "phoenix": "America/Phoenix",
    "philadelphia": "America/New_York",
    "san antonio": "America/Chicago",
    "san diego": "America/Los_Angeles",
    "dallas": "America/Chicago",
    "san jose": "America/Los_Angeles",
    "austin": "America/Chicago",
    "jacksonville": "America/New_York",
    "fort worth": "America/Chicago",
    "columbus": "America/New_York",
    "charlotte": "America/New_York",
    "san francisco": "America/Los_Angeles",
    "sf": "America/Los_Angeles",
    "indianapolis": "America/New_York",
    "seattle": "America/Los_Angeles",
    "denver": "America/Denver",
    "washington": "America/New_York",
    "dc": "America/New_York",
    "boston": "America/New_York",
    "el paso": "America/Denver",
    "detroit": "America/New_York",
    "nashville": "America/Chicago",
    "portland": "America/Los_Angeles",
    "oklahoma city": "America/Chicago",
    "las vegas": "America/Los_Angeles",
    "louisville": "America/New_York",
    "baltimore": "America/New_York",
    "milwaukee": "America/Chicago",
    "albuquerque": "America/Denver",
    "tucson": "America/Phoenix",
    "fresno": "America/Los_Angeles",
    "mesa": "America/Phoenix",
    "sacramento": "America/Los_Angeles",
    "atlanta": "America/New_York",
    "kansas city": "America/Chicago",
    "colorado springs": "America/Denver",
    "miami": "America/New_York",
    "raleigh": "America/New_York",
    "omaha": "America/Chicago",
    "long beach": "America/Los_Angeles",
    "virginia beach": "America/New_York",
    "oakland": "America/Los_Angeles",
    "minneapolis": "America/Chicago",
    "tulsa": "America/Chicago",
    "tampa": "America/New_York",
    "arlington": "America/Chicago",
    "new orleans": "America/Chicago",
    # International cities
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "berlin": "Europe/Berlin",
    "rome": "Europe/Rome",
    "madrid": "Europe/Madrid",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "mexico city": "America/Mexico_City",
    "sao paulo": "America/Sao_Paulo",
    "rio de janeiro": "America/Sao_Paulo",
    "buenos aires": "America/Argentina/Buenos_Aires",
    "moscow": "Europe/Moscow",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "bangkok": "Asia/Bangkok",
    "jakarta": "Asia/Jakarta",
    "manila": "Asia/Manila",
    "cairo": "Africa/Cairo",
    "johannesburg": "Africa/Johannesburg",
    "lagos": "Africa/Lagos",
}


def get_coordinates_for_city(city: str) -> dict:
    """Get latitude and longitude coordinates for a city using Open-Meteo's geocoding API.

    Args:
        city (str): The name of the city to geocode.

    Returns:
        dict: Contains status and either coordinates or error message.
    """
    try:
        # Use Open-Meteo's free geocoding API
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city, "count": 1, "language": "en", "format": "json"}

        response = requests.get(geocoding_url, params=params, timeout=10)

        if response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"Geocoding service error (HTTP {response.status_code}). Please try again later.",
            }

        data = response.json()

        if not data.get("results"):
            return {
                "status": "error",
                "error_message": f"City '{city}' not found. Please check the spelling and try again.",
            }

        result = data["results"][0]
        return {
            "status": "success",
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "city_name": result["name"],
            "country": result.get("country", ""),
            "admin1": result.get("admin1", ""),
        }

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Geocoding service request timed out. Please try again.",
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": "Unable to connect to geocoding service. Please check your internet connection.",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error getting coordinates for {city}: {str(e)}",
        }


def get_weather_description(weather_code: int) -> str:
    """Convert Open-Meteo weather code to human-readable description.

    Args:
        weather_code (int): Weather code from Open-Meteo API.

    Returns:
        str: Human-readable weather description.
    """
    # Weather code mapping based on Open-Meteo documentation
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return weather_codes.get(weather_code, f"Unknown weather (code: {weather_code})")
