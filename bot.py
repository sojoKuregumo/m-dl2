import pyrogram
from time import time 
from loguru import logger

from pyrogram import idle
import random, os, shutil, asyncio

from pyrogram import utils as pyroutils
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class Vars:
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
    UPDATE_CHANNEL = int(os.environ.get("UPDATE_CHANNEL", "0"))
    DB_URL = os.environ.get("DB_URL", "")
    DB_NAME = os.environ.get("DB_NAME", "Manhwadb")
    PORT = int(os.environ.get("PORT", "8080"))
    ADMINS = list(map(int, os.environ.get("ADMINS", "").split(","))) if os.environ.get("ADMINS") else []
    IS_PRIVATE = os.environ.get("IS_PRIVATE", None)
    CONSTANT_DUMP_CHANNEL = os.environ.get("CONSTANT_DUMP_CHANNEL", None)
    WEBS_HOST = os.environ.get("WEBS_HOST", None)
    FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")
    SHORTENER = os.environ.get("SHORTENER", None)
    SHORTENER_API = os.environ.get("SHORTENER_API", "")
    DURATION = int(os.environ.get("DURATION", "20"))

    PING = time()

    # ✅ plugins added back
    plugins = dict(root="TG")

    PICS = (
        "https://ik.imagekit.io/jbxs2z512/hd-anime-prr1y1k5gqxfcgpv.jpg?updatedAt=1748487947183",
        "https://ik.imagekit.io/jbxs2z512/naruto_GxcPgSeOy.jpg?updatedAt=1748486799631",
        "https://ik.imagekit.io/jbxs2z512/dazai-osamu-sunset-rooftop-anime-wallpaper-cover.jpg?updatedAt=1748488276069",
        "https://ik.imagekit.io/jbxs2z512/thumb-1920-736461.png?updatedAt=1748488419323",
        # ... (rest of your links here unchanged)
    )


pyroutils.MIN_CHAT_ID = -99999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

class Manhwa_Bot(pyrogram.Client, Vars):
    def __init__(self):
        super().__init__(
            "ManhwaBot",
            api_id=self.API_ID,
            api_hash=self.API_HASH,
            bot_token=self.BOT_TOKEN,
            plugins=self.plugins,
            workers=50,
        )
        self.logger = logger
        self.__version__ = pyrogram.__version__
    
    async def start(self):
        await super().start()
        
        async def run_flask():
            cmds = ("gunicorn", "app:app")
            process = await asyncio.create_subprocess_exec(
                *cmds,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Flask app failed to start: {stderr.decode()}")
            
            logger.info("Webs app started successfully")
        
        usr_bot_me = await self.get_me()
        
        if os.path.exists("restart_msg.txt"):
            with open("restart_msg.txt", "r") as f:
                chat_id, message_id = f.read().split(":")
                f.close()

            try:
                await self.edit_message_text(int(chat_id), int(message_id), "<code>Restarted Successfully</code>")
            except Exception as e:
                logger.exception(e)

            os.remove("restart_msg.txt")
        
        if os.path.exists("Process"):
            shutil.rmtree("Process")
        
        # ✅ raw string to avoid SyntaxWarning
        self.logger.info(r"""
     ___       __   ___  ________  ________  ________  ________          ________  ________  _________  ________      
    |\  \     |\  \|\  \|\_____  \|\   __  \|\   __  \|\   ___ \        |\   __  \|\   __  \|\___   ___\\   ____\     
    \ \  \    \ \  \ \  \\|___/  /\ \  \|\  \ \  \|\  \ \  \_|\ \       \ \  \|\ /\ \  \|\  \|___ \  \_\ \  \___|_    
     \ \  \  __\ \  \ \  \   /  / /\ \   __  \ \   _  _\ \  \ \\ \       \ \   __  \ \  \\\  \   \ \  \ \ \_____  \   
      \ \  \|\__\_\  \ \  \ /  /_/__\ \  \ \  \ \  \\  \\ \  \_\\ \       \ \  \|\  \ \  \\\  \   \ \  \ \|____|\  \  
       \ \____________\ \__\\________\ \__\ \__\ \__\\ _\\ \_______\       \ \_______\ \_______\   \ \__\  ____\_\  \ 
        \|____________|\|__|\|_______|\|__|\|__|\|__|\|__|\|_______|        \|_______|\|_______|    \|__| |\_________\
                                                                                                          \|_________|
        """)
        self.username = usr_bot_me.username
        self.logger.info("Made By https://t.me/Wizard_Bots ")
        self.logger.info(f"Manhwa Bot Started as {usr_bot_me.first_name} | @{usr_bot_me.username}")
        
        if self.WEBS_HOST:
            await run_flask()
        
        MSG = """<blockquote><b>🔥 SYSTEMS ONLINE. READY TO RUMBLE. 🔥
Sleep mode deactivated. Neural cores at 100%. Feed me tasks, and watch magic happen. Let’s. Get. Dangerous.</b></blockquote>"""
        
        PICS = random.choice(Vars.PICS)
        
        button = [[
            InlineKeyboardButton('*Start Now*', url=f"https://t.me/{usr_bot_me.username}?start=start"),
            InlineKeyboardButton("*Channel*", url="https://t.me/Wizard_Bots")
        ]]
        
        try:
            await self.send_photo(self.UPDATE_CHANNEL, photo=PICS, caption=MSG, reply_markup=InlineKeyboardMarkup(button))
        except:
            pass

    
    async def stop(self):
        await super().stop()
        self.logger.info("Manhwa Bot Stopped")


Bot = Manhwa_Bot()
