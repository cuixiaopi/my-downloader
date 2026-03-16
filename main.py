import sys
import os

# 🌟 终极补丁：自动递归查找当前目录下的所有 site-packages 并加入路径
def add_all_site_packages():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(app_dir):
        if "site-packages" in root:
            if root not in sys.path:
                sys.path.append(root)

add_all_site_packages()

import flet as ft
import yt_dlp
import subprocess
import shutil

def main(page: ft.Page):
    page.title = "MPD 下载器"
    page.theme_mode = ft.ThemeMode.DARK
    
    url_input = ft.TextField(label="MPD 链接", value="https://cdn-dl.webstream.ne.jp/cdn-dl27/dl/giga/tbw31/tbw31_hd_01_6000k.mpd")
    key_input = ft.TextField(label="解密 Key", value="74cf87a7594b3ac7e5a4e6fab7f53796")
    log_text = ft.Text("等待任务...", color=ft.colors.GREEN_400)

    def log(msg):
        log_text.value += f"\n{msg}"
        page.update()

    def run_task(e):
        btn.disabled = True
        log("开始处理...")
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cache_dir = os.environ.get("TMPDIR", "/data/local/tmp")
            ffmpeg_path = os.path.join(cache_dir, "ffmpeg")
            
            # 释放 FFmpeg
            if not os.path.exists(ffmpeg_path):
                shutil.copy(os.path.join(base_dir, "assets", "ffmpeg"), ffmpeg_path)
                os.chmod(ffmpeg_path, 0o777)
            
            # 下载
            out_template = os.path.join(cache_dir, "tbw_31_final.%(ext)s")
            ydl_opts = {'video_password': f"8045e66376cb4efdae49a6315846f1cb:{key_input.value}", 'outtmpl': out_template}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_input.value])
            
            log("下载完成，正在解密...")
            
            # 合并
            cmd = [ffmpeg_path, '-y', '-decryption_key', key_input.value, '-i', os.path.join(cache_dir, "tbw_31_final.ftbw31_hd_01_6000k_v.mp4"), '-decryption_key', key_input.value, '-i', os.path.join(cache_dir, "tbw_31_final.ftbw31_hd_01_6000k_a.m4a"), '-c', 'copy', os.path.join(cache_dir, "final_video.mp4")]
            subprocess.run(cmd)
            log("✅ 成功！文件位于: " + cache_dir)
        except Exception as ex:
            log(f"❌ 出错: {str(ex)}")
        finally:
            btn.disabled = False
            page.update()

    btn = ft.ElevatedButton("开始", on_click=run_task)
    page.add(url_input, key_input, btn, log_text)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
