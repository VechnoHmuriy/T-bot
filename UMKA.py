import asyncio
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
import requests
import pandas as pd
from io import BytesIO

# === SETTINGS ===
TOKEN = "7933808662:AAEb-4ztRVmOPyZCFdfqRw6J5RwbYTtZJV8"
EXCEL_URL = "https://norvuz.ru/upload/timetable/1-ochnoe.xls"

# === LOGGING ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Schedule", callback_data="menu_rasp")],
        [InlineKeyboardButton("🏛 Structure", callback_data="menu_struct")],
        [InlineKeyboardButton("📋 Dean's Office", callback_data="menu_dekanat")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    await update.message.reply_text("Welcome! Please choose a section:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# === MENU HANDLER ===
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_rasp":
        keyboard = [
            [InlineKeyboardButton("Exam Session", callback_data="rasp_sess")],
            [InlineKeyboardButton("Classes", callback_data="rasp_pairs")],
            [InlineKeyboardButton("Backlogs", callback_data="rasp_debt")],
            [InlineKeyboardButton("Refresh", callback_data="rasp_update")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_start")]
        ]
        await query.edit_message_text("📅 Schedule:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_struct":
        keyboard = [
            [InlineKeyboardButton("Faculties", callback_data="struct_faculty")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_start")]
        ]
        await query.edit_message_text("🏛 Structure:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_dekanat":
        keyboard = [
            [InlineKeyboardButton("Dean GTF", callback_data="dekanat_gtf")],
            [InlineKeyboardButton("Dean FEEU", callback_data="dekanat_feeu")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_start")]
        ]
        await query.edit_message_text("📋 Deans' offices:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "help":
        await query.edit_message_text("Use /start to restart. Navigate via the buttons.")

    elif data == "back_start":
        await start(update, context)

# === FUNCTION: SCHEDULE BY GROUP ===
def get_schedule(group_name: str) -> str:
    try:
        response = requests.get(EXCEL_URL)
        if response.status_code != 200:
            return "❌ Failed to download the schedule file."

        xls = pd.read_excel(BytesIO(response.content), sheet_name=None)
        result = []

        for sheet, df in xls.items():
            df = df.fillna("")
            for _, row in df.iterrows():
                if any(group_name.lower() in str(cell).lower() for cell in row):
                    line = " | ".join(str(cell) for cell in row if str(cell).strip())
                    result.append(line)

        if not result:
            return f"⚠️ Group {group_name} not found."

        return f"📅 Schedule for {group_name}:\n\n" + "\n".join(result)
    except Exception as e:
        return f"❌ Error reading schedule: {e}"

# === COMMAND /schedule ===
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /schedule IS-101")
        return
    group = context.args[0]
    text = get_schedule(group)
    for i in range(0, len(text), 4096):
        await update.message.reply_text(text[i:i+4096])

# === ОСНОВНОЙ ЗАПУСК ===
from telegram.ext import ApplicationBuilder

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CallbackQueryHandler(menu_handler))

    print("✅ Bot is running...")
    app.run_polling() 