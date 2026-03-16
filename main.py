import flet as ft
import os
import shutil
import subprocess
import threading
import traceback
import time

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # UI组件
    url_input = ft.TextField(
        label="MPD 链接", 
        border_radius=10,
        hint_text="例如: https://example.com/video.mpd"
    )
    
    key_input = ft.TextField(
        label="32位 KEY", 
        border_radius=10,
        hint_text="64个字符的解密密钥"
    )
    
    log_box = ft.TextField(
        label="运行日志",
        multiline=True,
        read_only=True,
        min_lines=15,
        text_size=12
    )
    
    pb = ft.ProgressBar(visible=False)
    
    def log(msg):
        log_box.value += msg + "\n"
        page.update()
    
    def check_android_permission():
        """Android权限检查（简化版）"""
        try:
            # 尝试在Download目录创建测试文件
            test_path = "/storage/emulated/0/Download/test_permission.txt"
            
            # 先创建目录（如果不存在）
            os.makedirs(os.path.dirname(test_path), exist_ok=True)
            
            with open(test_path, "w") as f:
                f.write("test")
            
            os.remove(test_path)
            return True
        except:
            return False
    
    def request_permission_dialog():
        """显示权限请求提示"""
        dlg = ft.AlertDialog(
            title=ft.Text("需要存储权限"),
            content=ft.Column([
                ft.Text("请到系统设置中授予存储权限：", weight=ft.FontWeight.BOLD),
                ft.Text("1. 打开手机 设置"),
                ft.Text("2. 找到 'DRM 下载大师'"),
                ft.Text("3. 进入 权限 或 应用信息"),
                ft.Text("4. 选择 '文件和媒体' 权限"),
                ft.Text("5. 选择 '允许管理所有文件'"),
            ], tight=True),
            actions=[
                ft.TextButton("确定", on_click=lambda e: page.close(dlg))
            ]
        )
        page.dialog = dlg
        dlg.open = True
    
    def get_ffmpeg_executable():
        """获取FFmpeg可执行文件路径"""
        # 首先检查assets目录
        assets_ffmpeg = os.path.join("assets", "ffmpeg")
        if os.path.exists(assets_ffmpeg):
            return assets_ffmpeg
        
        # 如果assets没有，尝试从APK内部复制
        try:
            # Android上，Flet会将assets复制到可访问的目录
            app_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths = [
                os.path.join(app_dir, "assets", "ffmpeg"),
                os.path.join(os.environ.get("FLET_APP_DATA", ""), "ffmpeg"),
                "ffmpeg"  # 系统PATH
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        except:
            pass
        
        return None
    
    def run(e):
        # 检查权限
        if not check_android_permission():
            log("⚠️ 存储权限不足")
            request_permission_dialog()
            return
        
        btn.disabled = True
        pb.visible = True
        page.update()
        
        def download_task():
            try:
                log("🚀 开始下载流程...")
                
                # 1. 获取FFmpeg
                ffmpeg_path = get_ffmpeg_executable()
                if not ffmpeg_path:
                    log("❌ 找不到FFmpeg，请重新安装应用")
                    return
                
                log(f"✅ FFmpeg路径: {ffmpeg_path}")
                
                # 2. 检查文件权限
                if not os.access(ffmpeg_path, os.X_OK):
                    os.chmod(ffmpeg_path, 0o755)
                    log("✅ 已设置FFmpeg执行权限")
                
                # 3. 验证输入
                url = url_input.value.strip()
                key = key_input.value.strip()
                
                if not url:
                    log("❌ 请输入MPD链接")
                    return
                
                if not key or len(key) != 64:
                    log("❌ 密钥必须是64个字符（32字节）")
                    return
                
                # 4. 设置输出路径
                output_dir = "/storage/emulated/0/Download"
                if not os.path.exists(output_dir):
                    # 尝试其他路径
                    output_dir = "/sdcard/Download"
                
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
                timestamp = int(time.time())
                output_file = os.path.join(output_dir, f"video_{timestamp}.mp4")
                
                log(f"📁 输出到: {output_file}")
                
                # 5. 执行FFmpeg命令
                cmd = [
                    ffmpeg_path,
                    "-decryption_key", key,
                    "-i", url,
                    "-c", "copy",
                    "-y", output_file
                ]
                
                log("🎬 开始下载和解密...")
                
                # 执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # 读取进度
                for line in process.stdout:
                    if "time=" in line or "speed=" in line:
                        # 提取进度信息
                        import re
                        time_match = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
                        if time_match:
                            log(f"⏱️ 进度: {time_match.group(1)}")
                
                process.wait()
                
                if process.returncode == 0:
                    if os.path.exists(output_file):
                        size = os.path.getsize(output_file) / (1024 * 1024)
                        log(f"✅ 下载完成！大小: {size:.2f} MB")
                        log(f"📁 保存到: {output_file}")
                    else:
                        log("✅ 命令执行成功")
                else:
                    log(f"❌ 下载失败，错误码: {process.returncode}")
                
            except PermissionError:
                log("❌ 权限被拒绝")
                log("请在Android设置中授予'管理所有文件'权限")
                request_permission_dialog()
            except FileNotFoundError:
                log("❌ FFmpeg未找到，构建可能有问题")
            except Exception as ex:
                log(f"💥 错误: {str(ex)}")
                log(traceback.format_exc())
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()
        
        # 在新线程中执行下载
        threading.Thread(target=download_task, daemon=True).start()
    
    # 创建按钮
    btn = ft.ElevatedButton("开始下载", on_click=run)
    
    # 添加帮助文本
    help_text = ft.Text(
        "注意：Android 14需要手动开启'管理所有文件'权限",
        size=12,
        color=ft.colors.ORANGE_700
    )
    
    # 添加到页面
    page.add(
        ft.Column([
            ft.Text("DRM 下载大师", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            url_input,
            key_input,
            help_text,
            btn,
            pb,
            log_box
        ])
    )
    
    # 初始日志
    log("应用已启动")
    log("点击'开始下载'按钮进行测试")

ft.app(target=main)
