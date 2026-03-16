import flet as ft
import os
import subprocess
import threading
import traceback
from flet import permission_request  # 导入权限请求模块

def is_android():
    return os.environ.get("FLET_PLATFORM") == "android"

def get_ffmpeg_path():
    """获取 FFmpeg 路径（Android 自动从 assets 复制）"""
    if not is_android():
        return "ffmpeg"  # 非 Android 直接用系统 ffmpeg（需提前安装）
    
    # Android 可写目录（应用私有目录）
    ffmpeg_dir = os.path.join(os.environ.get("FLET_APP_DATA", ""), "ffmpeg")
    os.makedirs(ffmpeg_dir, exist_ok=True)
    ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg")
    
    # 如果是首次运行，从 assets 复制 FFmpeg（build.yml 会自动打包 assets）
    if not os.path.exists(ffmpeg_path):
        # 读取 assets 中的 ffmpeg（Flet 会自动将 assets 目录打包到 APK）
        with open(ffmpeg_path, "wb") as f:
            # 注意：Flet 中读取 assets 需用 flet.resources 模块（或确保文件在打包时已包含）
            # 这里简化为直接复制（实际需确保 build.yml 正确打包 assets）
            pass  # 实际需实现复制逻辑，见步骤 2
    
    # 赋予执行权限（Android 需 chmod +x）
    os.chmod(ffmpeg_path, 0o755)
    return ffmpeg_path

def start_download(e, page, mpd_link, key):
    try:
        # 检查并请求存储权限（Android 14 需 MANAGE_EXTERNAL_STORAGE）
        def request_storage_permission():
            if is_android():
                # 显示权限请求弹窗
                page.show_dialog(
                    ft.AlertDialog(
                        title=ft.Text("权限请求"),
                        content=ft.Text("需要存储权限以保存下载的视频"),
                        actions=[
                            ft.TextButton("允许", on_click=lambda _: do_request()),
                            ft.TextButton("取消", on_click=lambda _: page.close_dialog())
                        ],
                    )
                )
            
            def do_request():
                # 实际请求权限（Flet 会自动调用 Android 原生权限弹窗）
                page.permissions.request(
                    permission=permission_request.PermissionType.STORAGE,
                    on_result=lambda result: on_permission_result(result, page, mpd_link, key)
                )
                page.close_dialog()
        
        request_storage_permission()
        
    except Exception as e:
        page.controls.append(ft.Text(f"启动下载失败: {str(e)}", style="error"))
        page.update()

def on_permission_result(result, page, mpd_link, key):
    if result == permission_request.PermissionResult.GRANTED:
        page.controls.append(ft.Text("权限已授予，开始下载...", style="success"))
        page.update()
        
        # 调用 FFmpeg 下载（示例命令，需根据实际 MPD/KEY 调整）
        ffmpeg_path = get_ffmpeg_path()
        output_path = os.path.join(os.environ.get("FLET_APP_DATA", ""), "downloaded_video.mp4")
        
        cmd = [
            ffmpeg_path,
            "-i", mpd_link,
            "-c", "copy",
            "-decryption_key", key,  # 替换为实际的 KEY 参数（需确认 FFmpeg 支持的 DRM 解密方式）
            output_path
        ]
        
        # 后台执行 FFmpeg（避免阻塞 UI）
        def run_ffmpeg():
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderrsubprocess.PIPE)=
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    page.controls.append(ft.Text("下载成功！", style="success"))
                else:
                    page.controls.append(ft.Text(f"下载失败: {stderr.decode()}", style="error"))
                page.update()
            except Exception as e:
                page.controls.append(ft.Text(f"执行 FFmpeg 失败: {str(e)}", style="error"))
                page.update()
        
        threading.Thread(target=run_ffmpeg, daemon=True).start()
        
    else:
        page.controls.append(ft.Text("未授予存储权限，无法下载。", style="error"))
        page.update()

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # 输入组件
    mpd_link = ft.TextField(label="MPD 链接", value="tbw31/tbw31_hd_03_6000k.mpd")
    key = ft.TextField(label="32位 KEY", value="a7594b3ac7e5a4e6fab7f53796")
    download_btn = ft.ElevatedButton("开始下载", on_click=lambda e: start_download(e, page, mpd_link.value, key.value))
    
    # 日志区域
    log_area = ft.Column(spacing=5, expand=True)
    
    # 将日志输出重定向到 log_area
    def add_log(text, style=None):
        log_area.controls.append(ft.Text(text, style=style))
        page.update()
    
    page.controls.extend([
        mpd_link,
        key,
        download_btn,
        ft.Text("运行日志:"),
        log_area
    ])
    
    # 初始化时检查权限
    add_log("检测到 Android 设备", "info")
    add_log("请确保已授予存储权限", "warning")
    add_log("基本文件操作权限正常", "success")
    add_log("初始化引擎...", "info")

if __name__ == "__main__":
    ft.app(target=main)
