# bash_interface.py - واجهة الاتصال مع سكربتات Bash
import subprocess
import json
import os

class BashInterface:
    def __init__(self):
        # تحديد مسارات السكربتات بشكل ديناميكي
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.processor_script = os.path.join(base_dir, "bash_src", "video_processor.sh")
        self.utils_script = os.path.join(base_dir, "bash_src", "utils.sh")
        
        # التأكد من وجود السكربتات
        if not os.path.exists(self.processor_script):
            raise FileNotFoundError(f"السكربت غير موجود: {self.processor_script}")
        if not os.path.exists(self.utils_script):
            raise FileNotFoundError(f"السكربت غير موجود: {self.utils_script}")
    
    def _run_bash_script(self, script_path, args):
        """تشغيل سكربت Bash وإرجاع النتيجة كـ JSON"""
        try:
            result = subprocess.run(
                ["bash", script_path] + args,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid JSON response"}
            
            return {"success": False, "error": result.stderr or "No output"}
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def record_clip(self, source_url, output_path, duration, watermark_text="", watermark_enabled=True):
        """تسجيل مقطع فيديو مع علامة مائية"""
        args = [
            "record_clip",
            source_url,
            output_path,
            str(duration),
            watermark_text if watermark_enabled else "",
            "true" if watermark_enabled else "false"
        ]
        result = self._run_bash_script(self.processor_script, args)
        return result
import json
import os

class BashInterface:
    """واجهة للتواصل مع سكربتات Bash"""
    
    def __init__(self, bash_dir="bash_src"):
        self.bash_dir = bash_dir
        self.video_processor = os.path.join(bash_dir, "video_processor.sh")
        self.utils_script = os.path.join(bash_dir, "utils.sh")
        
        # التأكد من وجود السكربتات
        if not os.path.exists(self.video_processor):
            raise FileNotFoundError(f"Video processor script not found: {self.video_processor}")
        if not os.path.exists(self.utils_script):
            raise FileNotFoundError(f"Utils script not found: {self.utils_script}")
    
    def _run_bash_script(self, script_path, args, timeout=90):
        """تشغيل سكربت Bash وإرجاع النتيجة"""
        try:
            result = subprocess.run(
                ["bash", script_path] + args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # محاولة تحليل الناتج كـ JSON
            try:
                output = json.loads(result.stdout.strip())
                return {
                    "success": result.returncode == 0,
                    "exit_code": result.returncode,
                    "data": output,
                    "stderr": result.stderr
                }
            except json.JSONDecodeError:
                return {
                    "success": result.returncode == 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "error": "Timeout expired"
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e)
            }
    
    def record_clip(self, source_url, output_path, duration, watermark_text="", watermark_enabled=True):
        """تسجيل مقطع فيديو مع علامة مائية باستخدام Bash"""
        args = [
            "record",
            source_url,
            output_path,
            str(duration),
            watermark_text,
            "true" if watermark_enabled else "false"
        ]
        
        result = self._run_bash_script(self.video_processor, args)
        return result
    
    def compress_video(self, input_path, output_path, crf=28):
        """ضغط فيديو باستخدام Bash"""
        args = ["compress", input_path, output_path, str(crf)]
        result = self._run_bash_script(self.video_processor, args)
        return result
    
    def get_video_info(self, video_path):
        """الحصول على معلومات الفيديو باستخدام Bash"""
        args = ["info", video_path]
        result = self._run_bash_script(self.utils_script, args)
        return result
    
    def cleanup_temp_files(self, temp_dir="/tmp", pattern="smart_clip_*.mp4"):
        """تنظيف الملفات المؤقتة باستخدام Bash"""
        args = ["cleanup", temp_dir, pattern]
        result = self._run_bash_script(self.utils_script, args)
        return result
    
    def check_ffmpeg(self):
        """التحقق من توفر FFmpeg باستخدام Bash"""
        args = ["check_ffmpeg"]
        result = self._run_bash_script(self.utils_script, args)
        return result
    
    def check_disk_space(self, path="."):
        """التحقق من المساحة المتاحة باستخدام Bash"""
        args = ["check_disk", path]
        result = self._run_bash_script(self.utils_script, args)
        return result
    
    def create_directory(self, dir_path):
        """إنشاء مجلد آمن باستخدام Bash"""
        args = ["create_dir", dir_path]
        result = self._run_bash_script(self.utils_script, args)
        return result
    
    def log_message(self, message, level="INFO", log_file="logs/bash.log"):
        """تسجيل رسالة في ملف log باستخدام Bash"""
        args = ["log", log_file, message, level]
        result = self._run_bash_script(self.utils_script, args)
        return result
