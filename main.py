import flet as ft
import os
import shutil
import stat
import subprocess
import threading

def main(page: ft.Page):
    page.title = "DRM 下载助手"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # UI 控件
    url_input = ft.TextField(label="MPD 链接", border_radius=10)
    key_input = ft.TextField(label="32位 Key (Decryption Key)", border_radius=10)
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=12, text_size=12)
    pb = ft.ProgressBar(visible=False)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    def get_ffmpeg_path():
        # 【重点修复】不要用 page.pwa_config.path，改用环境变量获取安卓私有目录
        # 这样可以彻底解决启动白屏崩溃的问题
        data_dir = os.environ.get("FLET_APP_DATA", os.getcwd())
        ffmpeg_bin = os.path.join(data_dir, "ffmpeg")
        
        if not os.path.exists(ffmpeg_bin):
            logger("正在部署引擎...")
            try:
                # 定位打包进去的资源文件路径
                base_path = os.path.dirname(__file__)
                src = os.path.join(base_path, "assets", "ffmpeg")
                
                if os.path.exists(src):
                    shutil.copy(src, ffmpeg_bin)
                    os.chmod(ffmpeg_bin, os.stat(ffmpeg_bin).st_mode | stat.S_IEXEC)
                    logger("✅ 引擎部署成功")
                else:
                    logger("❌ 找不到原始资源文件 assets/ffmpeg")
            except Exception as e:
                logger(f"❌ 部署失败: {e}")
        return ffmpeg_bin

    def download_thread():
        engine = get_ffmpeg_path()
        url = url_input.value.strip()
        key = key_input.value.strip()
        
        if not url or not key:
            logger("⚠️ 提示：请填入链接和Key")
            return

        btn.disabled = True
        pb.visible = True
        page.update()

        try:
            # 路径适配：尝试下载到手机下载文件夹
            save_path = "/sdcard/Download/video_result.mp4"
            # 如果是安卓11+没权限，会存到 App 的私有存储里
            if not os.access("/sdcard/Download", os.W_OK):
                 save_path = os.path.join(os.environ.get("FLET_APP_STORAGE", os.getcwd()), "video.mp4")

            logger(f"🚀 开始处理，目标：{save_path}")
            
            # 调用 FFmpeg 执行解密下载
            cmd = [engine, "-decryption_key", key, "-i", url, "-c", "copy", "-y", save_path]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                if "size=" in line or "time=" in line:
                    logger(f"进度: {line.strip()}")
            process.wait()

            if process.returncode == 0:
                logger(f"✅ 完成！文件位置: {save_path}")
            else:
                logger(f"❌ 失败，退出码: {process.returncode}")

        except Exception as ex:
            logger(f"💥 异常: {str(ex)}")
        
        btn.disabled = False
        pb.visible = False
        page.update()

    def start_click(e):
        # 使用线程防止界面卡死
        threading.Thread(target=download_thread, daemon=True).start()

    btn = ft.ElevatedButton("开始解密并下载", on_click=start_click, icon=ft.icons.DOWNLOAD)
    page.add(ft.Column([url_input, key_input, ft.Center(btn), pb, log_box]))

# 增加全局捕获
try:
    ft.app(target=main)
except Exception as e:
    print(f"App Crash: {e}")
