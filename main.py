import sys
import os
# 强制加载打包环境中的 site-packages 目录，解决 ModuleNotFoundError: No module named 'flet'
app_dir = os.path.dirname(os.path.abspath(__file__))
site_packages = os.path.join(app_dir, "lib", "python3.11", "site-packages")
if os.path.exists(site_packages):
    sys.path.append(site_packages)

import flet as ft
import yt_dlp
import subprocess
import shutil
import stat

def main(page: ft.Page):
    page.title = "MPD 下载解密器"
    page.padding = 20
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.DARK

    # UI 界面元素
    url_input = ft.TextField(label="MPD 链接", value="https://cdn-dl.webstream.ne.jp/cdn-dl27/dl/giga/tbw31/tbw31_hd_01_6000k.mpd")
    key_input = ft.TextField(label="解密 Key", value="74cf87a7594b3ac7e5a4e6fab7f53796")
    log_text = ft.Text("状态：等待开始...", size=13, color=ft.colors.GREEN_400)
    
    def log(msg):
        log_text.value += f"\n{msg}"
        page.update()

    def run_task(e):
        btn_start.disabled = True
        log_text.value = "=== 任务开始 ==="
        page.update()

        try:
            # ================= 1. 路径初始化 =================
            base_dir = os.path.dirname(os.path.abspath(__file__))
            assets_ffmpeg = os.path.join(base_dir, "assets", "ffmpeg")
            
            # 使用 Android 的私有缓存目录，这是唯一有写权限且允许执行二进制文件的地方
            cache_dir = os.environ.get("TMPDIR", "/data/local/tmp")
            ffmpeg_path = os.path.join(cache_dir, "ffmpeg")
            
            # 下载目标目录：App 的私有数据目录
            download_dir = os.path.join(base_dir, "downloads")
            os.makedirs(download_dir, exist_ok=True)
            
            out_template = os.path.join(download_dir, "tbw_31_final.%(ext)s")
            final_out = os.path.join(download_dir, "final_video.mp4")

            # ================= 2. 释放 FFmpeg 到可执行区 =================
            log("-> 准备 FFmpeg 环境...")
            if not os.path.exists(ffmpeg_path):
                if os.path.exists(assets_ffmpeg):
                    shutil.copy(assets_ffmpeg, ffmpeg_path)
                    os.chmod(ffmpeg_path, 0o777)
                    log("-> FFmpeg 释放并授权成功")
                else:
                    log(f"❌ 错误：在 {assets_ffmpeg} 找不到 FFmpeg 文件")
                    return

            # ================= 3. yt-dlp 下载 =================
            log("-> 启动 yt-dlp 下载...")
            ydl_opts = {
                'allow_unplayable_formats': True,
                'video_password': f"8045e66376cb4efdae49a6315846f1cb:{key_input.value}",
                'outtmpl': out_template,
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_input.value])

            log("✅ 下载完成，准备解密...")

            # ================= 4. FFmpeg 解密 =================
            video_in = os.path.join(download_dir, "tbw_31_final.ftbw31_hd_01_6000k_v.mp4")
            audio_in = os.path.join(download_dir, "tbw_31_final.ftbw31_hd_01_6000k_a.m4a")

            if os.path.exists(final_out):
                os.remove(final_out)

            cmd = [
                ffmpeg_path, '-y',
                '-decryption_key', key_input.value, '-i', video_in,
                '-decryption_key', key_input.value, '-i', audio_in,
                '-c', 'copy', final_out
            ]

            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if process.returncode == 0:
                log(f"🎉 成功！\n视频已保存在:\n{final_out}")
            else:
                log(f"❌ FFmpeg 报错: {process.stderr}")

        except Exception as ex:
            log(f"❌ 发生异常: {str(ex)}")
        finally:
            btn_start.disabled = False
            page.update()

    btn_start = ft.ElevatedButton("开始下载并解密", on_click=run_task, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)

    page.add(
        ft.Column([
            url_input,
            key_input,
            btn_start,
            ft.Divider(height=20, color=ft.colors.WHITE24),
            ft.Container(
                content=log_text,
                padding=10,
                bgcolor=ft.colors.BLACK45,
                border_radius=8
            )
        ], spacing=15)
    )

ft.app(target=main, assets_dir="assets")
