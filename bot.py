
import os
import asyncio
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")
VIP_CHAT_ID = os.getenv("VIP_CHAT_ID")

trades = {}
alerted = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "NASDAQ ZONE Bot aktif!\n"
        "/ekle AAPL 250\n"
        "/liste\n"
        "/sil AAPL"
    )

async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Kullanım: /ekle AAPL 250")
        return

    symbol = context.args[0].upper()

    try:
        level = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Geçerli bir fiyat gir.")
        return

    trades[symbol] = level
    alerted.discard(symbol)

    await update.message.reply_text(
        f"{symbol} eklendi.\nKırılım seviyesi: {level}"
    )

async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not trades:
        await update.message.reply_text("Henüz işlem eklenmedi.")
        return

    message = "NASDAQ ZONE İŞLEMLERİ\n\n"
    for symbol, level in trades.items():
        message += f"{symbol}: {level}\n"

    await update.message.reply_text(message)

async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kullanım: /sil AAPL")
        return

    symbol = context.args[0].upper()
    trades.pop(symbol, None)
    alerted.discard(symbol)

    await update.message.reply_text(f"{symbol} silindi.")

async def monitor(app):
    while True:
        for symbol, level in list(trades.items()):
            try:
                url = (
                    "https://finnhub.io/api/v1/quote"
                    f"?symbol={symbol}&token={FINNHUB_TOKEN}"
                )
                data = requests.get(url, timeout=10).json()
                price = float(data.get("c", 0))

                if price <= 0:
                    continue

                distance = (level - price) / level * 100

                if 0 <= distance <= 2 and symbol not in alerted:
                    await app.bot.send_message(
                        chat_id=VIP_CHAT_ID,
                        text=(
                            f"🚨 NASDAQ ZONE VIP ALARM\n\n"
                            f"📊 Hisse: {symbol}\n"
                            f"💰 Güncel fiyat: {price}\n"
                            f"🎯 Kırılım seviyesi: {level}\n"
                            f"⚡ Kırılıma uzaklık: %{distance:.2f}"
                        )
                    )
                    alerted.add(symbol)

            except Exception as e:
                print(f"{symbol} hata: {e}")

        await asyncio.sleep(60)

async def post_init(app):
    asyncio.create_task(monitor(app))

def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("sil", sil))

    app.run_polling()

if __name__ == "__main__":
    main()
                              
