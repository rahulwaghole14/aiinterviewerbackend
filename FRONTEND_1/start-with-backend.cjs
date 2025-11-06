#!/usr/bin/env node

/**
 * Combined Server Starter for AI Interview Platform
 * Cross-platform Node.js script to start both backend and frontend
 */

const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');

class ServerManager {
    constructor() {
        this.backendProcess = null;
        this.frontendProcess = null;
        this.baseDir = path.dirname(__dirname);
        this.frontendDir = __dirname;
        this.venvPath = path.join(this.baseDir, 'venv');
        this.isWindows = process.platform === 'win32';
        
        // Set up signal handlers
        process.on('SIGINT', () => this.cleanup());
        process.on('SIGTERM', () => this.cleanup());
        process.on('exit', () => this.cleanup());
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const colors = {
            info: '\x1b[36m',    // Cyan
            success: '\x1b[32m', // Green
            error: '\x1b[31m',   // Red
            warning: '\x1b[33m', // Yellow
            reset: '\x1b[0m'     // Reset
        };
        
        console.log(`${colors[type]}[${timestamp}] ${message}${colors.reset}`);
    }

    async checkPrerequisites() {
        this.log('🔍 Checking prerequisites...');
        
        // Check if virtual environment exists
        if (!fs.existsSync(this.venvPath)) {
            this.log('❌ Virtual environment not found. Please run setup first.', 'error');
            return false;
        }
        
        // Check if node_modules exists
        const nodeModules = path.join(this.frontendDir, 'node_modules');
        if (!fs.existsSync(nodeModules)) {
            this.log('📦 Installing frontend dependencies...', 'warning');
            try {
                await this.runCommand('npm install', this.frontendDir);
            } catch (error) {
                this.log('❌ Failed to install frontend dependencies', 'error');
                return false;
            }
        }
        
        this.log('✅ All prerequisites met!', 'success');
        return true;
    }

    runCommand(command, cwd = process.cwd()) {
        return new Promise((resolve, reject) => {
            exec(command, { cwd }, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });
    }

    async startBackend() {
        this.log('🚀 Starting Django backend server...');
        
        try {
            const pythonCmd = this.isWindows 
                ? path.join(this.venvPath, 'Scripts', 'python.exe')
                : path.join(this.venvPath, 'bin', 'python');
                
            const args = ['manage.py', 'runserver', '127.0.0.1:8000'];
            
            this.backendProcess = spawn(pythonCmd, args, {
                cwd: this.baseDir,
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            this.backendProcess.stdout.on('data', (data) => {
                const lines = data.toString().trim().split('\n');
                lines.forEach(line => {
                    if (line.trim()) {
                        this.log(`[BACKEND] ${line}`, 'info');
                    }
                });
            });
            
            this.backendProcess.stderr.on('data', (data) => {
                const lines = data.toString().trim().split('\n');
                lines.forEach(line => {
                    if (line.trim()) {
                        this.log(`[BACKEND ERROR] ${line}`, 'error');
                    }
                });
            });
            
            this.backendProcess.on('close', (code) => {
                this.log(`Backend process exited with code ${code}`, 'warning');
            });
            
            // Wait a bit to ensure it started
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            if (this.backendProcess.killed) {
                throw new Error('Backend process failed to start');
            }
            
            this.log('✅ Backend server started on http://127.0.0.1:8000', 'success');
            return true;
            
        } catch (error) {
            this.log(`❌ Failed to start backend server: ${error.message}`, 'error');
            return false;
        }
    }

    async startFrontend() {
        this.log('🚀 Starting React frontend server...');
        try {
            // Use exec with shell to avoid Windows spawn EINVAL issues
            const child = exec('npm run dev', { cwd: this.frontendDir, windowsHide: true }, (error) => {
                if (error) {
                    this.log(`[FRONTEND ERROR] ${error.message}`, 'error');
                }
            });

            this.frontendProcess = child;

            child.stdout.on('data', (data) => {
                const lines = data.toString().trim().split('\n');
                lines.forEach(line => line.trim() && this.log(`[FRONTEND] ${line}`, 'info'));
            });

            child.stderr.on('data', (data) => {
                const lines = data.toString().trim().split('\n');
                lines.forEach(line => line.trim() && this.log(`[FRONTEND ERROR] ${line}`, 'error'));
            });

            // Wait briefly and assume successful spawn if still running
            await new Promise(resolve => setTimeout(resolve, 3000));
            if (child.killed) throw new Error('Frontend process failed to start');

            this.log('✅ Frontend server started on http://localhost:5173', 'success');
            return true;
        } catch (error) {
            this.log(`❌ Failed to start frontend server: ${error.message}`, 'error');
            return false;
        }
    }

    cleanup() {
        this.log('🛑 Stopping servers...', 'warning');
        
        if (this.backendProcess && !this.backendProcess.killed) {
            this.backendProcess.kill('SIGTERM');
            this.log('✅ Backend server stopped', 'success');
        }
        
        if (this.frontendProcess && !this.frontendProcess.killed) {
            this.frontendProcess.kill('SIGTERM');
            this.log('✅ Frontend server stopped', 'success');
        }
    }

    async run() {
        this.log('🎯 AI Interview Platform - Combined Server Starter');
        console.log('==================================================');
        
        // Check prerequisites
        if (!(await this.checkPrerequisites())) {
            process.exit(1);
        }
        
        // Start backend first
        const backendStarted = await this.startBackend();
        
        if (!backendStarted) {
            this.log('❌ Failed to start backend server', 'error');
            process.exit(1);
        }
        
        // Start frontend
        const frontendStarted = await this.startFrontend();
        
        if (!frontendStarted) {
            this.log('❌ Failed to start frontend server', 'error');
            this.cleanup();
            process.exit(1);
        }
        
        this.log('🎉 Both servers are running!', 'success');
        this.log('📍 Backend:  http://127.0.0.1:8000', 'info');
        this.log('📍 Frontend: http://localhost:5173', 'info');
        this.log('💡 Press Ctrl+C to stop both servers', 'warning');
        
        // Keep the process alive
        const keepAlive = () => {
            if (this.backendProcess && this.backendProcess.killed) {
                this.log('❌ Backend process died', 'error');
                this.cleanup();
                process.exit(1);
            }
            
            if (this.frontendProcess && this.frontendProcess.killed) {
                this.log('❌ Frontend process died', 'error');
                this.cleanup();
                process.exit(1);
            }
            
            setTimeout(keepAlive, 1000);
        };
        
        keepAlive();
    }
}

// Run the server manager
if (require.main === module) {
    const manager = new ServerManager();
    manager.run().catch(error => {
        console.error('❌ Fatal error:', error);
        process.exit(1);
    });
}

module.exports = ServerManager;
