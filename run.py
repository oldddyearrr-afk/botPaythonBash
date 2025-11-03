#!/usr/bin/env python3
# run.py - نقطة الدخول الرئيسية للمشروع
import sys
import os

# إضافة المسار الجذري للمشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python_src.main import main
import asyncio

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 تليجرام بوت للبث المباشر - Python + Bash Integration")
    print("=" * 60)
    asyncio.run(main())
