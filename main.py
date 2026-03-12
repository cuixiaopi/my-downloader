import flet as ft
import os
import shutil
import stat
import subprocess

def main(page: ft.Page):
    page.title = "DRM 下载器"
    page.scroll = ft.ScrollMode.AUTO
    
    # UI 界面
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=10)
    url_input = ft.TextField(label="MPD 链接", border_radius=10)
    key_input = ft.TextField(label="32位 Key", border_radius=10)
    
    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    # --- 核心：在安卓内提取并赋予 ffmpeg 权限 ---
    def get_ffmpeg():
        # 获取 App 内部私有目录，只有这里才允许执行程序
        data_dir = page.pwa_config.path if hasattr(page, 'pwa_config') else os.getcwd()
        ffmpeg_bin = os.path.join(data_dir, "ffmpeg")
        
        if not os.path.exists(ffmpeg_bin):
            logger("正在从资源包部署引擎...")
            try:
                # 找到打包在 assets 里的文件
                src = os.path.join(os.path.dirname(__file__), "assets", "ffmpeg")
                shutil.copy(src, ffmpeg_bin)
                # 关键：赋予 chmod +x 权限
                os.chmod(ffmpeg_bin, os.stat(ffmpeg_bin).st_mode | stat.S_IEXEC)
                logger("引擎部署成功！")
            except Exception as e:
                logger(f"部署失败: {e}")
                return None
        return ffmpeg_bin

    def start_job(e):
        ffmpeg_path = get_ffmpeg()
        if not ffmpeg_path: return
        
        logger("🚀 任务开始...")
        # 之后这里可以写具体的 yt-dlp 和 ffmpeg 调用命令
        logger(f"当前引擎位置: {ffmpeg_path}")
        page.update()

    btn = ft.ElevatedButton("验证环境并运行", on_click=start_job)
    page.add(ft.Column([url_input, key_input, btn, log_box]))

ft.app(target=main)