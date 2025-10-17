# Combined Server Startup Guide

This guide explains how to start both the Django backend and React frontend servers simultaneously.

## 🚀 Quick Start Options

### Option 1: Python Script (Recommended)
```bash
# From the backend root directory
python start_servers.py
```

### Option 2: Shell Script (Unix/Linux/macOS)
```bash
# From the backend root directory
./start_servers.sh
```

### Option 3: Node.js Script (Cross-platform)
```bash
# From the frontend directory
cd frontend
npm run start
# OR
npm run start:both
# OR
npm run start:full
```

### Option 4: Direct Node.js
```bash
# From the frontend directory
cd frontend
node start-with-backend.js
```

## 📋 Prerequisites

Before running any of the combined startup scripts, ensure you have:

1. **Backend Setup:**
   - Python virtual environment created: `python3 -m venv venv`
   - Virtual environment activated: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
   - Dependencies installed: `pip install -r requirements.txt`
   - Database migrated: `python manage.py migrate`

2. **Frontend Setup:**
   - Node.js and npm installed
   - Frontend dependencies will be installed automatically if missing

## 🔧 What Each Script Does

### Python Script (`start_servers.py`)
- ✅ Cross-platform compatibility (Windows, macOS, Linux)
- ✅ Automatic prerequisite checking
- ✅ Automatic frontend dependency installation
- ✅ Process monitoring and graceful shutdown
- ✅ Colored output with timestamps
- ✅ Error handling and logging

### Shell Script (`start_servers.sh`)
- ✅ Unix/Linux/macOS optimized
- ✅ Colored terminal output
- ✅ Background process management
- ✅ Log file generation (`backend.log`, `frontend.log`)
- ✅ Signal handling for clean shutdown

### Node.js Script (`start-with-backend.js`)
- ✅ Cross-platform Node.js solution
- ✅ Real-time output streaming
- ✅ Process lifecycle management
- ✅ Integrated with npm scripts

## 🌐 Server URLs

When both servers are running:
- **Backend API:** http://127.0.0.1:8000
- **Frontend App:** http://localhost:5173

## 🛑 Stopping Servers

All scripts support graceful shutdown:
- Press `Ctrl+C` to stop both servers
- Scripts will automatically clean up processes
- No manual process killing required

## 🔍 Troubleshooting

### Common Issues:

1. **Virtual environment not found:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Unix
   # OR
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Frontend dependencies missing:**
   - Scripts will auto-install, but you can manually run:
   ```bash
   cd frontend
   npm install
   ```

3. **Port conflicts:**
   - Backend uses port 8000
   - Frontend uses port 5173
   - Make sure these ports are available

4. **Permission denied (Unix):**
   ```bash
   chmod +x start_servers.sh
   ```

## 📊 Script Comparison

| Feature | Python Script | Shell Script | Node.js Script |
|---------|---------------|--------------|----------------|
| Cross-platform | ✅ | ❌ (Unix only) | ✅ |
| Auto-install deps | ✅ | ✅ | ✅ |
| Real-time logs | ✅ | ✅ (to files) | ✅ |
| Process monitoring | ✅ | ✅ | ✅ |
| Graceful shutdown | ✅ | ✅ | ✅ |
| Colored output | ✅ | ✅ | ✅ |

## 🎯 Recommended Usage

- **Development:** Use Python script for best cross-platform experience
- **Unix/Linux:** Shell script for native integration
- **Node.js projects:** Use npm scripts from frontend directory

## 🔧 Customization

You can modify any of the scripts to:
- Change default ports
- Add additional services
- Customize logging behavior
- Add health checks
- Integrate with other tools

## 📝 Example Output

```
🎯 AI Interview Platform - Combined Server Starter
==================================================
🔍 Checking prerequisites...
✅ All prerequisites met!
🚀 Starting Django backend server...
✅ Backend server started on http://127.0.0.1:8000
🚀 Starting React frontend server...
✅ Frontend server started on http://localhost:5173

🎉 Both servers are running!
📍 Backend:  http://127.0.0.1:8000
📍 Frontend: http://localhost:5173

💡 Press Ctrl+C to stop both servers
```
