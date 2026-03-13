import flet as ft
import os
import shutil
import subprocess
import threading
import traceback

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- 1. 界面组件 ---
    url_input = ft.TextField(label="MPD 链接 (不填则仅测试引擎)", border_radius=10)
    key_input = ft.TextField(label="32位 Key", border_radius=10)
    log_box = ft.TextField(label="界面日志", multiline=True, read_only=True, min_lines=15, text_size=12)
    pb = ft.ProgressBar(visible=False)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    # 初始化日志
    logger("✅ 界面加载成功！系统准备就绪。")

    # --- 2. 核心任务（放在按钮点击后执行，绝对不导致启动白屏） ---
    def run_task(e):
        btn.disabled = True
        pb.visible = True
        page.update()

        def process():
            try:
                # 第一步：穿透路径部署引擎
                flet_app_data = os.environ.get("FLET_APP_DATA", os.getcwd())
                # 往上跳两级，到达 /data/data/包名/files
                base_files = flet_app_data
                for _ in range(2): 
                    base_files = os.path.dirname(base_files)
                target_ffmpeg = os.path.join(base_files, "ffmpeg")

                logger(f"\n📂 部署引擎至: {target_ffmpeg}")
                
                src_ffmpeg = os.path.join(os.path.dirname(__file__), "assets", "ffmpeg")
                if not os.path.exists(src_ffmpeg):
                    logger("❌ 致命错误：APK 内找不到 assets/ffmpeg")
                    return

                # 复制并强制赋权
                shutil.copy(src_ffmpeg, target_ffmpeg)
                os.chmod(target_ffmpeg, 0o777)

                url = url_input.value.strip()
                key = key_input.value.strip()

                if url and key:
                    # 第二步：如果有链接，执行真实下载
                    out_dir = "/sdcard/Download"
                    if not os.path.exists(out_dir):
                        out_dir = flet_app_data
                    out_file = os.path.join(out_dir, "video.mp4")

                    logger(f"🚀 开始下载解密...\n目标: {out_file}")
                    
                    # 使用 sh -c 绕过安卓 10+ 执行限制
                    cmd = f"chmod 777 {target_ffmpeg} && {target_ffmpeg} -decryption_key {key} -i '{url}' -c copy -y {out_file}"
                    
                    # 实时输出进度
                    p = subprocess.Popen(["/system/bin/sh", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in p.stdout:
                        if "size=" in line or "time=" in line:
                            logger(f"进度: {line.strip()}")
                    p.wait()

                    if p.returncode == 0:
                        logger("🎉 下载完成！请去文件夹查看。")
                    else:
                        logger(f"⚠️ 执行结束，返回码: {p.returncode}")
                else:
                    # 如果没填链接，仅仅测试引擎是否激活
                    logger("🧪 链接为空，开始测试引擎权限...")
                    cmd = f"chmod 777 {target_ffmpeg} && {target_ffmpeg} -version"
                    res = subprocess.run(["/system/bin/sh", "-c", cmd], capture_output=True, text=True)
                    
                    if "ffmpeg version" in res.stdout:
                        logger(f"🎉 突破成功！引擎已激活：\n{res.stdout[:60]}")
                    else:
                        logger(f"❌ 权限依旧被拦截！\nErr: {res.stderr}")

            except Exception as ex:
                logger(f"💥 运行崩溃: {traceback.format_exc()}")
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()

        # 开新线程，防止界面卡死
        threading.Thread(target=process, daemon=True).start()

    btn = ft.ElevatedButton("激活引擎并下载", on_click=run_task)
    page.add(ft.Column([url_input, key_input, btn, pb, log_box]))

# 保证最外层不会崩
try:
    ft.app(target=main)
except Exception as e:
    print(f"App Crash: {e}")
