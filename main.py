import flet as ft
import yt_dlp
import subprocess
import os
import shutil
import stat

def main(page: ft.Page):
    page.title = "简单 MPD 下载器"
    page.padding = 20
    page.scroll = "auto"

    # UI 元素
    url_input = ft.TextField(label="MPD 链接", value="https://cdn-dl.webstream.ne.jp/cdn-dl27/dl/giga/tbw31/tbw31_hd_01_6000k.mpd")
    key_input = ft.TextField(label="解密 Key", value="74cf87a7594b3ac7e5a4e6fab7f53796")
    log_text = ft.Text("等待操作...", size=12)
    
    def log(msg):
        log_text.value += f"\n{msg}"
        page.update()

    def run_task(e):
        btn_start.disabled = True
        log_text.value = "开始任务..."
        page.update()

        try:
            # 1. 配置路径 (安卓内部存储的缓存目录)
            cache_dir = os.environ.get("TMPDIR", "/data/local/tmp")
            ffmpeg_path = os.path.join(cache_dir, "ffmpeg")
            
            # 视频输出路径设为安卓的公共下载目录 (Downloads)
            # 在 Flet 安卓环境中，通常可以写到 /storage/emulated/0/Download
            download_dir = "/storage/emulated/0/Download"
            if not os.path.exists(download_dir):
                download_dir = cache_dir # 如果找不到公共目录，降级到缓存目录
                
            out_template = os.path.join(download_dir, "tbw_31_final.%(ext)s")
            final_out = os.path.join(download_dir, "final_video.mp4")

            # 2. 释放并赋权 FFmpeg 二进制文件
            log("正在初始化 FFmpeg 环境...")
            # 注意：在 Flet 中，assets 目录下的文件会被打包进去，可以通过相对路径读取
            if not os.path.exists(ffmpeg_path):
                assets_ffmpeg = "assets/ffmpeg"
                if os.path.exists(assets_ffmpeg):
                    shutil.copy(assets_ffmpeg, ffmpeg_path)
                    # 赋予可执行权限 (chmod +x)
                    os.chmod(ffmpeg_path, os.stat(ffmpeg_path).st_mode | stat.S_IEXEC)
                else:
                    log("错误：找不到 assets/ffmpeg 文件，请确保已打包！")
                    return

            # 3. 运行 yt-dlp
            log("正在通过 yt-dlp 下载...")
            ydl_opts = {
                'allow_unplayable_formats': True,
                'video_password': f"8045e66376cb4efdae49a6315846f1cb:{key_input.value}",
                'outtmpl': out_template,
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_input.value])

            log("下载完成，开始 FFmpeg 解密...")

            # 4. 运行 FFmpeg 解密合并
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
                log(f"✅ 处理成功！文件保存在:\n{final_out}")
            else:
                log(f"❌ FFmpeg 报错:\n{process.stderr}")

        except Exception as ex:
            log(f"发生异常: {str(ex)}")
        finally:
            btn_start.disabled = False
            page.update()

    btn_start = ft.ElevatedButton("开始下载并解密", on_click=run_task)

    # 将 UI 添加到页面
    page.add(
        url_input,
        key_input,
        btn_start,
        ft.Divider(),
        log_text
    )

ft.app(target=main, assets_dir="assets")
