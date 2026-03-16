import flet as ft
import os
import shutil
import subprocess
import threading
import traceback
import sys
from pathlib import Path

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # 初始化权限状态
    page.platform.increment_asset_version()
    
    url_input = ft.TextField(label="MPD 链接", border_radius=10, width=400)
    key_input = ft.TextField(label="32位 KEY", border_radius=10, width=400)
    
    log_box = ft.TextField(
        label="运行日志",
        multiline=True,
        read_only=True,
        min_lines=15,
        text_size=12,
        width=400
    )
    
    pb = ft.ProgressBar(visible=False, width=400)
    
    # 权限相关变量
    has_permission = False
    
    def log(msg):
        log_box.value += msg + "\n"
        page.update()
    
    def check_permission(e):
        nonlocal has_permission
        
        # 在 Android 上，尝试请求权限
        if page.platform == "android":
            try:
                from android.permissions import Permission, request_permission
                from android.storage import app_external_storage_path
                
                # 请求存储权限
                permissions = [Permission.WRITE_EXTERNAL_STORAGE, 
                              Permission.READ_EXTERNAL_STORAGE]
                
                for perm in permissions:
                    result = request_permission(perm)
                    if result:
                        log(f"✅ 已获取权限: {perm}")
                        has_permission = True
                    else:
                        log(f"❌ 权限被拒绝: {perm}")
                        has_permission = False
                        
                if has_permission:
                    # 获取 Android 的 Downloads 目录
                    downloads_path = "/storage/emulated/0/Download"
                    if os.path.exists(downloads_path):
                        log(f"📁 下载目录: {downloads_path}")
                        return downloads_path
                        
            except ImportError:
                log("⚠️ 非 Android 环境，跳过权限检查")
                has_permission = True
        else:
            has_permission = True
            
        return None
    
    def get_android_download_path():
        """获取 Android 的下载路径"""
        try:
            # 尝试多种可能的下载路径
            possible_paths = [
                "/storage/emulated/0/Download",
                "/sdcard/Download",
                "/storage/self/primary/Download",
                str(Path.home() / "Download")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
                    
            # 如果都不存在，使用当前应用的目录
            from android.storage import app_external_storage_path
            app_storage = app_external_storage_path()
            download_dir = os.path.join(app_storage, "Download")
            os.makedirs(download_dir, exist_ok=True)
            return download_dir
            
        except Exception as e:
            log(f"⚠️ 无法获取下载路径: {e}")
            return "/sdcard/Download"  # 回退到默认路径
    
    def run(e):
        nonlocal has_permission
        
        # 检查权限
        downloads_path = check_permission(e)
        if downloads_path is None and page.platform == "android":
            log("❌ 请先授予存储权限！")
            return
            
        btn.disabled = True
        pb.visible = True
        page.update()
        
        def task():
            try:
                log("🚀 初始化引擎...")
                
                app_dir = os.getcwd()
                ffmpeg_src = os.path.join(app_dir, "assets", "ffmpeg")
                
                data_dir = os.environ.get("FLET_APP_DATA", app_dir)
                ffmpeg_bin = os.path.join(data_dir, "ffmpeg")
                
                # 复制 ffmpeg
                if os.path.exists(ffmpeg_src):
                    shutil.copy(ffmpeg_src, ffmpeg_bin)
                    os.chmod(ffmpeg_bin, 0o755)
                    log("✅ FFmpeg 已部署")
                else:
                    log("❌ 找不到 ffmpeg 文件")
                    return
                
                url = url_input.value.strip()
                key = key_input.value.strip()
                
                if not url or not key:
                    log("❌ 请输入 MPD 链接和 KEY")
                    return
                
                # 在 Android 上使用正确的下载路径
                if page.platform == "android":
                    base_path = get_android_download_path()
                    out_file = os.path.join(base_path, "video.mp4")
                    
                    # 确保目录存在
                    os.makedirs(os.path.dirname(out_file), exist_ok=True)
                    log(f"📁 文件将保存到: {out_file}")
                else:
                    out_file = "video.mp4"
                
                # 构建命令
                cmd = [
                    ffmpeg_bin,
                    "-decryption_key", key,
                    "-i", url,
                    "-c", "copy",
                    "-y", out_file
                ]
                
                log(f"🎬 开始下载到: {out_file}")
                log(f"🔧 命令: {' '.join(cmd[:6])} ...")
                
                # 执行命令
                p = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                # 读取输出
                for line in p.stdout:
                    if "time=" in line or "speed=" in line:
                        log(f"📈 {line.strip()}")
                    elif "error" in line.lower():
                        log(f"⚠️ {line.strip()}")
                
                p.wait()
                
                if p.returncode == 0:
                    log(f"✅ 下载完成！")
                    log(f"📁 文件位置: {out_file}")
                    
                    # 在 Android 上显示通知
                    if page.platform == "android":
                        try:
                            from android.toast import toast
                            toast("下载完成！文件已保存到下载文件夹")
                        except ImportError:
                            pass
                else:
                    log(f"❌ 失败，返回码 {p.returncode}")
                    log(f"🔧 完整命令: {' '.join(cmd)}")
                
            except Exception as ex:
                log("💥 崩溃：")
                log(str(ex))
                log(traceback.format_exc())
                
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()
        
        threading.Thread(target=task, daemon=True).start()
    
    # 添加权限按钮
    perm_btn = ft.ElevatedButton(
        "请求存储权限",
        on_click=check_permission,
        icon=ft.icons.LOCK_OPEN
    )
    
    btn = ft.ElevatedButton("开始下载", on_click=run, icon=ft.icons.DOWNLOAD)
    
    # 添加说明文本
    info_text = ft.Text(
        "⚠️ 注意：Android 10+ 需要授予存储权限才能保存文件",
        size=12,
        color=ft.colors.ORANGE
    )
    
    page.add(
        ft.Column([
            ft.Container(height=20),
            url_input,
            key_input,
            ft.Row([perm_btn, btn], spacing=20),
            info_text,
            pb,
            log_box
        ], scroll=ft.ScrollMode.AUTO)
    )
    
    # 页面加载时检查权限
    def on_page_load(e):
        if page.platform == "android":
            log("📱 Android 设备检测到，请先请求存储权限")
    
    page.on_load = on_page_load

ft.app(target=main)
