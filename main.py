import flet as ft
import os
import sys
import time
import threading

# 调试日志
def log(msg):
    with open("/data/data/com.flet.downloader/files/app.log", "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

def main(page: ft.Page):
    try:
        log("=== 应用启动 ===")
        
        # 1. 强制设置页面属性
        page.title = "DRM下载器"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.bgcolor = ft.colors.WHITE
        
        log("页面对象创建成功")
        
        # 2. 立即显示内容（不等待）
        loading_text = ft.Text("正在加载...", size=20, color=ft.colors.BLUE)
        page.add(loading_text)
        page.update()
        
        log("已显示加载界面")
        
        # 3. 延迟加载主界面（避免初始化阻塞）
        def load_main_ui():
            time.sleep(1)  # 给WebView一点时间
            
            try:
                # 检查ffmpeg
                ffmpeg_path = "assets/ffmpeg"
                has_ffmpeg = os.path.exists(ffmpeg_path)
                
                # 检查权限
                can_write = False
                try:
                    with open("/sdcard/test.txt", "w") as f:
                        f.write("test")
                    os.remove("/sdcard/test.txt")
                    can_write = True
                except:
                    can_write = False
                
                # 更新UI
                page.controls.clear()
                
                # 状态指示器
                status_color = ft.colors.GREEN if can_write else ft.colors.RED
                status_text = ft.Text(
                    "✓ 就绪" if can_write else "✗ 需要权限",
                    color=status_color,
                    size=18
                )
                
                # 主界面
                main_column = ft.Column([
                    ft.Text("DRM下载大师", 
                           size=28, 
                           weight=ft.FontWeight.BOLD,
                           color=ft.colors.BLUE_800),
                    
                    ft.Divider(height=20),
                    
                    ft.Text("当前状态:", size=16),
                    ft.Row([
                        ft.Icon(ft.icons.CHECK if has_ffmpeg else ft.icons.ERROR,
                               color=ft.colors.GREEN if has_ffmpeg else ft.colors.RED),
                        ft.Text(f"FFmpeg: {'已安装' if has_ffmpeg else '未找到'}"),
                    ]),
                    
                    ft.Row([
                        ft.Icon(ft.icons.CHECK if can_write else ft.icons.WARNING,
                               color=ft.colors.GREEN if can_write else ft.colors.ORANGE),
                        ft.Text(f"存储权限: {'已授权' if can_write else '未授权'}"),
                    ]),
                    
                    ft.Divider(height=20),
                    
                    ft.Text("输入:", size=16, weight=ft.FontWeight.BOLD),
                    ft.TextField(
                        label="MPD链接",
                        width=300,
                        border_color=ft.colors.BLUE_400
                    ),
                    
                    ft.TextField(
                        label="32位KEY",
                        width=300,
                        border_color=ft.colors.BLUE_400,
                        password=True,
                        can_reveal_password=True
                    ),
                    
                    ft.Divider(height=20),
                    
                    ft.ElevatedButton(
                        "开始下载",
                        icon=ft.icons.DOWNLOAD,
                        on_click=lambda e: start_download(page)
                    ),
                    
                    ft.Text("", size=12, color=ft.colors.GREY),
                    
                    status_text
                ], 
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                
                page.add(main_column)
                page.update()
                log("主界面加载完成")
                
            except Exception as e:
                log(f"加载主界面出错: {str(e)}")
                show_error_page(page, str(e))
        
        # 在新线程中加载主界面
        threading.Thread(target=load_main_ui, daemon=True).start()
        
        log("启动界面线程")
        
    except Exception as e:
        log(f"主函数出错: {str(e)}")
        # 尝试显示错误页面
        try:
            page.controls.clear()
            page.add(ft.Text(f"启动错误: {str(e)}", color=ft.colors.RED))
            page.update()
        except:
            pass

def show_error_page(page, error_msg):
    """显示错误页面"""
    try:
        page.controls.clear()
        page.add(
            ft.Column([
                ft.Text("❌ 启动失败", size=24, color=ft.colors.RED),
                ft.Text(f"错误: {error_msg[:100]}", size=14),
                ft.Divider(),
                ft.Text("请尝试:", size=16),
                ft.Text("1. 重启应用", size=14),
                ft.Text("2. 清除应用数据", size=14),
                ft.Text("3. 重新安装", size=14),
                ft.ElevatedButton("退出应用", 
                                on_click=lambda e: os._exit(0))
            ], spacing=10)
        )
        page.update()
    except:
        pass

def start_download(page):
    """开始下载"""
    try:
        page.controls[-1].value = "开始下载..."
        page.update()
        time.sleep(2)
        page.controls[-1].value = "下载完成!"
        page.update()
    except:
        pass

# 启动应用
if __name__ == "__main__":
    # 创建日志目录
    try:
        os.makedirs("/data/data/com.flet.downloader/files", exist_ok=True)
    except:
        pass
    
    # 启动应用
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,  # 强制使用WebView
        assets_dir="assets"
    )
