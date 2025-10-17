#!/usr/bin/env python3
"""
Combined Server Starter for AI Interview Platform
Starts both Django backend and React frontend servers simultaneously
"""

import os
import sys
import subprocess
import threading
import time
import signal
import platform
from pathlib import Path


class ServerManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.base_dir = Path(__file__).parent
        self.frontend_dir = self.base_dir / "frontend"
        self.venv_path = self.base_dir / "venv"

        # Determine the correct python and pip commands based on OS
        if platform.system() == "Windows":
            self.python_cmd = str(self.venv_path / "Scripts" / "python.exe")
            self.pip_cmd = str(self.venv_path / "Scripts" / "pip.exe")
            self.activate_cmd = str(self.venv_path / "Scripts" / "activate.bat")
        else:
            self.python_cmd = str(self.venv_path / "bin" / "python")
            self.pip_cmd = str(self.venv_path / "bin" / "pip")
            self.activate_cmd = f"source {self.venv_path / 'bin' / 'activate'}"

    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")

        # Check if virtual environment exists
        if not self.venv_path.exists():
            print("❌ Virtual environment not found. Please run the setup first.")
            return False

        # Check if frontend directory exists
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found.")
            return False

        # Check if node_modules exists in frontend
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            try:
                subprocess.run(["npm", "install"], cwd=self.frontend_dir, check=True)
            except subprocess.CalledProcessError:
                print("❌ Failed to install frontend dependencies.")
                return False

        print("✅ All prerequisites met!")
        return True

    def start_backend(self):
        """Start the Django backend server"""
        print("🚀 Starting Django backend server...")
        try:
            if platform.system() == "Windows":
                # Windows command
                cmd = [self.python_cmd, "manage.py", "runserver", "127.0.0.1:8000"]
            else:
                # Unix command
                cmd = (
                    f"{self.activate_cmd} && python manage.py runserver 127.0.0.1:8000"
                )

            if platform.system() == "Windows":
                self.backend_process = subprocess.Popen(
                    cmd,
                    cwd=self.base_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            else:
                self.backend_process = subprocess.Popen(
                    cmd,
                    cwd=self.base_dir,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                )

            print("✅ Backend server started on http://127.0.0.1:8000")

        except Exception as e:
            print(f"❌ Failed to start backend server: {e}")
            return False
        return True

    def start_frontend(self):
        """Start the React frontend server"""
        print("🚀 Starting React frontend server...")
        try:
            cmd = ["npm", "run", "dev"]

            if platform.system() == "Windows":
                self.frontend_process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            else:
                self.frontend_process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                )

            print("✅ Frontend server started on http://localhost:5173")

        except Exception as e:
            print(f"❌ Failed to start frontend server: {e}")
            return False
        return True

    def monitor_processes(self):
        """Monitor both processes and handle output"""

        def monitor_backend():
            if self.backend_process:
                for line in iter(self.backend_process.stdout.readline, ""):
                    if line:
                        print(f"[BACKEND] {line.strip()}")

        def monitor_frontend():
            if self.frontend_process:
                for line in iter(self.frontend_process.stdout.readline, ""):
                    if line:
                        print(f"[FRONTEND] {line.strip()}")

        # Start monitoring threads
        backend_thread = threading.Thread(target=monitor_backend, daemon=True)
        frontend_thread = threading.Thread(target=monitor_frontend, daemon=True)

        backend_thread.start()
        frontend_thread.start()

    def stop_servers(self):
        """Stop both servers gracefully"""
        print("\n🛑 Stopping servers...")

        if self.backend_process:
            try:
                if platform.system() == "Windows":
                    self.backend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                print("✅ Backend server stopped")
            except Exception as e:
                print(f"⚠️  Error stopping backend: {e}")

        if self.frontend_process:
            try:
                if platform.system() == "Windows":
                    self.frontend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                print("✅ Frontend server stopped")
            except Exception as e:
                print(f"⚠️  Error stopping frontend: {e}")

    def run(self):
        """Main execution method"""
        print("🎯 AI Interview Platform - Combined Server Starter")
        print("=" * 50)

        # Check prerequisites
        if not self.check_prerequisites():
            sys.exit(1)

        # Start servers
        backend_started = self.start_backend()
        time.sleep(2)  # Give backend time to start

        frontend_started = self.start_frontend()

        if not backend_started or not frontend_started:
            print("❌ Failed to start one or more servers")
            self.stop_servers()
            sys.exit(1)

        print("\n🎉 Both servers are running!")
        print("📍 Backend:  http://127.0.0.1:8000")
        print("📍 Frontend: http://localhost:5173")
        print("\n💡 Press Ctrl+C to stop both servers")

        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self.stop_servers()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Monitor processes
        self.monitor_processes()

        try:
            # Keep the main thread alive
            while True:
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ Backend process died")
                    break
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ Frontend process died")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_servers()


if __name__ == "__main__":
    manager = ServerManager()
    manager.run()
