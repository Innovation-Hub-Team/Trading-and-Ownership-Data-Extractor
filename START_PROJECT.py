#!/usr/bin/env python3
"""
Trading and Ownership Data Extractor - ONE CLICK START
Just run this file and everything will work!
"""

import os
import sys
import subprocess
import platform
import time
import webbrowser
from pathlib import Path

def run_command(command, shell=False):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_python():
    """Check if Python is available"""
    print("Checking Python...")
    if run_command([sys.executable, "--version"]):
        print("Python found")
        return True
    else:
        print("Python not found. Please install Python 3.8+ from python.org")
        input("Press Enter to exit...")
        return False

def check_node():
    """Check if Node.js is available"""
    print("Checking Node.js...")
    if run_command(["node", "--version"]):
        print("Node.js found")
        return True
    else:
        print("Node.js not found. Please install Node.js 14+ from nodejs.org")
        input("Press Enter to exit...")
        return False

def install_dependencies():
    """Install all dependencies"""
    print("\nInstalling dependencies...")
    
    # Install Python dependencies
    print("Installing Python packages...")
    os.chdir("backend")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
        print("Python dependencies failed")
        return False
    os.chdir("..")
    
    # Install Node.js dependencies
    print("Installing Node.js packages...")
    os.chdir("frontend")
    if not run_command(["npm", "install"]):
        print("Node.js dependencies failed")
        return False
    os.chdir("..")
    
    print("All dependencies installed")
    return True

def start_services():
    """Start both backend and frontend"""
    print("\nStarting services...")
    
    # Start backend
    print("Starting backend...")
    os.chdir("backend")
    if platform.system() == "Windows":
        backend = subprocess.Popen([sys.executable, "start_server.py"], 
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        backend = subprocess.Popen([sys.executable, "start_server.py"])
    os.chdir("..")
    
    # Wait for backend
    time.sleep(5)
    
    # Start frontend
    print("Starting frontend...")
    os.chdir("frontend")
    if platform.system() == "Windows":
        frontend = subprocess.Popen(["npm", "start"], 
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        frontend = subprocess.Popen(["npm", "start"])
    os.chdir("..")
    
    # Wait for frontend
    time.sleep(10)
    
    return backend, frontend

def main():
    """Main function - everything happens here"""
    print("=" * 60)
    print("🚀 Trading and Ownership Data Extractor")
    print("=" * 60)
    print("🎯 ONE CLICK START - Everything will be set up automatically!")
    print()
    
    # Check prerequisites
    if not check_python() or not check_node():
        return
    
    # Install dependencies
    if not install_dependencies():
        input("Press Enter to exit...")
        return
    
    # Start services
    backend, frontend = start_services()
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! Your app is ready!")
    print("=" * 60)
    print("✅ Backend: http://localhost:5003")
    print("✅ Frontend: http://localhost:3000")
    print()
    
    # Open browser
    try:
        webbrowser.open("http://localhost:3000")
        print("🌐 Browser opened automatically!")
    except:
        print("🌐 Please open: http://localhost:3000")
    
    print("\n💡 To stop: Close the command windows")
    print("💡 To restart: Run this script again")
    print("\n🎯 Enjoy your Trading and Ownership Data Extractor!")
    
    # Keep running
    try:
        input("\nPress Enter to stop all services...")
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Stopping services...")
    backend.terminate()
    frontend.terminate()
    print("✅ Done!")

if __name__ == "__main__":
    main()
