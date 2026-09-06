import multiprocessing
import subprocess
import os
import sys

BOTS = [
    os.path.join("acc botspam", "main.py"),
    os.path.join("bottele", "main.py"),
    os.path.join("bot tl hongan", "main.py"),
    os.path.join("bot cho thuê sim otp", "main2.py")
]

def run_script(script_path):
    print(f"=== Bắt đầu chạy: {script_path} ===")
    if not os.path.exists(script_path):
        print(f"❌ LỖI: Không tìm thấy file {script_path}")
        return
    try:
        # Chạy file và in trực tiếp lỗi ra log
        result = subprocess.run([sys.executable, os.path.basename(script_path)], cwd=os.path.dirname(script_path), capture_output=True, text=True)
        if result.stderr:
            print(f"❌ Lỗi tại {script_path}:\n{result.stderr}")
    except Exception as e:
        print(f"❌ Ngoại lệ tại {script_path}: {e}")

if __name__ == "__main__":
    processes = []
    for bot in BOTS:
        p = multiprocessing.Process(target=run_script, args=(bot,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
