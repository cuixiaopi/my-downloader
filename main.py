import flet as ft
import os
import shutil
import subprocess
import threading
import traceback
from pathlib import Path
import sys

def main(page: ft.Page):
    page.title = "DRM 下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 700
    page.window_resizable = False
    
    url_input = ft.TextField(
        label="MPD 链接", 
        border_radius=10, 
        width=380,
        hint_text="请输入 MPD 文件链接"
    )
    
    key_input = ft.TextField(
        label="32位 KEY", 
        border_radius=10, 
        width=380,
        hint_text="请输入 32 位解密密钥",
        password=True,
        can_reveal_password=True
    )
    
    log_box = ft.TextField(
        label="运行日志",
        multiline=True,
        read_only=True,
        min_lines=15,
        text_size=12,
        width=380
    )
    
    pb = ft.ProgressBar(visible=False, width=380)
    
    # 状态标签
    status_text = ft.Text("就绪", color=ft.colors.BLUE)
    
    def log(msg):
        log_box.value += msg + "\n"
        page.update()
    
    def get_android_storage_path():
        """获取 Android 存储路径"""
        try:
            # 尝试多种可能的下载路径
            possible_paths = [
                "/storage/emulated/0/Download",
                "/sdcard/Download",
                "/storage/self/primary/Download",
                str(Path.home() / "Download"),
                "/storage/emulated/0/Android/data/com.example.drmdownloader/files/Download"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    log(f"✅ 找到存储路径: {path}")
                    return path
                else:
                    # 尝试创建目录
                    try:
                        os.makedirs(path, exist_ok=True)
                        if os.path.exists(path):
                            log(f"✅ 创建存储路径: {path}")
                            return path
                    except:
                        continue
            
            # 如果都不行，使用当前目录
            current_dir = os.getcwd()
            download_dir = os.path.join(current_dir, "Download")
            os.makedirs(download_dir, exist_ok=True)
            log(f"⚠️ 使用应用目录: {download_dir}")
            return download_dir
            
        except Exception as e:
            log(f"❌ 获取存储路径失败: {e}")
            return "/sdcard/Download"  # 回退到默认路径
    
    def check_storage_permission():
        """检查存储权限（简化版本）"""
        try:
            # 尝试在 Android 环境中获取权限
            if hasattr(page, 'platform') and page.platform == "android":
                log("📱 检测到 Android 环境")
                log("⚠️ 请确保已授予存储权限")
                
                # 测试写入权限
                test_path = "/storage/emulated/0/Download/test_permission.txt"
                try:
                    with open(test_path, "w") as f:
                        f.write("test")
                    os.remove(test_path)
                    log("✅ 存储权限测试通过")
                    return True
                except Exception as e:
                    log(f"❌ 存储权限不足: {e}")
                    log("📱 请在系统设置中手动授予存储权限")
                    return False
            return True
        except:
            return True  # 非 Android 环境默认返回 True
    
    def get_ffmpeg_path():
        """获取 FFmpeg 路径"""
        app_dir = os.getcwd()
        
        # 尝试从 assets 目录查找
        ffmpeg_src = os.path.join(app_dir, "assets", "ffmpeg")
        if os.path.exists(ffmpeg_src):
            return ffmpeg_src
        
        # 尝试从 data 目录查找
        data_dir = os.environ.get("FLET_APP_DATA", app_dir)
        ffmpeg_data = os.path.join(data_dir, "ffmpeg")
        if os.path.exists(ffmpeg_data):
            return ffmpeg_data
        
        # 如果在 Android APK 中，文件可能在别的位置
        # 尝试常见路径
        possible_paths = [
            os.path.join(app_dir, "files", "assets", "ffmpeg"),
            os.path.join("/data/data/com.example.drmdownloader/files", "ffmpeg"),
            "/data/user/0/com.example.drmdownloader/files/ffmpeg"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def copy_ffmpeg_to_data_dir():
        """将 ffmpeg 复制到可执行目录"""
        try:
            ffmpeg_src = get_ffmpeg_path()
            if not ffmpeg_src or not os.path.exists(ffmpeg_src):
                log("❌ 找不到 ffmpeg 文件")
                return None
            
            # 复制到应用数据目录
            data_dir = os.environ.get("FLET_APP_DATA", os.getcwd())
            ffmpeg_dst = os.path.join(data_dir, "ffmpeg")
            
            shutil.copy2(ffmpeg_src, ffmpeg_dst)
            os.chmod(ffmpeg_dst, 0o755)
            
            log(f"✅ FFmpeg 已部署到: {ffmpeg_dst}")
            return ffmpeg_dst
            
        except Exception as e:
            log(f"❌ 部署 FFmpeg 失败: {e}")
            return None
    
    def run(e):
        btn.disabled = True
        pb.visible = True
        status_text.value = "处理中..."
        status_text.color = ft.colors.ORANGE
        page.update()
        
        def task():
            try:
                log("=" * 40)
                log("🚀 启动下载任务")
                
                # 1. 检查存储权限
                if not check_storage_permission():
                    log("❌ 存储权限不足，无法继续")
                    return
                
                # 2. 获取存储路径
                base_path = get_android_storage_path()
                
                # 3. 部署 FFmpeg
                ffmpeg_path = copy_ffmpeg_to_data_dir()
                if not ffmpeg_path:
                    return
                
                # 4. 验证输入
                url = url_input.value.strip()
                key = key_input.value.strip()
                
                if not url:
                    log("❌ 请输入 MPD 链接")
                    return
                
                if not key or len(key) != 32:
                    log("❌ KEY 必须是 32 位十六进制字符串")
                    return
                
                # 5. 准备输出文件
                timestamp = ft.datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                out_file = os.path.join(base_path, f"video_{timestamp}.mp4")
                
                # 确保目录存在
                os.makedirs(os.path.dirname(out_file), exist_ok=True)
                
                log(f"📁 输出文件: {out_file}")
                log(f"🔑 密钥: {key[:8]}...")
                log(f"🌐 链接: {url[:50]}..." if len(url) > 50 else f"🌐 链接: {url}")
                
                # 6. 构建命令
                cmd = [
                    ffmpeg_path,
                    "-decryption_key", key,
                    "-i", url,
                    "-c", "copy",
                    "-y",  # 覆盖输出文件
                    out_file
                ]
                
                log("🎬 开始下载...")
                status_text.value = "下载中..."
                status_text.color = ft.colors.GREEN
                page.update()
                
                # 7. 执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 实时读取输出
                for line in iter(process.stdout.readline, ''):
                    if line:
                        if "time=" in line and "speed=" in line:
                            # 提取时间信息
                            import re
                            time_match = re.search(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})', line)
                            speed_match = re.search(r'speed=([\d.]+)x', line)
                            
                            if time_match and speed_match:
                                log(f"⏱️ 进度: {time_match.group(1)}, 速度: {speed_match.group(1)}x")
                        elif "error" in line.lower() or "failed" in line.lower():
                            log(f"⚠️ 错误: {line.strip()}")
                        elif "frame=" in line:
                            log(f"📊 {line.strip()}")
                
                process.wait()
                
                # 8. 检查结果
                if process.returncode == 0:
                    if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                        file_size = os.path.getsize(out_file) / (1024 * 1024)  # MB
                        log(f"✅ 下载完成！")
                        log(f"📁 文件: {out_file}")
                        log(f"💾 大小: {file_size:.2f} MB")
                        status_text.value = "下载完成"
                        status_text.color = ft.colors.GREEN
                        
                        # 显示完成消息
                        page.snack_bar = ft.SnackBar(
                            ft.Text(f"下载完成！文件大小: {file_size:.2f} MB"),
                            bgcolor=ft.colors.GREEN
                        )
                        page.snack_bar.open = True
                    else:
                        log("❌ 文件创建失败")
                        status_text.value = "文件创建失败"
                        status_text.color = ft.colors.RED
                else:
                    log(f"❌ 下载失败，返回码: {process.returncode}")
                    status_text.value = "下载失败"
                    status_text.color = ft.colors.RED
                
            except subprocess.CalledProcessError as e:
                log(f"❌ 命令执行失败: {e}")
                status_text.value = "命令执行失败"
                status_text.color = ft.colors.RED
                
            except Exception as ex:
                log("💥 程序异常:")
                log(str(ex))
                log(traceback.format_exc())
                status_text.value = "程序异常"
                status_text.color = ft.colors.RED
                
            finally:
                btn.disabled = False
                pb.visible = False
                page.update()
        
        threading.Thread(target=task, daemon=True).start()
    
    def check_permission(e):
        """检查权限按钮"""
        log("🔍 检查存储权限...")
        if check_storage_permission():
            log("✅ 存储权限正常")
        else:
            log("❌ 存储权限有问题，请检查系统设置")
    
    def clear_log(e):
        """清空日志"""
        log_box.value = ""
        page.update()
    
    # 创建按钮
    perm_btn = ft.ElevatedButton(
        "检查权限",
        on_click=check_permission,
        icon=ft.icons.PERM_DATA_SETTING,
        width=120
    )
    
    clear_btn = ft.ElevatedButton(
        "清空日志",
        on_click=clear_log,
        icon=ft.icons.CLEAR_ALL,
        width=120
    )
    
    btn = ft.ElevatedButton(
        "开始下载",
        on_click=run,
        icon=ft.icons.DOWNLOAD,
        width=380
    )
    
    # 添加说明
    instruction = ft.Column([
        ft.Text("使用说明:", weight=ft.FontWeight.BOLD, size=16),
        ft.Text("1. 粘贴 MPD 链接", size=12),
        ft.Text("2. 输入 32 位解密密钥", size=12),
        ft.Text("3. 点击'检查权限'确保有存储权限", size=12),
        ft.Text("4. 点击'开始下载'", size=12),
        ft.Text("注意: 需要 Android 存储权限", size=12, color=ft.colors.RED)
    ])
    
    # 布局
    page.add(
        ft.Column([
            ft.Container(height=10),
            instruction,
            ft.Container(height=10),
            url_input,
            key_input,
            ft.Row([perm_btn, clear_btn], alignment=ft.MainAxisAlignment.CENTER),
            btn,
            status_text,
            pb,
            ft.Text("运行日志:", weight=ft.FontWeight.BOLD),
            log_box
        ], scroll=ft.ScrollMode.AUTO)
    )

# 启动应用
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
