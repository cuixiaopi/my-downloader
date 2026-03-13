import sys
import os
import traceback

# 1. 建立全局防崩溃日志系统
# 优先将日志写在手机公共的 Download 文件夹，方便你直接用文件管理器查看
log_file = "/sdcard/Download/flet_crash_log.txt"

# 如果没有写入权限，退而求其次保存在 App 私有目录
if not os.path.exists("/sdcard/Download"):
    log_file = os.path.join(os.environ.get("FLET_APP_DATA", os.getcwd()), "flet_crash_log.txt")

try:
    with open(log_file, "w") as f:
        f.write("--- 🚀 App 启动检测 ---\n")
except Exception:
    pass

# 接管所有未捕获的 Python 致命错误
def global_exception_handler(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        with open(log_file, "a") as f:
            f.write(f"\n💥 全局致命崩溃:\n{err_msg}\n")
    except Exception:
        pass

sys.excepthook = global_exception_handler

# 2. 尝试加载业务代码
try:
    import flet as ft
    import shutil
    import subprocess
    import threading

    def main(page: ft.Page):
        page.title = "诊断模式"
        page.scroll = ft.ScrollMode.AUTO
        
        info = ft.Text("✅ 界面加载成功！如果你看到了这行字，说明没有白屏，Python 引擎启动正常。", color="green", weight="bold")
        log_box = ft.TextField(label="界面日志", multiline=True, min_lines=10)
        
        page.add(ft.Column([info, log_box]))

    # 启动 UI
    ft.app(target=main)

except Exception as e:
    # 捕获 import 失败或 ft.app 启动失败
    err = traceback.format_exc()
    try:
        with open(log_file, "a") as f:
            f.write(f"\n🔥 启动阶段崩溃:\n{err}\n")
    except Exception:
        pass
