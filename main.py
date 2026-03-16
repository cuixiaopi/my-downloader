import flet as ft
import os
import shutil
import subprocess
import threading
import traceback

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT

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

    def run(e):

        btn.disabled = True
        pb.visible = True
        page.update()

        def task():
            try:

                log("🚀 初始化引擎...")

                app_dir = os.getcwd()
                ffmpeg_src = os.path.join(app_dir, "assets", "ffmpeg")

                data_dir = os.environ.get("FLET_APP_DATA", app_dir)

                ffmpeg_bin = os.path.join(data_dir, "ffmpeg")

                shutil.copy(ffmpeg_src, ffmpeg_bin)
                os.chmod(ffmpeg_bin, 0o755)

                log("✅ FFmpeg 已部署")

                url = url_input.value.strip()
                key = key_input.value.strip()

                out_file = "/sdcard/Download/video.mp4"

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

                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                for line in p.stdout:
                    if "time=" in line:
                        log("📈 " + line.strip())

                p.wait()

                if p.returncode == 0:
                    log("✅ 下载完成！文件在 Download 文件夹")
                else:
                    log(f"❌ 失败，返回码 {p.returncode}")

            except Exception:
                log("💥 崩溃：")
                log(traceback.format_exc())

            finally:
                btn.disabled = False
                pb.visible = False
                page.update()

        threading.Thread(target=task).start()

    btn = ft.ElevatedButton("开始下载", on_click=run)

    page.add(
        ft.Column([
            url_input,
            key_input,
            btn,
            pb,
            log_box
        ])
    )


ft.app(target=main)  
