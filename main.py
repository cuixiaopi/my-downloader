import flet as ft
import os
import sys
import time
import traceback
import subprocess
import threading
from datetime import datetime

# 调试日志函数
def debug_log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {msg}"
    
    # 输出到stderr（在Android上可看到）
    print(log_msg, file=sys.stderr)
    
    # 保存到文件（用于调试）
    try:
        with open("/data/data/com.flet.my_downloader/files/debug.log", "a") as f:
            f.write(log_msg + "\n")
    except:
        pass
    
    return log_msg

def main(page: ft.Page):
    debug_log("=== 应用启动 ===")
    
    # 全局变量
    logs = []
    has_permission = False
    
    page.title = "DRM 下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # UI组件
    status_bar = ft.Text("🔴 初始化中...", size=16, color=ft.colors.RED)
    
    debug_box = ft.Column(
        [],
        scroll=ft.ScrollMode.AUTO,
        height=300,
        spacing=5
    )
    
    debug_container = ft.Container(
        content=debug_box,
        border=ft.border.all(1, ft.colors.GREY_300),
        border_radius=5,
        padding=10,
        visible=True
    )
    
    url_input = ft.TextField(label="MPD 链接", width=350)
    key_input = ft.TextField(label="32位 KEY (64字符)", width=350)
    
    progress_bar = ft.ProgressBar(width=350, visible=False)
    result_text = ft.Text("")
    
    def add_debug_log(msg, level="INFO"):
        color_map = {
            "INFO": ft.colors.BLUE,
            "SUCCESS": ft.colors.GREEN,
            "ERROR": ft.colors.RED,
            "WARN": ft.colors.ORANGE
        }
        
        log_msg = debug_log(msg, level)
        logs.append(log_msg)
        
        # 更新UI
        debug_box.controls.append(
            ft.Text(log_msg, size=12, color=color_map.get(level, ft.colors.BLACK))
        )
        
        # 保持最后50条日志
        if len(debug_box.controls) > 50:
            debug_box.controls.pop(0)
        
        page.update()
    
    def check_environment():
        """检查运行环境"""
        add_debug_log("🔍 检查环境...")
        
        # 检查平台
        platform = os.environ.get("FLET_PLATFORM", "unknown")
        add_debug_log(f"平台: {platform}")
        add_debug_log(f"Python: {sys.version}")
        
        # 检查目录权限
        test_dirs = [
            os.getcwd(),
            os.environ.get("FLET_APP_DATA", ""),
            "/data/data/com.flet.my_downloader/files"
        ]
        
        for d in test_dirs:
            if d and os.path.exists(d):
                add_debug_log(f"目录可访问: {d}")
                try:
                    test_file = os.path.join(d, "test.txt")
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    add_debug_log(f"  ✓ 可写入", "SUCCESS")
                except Exception as e:
                    add_debug_log(f"  ✗ 不可写入: {str(e)}", "ERROR")
        
        return platform == "android"
    
    def test_storage_permission():
        """测试存储权限"""
        add_debug_log("📱 测试存储权限...")
        
        test_paths = [
            "/sdcard/Download/test.txt",
            "/storage/emulated/0/Download/test.txt",
            os.path.join(os.environ.get("EXTERNAL_STORAGE", ""), "Download/test.txt")
        ]
        
        for path in test_paths:
            try:
                dir_path = os.path.dirname(path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    add_debug_log(f"创建目录: {dir_path}")
                
                with open(path, "w") as f:
                    f.write(f"test {time.time()}")
                add_debug_log(f"✓ 写入成功: {path}", "SUCCESS")
                
                os.remove(path)
                add_debug_log(f"✓ 删除成功: {path}", "SUCCESS")
                return True
                
            except Exception as e:
                add_debug_log(f"✗ 权限测试失败 {path}: {str(e)}", "ERROR")
        
        return False
    
    def find_ffmpeg():
        """查找FFmpeg可执行文件"""
        add_debug_log("🔍 查找FFmpeg...")
        
        search_paths = [
            "assets/ffmpeg",
            "ffmpeg",
            os.path.join(os.environ.get("FLET_APP_DATA", ""), "ffmpeg"),
            "/data/data/com.flet.my_downloader/files/ffmpeg",
            "/system/bin/ffmpeg"
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                add_debug_log(f"✓ 找到FFmpeg: {path}", "SUCCESS")
                
                # 检查权限
                try:
                    st = os.stat(path)
                    add_debug_log(f"  权限: {oct(st.st_mode)}")
                    add_debug_log(f"  大小: {st.st_size} bytes")
                    
                    if not os.access(path, os.X_OK):
                        os.chmod(path, 0o755)
                        add_debug_log("  已添加执行权限")
                    
                    return path
                except Exception as e:
                    add_debug_log(f"  ✗ 权限错误: {str(e)}", "ERROR")
        
        add_debug_log("✗ 未找到FFmpeg", "ERROR")
        return None
    
    def test_ffmpeg(ffmpeg_path):
        """测试FFmpeg功能"""
        add_debug_log("🧪 测试FFmpeg...")
        
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                add_debug_log(f"✓ FFmpeg版本: {version_line}", "SUCCESS")
                return True
            else:
                add_debug_log(f"✗ FFmpeg测试失败: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            add_debug_log("✗ FFmpeg测试超时", "ERROR")
            return False
        except Exception as e:
            add_debug_log(f"✗ FFmpeg测试异常: {str(e)}", "ERROR")
            return False
    
    def on_permission_test(e):
        """手动测试权限"""
        add_debug_log("🔧 手动权限测试...")
        
        if test_storage_permission():
            status_bar.value = "🟢 存储权限正常"
            status_bar.color = ft.colors.GREEN
            has_permission = True
        else:
            status_bar.value = "🔴 需要存储权限"
            status_bar.color = ft.colors.RED
            
            # 显示手动设置指引
            add_debug_log("请手动设置权限:", "WARN")
            add_debug_log("1. 打开手机设置 → 应用 → 本应用", "WARN")
            add_debug_log("2. 权限 → 文件和媒体 → 允许管理所有文件", "WARN")
        
        page.update()
    
    def on_ffmpeg_test(e):
        """测试FFmpeg"""
        ffmpeg_path = find_ffmpeg()
        if ffmpeg_path:
            test_ffmpeg(ffmpeg_path)
        page.update()
    
    def on_start_download(e):
        """开始下载"""
        add_debug_log("🚀 开始下载任务...")
        
        # 验证输入
        url = url_input.value.strip()
        key = key_input.value.strip()
        
        if not url:
            add_debug_log("✗ 请输入MPD链接", "ERROR")
            return
        
        if not key or len(key) != 64:
            add_debug_log("✗ KEY必须是64字符", "ERROR")
            return
        
        # 检查权限
        if not test_storage_permission():
            add_debug_log("✗ 没有存储权限，请先测试权限", "ERROR")
            return
        
        # 查找FFmpeg
        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            add_debug_log("✗ 找不到FFmpeg", "ERROR")
            return
        
        # 测试FFmpeg
        if not test_ffmpeg(ffmpeg_path):
            add_debug_log("✗ FFmpeg测试失败", "ERROR")
            return
        
        # 禁用按钮，显示进度
        start_btn.disabled = True
        progress_bar.visible = True
        result_text.value = ""
        page.update()
        
        def download_task():
            try:
                add_debug_log("📥 开始下载...")
                
                # 输出路径
                timestamp = int(time.time())
                output_path = f"/sdcard/Download/video_{timestamp}.mp4"
                add_debug_log(f"输出路径: {output_path}")
                
                # 执行命令
                cmd = [
                    ffmpeg_path,
                    "-decryption_key", key,
                    "-i", url,
                    "-c", "copy",
                    "-y", output_path
                ]
                
                add_debug_log(f"执行命令: {' '.join(cmd[:6])}...")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # 读取输出
                for line in process.stdout:
                    if "time=" in line:
                        add_debug_log(f"进度: {line.strip()[:80]}")
                    elif "error" in line.lower() or "fail" in line.lower():
                        add_debug_log(f"错误: {line.strip()}", "ERROR")
                
                process.wait()
                
                if process.returncode == 0:
                    if os.path.exists(output_path):
                        size = os.path.getsize(output_path) / (1024 * 1024)
                        add_debug_log(f"✅ 下载完成! 大小: {size:.2f}MB", "SUCCESS")
                        result_text.value = f"✅ 下载完成! 文件: {output_path}"
                    else:
                        add_debug_log("✅ 命令执行成功，但文件未找到", "WARN")
                else:
                    add_debug_log(f"❌ 下载失败，错误码: {process.returncode}", "ERROR")
                    result_text.value = "❌ 下载失败"
                
            except Exception as e:
                add_debug_log(f"💥 下载异常: {str(e)}", "ERROR")
                add_debug_log(traceback.format_exc(), "ERROR")
                result_text.value = f"❌ 错误: {str(e)}"
            finally:
                start_btn.disabled = False
                progress_bar.visible = False
                page.update()
        
        # 在新线程中执行
        threading.Thread(target=download_task, daemon=True).start()
    
    def on_clear_logs(e):
        """清空日志"""
        debug_box.controls.clear()
        page.update()
    
    def on_copy_logs(e):
        """复制日志"""
        all_logs = "\n".join(logs[-20:])
        page.set_clipboard(all_logs)
        add_debug_log("📋 日志已复制到剪贴板", "SUCCESS")
    
    # 创建按钮
    permission_btn = ft.ElevatedButton("测试权限", on_click=on_permission_test)
    ffmpeg_btn = ft.ElevatedButton("测试FFmpeg", on_click=on_ffmpeg_test)
    start_btn = ft.ElevatedButton("开始下载", on_click=on_start_download)
    clear_btn = ft.OutlinedButton("清空日志", on_click=on_clear_logs)
    copy_btn = ft.OutlinedButton("复制日志", on_click=on_copy_logs)
    
    # 添加到页面
    page.add(
        ft.Column([
            ft.Text("DRM 下载大师 - 调试版", size=24, weight=ft.FontWeight.BOLD),
            status_bar,
            ft.Divider(),
            
            ft.Row([permission_btn, ffmpeg_btn], spacing=10),
            ft.Divider(),
            
            url_input,
            key_input,
            start_btn,
            progress_bar,
            result_text,
            ft.Divider(),
            
            ft.Row([
                ft.Text("调试日志:", size=16, weight=ft.FontWeight.BOLD),
                clear_btn,
                copy_btn
            ]),
            debug_container
        ], scroll=ft.ScrollMode.AUTO)
    )
    
    # 初始检查
    add_debug_log("🔧 初始化检查...")
    is_android = check_environment()
    
    if is_android:
        status_bar.value = "📱 Android设备检测到"
        if test_storage_permission():
            status_bar.value = "🟢 权限正常"
            status_bar.color = ft.colors.GREEN
            has_permission = True
        else:
            status_bar.value = "🟡 需要存储权限"
            status_bar.color = ft.colors.ORANGE
    else:
        status_bar.value = "💻 PC环境"
        status_bar.color = ft.colors.BLUE
    
    # 查找并测试FFmpeg
    ffmpeg_path = find_ffmpeg()
    if ffmpeg_path:
        test_ffmpeg(ffmpeg_path)
    
    add_debug_log("✅ 应用初始化完成")
    page.update()

# 启动应用
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        debug_log(f"💥 应用启动失败: {str(e)}", "ERROR")
        debug_log(traceback.format_exc(), "ERROR")
