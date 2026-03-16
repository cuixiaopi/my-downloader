import flet as ft
import os
import shutil
import subprocess
import threading
import traceback

def is_android():
    return os.environ.get("FLET_PLATFORM") == "android"

def request_storage_permission(page: ft.Page, log_func):
    if not is_android():
        return True
    
    try:
        permission = "android.permission.WRITE_EXTERNAL_STORAGE"
        result = page.permissions.request(permission)
        if result:
            log_func("✅ 已获得存储权限")
            return True
        else:
            log_func("❌ 权限请求被拒绝，请手动授权")
            return False
    except Exception as e:
        log_func(f"⚠️ 权限请求出错: {str(e)}")
        return False

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE

    url_input = ft.TextField(label="MPD 链接", border_radius=10)
    key_input = ft.TextField(label="32位 KEY", border_radius=10)

    log_box = ft.TextField(
        label="运行日志",
        multiline=True,
        read_only=True,
        min_lines=15,
        text_size=12
    )

    pb = ft.ProgressBar(visible=False)

    def log(msg):
        log_box.value += msg + "\n"
        page.update()

    # 初始化时检查权限
    def init_check():
        if is_android():
            log("📱 检测到 Android 设备")
            log("请确保已授予存储权限")
            
            # 创建测试文件检查权限
            try:
                test_path = os.path.join(os.getcwd(), "permission_test.txt")
                with open(test_path, "w") as f:
                    f.write("test")
                os.remove(test_path)
                log("✅ 基本文件操作权限正常")
            except Exception as e:
                log(f"⚠️ 文件权限可能有问题: {str(e)}")

    btn = ft.ElevatedButton("开始下载")

    def run(e):
        btn.disabled = True
        pb.visible = True
        page.update()

        def task():
            try:
                log("🚀 初始化引擎...")

                # 检查是否在 Android 上
                if is_android():
                    # 请求存储权限
                    if not request_storage_permission(page, log):
                        log("❌ 缺少存储权限，无法继续")
                        return

                app_dir = os.getcwd()
                ffmpeg_src = os.path.join(app_dir, "assets", "ffmpeg")
                
                if not os.path.exists(ffmpeg_src):
                    log("❌ 找不到 FFmpeg 文件")
                    return

                data_dir = os.environ.get("FLET_APP_DATA", app_dir)
                ffmpeg_bin = os.path.join(data_dir, "ffmpeg")

                # 复制 ffmpeg 到可执行位置
                shutil.copy(ffmpeg_src, ffmpeg_bin)
                os.chmod(ffmpeg_bin, 0o755)
                
                log("✅ FFmpeg 已部署")

                url = url_input.value.strip()
                key = key_input.value.strip()
                
                if not url:
                    log("❌ 请输入 MPD 链接")
                    return
                    
                if not key or len(key) != 64:  # 32字节 = 64字符
                    log("❌ 请输入正确的 32位 KEY (64字符)")
                    return

                # 选择输出路径（Android 和 PC 兼容）
                if is_android():
                    out_file = "/sdcard/Download/video.mp4"
                    # 备选路径
                    alt_path = "/storage/emulated/0/Download/video.mp4"
                else:
                    out_file = "video.mp4"
                    alt_path = out_file

                # 尝试不同路径
                try:
                    test_dir = os.path.dirname(out_file)
                    if test_dir and not os.path.exists(test_dir):
                        log(f"⚠️ 路径不存在，尝试备用路径: {alt_path}")
                        out_file = alt_path
                except:
                    out_file = alt_path

                log(f"📁 输出路径: {out_file}")

                cmd = [
                    ffmpeg_bin,
                    "-decryption_key",
                    key,
                    "-i",
                    url,
                    "-c",
                    "copy",
                    "-y",
                    out_file
                ]

                log("🎬 开始下载...")
                log(f"执行命令: {' '.join(cmd[:3])} ...")

                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                for line in p.stdout:
                    if "time=" in line or "speed=" in line:
                        log(f"📈 {line.strip()[:80]}")

                p.wait()

                if p.returncode == 0:
                    log("✅ 下载完成！")
                    if os.path.exists(out_file):
                        size = os.path.getsize(out_file) / (1024 * 1024)
                        log(f"✅ 文件大小: {size:.2f} MB")
                    else:
                        log("✅ 文件可能在其他路径")
                else:
                    log(f"❌ 失败，返回码 {p.returncode}")

            except Exception:
                log("💥 程序崩溃：")
                log(traceback.format_exc())
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()

        threading.Thread(target=task, daemon=True).start()

    btn.on_click = run

    page.add(
        ft.Column([
            ft.Text("DRM 下载大师", size=24, weight=ft.FontWeight.BOLD),
            url_input,
            key_input,
            btn,
            pb,
            log_box
        ])
    )
    
    # 初始化检查
    init_check()

ft.app(target=main)
