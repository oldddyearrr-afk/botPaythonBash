# streaming.py - نظام البث (Producer/Consumer)
import time
import asyncio
import os
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from telegram import Bot
from python_src.bash_interface import BashInterface

class BroadcastController:
    """المتحكم الرئيسي في البث"""
    
    def __init__(self, config, bot, stats, active_users):
        self.config = config
        self.bot = bot
        self.stats = stats
        self.active_users = active_users
        
        # واجهة Bash
        self.bash = BashInterface()
        
        # حالة البث
        self.broadcast_running = False
        self.stream_position = 0.0
        self.stream_lock = threading.Lock()
        
        # قائمة الانتظار
        self.clip_queue = Queue(maxsize=self.config.get("BUFFER_SIZE", 5))
        
        # حالة Producer/Consumer
        self.producer_running = False
        self.consumer_running = False
        
        # إنشاء المجلدات المطلوبة باستخدام Bash
        for directory in ["temp_clips", "logs"]:
            result = self.bash.create_directory(directory)
            if result["success"]:
                print(f"📁 {directory}/ جاهز")
            else:
                error_msg = result.get("error", "Unknown error")
                raise RuntimeError(f"فشل إنشاء المجلد {directory}/: {error_msg}")
        
        # التحقق من FFmpeg عند البداية
        result = self.bash.check_ffmpeg()
        if result["success"] and result["data"].get("installed"):
            print(f"✅ FFmpeg متوفر")
        else:
            print(f"⚠️ تحذير: FFmpeg غير متوفر")
    
    def is_running(self):
        return self.broadcast_running
    
    def get_stream_position(self):
        with self.stream_lock:
            return self.stream_position
    
    def get_queue_size(self):
        return self.clip_queue.qsize()
    
    def stop_broadcast(self):
        self.broadcast_running = False
    
    async def start_broadcast(self):
        """بدء البث"""
        self.broadcast_running = True
        self.stream_position = 0.0
        
        # تفريغ القائمة
        while not self.clip_queue.empty():
            try:
                self.clip_queue.get_nowait()
            except:
                break
        
        await self._broadcast_loop()
    
    def _smart_producer(self):
        """المنتج الذكي - يسجل المقاطع باستخدام Bash"""
        self.producer_running = True
        clip_counter = 0
        clip_duration = float(self.config.get("CLIP_SECONDS"))
        failures = 0
        
        print("🎬 المنتج الذكي (Bash): بدء العمل")
        
        while self.broadcast_running:
            try:
                clip_counter += 1
                
                with self.stream_lock:
                    current_position = self.stream_position
                
                # استخدام temp_clips بدلاً من /tmp
                output_path = f"temp_clips/smart_clip_{clip_counter}.mp4"
                
                print(f"⏺️  تسجيل #{clip_counter} من [{current_position:.1f}ث] (Bash)")
                
                start_time = time.time()
                
                # استدعاء Bash لتسجيل المقطع
                result = self.bash.record_clip(
                    source_url=self.config.get("SOURCE_URL"),
                    output_path=output_path,
                    duration=clip_duration,
                    watermark_text=self.config.get("BOTTOM_WATERMARK_TEXT", ""),
                    watermark_enabled=self.config.get("BOTTOM_WATERMARK_ENABLED", True)
                )
                
                elapsed = time.time() - start_time
                
                if result["success"] and os.path.exists(output_path) and self.broadcast_running:
                    with self.stream_lock:
                        self.stream_position += clip_duration
                    
                    self.clip_queue.put((output_path, current_position, clip_counter), timeout=5)
                    print(f"✅ #{clip_counter} ({elapsed:.1f}ث) → التالي: {self.stream_position:.1f}ث | Q:{self.clip_queue.qsize()}")
                    failures = 0
                else:
                    self.stats["clips_failed"] += 1
                    failures += 1
                    error_msg = result.get("data", {}).get("error", "Unknown error") if "data" in result else result.get("error", "Unknown")
                    print(f"❌ فشل #{clip_counter}: {error_msg}")
                    
                    if failures >= 3:
                        print("⚠️ فشل متكرر، انتظار 15ث")
                        time.sleep(15)
                        failures = 0
                    else:
                        time.sleep(3)
                        
            except Exception as e:
                print(f"🚨 خطأ producer: {str(e)[:50]}")
                failures += 1
                time.sleep(3 if failures < 3 else 15)
        
        self.producer_running = False
        print("🛑 المنتج: توقف")
    
    async def _smart_consumer(self):
        """المستهلك الذكي - يرسل المقاطع"""
        self.consumer_running = True
        print("📤 المستهلك الذكي: بدء الإرسال")
        
        while self.broadcast_running:
            try:
                try:
                    clip_path, position, counter = self.clip_queue.get(timeout=1)
                except Empty:
                    await asyncio.sleep(0.3)
                    continue
                
                print(f"📤 إرسال #{counter} (من {position:.1f}ث)")
                
                try:
                    await self._send_clip(clip_path)
                except Exception as e:
                    print(f"❌ خطأ إرسال #{counter}: {str(e)[:50]}")
                    try:
                        if os.path.exists(clip_path):
                            os.remove(clip_path)
                    except:
                        pass
                
                sleep_time = self.config.get("SLEEP_BETWEEN", 0)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    
            except Exception as e:
                print(f"🚨 خطأ consumer: {str(e)[:50]}")
                await asyncio.sleep(1)
        
        self.consumer_running = False
        print("🛑 المستهلك: توقف")
    
    async def _send_clip(self, clip_path):
        """إرسال مقطع للقناة والمشتركين"""
        if not os.path.exists(clip_path):
            return False
        
        success_count = 0
        
        # إرسال للقناة
        try:
            with open(clip_path, "rb") as f:
                await self.bot.send_video(
                    chat_id=self.config.get("CHANNEL_ID"),
                    video=f,
                    supports_streaming=True,
                    read_timeout=300,
                    write_timeout=300
                )
            success_count += 1
            print("✅ القناة")
        except Exception as e:
            print(f"❌ القناة: {str(e)[:50]}")
        
        # إرسال للمشتركين
        for user_id in self.active_users:
            try:
                with open(clip_path, "rb") as f:
                    await self.bot.send_video(
                        chat_id=user_id,
                        video=f,
                        supports_streaming=True,
                        read_timeout=300,
                        write_timeout=300
                    )
                success_count += 1
            except:
                pass
            await asyncio.sleep(0.1)
        
        # حذف الملف
        try:
            if os.path.exists(clip_path):
                os.remove(clip_path)
        except:
            pass
        
        self.stats["clips_sent"] += 1
        print(f"📊 {success_count}/{len(self.active_users) + 1}")
        return success_count > 0
    
    async def _send_start_message(self):
        """إرسال رسالة بداية البث"""
        try:
            await self.bot.send_message(
                chat_id=self.config.get("CHANNEL_ID"),
                text="🎬 البث الذكي بدأ\n✨ Python + Bash 🚀"
            )
        except:
            pass
        
        for user_id in self.active_users:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text="🎬 البث الذكي بدأ\n✨ Python + Bash 🚀"
                )
            except:
                pass
            await asyncio.sleep(0.1)
    
    async def _broadcast_loop(self):
        """حلقة البث الرئيسية"""
        print("🎬 بدء البث الذكي (Python + Bash)...")
        await self._send_start_message()
        await asyncio.sleep(1)
        
        executor = ThreadPoolExecutor(max_workers=3)
        loop = asyncio.get_event_loop()
        
        # تشغيل Producer في thread منفصل
        loop.run_in_executor(executor, self._smart_producer)
        
        # تشغيل Consumer
        await self._smart_consumer()
