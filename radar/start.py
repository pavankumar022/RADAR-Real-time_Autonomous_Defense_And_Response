import os
import sys
import shutil
import subprocess

def main():
    print("=========================================")
    print("  RADAR - Real-time Autonomous Defense")
    print("        And Response")
    print("=========================================")
    print("Starting RADAR...\n")

    # Determine virtual environment python
    if sys.platform == "win32":
        python_exe = os.path.join(".venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join(".venv", "bin", "python")

    if not os.path.exists(python_exe):
        print(f"ERROR: Virtual environment python not found at: {python_exe}")
        print("Please run setup.bat (or setup.sh) first to configure the environment!")
        sys.exit(1)

    # Check for .env file
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("[INFO] Created .env from .env.example (demo mode)")
        else:
            print("[WARNING] .env.example not found. Creating empty .env")
            with open(".env", "w") as f:
                f.write("# RADAR configuration\n")

    # Check if frontend is built
    dist_index = os.path.join("backend", "dist", "index.html")
    if not os.path.exists(dist_index):
        print("[INFO] Frontend dist not found. Building now...")
        frontend_dir = os.path.join(os.getcwd(), "frontend")
        
        # Run npm install if node_modules doesn't exist
        if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
            print("[INFO] node_modules not found in frontend. Running npm install...")
            try:
                subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True, check=True)
            except Exception as e:
                print(f"ERROR: Failed to run npm install: {e}")
                sys.exit(1)

        # Run npm run build
        try:
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True, check=True)
            # Copy built files
            backend_dist = os.path.join("backend", "dist")
            if os.path.exists(backend_dist):
                shutil.rmtree(backend_dist)
            shutil.copytree(os.path.join("frontend", "dist"), backend_dist)
            print("[OK] Frontend built and copied to backend/dist")
        except Exception as e:
            print(f"ERROR: Failed to build frontend: {e}")
            sys.exit(1)

    print("\n============================================================")
    print(" RADAR is starting at: http://localhost:54321")
    print("============================================================\n")

    # Launch uvicorn
    cmd = [python_exe, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "54321", "--reload"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping RADAR...")

if __name__ == "__main__":
    main()
