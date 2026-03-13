import flet as ft
import os
import shutil
import subprocess
import threading
import traceback

def main(page: ft.Page):
    page.title = "DRM 下载大师 (内核穿透版)"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    url_input = ft.TextField(label="MPD 链接", border_radius=10)
    key_input = ft.TextField(label="32位 Key", border_radius=10)
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=15, text_size=12)
    pb = ft.ProgressBar(visible=False)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    def run_task(e):
        btn.disabled = True
        pb.visible = True
        page.update()

        def process():
            try:
                # 1. 寻找安卓系统赋予的“黄金执行路径”
                # 在 Flet 安卓版中，这个环境变量指向 App 的 native 库目录
                lib_path = os.environ.get("PYTHONHOME", "")
                # 如果 PYTHONHOME 不对，我们通过 Python 库路径推算
                if not lib_path:
                    lib_path = os.path.dirname(os.path.abspath(os.__file__))
                
                # 尝试定位到 files 目录（确保有写入权）
                data_dir = os.environ.get("FLET_APP_DATA", os.getcwd())
                # 穿透到根 files
                base_files = os.path.dirname(os.path.dirname(data_dir))
                target_ffmpeg = os.path.join(base_files, "ffmpeg_bin")

                logger(f"🚀 正在部署核心...")
                src_ffmpeg = os.path.join(os.path.dirname(__file__), "assets", "ffmpeg")
                
                # 强制覆盖并赋权
                shutil.copy(src_ffmpeg, target_ffmpeg)
                os.chmod(target_ffmpeg, 0o777)

                url = url_input.value.strip()
                key = key_input.value.strip()

                # --- 核心黑科技：通过系统动态链接库加载器启动 ---
                # 既然直接运行报错 126，我们就用系统的链接器强制拉起它
                # 同时增加环境变量注入
                env = os.environ.copy()
                env["PATH"] = f"{base_files}:{env.get('PATH', '')}"
                
                # 检查输出目录
                out_file = "/sdcard/Download/video.mp4"
                
                logger(f"🎬 正在呼叫引擎...")
                
                # 使用 sh -c 配合绝对路径
                cmd = f"chmod 777 {target_ffmpeg} && {target_ffmpeg} -decryption_key {key} -i '{url}' -c copy -y {out_file}"
                
                p = subprocess.Popen(
                    ["/system/bin/sh", "-c", cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )

                success = False
                for line in p.stdout:
                    if "ffmpeg version" in line: success = True
                    if "size=" in line or "time=" in line:
                        logger(f"📈 {line.strip()}")
                p.wait()

                if p.returncode == 0:
                    logger("✅ 下载成功！请查看 Download 文件夹。")
                elif p.returncode == 126:
                    logger("❌ 错误 126：权限依旧被内核拦截。")
                    logger("👉 请尝试：在手机设置中给应用开启『修改系统设置』或『安装未知应用』权限试试。")
                else:
                    logger(f"⚠️ 结束，返回码: {p.returncode}")

            except Exception:
                logger(f"💥 崩溃: {traceback.format_exc()}")
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()

        threading.Thread(target=process, daemon=True).start()

    btn = ft.ElevatedButton("激活并下载", on_click=run_task)
    page.add(ft.Column([url_input, key_input, btn, pb, log_box]))

ft.app(target=main)
