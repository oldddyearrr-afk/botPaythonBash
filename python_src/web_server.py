# web_server.py - خادم الويب
from aiohttp import web

async def handle_health(request):
    """معالج صفحة الصحة"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Bot Status</title>
    </head>
    <body style="margin:0;padding:0;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:Arial,sans-serif;">
        <div style="text-align:center;">
            <h1 style="font-size:36px;margin:0;">🤖 is bot live</h1>
            <p style="font-size:18px;margin:10px 0 0 0;">by: @xl9rr</p>
            <p style="font-size:14px;color:#666;margin:10px 0 0 0;">Python + Bash Integration</p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def start_web_server():
    """تشغيل خادم الويب"""
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    print("🌐 Web Server: http://0.0.0.0:5000")
