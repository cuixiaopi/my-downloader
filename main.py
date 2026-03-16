import flet as ft
import os
import shutil
import subprocess
import threading
import traceback
from flet import Permission, permission_request  # 导入权限请求模块

def is_android():
    return os.environ.get("FLET_PLATFORM") == "android"

def get_ffmpeg_path(page: ft.Page):
    """获取 ffmpeg 可执行文件的路径（Android 需复制到可写目录）"""
    if not is_android():
        return "ffmpeg"  # 非 Android 直接用系统 ffmpeg（需提前安装）
    
    # Android 可写目录（内部存储/外部存储）
    app_dir = os.path.join(os.environ.get("FLET_APP_DATA", ""), "ffmpeg")
    # 确保目录存在
    os.makedirs(app_dir, exist_ok=True)
    ffmpeg_bin = os.path.join(app_dir, "ffmpeg")
    
    # 如果 ffmpeg 不存在，从 assets 复制（首次运行）
    if not os.path.exists(ffmpeg_bin):
        # 注意：Flet 打包时，assets 目录会被包含在应用中，需确保 ffmpeg 已放入 assets
        # 这里假设你在 GitHub Actions 构建时已把 ffmpeg 放到 assets 目录
        src_ffmpeg = os.path.join(os.environ.get("FLET_APP_ASSETS", ""), "ffmpeg")
        if os.path.exists(src_ffmpeg):
            shutil.copy(src_ffmpeg, ffmpeg_bin)
            os.chmod(ffmpeg_bin, 0o755)  # 赋予执行权限
        else:
            page.snack_bar = ft.SnackBar(ft.Text("FFmpeg 未找到，请重新安装应用！"))
            page.snack_bar.open = True
            page.update()
            return None
    return ffmpeg_bin

def request_storage_permission(page: ft.Page):
    """请求 Android 存储权限"""
    if not is_android():
        return True
    # 定义需要的权限（Android 13+ 需用 WRITE_MEDIA_VIDEO 等，但 WRITE_EXTERNAL_STORAGE 兼容旧版）
    permissions = [Permission.WRITE_EXTERNAL_STORAGE]
    # 发起权限请求
    results = permission_request(page, permissions)
    # 检查是否所有权限都被授予
    return all(results.values())

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE

    url_input = ft.TextField(label="MPD 链接", border_radius=10)
    key_input = ft.TextField(label="32位 KEY", border_radius=10)
    log_box = ft.TextField(
        label="运行日志",
        multiline=True,
        read_only=True,
        min_lines=15,
        text_size=12
    )
    pb = ft.ProgressBar(visible=False)
    btn = ft.ElevatedButton("开始下载", disabled=True)  # 初始禁用，等待权限检查

    def log(msg):
        log_box.value += msg + "\n"
        page.update()

    def check_permission_and_enable():
        """检查权限，若通过则启用按钮"""
        if is_android():
            has_perm = request_storage_permission(page)
            if has_perm:
                log("✅ 存储权限已获取")
                btn.disabled = False
            else:
                log("❌ 存储权限获取失败，请手动开启后重试")
        else:
            btn.disabled = False  # 非 Android 直接启用
        page.update()

    # 应用启动时检查权限
    page.on_ready = lambda e: check_permission_and_enable()

    def run(e):
        btn.disabled = True
        pb.visible = True
        page.update()

        def task():
            try:
                log("🚀 初始化引擎...")
                ffmpeg_bin = get_ffmpeg_path(page)
                if not ffmpeg_bin:
                    return

                url = url_input.value.strip()
                key = key_input.value.strip()
                out_file = "/sdcard/Download/video.mp4"  # Android 下载路径

                # 构造 ffmpeg 命令（解密并下载）
                cmd = [
                    ffmpeg_bin,
                    "-decryption_key", key,
                    "-i", url,
                    "-c", "copy",
                    "-y", out_file
                ]

                log("🎬 开始下载...")
                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                # 实时读取输出（显示进度）
                for line in p.stdout:
                    if "time=" in line:
                        log("📈 " + line.strip())

                p.wait()
                if p.returncode == 0:
                    log("✅ 下载完成！文件在 Download 文件夹")
                else:
                    log(f"❌ 失败，返回码 {p.returncode}")

            except Exception:
                log("💥 崩溃：")
                log(traceback.format_exc())
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()

        threading.Thread(target=task).start()

    btn.on_click = run
    page.add(
        ft.Column([
            url_input,
            key_input,
            btn,
            pb,
            log_box
        ])
    )

ft.app(target=main)
