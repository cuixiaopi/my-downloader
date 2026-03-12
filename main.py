import flet as ft
import os
import shutil
import stat
import subprocess
import threading

def main(page: ft.Page):
    page.title = "DRM 视频大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.scroll = ft.ScrollMode.AUTO
    
    # UI 布局
    url_input = ft.TextField(label="MPD 链接", hint_text="https://...", border_radius=10)
    key_input = ft.TextField(label="32位 Key", hint_text="例如: 1234567890abcdef...", border_radius=10)
    name_input = ft.TextField(label="保存文件名", value="video_result", border_radius=10)
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=12, text_size=12)
    pb = ft.ProgressBar(visible=False)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    def get_ffmpeg_engine():
        # 获取安卓应用私有数据目录，这是运行二进制文件最稳的地方
        data_dir = os.environ.get("FLET_APP_DATA", os.getcwd())
        ffmpeg_bin = os.path.join(data_dir, "ffmpeg")
        
        if not os.path.exists(ffmpeg_bin):
            try:
                # 从安装包内部资源(assets)复制到可执行路径
                base_path = os.path.dirname(__file__)
                src = os.path.join(base_path, "assets", "ffmpeg")
                if os.path.exists(src):
                    shutil.copy(src, ffmpeg_bin)
                    # 授予执行权限
                    os.chmod(ffmpeg_bin, os.stat(ffmpeg_bin).st_mode | stat.S_IEXEC)
                    logger("✅ 引擎部署成功")
                else:
                    logger("❌ 资源目录缺失 ffmpeg")
            except Exception as e:
                logger(f"❌ 引擎初始化失败: {e}")
        return ffmpeg_bin

    def run_download():
        engine = get_ffmpeg_engine()
        url = url_input.value.strip()
        key = key_input.value.strip()
        
        if not url or not key:
            logger("⚠️ 提示：请填入链接和Key")
            return

        btn.disabled = True
        pb.visible = True
        page.update()

        try:
            # 路径适配：尝试公共下载区，失败则使用私有目录
            save_dir = "/sdcard/Download"
            if not os.path.exists(save_dir):
                save_dir = os.environ.get("FLET_APP_STORAGE", os.getcwd())
            
            output_file = os.path.join(save_dir, f"{name_input.value}.mp4")
            logger(f"📂 正在保存至: {output_file}")

            # 核心解密下载指令
            cmd = [
                engine,
                "-decryption_key", key,
                "-i", url,
                "-c", "copy",
                "-y",
                output_file
            ]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                if "size=" in line or "time=" in line:
                    logger(f"正在下载: {line.strip()}")
            process.wait()

            if process.returncode == 0:
                logger(f"✅ 下载并解密完成！")
            else:
                logger(f"❌ 出错，退出码: {process.returncode}")

        except Exception as ex:
            logger(f"💥 发生异常: {str(ex)}")
        
        btn.disabled = False
        pb.visible = False
        page.update()

    def start_click(e):
        threading.Thread(target=run_download, daemon=True).start()

    btn = ft.ElevatedButton("开始解密下载", on_click=start_click, icon=ft.icons.DOWNLOAD)
    page.add(ft.Column([url_input, key_input, name_input, ft.Center(btn), pb, log_box]))

# 启动 App
ft.app(target=main)
