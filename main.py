import flet as ft
import os
import shutil
import stat
import subprocess
import threading

def main(page: ft.Page):
    page.title = "DRM 视频大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    
    url_input = ft.TextField(label="MPD 链接", border_radius=10)
    key_input = ft.TextField(label="32位 Key (Decryption Key)", border_radius=10)
    name_input = ft.TextField(label="保存文件名", value="download_video", border_radius=10)
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=12, text_size=12)
    pb = ft.ProgressBar(visible=False)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    def get_ffmpeg():
        data_dir = page.pwa_config.path if hasattr(page, 'pwa_config') else os.getcwd()
        ffmpeg_bin = os.path.join(data_dir, "ffmpeg")
        if not os.path.exists(ffmpeg_bin):
            src = os.path.join(os.path.dirname(__file__), "assets", "ffmpeg")
            if os.path.exists(src):
                shutil.copy(src, ffmpeg_bin)
                os.chmod(ffmpeg_bin, os.stat(ffmpeg_bin).st_mode | stat.S_IEXEC)
        return ffmpeg_bin

    def run_download_logic():
        engine = get_ffmpeg()
        url = url_input.value.strip()
        key = key_input.value.strip()
        
        if not url or not key:
            logger("❌ 错误：链接或Key不能为空")
            return

        btn.disabled = True
        pb.visible = True
        page.update()

        try:
            # 1. 确定输出路径 (手机下载目录)
            output_dir = "/sdcard/Download"
            if not os.path.exists(output_dir):
                output_dir = os.getcwd()
            
            final_output = os.path.join(output_dir, f"{name_input.value}.mp4")
            
            logger("🚀 第一步：正在抓取并合并流 (yt-dlp)...")
            # 注意：安卓上直接调用命令行
            # 我们直接用 FFmpeg 配合 Key 处理 MPD
            cmd = [
                engine,
                "-decryption_key", key,
                "-i", url,
                "-c", "copy",
                "-y", # 覆盖同名文件
                final_output
            ]

            # 执行命令
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            for line in process.stdout:
                if "size=" in line: # 提取进度信息
                    logger(f"正在处理: {line.strip()}")
            
            process.wait()

            if process.returncode == 0:
                logger(f"✅ 任务完成！文件已保存至：{final_output}")
            else:
                logger("❌ 任务失败，请检查链接或Key是否正确。")

        except Exception as ex:
            logger(f"💥 异常: {str(ex)}")
        
        btn.disabled = False
        pb.visible = False
        page.update()

    def start_click(e):
        # 开启新线程运行，防止界面卡死
        threading.Thread(target=run_download_logic, daemon=True).start()

    btn = ft.ElevatedButton("开始解密并下载", on_click=start_click, icon=ft.icons.DOWNLOAD)
    page.add(ft.Column([url_input, key_input, name_input, ft.Center(btn), pb, log_box]))

ft.app(target=main)
