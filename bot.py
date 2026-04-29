import os
import requests
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# Railway variables recomendadas:
# TELEGRAM_TOKEN=token_del_bot
# OPENWEATHER_API_KEY=api_key_openweather
#
# También acepta TOKEN y API_KEY como nombres alternativos.
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN")
API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("API_KEY")


def formatear_hora(unix_time, timezone_offset=0):
    if unix_time in (None, "N/A"):
        return "N/A"

    try:
        dt = datetime.fromtimestamp(unix_time + timezone_offset, timezone.utc)
        return dt.strftime("%H:%M")
    except Exception:
        return "N/A"


def direccion_viento(grados):
    if grados in (None, "N/A"):
        return "N/A"

    try:
        direcciones = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        indice = round(grados / 45) % 8
        return direcciones[indice]
    except Exception:
        return "N/A"


def emoji_clima(descripcion):
    desc = str(descripcion).lower()

    if "torment" in desc or "thunderstorm" in desc:
        return "⛈️"
    if "lluv" in desc or "drizzle" in desc or "rain" in desc:
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
    if not isinstance(temp, (int, float)):
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


def formatear_numero(valor, sufijo=""):
    if isinstance(valor, (int, float)):
        return f"{round(valor, 1)}{sufijo}"

    return f"N/A{sufijo}" if sufijo else "N/A"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "Dime una ciudad 🌍\n"
        "Ejemplo: Almería, Madrid, París, Tokio..."
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    city = update.message.text.strip()

    if not city:
        await update.message.reply_text("Escribe una ciudad.")
        return

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "es",
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        try:
            data = response.json()
        except ValueError:
            await update.message.reply_text("La API devolvió una respuesta no válida.")
            return

        if response.status_code == 401:
            await update.message.reply_text("La API key de OpenWeather no es válida.")
            return

        if response.status_code == 404:
            await update.message.reply_text("No encontré esa ciudad 😅")
            return

        if response.status_code != 200 or not data.get("main"):
            await update.message.reply_text("No pude consultar el tiempo ahora mismo.")
            return

        nombre = data.get("name", city)
        pais = data.get("sys", {}).get("country", "")
        timezone_offset = data.get("timezone", 0)

        main_data = data.get("main", {})
        weather_data = data.get("weather", [{}])[0]
        wind_data = data.get("wind", {})
        clouds_data = data.get("clouds", {})
        sys_data = data.get("sys", {})

        temp = main_data.get("temp", "N/A")
        feels_like = main_data.get("feels_like", "N/A")
        temp_min = main_data.get("temp_min", "N/A")
        temp_max = main_data.get("temp_max", "N/A")
        humidity = main_data.get("humidity", "N/A")
        pressure = main_data.get("pressure", "N/A")

        descripcion = weather_data.get("description", "sin datos")
        clima_emoji = emoji_clima(descripcion)

        wind_speed = wind_data.get("speed", "N/A")
        wind_deg = wind_data.get("deg", None)
        wind_gust = wind_data.get("gust", "N/A")

        clouds = clouds_data.get("all", "N/A")
        visibility = data.get("visibility", "N/A")

        sunrise = sys_data.get("sunrise")
        sunset = sys_data.get("sunset")

        vis_km = (
            round(visibility / 1000, 1)
            if isinstance(visibility, (int, float))
            else "N/A"
        )

        viento_cardinal = direccion_viento(wind_deg)
        consejo = consejo_temperatura(temp)

        mensaje = (
            f"📍 {nombre}, {pais}\n"
            f"{clima_emoji} Estado: {str(descripcion).capitalize()}\n\n"
            f"🌡️ Temperatura: {formatear_numero(temp, '°C')}\n"
            f"🥵 Sensación térmica: {formatear_numero(feels_like, '°C')}\n"
            f"⬇️ Mínima: {formatear_numero(temp_min, '°C')}\n"
            f"⬆️ Máxima: {formatear_numero(temp_max, '°C')}\n\n"
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
    print("Iniciando bot del tiempo...")

    if not TOKEN:
        raise RuntimeError(
            "Falta TELEGRAM_TOKEN en Railway. "
            "También acepto TOKEN como nombre alternativo."
        )

    if not API_KEY:
        raise RuntimeError(
            "Falta OPENWEATHER_API_KEY en Railway. "
            "También acepto API_KEY como nombre alternativo."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, weather))

    print("Bot del tiempo arrancado correctamente.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()