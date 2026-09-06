import multiprocessing
import subprocess
import os
import sys

BOTS = [
    os.path.join("acc botspam", "telegram_bot", "main.py"),
    os.path.join("bottele", "main.py"),
    os.path.join("bot tl hongan", "main.py"),
    os.path.join("bot cho thuê sim otp", "main2.py")
]

def run_script(script_path):
    print(f"=== Bắt đầu chạy: {script_path} ===")
    if not os.path.exists(script_path):
        print(f"LỖI: Không tìm thấy file {script_path}")
        return
    
    dir_name = os.path.dirname(script_path)
    file_name = os.path.basename(script_path)
    
    try:
        result = subprocess.run(
            [sys.executable, file_name],
            cwd=dir_name if dir_name else None,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"Output [{script_path}]:\n{result.stdout}")
        if result.stderr:
            print(f"Lỗi [{script_path}]:\n{result.stderr}")
    except Exception as e:
        print(f"Ngoại lệ [{script_path}]: {e}")

if __name__ == "__main__":
    processes = []
    for bot in BOTS:
        p = multiprocessing.Process(target=run_script, args=(bot,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
