import flet as ft
import os
import shutil
import stat
import subprocess
import threading

def main(page: ft.Page):
    page.title = "DRM 视频大师"
    page.scroll = ft.ScrollMode.AUTO
    
    # 界面元素
    url_input = ft.TextField(label="MPD 链接", border_radius=10)
    key_input = ft.TextField(label="32位 Key", border_radius=10)
    name_input = ft.TextField(label="保存文件名", value="my_download", border_radius=10)
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=12, text_size=12)
    pb = ft.ProgressBar(visible=False)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    def get_ffmpeg_path():
        # 获取安卓内部可执行文件的私有路径
        # 这种写法比 pwa_config 更稳，不容易白屏
        data_dir = os.environ.get("FLET_APP_DATA", os.getcwd())
        ffmpeg_bin = os.path.join(data_dir, "ffmpeg")
        
        if not os.path.exists(ffmpeg_bin):
            try:
                # 寻找 assets 里的原始文件
                base_dir = os.path.dirname(__file__)
                src = os.path.join(base_dir, "assets", "ffmpeg")
                if os.path.exists(src):
                    shutil.copy(src, ffmpeg_bin)
                    os.chmod(ffmpeg_bin, os.stat(ffmpeg_bin).st_mode | stat.S_IEXEC)
                    logger("✅ 引擎部署成功")
                else:
                    logger("❌ 找不到 assets/ffmpeg")
            except Exception as e:
                logger(f"❌ 部署失败: {e}")
        return ffmpeg_bin

    def download_process():
        engine = get_ffmpeg_path()
        url = url_input.value.strip()
        key = key_input.value.strip()
        
        if not url or not key:
            logger("❌ 错误：链接或 Key 不能为空")
            return

        btn.disabled = True
        pb.visible = True
        page.update()

        try:
            # 优先保存在 Download 文件夹
            save_path = "/sdcard/Download"
            if not os.path.exists(save_path):
                save_path = os.environ.get("FLET_APP_STORAGE", os.getcwd())
            
            output_file = os.path.join(save_path, f"{name_input.value}.mp4")
            logger(f"📂 目标：{output_file}")

            # FFmpeg 解密命令
            cmd = [engine, "-decryption_key", key, "-i", url, "-c", "copy", "-y", output_file]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                if "size=" in line or "time=" in line:
                    logger(f"进度: {line.strip()}")
            process.wait()

            if process.returncode == 0:
                logger(f"✅ 下载成功！请在 Download 文件夹查看")
            else:
                logger(f"❌ 失败，请检查链接或Key。代码: {process.returncode}")

        except Exception as ex:
            logger(f"💥 异常: {str(ex)}")
        
        btn.disabled = False
        pb.visible = False
        page.update()

    def on_click(e):
        threading.Thread(target=download_process, daemon=True).start()

    btn = ft.ElevatedButton("开始解密并下载", on_click=on_click, icon=ft.icons.DOWNLOAD)
    page.add(ft.Column([url_input, key_input, name_input, ft.Center(btn), pb, log_box]))

# 增加全局异常捕获，防止启动白屏不显示错误
try:
    ft.app(target=main)
except Exception as e:
    import traceback
    with open("crash_log.txt", "w") as f:
        f.write(traceback.format_exc())
