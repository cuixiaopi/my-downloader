import flet as ft
import os
import shutil
import subprocess
import threading
import traceback
from flet import Permission, permission_request
from pathlib import Path
import json

def is_android():
    return os.environ.get("FLET_PLATFORM") == "android"

def get_android_storage_path():
    """获取 Android 的外部存储路径"""
    # Android 标准外部存储路径
    paths = [
        "/storage/emulated/0/Download",  # 主用户
        "/sdcard/Download",              # 传统路径
        os.path.expanduser("~/storage/shared/Download"),  # 某些设备
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    # 如果都没有，尝试获取环境变量
    ext_storage = os.environ.get("EXTERNAL_STORAGE", "")
    if ext_storage:
        download_path = os.path.join(ext_storage, "Download")
        if not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)
        return download_path
    
    return None

def get_ffmpeg_path(page: ft.Page):
    """获取 ffmpeg 可执行文件路径（Android 14 兼容）"""
    if not is_android():
        return "ffmpeg"  # PC端使用系统 ffmpeg
    
    # Android 应用私有目录
    app_data = os.environ.get("FLET_APP_DATA", "")
    if not app_data:
        app_data = "/data/data/com.flet.my_downloader/files"  # 默认路径
    
    ffmpeg_dir = os.path.join(app_data, "bin")
    os.makedirs(ffmpeg_dir, exist_ok=True)
    ffmpeg_bin = os.path.join(ffmpeg_dir, "ffmpeg")
    
    # 从 assets 复制 ffmpeg
    if not os.path.exists(ffmpeg_bin):
        # Android 上 assets 路径
        assets_dir = os.environ.get("FLET_APP_ASSETS", "")
        src_ffmpeg = os.path.join(assets_dir, "ffmpeg")
        
        if os.path.exists(src_ffmpeg):
            try:
                shutil.copy(src_ffmpeg, ffmpeg_bin)
                os.chmod(ffmpeg_bin, 0o755)
                page.snack_bar = ft.SnackBar(ft.Text("✅ FFmpeg 初始化完成"))
                page.snack_bar.open = True
                page.update()
            except Exception as e:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ FFmpeg 复制失败: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                return None
        else:
            # 尝试从打包的 assets 目录复制
            base_dir = os.path.dirname(os.path.abspath(__file__))
            src_assets = os.path.join(base_dir, "assets", "ffmpeg")
            if os.path.exists(src_assets):
                shutil.copy(src_assets, ffmpeg_bin)
                os.chmod(ffmpeg_bin, 0o755)
            else:
                return None
    return ffmpeg_bin

def check_and_request_permissions(page: ft.Page, log_func):
    """Android 14 权限检查和请求"""
    if not is_android():
        return True
    
    # Android 14 需要 MANAGE_EXTERNAL_STORAGE
    try:
        # 检查是否已有权限
        from android.permissions import check_permission, request_permissions, Permission
        
        # Android 14 需要的权限
        permissions = [
            Permission.MANAGE_EXTERNAL_STORAGE,  # 管理所有文件
            Permission.READ_EXTERNAL_STORAGE,     # 读取
            Permission.WRITE_EXTERNAL_STORAGE,    # 写入（兼容旧版本）
        ]
        
        # 检查权限
        granted = all(check_permission(p) for p in permissions)
        
        if not granted:
            log_func("📱 请求 Android 14 存储权限...")
            # 请求权限
            request_permissions(permissions)
            
            # 再次检查
            granted = all(check_permission(p) for p in permissions)
        
        if granted:
            log_func("✅ Android 14 权限已获得")
        else:
            log_func("⚠️ 部分权限未授予，可能需要手动设置")
            
        return granted
        
    except ImportError:
        # 非 Android 环境
        return True
    except Exception as e:
        log_func(f"⚠️ 权限检查异常: {str(e)}")
        return False

def main(page: ft.Page):
    page.title = "DRM 下载大师 (Android 14)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # 状态变量
    has_permission = False
    ffmpeg_path = None
    
    url_input = ft.TextField(
        label="MPD 链接", 
        border_radius=10,
        hint_text="输入视频的 MPD 链接"
    )
    key_input = ft.TextField(
        label="32位 KEY", 
        border_radius=10,
        hint_text="输入 64 字符的解密密钥"
    )
    
    log_box = ft.TextField(
        label="运行日志",
        multiline=True,
        read_only=True,
        min_lines=15,
        text_size=12
    )
    
    pb = ft.ProgressBar(visible=False)
    
    # 权限状态显示
    perm_status = ft.Text("🔴 等待权限检查", size=16, color=ft.colors.RED)
    
    def log(msg):
        log_box.value += msg + "\n"
        page.update()
    
    def check_initial_status():
        """初始化检查"""
        nonlocal ffmpeg_path, has_permission
        
        if is_android():
            log("📱 检测到 Android 14+ 设备")
            log("正在初始化...")
            
            # 获取 ffmpeg
            ffmpeg_path = get_ffmpeg_path(page)
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                log(f"✅ FFmpeg 位置: {ffmpeg_path}")
            else:
                log("❌ FFmpeg 初始化失败")
                return
            
            # 检查权限
            has_permission = check_and_request_permissions(page, log)
            if has_permission:
                perm_status.value = "🟢 权限已获取"
                perm_status.color = ft.colors.GREEN
                btn.disabled = False
            else:
                perm_status.value = "🔴 需要存储权限"
                perm_status.color = ft.colors.RED
                log("请在系统设置中开启存储权限:")
                log("1. 进入手机设置")
                log("2. 找到本应用")
                log("3. 权限 → 文件和媒体 → 允许")
                log("4. 或 特殊权限 → 安装未知应用 → 允许")
        else:
            log("💻 PC 环境")
            ffmpeg_path = "ffmpeg"
            has_permission = True
            perm_status.value = "🟢 PC 环境"
            perm_status.color = ft.colors.GREEN
            btn.disabled = False
        
        page.update()
    
    def on_permission_btn_click(e):
        """手动请求权限"""
        if is_android():
            has_perm = check_and_request_permissions(page, log)
            if has_perm:
                perm_status.value = "🟢 权限已获取"
                perm_status.color = ft.colors.GREEN
                btn.disabled = False
            else:
                # 引导用户手动设置
                show_manual_settings_dialog()
        page.update()
    
    def show_manual_settings_dialog():
        """显示手动设置指引"""
        dlg = ft.AlertDialog(
            title=ft.Text("手动设置权限"),
            content=ft.Column([
                ft.Text("Android 14 需要手动开启权限:", weight=ft.FontWeight.BOLD),
                ft.Text("1. 打开手机 设置"),
                ft.Text("2. 找到 'DRM 下载大师'"),
                ft.Text("3. 进入 权限 或 应用信息"),
                ft.Text("4. 选择 '文件和媒体' 权限"),
                ft.Text("5. 选择 '允许管理所有文件'"),
                ft.Text("6. 返回重新启动应用"),
            ], tight=True),
            actions=[ft.TextButton("确定", on_click=lambda e: page.close(dlg))]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()
    
    def run(e):
        if not has_permission:
            log("❌ 请先获取存储权限")
            return
        
        btn.disabled = True
        pb.visible = True
        page.update()
        
        def download_task():
            try:
                log("🚀 开始下载流程...")
                
                # 获取输入
                url = url_input.value.strip()
                key = key_input.value.strip()
                
                if not url:
                    log("❌ 请输入 MPD 链接")
                    return
                
                if not key or len(key) != 64:
                    log("❌ 密钥必须是 64 字符 (32字节)")
                    return
                
                # 获取输出路径
                if is_android():
                    download_dir = get_android_storage_path()
                    if not download_dir:
                        download_dir = "/storage/emulated/0/Download"
                    
                    # 确保目录存在
                    os.makedirs(download_dir, exist_ok=True)
                    
                    # 生成唯一文件名
                    import time
                    timestamp = int(time.time())
                    out_file = os.path.join(download_dir, f"video_{timestamp}.mp4")
                else:
                    out_file = "video.mp4"
                
                log(f"📁 输出路径: {out_file}")
                
                # 构建命令
                cmd = [
                    ffmpeg_path,
                    "-decryption_key", key,
                    "-i", url,
                    "-c", "copy",
                    "-y", out_file
                ]
                
                log("🎬 执行下载命令...")
                log(f"命令: {' '.join(cmd[:6])}...")
                
                # 执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 读取输出
                for line in process.stdout:
                    if "time=" in line:
                        # 提取时间信息
                        import re
                        time_match = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
                        if time_match:
                            log(f"⏱️ 进度: {time_match.group(1)}")
                    
                    if "speed=" in line:
                        speed_match = re.search(r"speed=([\d\.]+)x", line)
                        if speed_match:
                            log(f"🚀 速度: {speed_match.group(1)}x")
                
                process.wait()
                
                if process.returncode == 0:
                    if os.path.exists(out_file):
                        size_mb = os.path.getsize(out_file) / (1024 * 1024)
                        log(f"✅ 下载完成! 文件大小: {size_mb:.2f} MB")
                        log(f"📁 保存到: {out_file}")
                    else:
                        log("⚠️ 命令成功但文件未找到，可能在其他位置")
                else:
                    log(f"❌ 下载失败，返回码: {process.returncode}")
                    log("可能的原因:")
                    log("1. 网络连接问题")
                    log("2. 密钥错误")
                    log("3. 链接失效")
                    log("4. 存储空间不足")
                
            except Exception as ex:
                log(f"💥 发生错误: {str(ex)}")
                log(traceback.format_exc())
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()
        
        # 在新线程中执行下载
        threading.Thread(target=download_task, daemon=True).start()
    
    # 创建按钮
    perm_btn = ft.ElevatedButton(
        "检查/请求权限",
        on_click=on_permission_btn_click
    )
    
    btn = ft.ElevatedButton(
        "开始下载",
        on_click=run,
        disabled=True
    )
    
    # 添加到页面
    page.add(
        ft.Column([
            ft.Text("DRM 下载大师", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Android 14 版本", size=12, color=ft.colors.BLUE_GREY),
            ft.Divider(),
            perm_status,
            perm_btn,
            ft.Divider(),
            url_input,
            key_input,
            btn,
            pb,
            log_box
        ], scroll=ft.ScrollMode.AUTO)
    )
    
    # 启动时检查
    page.on_load = lambda e: check_initial_status()

ft.app(target=main)
