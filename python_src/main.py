# main.py - الملف الرئيسي للبوت
import asyncio
import time
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from python_src.config_manager import ConfigManager
from python_src.web_server import start_web_server
from python_src.bot_commands import BotCommands
from python_src.streaming import BroadcastController

async def main():
    """الدالة الرئيسية"""
    
    # تحميل الإعدادات
    config = ConfigManager("config.json")
    
    # التحقق من المتغيرات المطلوبة
    if not config.validate_required_vars():
        exit(1)
    
    # إنشاء البوت
    bot = Bot(token=config.get("BOT_TOKEN"))
    
    # المتغيرات المشتركة
    stats = {"clips_sent": 0, "clips_failed": 0, "uptime_start": time.time()}
    active_users = []
    
    # إضافة المالك للمشتركين
    owner_id = str(config.get("YOUR_USER_ID"))
    if owner_id not in active_users:
        active_users.append(owner_id)
    
    # تعديل معرف القناة إذا لزم الأمر
    channel_id = str(config.get("CHANNEL_ID")).strip()
    if not channel_id.startswith("-100") and not channel_id.startswith("@"):
        if not channel_id.startswith("-"):
            channel_id = f"-100{channel_id}"
        config.set("CHANNEL_ID", channel_id)
    
    print(f"👥 المشتركين: {len(active_users)}")
    print(f"📺 القناة: {channel_id}")
    print(f"🔧 Architecture: Python + Bash")
    
    # إنشاء متحكم البث
    broadcast_controller = BroadcastController(config, bot, stats, active_users)
    
    # إنشاء معالجات الأوامر
    bot_commands = BotCommands(config, stats, active_users, broadcast_controller)
    
    # تشغيل خادم الويب
    asyncio.create_task(start_web_server())
    
    # حلقة رئيسية مع إعادة المحاولة
    while True:
        try:
            application = Application.builder().token(config.get("BOT_TOKEN")).build()
            
            # إضافة معالجات الأوامر
            application.add_handler(CommandHandler("start", bot_commands.start_command))
            application.add_handler(CommandHandler("startLIVE", bot_commands.startlive_command))
            application.add_handler(CommandHandler("stopLIVE", bot_commands.stoplive_command))
            application.add_handler(CommandHandler("help", bot_commands.help_command))
            application.add_handler(CommandHandler("stats", bot_commands.stats_command))
            application.add_handler(CommandHandler("setbottom", bot_commands.setbottom_command))
            application.add_handler(CommandHandler("wbottom", bot_commands.wbottom_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.any_message))
            
            # تهيئة البوت
            await application.initialize()
            await application.start()
            
            if application.updater:
                await application.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES
                )
            
            print("✅ البوت يعمل")
            print("⏸️  استخدم /startLIVE للبدء")
            print("🚀 Python + Bash Integration Active")
            
            # انتظار لانهائي
            await asyncio.Event().wait()
            
        except Exception as e:
            print(f"🚨 خطأ: {str(e)[:100]}")
            print("🔄 إعادة المحاولة بعد 30ث")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
