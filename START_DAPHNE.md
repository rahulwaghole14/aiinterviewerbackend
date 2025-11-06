# How to Start Daphne Server

Daphne is the ASGI server used for this Django application to support WebSocket connections (for real-time AI interviews).

## Quick Start (Windows)

### Method 1: Using Command Line (Recommended)

1. **Activate your virtual environment:**
   ```powershell
   cd "C:\Users\ADMIN\Downloads\ai interview portal (1)"
   venv\Scripts\activate
   ```

2. **Start Daphne:**
   ```powershell
   daphne -b 127.0.0.1 -p 8000 interview_app.asgi:application
   ```

   Or if you prefer to see output in a new window:
   ```powershell
   start cmd /k "venv\Scripts\activate && daphne -b 127.0.0.1 -p 8000 interview_app.asgi:application"
   ```

### Method 2: Using Python Module

```powershell
venv\Scripts\python.exe -m daphne -b 127.0.0.1 -p 8000 interview_app.asgi:application
```

## What You Should See

When Daphne starts successfully, you'll see:
```
2024-XX-XX XX:XX:XX [INFO] Starting server at tcp:port=8000:interface=127.0.0.1
2024-XX-XX XX:XX:XX [INFO] HTTP/2 support not enabled (install the http2 and tls Twisted extras)
2024-XX-XX XX:XX:XX [INFO] Configuring endpoint tcp:port=8000:interface=127.0.0.1
2024-XX-XX XX:XX:XX [INFO] Listening on TCP address 127.0.0.1:8000
```

## Troubleshooting

### If Daphne is not installed:
```powershell
pip install daphne
```

### If you get "Module not found" error:
Make sure you're in the project root directory and your virtual environment is activated.

### If port 8000 is already in use:
Use a different port:
```powershell
daphne -b 127.0.0.1 -p 8001 interview_app.asgi:application
```

## Stopping the Server

Press `Ctrl+C` in the terminal where Daphne is running, or close the command window if using `start cmd /k`.

## Difference from `runserver`

- **`python manage.py runserver`**: Django's development server (HTTP only, no WebSocket support)
- **`daphne`**: ASGI server (HTTP + WebSocket support for real-time features)

For AI interviews with WebSocket connections, you **must use Daphne**.

