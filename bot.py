import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


TOKEN = os.getenv("8576848943:AAFXA8S-XFMY1ezUDqk1WwcB2Z9WOZLbAcU")
API_KEY = os.getenv("a3ca679b828a23fb0ff7faa68aab492f")


def formatear_hora(unix_time, timezone_offset=0):
    if unix_time in (None, "N/A"):
        return "N/A"
    dt = datetime.utcfromtimestamp(unix_time + timezone_offset)
    return dt.strftime("%H:%M")


def direccion_viento(grados):
    if grados in (None, "N/A"):
        return "N/A"

    direcciones = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    indice = round(grados / 45) % 8
    return direcciones[indice]


def emoji_clima(descripcion):
    desc = descripcion.lower()

    if "torment" in desc:
        return "⛈️"
    if "lluv" in desc or "drizzle" in desc:
        return "🌧️"
    if "nieve" in desc or "snow" in desc:
        return "❄️"
    if "niebla" in desc or "mist" in desc or "fog" in desc or "haze" in desc:
        return "🌫️"
    if "nube" in desc or "cloud" in desc:
        return "☁️"
    if "despejado" in desc or "clear" in desc:
        return "☀️"

    return "🌤️"


def consejo_temperatura(temp):
    if temp == "N/A":
        return ""

    if temp >= 35:
        return "🔥 Hace muchísimo calor"
    if temp >= 28:
        return "😅 Hace bastante calor"
    if temp >= 20:
        return "👌 Temperatura agradable"
    if temp >= 10:
        return "🧥 Fresquito suave"
    return "🥶 Hace frío"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Dime una ciudad 🌍\n"
        "Ejemplo: Almería, Madrid, París, Tokio..."
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()

    if not city:
        await update.message.reply_text("Escribe una ciudad.")
        return

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "es"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or not data.get("main"):
            await update.message.reply_text("No encontré esa ciudad 😅")
            return

        nombre = data.get("name", city)
        pais = data.get("sys", {}).get("country", "")
        timezone_offset = data.get("timezone", 0)

        temp = data["main"].get("temp", "N/A")
        feels_like = data["main"].get("feels_like", "N/A")
        temp_min = data["main"].get("temp_min", "N/A")
        temp_max = data["main"].get("temp_max", "N/A")
        humidity = data["main"].get("humidity", "N/A")
        pressure = data["main"].get("pressure", "N/A")

        descripcion = data["weather"][0].get("description", "sin datos")
        clima_emoji = emoji_clima(descripcion)

        wind_speed = data.get("wind", {}).get("speed", "N/A")
        wind_deg = data.get("wind", {}).get("deg", None)
        wind_gust = data.get("wind", {}).get("gust", "N/A")

        clouds = data.get("clouds", {}).get("all", "N/A")
        visibility = data.get("visibility", "N/A")

        sunrise = data.get("sys", {}).get("sunrise")
        sunset = data.get("sys", {}).get("sunset")

        vis_km = round(visibility / 1000, 1) if isinstance(visibility, (int, float)) else "N/A"
        viento_cardinal = direccion_viento(wind_deg)
        consejo = consejo_temperatura(temp)

        mensaje = (
            f"📍 {nombre}, {pais}\n"
            f"{clima_emoji} Estado: {descripcion.capitalize()}\n\n"
            f"🌡️ Temperatura: {temp}°C\n"
            f"🥵 Sensación térmica: {feels_like}°C\n"
            f"⬇️ Mínima: {temp_min}°C\n"
            f"⬆️ Máxima: {temp_max}°C\n\n"
            f"💧 Humedad: {humidity}%\n"
            f"🧭 Presión: {pressure} hPa\n"
            f"🌬️ Viento: {wind_speed} m/s ({viento_cardinal})\n"
            f"🌀 Ráfagas: {wind_gust} m/s\n"
            f"☁️ Nubes: {clouds}%\n"
            f"👀 Visibilidad: {vis_km} km\n"
            f"🌅 Amanecer: {formatear_hora(sunrise, timezone_offset)}\n"
            f"🌇 Atardecer: {formatear_hora(sunset, timezone_offset)}"
        )

        if consejo:
            mensaje += f"\n\n{consejo}"

        await update.message.reply_text(mensaje)

    except requests.exceptions.Timeout:
        await update.message.reply_text("La consulta tardó demasiado. Prueba otra vez.")
    except requests.exceptions.RequestException:
        await update.message.reply_text("Error de conexión con la API del tiempo.")
    except Exception as e:
        await update.message.reply_text(f"Error inesperado: {e}")


def main():
    if not TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno.")

    if not API_KEY:
        raise RuntimeError("Falta OPENWEATHER_API_KEY en variables de entorno.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, weather))

    print("Bot del tiempo arrancado...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()