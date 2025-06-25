from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

API_ID = int(os.getenv("API_ID", 123456))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
ADMINS = list(map(int, os.getenv("ADMINS", "").split()))

client = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo["forwardbot"]
collection = db["chats"]

app = FastAPI()

def is_admin(user_id):
    return user_id in ADMINS

@client.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    if is_admin(message.from_user.id):
        await message.reply_text("👋 Hello Admin! Use /help to see available commands.")

@client.on_message(filters.command("help") & filters.private)
async def help_cmd(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    help_text = (
        "**Forward Bot Commands:**\n"
        "/addchat <source> <destination> - Add source to destination\n"
        "/delchat <source> <destination> - Delete source to destination\n"
        "/help - Show this help message\n"
        "/start - Start message"
    )
    await message.reply_text(help_text)

@client.on_message(filters.command("addchat") & filters.private)
async def add_chat(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, source, dest = message.text.split()
        collection.update_one({"source": source, "destination": dest}, {"$set": {"source": source, "destination": dest}}, upsert=True)
        await message.reply_text("✅ Chat pair added and refreshed.")
    except ValueError:
        await message.reply_text("❌ Usage: /addchat <source> <destination>")

@client.on_message(filters.command("delchat") & filters.private)
async def del_chat(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, source, dest = message.text.split()
        result = collection.delete_one({"source": source, "destination": dest})
        if result.deleted_count:
            await message.reply_text("✅ Chat pair removed.")
        else:
            await message.reply_text("❌ Pair not found.")
    except ValueError:
        await message.reply_text("❌ Usage: /delchat <source> <destination>")
@client.on_message(filters.command("list") & filters.private)
async def list_chats(_, message: Message):
    if not is_admin(message.from_user.id):
        return

    pairs = list(collection.find())
    if not pairs:
        await message.reply_text("⚠️ No chat pairs found.")
        return

    text = "**📋 Chat Pairs:**\n\n"
    for i, pair in enumerate(pairs, start=1):
        text += f"{i}. Source: `{pair['source']}` → Destination: `{pair['destination']}`\n"

    await message.reply_text(text)

@client.on_message(filters.channel)
async def forward_media(_, message: Message):
    if not (message.video or message.document or message.photo or message.audio):
        return
    chat_pairs = list(collection.find({"source": str(message.chat.id)}))
    for pair in chat_pairs:
        try:
            await client.copy_message(
                chat_id=int(pair["destination"]),
                from_chat_id=message.chat.id,
                message_id=message.id
            )
            await asyncio.sleep(2)  # per-destination delay
        except Exception as e:
            print(f"Failed to forward to {pair['destination']}: {e}")

# FastAPI health check endpoint with HEAD support
@app.route("/", methods=["GET", "HEAD"])
async def health_check(request: Request):
    return JSONResponse({"status": "healthy"})

async def send_restart_message():
    for admin_id in ADMINS:
        try:
            await client.send_message(admin_id, "✅ Bot restarted and is now running.")
        except Exception:
            pass

async def start_bot():
    await client.start()
    print("Bot started!")
    await send_restart_message()

    # Create two asyncio tasks
    forever_event = asyncio.Event()
    bot_task = asyncio.create_task(forever_event.wait())  # Keeps bot running

    config = uvicorn.Config(app=app, host="0.0.0.0", port=8080, log_level="info", loop="asyncio")
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())

    await asyncio.gather(bot_task, api_task)
