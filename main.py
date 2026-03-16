import flet as ft
import yt_dlp
import subprocess
import os
import shutil
import stat
import glob

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
            # ================= 1. 准备目录 =================
            app_dir = os.getcwd() 
            assets_ffmpeg = os.path.join(app_dir, "assets", "ffmpeg")
            
            # 找到安卓内部的安全缓存目录 (在这个目录下才能执行二进制文件)
            cache_dir = os.environ.get("TMPDIR", os.path.join(app_dir, "tmp"))
            os.makedirs(cache_dir, exist_ok=True)
            ffmpeg_path = os.path.join(cache_dir, "ffmpeg")

            # 视频下载目录 (放在缓存目录避免安卓权限弹窗)
            download_dir = cache_dir 
            out_template = os.path.join(download_dir, "tbw_31_final.%(ext)s")
            final_out = os.path.join(download_dir, "final_video.mp4")

            # ================= 2. 释放 FFmpeg =================
            log("-> 准备 FFmpeg 解密环境...")
            if os.path.exists(assets_ffmpeg):
                shutil.copy(assets_ffmpeg, ffmpeg_path)
                # 满权限赋权：chmod 777
                os.chmod(ffmpeg_path, 0o777) 
            else:
                log(f"❌ 严重错误：找不到打包的 FFmpeg")
                return

            # ================= 3. yt-dlp 下载 =================
            log("-> 启动 yt-dlp 下载 (请耐心等待)...")
            ydl_opts = {
                'allow_unplayable_formats': True,
                'video_password': f"8045e66376cb4efdae49a6315846f1cb:{key_input.value}",
                'outtmpl': out_template,
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_input.value])

            log("✅ 下载完成！")
            log("-> 启动 FFmpeg 进行解密和合并...")

            # ================= 4. FFmpeg 解密 =================
            # 自动寻找下载下来的分离的音视频文件
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
                log(f"🎉 完美成功！\n\n为了绕过安卓14权限限制，视频已保存在App专属私有目录:\n{final_out}\n\n(你可以用 MT管理器 访问上述路径提取视频)")
            else:
                log(f"❌ FFmpeg 报错:\n{process.stderr}")

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
