# bot_commands.py - أوامر البوت
import asyncio
import time
from telegram import Update
from telegram.ext import ContextTypes

class BotCommands:
    def __init__(self, config, stats, active_users, broadcast_controller):
        self.config = config
        self.stats = stats
        self.active_users = active_users
        self.broadcast_controller = broadcast_controller
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return

        user_id = str(update.effective_user.id)
        if user_id not in self.active_users:
            self.active_users.append(user_id)

        status = "🟢 يعمل" if self.broadcast_controller.is_running() else "🔴 متوقف"
        await update.message.reply_text(
            f"✅ أهلاً بك\n\n"
            f"البث: {status}\n"
            f"المشتركين: {len(self.active_users)}\n\n"
            f"/help - عرض الأوامر"
        )
    
    async def startlive_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return

        user_id = str(update.effective_user.id)

        if user_id != self.config.get("YOUR_USER_ID"):
            await update.message.reply_text("❌ للمالك فقط")
            return

        if self.broadcast_controller.is_running():
            await update.message.reply_text("⚠️ البث يعمل")
            return

        await update.message.reply_text("🎬 جاري بدء البث الذكي...")
        
        # بدء البث
        asyncio.create_task(self.broadcast_controller.start_broadcast())
        await asyncio.sleep(2)
        
        await update.message.reply_text(
            f"✅ البث نشط (Python + Bash 🚀)\n"
            f"المشتركين: {len(self.active_users)}\n"
            f"المدة: {self.config.get('CLIP_SECONDS')}ث\n"
            f"Buffer: {self.config.get('BUFFER_SIZE')} مقاطع"
        )
    
    async def stoplive_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return

        user_id = str(update.effective_user.id)

        if user_id != self.config.get("YOUR_USER_ID"):
            await update.message.reply_text("❌ للمالك فقط")
            return

        if not self.broadcast_controller.is_running():
            await update.message.reply_text("⚠️ البث متوقف")
            return

        await update.message.reply_text("🛑 جاري الإيقاف...")
        self.broadcast_controller.stop_broadcast()
        await asyncio.sleep(2)
        await update.message.reply_text("✅ تم إيقاف البث")
    
    async def setbottom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return

        user_id = str(update.effective_user.id)
        if user_id != self.config.get("YOUR_USER_ID"):
            await update.message.reply_text("❌ للمالك فقط")
            return

        if not context.args:
            await update.message.reply_text(
                f"العلامة السفلية: {self.config.get('BOTTOM_WATERMARK_TEXT')}\n\n"
                "مثال: /setbottom Telegram | @media_ayham"
            )
            return

        new_text = " ".join(context.args)
        self.config.set("BOTTOM_WATERMARK_TEXT", new_text)
        await update.message.reply_text(f"✅ تم تغيير العلامة السفلية إلى:\n{new_text}")
    
    async def wbottom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return

        user_id = str(update.effective_user.id)
        if user_id != self.config.get("YOUR_USER_ID"):
            await update.message.reply_text("❌ للمالك فقط")
            return

        current = self.config.get('BOTTOM_WATERMARK_ENABLED', True)
        new_status = not current
        self.config.set('BOTTOM_WATERMARK_ENABLED', new_status)

        status_text = "🟢 مفعلة" if new_status else "🔴 معطلة"
        await update.message.reply_text(f"✅ العلامة السفلية: {status_text}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return

        user_id = str(update.effective_user.id)
        if user_id != self.config.get("YOUR_USER_ID"):
            return

        uptime = time.time() - self.stats["uptime_start"]
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        status = "🟢 يعمل" if self.broadcast_controller.is_running() else "🔴 متوقف"

        bottom_status = "🟢" if self.config.get('BOTTOM_WATERMARK_ENABLED') else "🔴"

        queue_size = self.broadcast_controller.get_queue_size()

        await update.message.reply_text(
            f"📊 الإحصائيات\n\n"
            f"البث: {status}\n"
            f"الموضع: {self.broadcast_controller.get_stream_position():.1f}ث\n"
            f"Buffer: {queue_size}/{self.config.get('BUFFER_SIZE')}\n"
            f"المشتركين: {len(self.active_users)}\n"
            f"المقاطع: {self.stats['clips_sent']}\n"
            f"فشل: {self.stats['clips_failed']}\n"
            f"الوقت: {hours}س {minutes}د\n\n"
            f"العلامة المائية:\n"
            f"{bottom_status} السفلية: {self.config.get('BOTTOM_WATERMARK_TEXT')}\n\n"
            f"🔧 Bash Integration: Active"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return

        await update.message.reply_text(
            "📋 قائمة الأوامر\n\n"
            "للجميع:\n"
            "/start - بدء البوت\n"
            "/help - قائمة الأوامر\n\n"
            "للمالك فقط:\n"
            "/startLIVE - تشغيل البث 🟢\n"
            "/stopLIVE - إيقاف البث 🔴\n\n"
            "العلامة المائية:\n"
            "/setbottom - تغيير نص العلامة المتحركة 🔄\n"
            "/wbottom - تفعيل/تعطيل العلامة\n"
            "/stats - الإحصائيات\n\n"
            "✨ بث ذكي: Python + Bash 🚀"
        )
    
    async def any_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.message:
            return

        user_id = str(update.effective_user.id)
        if user_id not in self.active_users:
            self.active_users.append(user_id)
            await update.message.reply_text("✅ تم تسجيلك في البث")
        else:
            await update.message.reply_text("✅ أنت مسجل")
