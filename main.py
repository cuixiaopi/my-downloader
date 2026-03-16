import flet as ft
import time
import os
import sys
import threading
from datetime import datetime

# 调试函数 - 记录日志到文件和控制台
def debug_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # 输出到控制台
    print(log_entry, file=sys.stderr, flush=True)
    
    # 尝试写入日志文件
    try:
        log_dir = "/data/data/com.flet.downloader/files"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except:
        pass  # 忽略文件写入错误
    
    return log_entry

def main(page: ft.Page):
    try:
        debug_log("========== 应用启动 ==========")
        
        # 1. 基本页面设置
        page.title = "DRM下载大师"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.bgcolor = ft.colors.WHITE
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        debug_log("页面设置完成")
        
        # 2. 立即显示加载界面
        loading_container = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50, stroke_width=2),
                ft.Text("正在启动应用...", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("请稍候", size=14, color=ft.colors.GREY_600)
            ], 
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        
        page.add(loading_container)
        page.update()
        debug_log("加载界面已显示")
        
        # 3. 延迟显示主界面
        def load_main_interface():
            time.sleep(2)  # 等待2秒，确保WebView完全加载
            
            try:
                debug_log("开始加载主界面")
                
                # 清除加载界面
                page.controls.clear()
                
                # 状态变量
                status_messages = []
                
                # 检查环境
                platform = sys.platform
                is_android = "linux" in platform and "android" in platform
                status_messages.append(f"平台: {'Android' if is_android else 'PC'}")
                
                # 检查可写目录
                try:
                    test_file = "test.txt"
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    status_messages.append("✓ 基本文件权限: 正常")
                except Exception as e:
                    status_messages.append(f"✗ 基本文件权限: {str(e)[:30]}")
                
                # 创建主界面
                url_input = ft.TextField(
                    label="MPD链接",
                    hint_text="输入视频的.mpd文件链接",
                    width=350,
                    border_color=ft.colors.BLUE_400
                )
                
                key_input = ft.TextField(
                    label="解密密钥 (32位)",
                    hint_text="输入64个字符的解密密钥",
                    width=350,
                    password=True,
                    can_reveal_password=True,
                    border_color=ft.colors.BLUE_400
                )
                
                result_text = ft.Text("", size=14)
                status_display = ft.Column(
                    [ft.Text(msg, size=12) for msg in status_messages],
                    spacing=5
                )
                
                def on_download_click(e):
                    debug_log("下载按钮被点击")
                    result_text.value = "正在准备下载..."
                    result_text.color = ft.colors.BLUE
                    page.update()
                    
                    # 验证输入
                    url = url_input.value.strip()
                    key = key_input.value.strip()
                    
                    if not url:
                        result_text.value = "❌ 请输入MPD链接"
                        result_text.color = ft.colors.RED
                        page.update()
                        return
                    
                    if not key or len(key) != 64:
                        result_text.value = "❌ 密钥必须是64个字符"
                        result_text.color = ft.colors.RED
                        page.update()
                        return
                    
                    # 模拟下载过程
                    def simulate_download():
                        time.sleep(1)
                        result_text.value = "⏳ 正在连接服务器..."
                        result_text.color = ft.colors.ORANGE
                        page.update()
                        
                        time.sleep(2)
                        result_text.value = "⏳ 正在下载视频..."
                        result_text.color = ft.colors.ORANGE
                        page.update()
                        
                        time.sleep(2)
                        result_text.value = "✅ 下载完成！(模拟)"
                        result_text.color = ft.colors.GREEN
                        page.update()
                        
                        debug_log("模拟下载完成")
                    
                    threading.Thread(target=simulate_download, daemon=True).start()
                
                def on_test_permission(e):
                    debug_log("测试权限按钮被点击")
                    result_text.value = "正在测试存储权限..."
                    result_text.color = ft.colors.BLUE
                    page.update()
                    
                    try:
                        # 尝试Android存储路径
                        test_paths = [
                            "/sdcard/Download/test.txt",
                            "/storage/emulated/0/Download/test.txt"
                        ]
                        
                        for path in test_paths:
                            try:
                                dir_path = os.path.dirname(path)
                                if dir_path and not os.path.exists(dir_path):
                                    os.makedirs(dir_path, exist_ok=True)
                                
                                with open(path, "w") as f:
                                    f.write(f"test {datetime.now().strftime('%H:%M:%S')}")
                                
                                os.remove(path)
                                result_text.value = f"✅ 存储权限正常: {path}"
                                result_text.color = ft.colors.GREEN
                                page.update()
                                return
                            except Exception as e:
                                debug_log(f"权限测试失败 {path}: {str(e)}")
                        
                        result_text.value = "❌ 需要手动授予存储权限"
                        result_text.color = ft.colors.RED
                        
                    except Exception as e:
                        result_text.value = f"❌ 权限测试错误: {str(e)[:30]}"
                        result_text.color = ft.colors.RED
                    
                    page.update()
                
                def on_clear_logs(e):
                    url_input.value = ""
                    key_input.value = ""
                    result_text.value = ""
                    page.update()
                    debug_log("输入已清空")
                
                # 构建主界面
                main_column = ft.Column([
                    # 标题区域
                    ft.Container(
                        content=ft.Column([
                            ft.Text("DRM下载大师", 
                                   size=28, 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.colors.BLUE_700,
                                   text_align=ft.TextAlign.CENTER),
                            ft.Text("Android专用版 v1.0", 
                                   size=12, 
                                   color=ft.colors.GREY_600,
                                   text_align=ft.TextAlign.CENTER)
                        ]),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=20)
                    ),
                    
                    ft.Divider(height=1, color=ft.colors.GREY_300),
                    
                    # 状态信息
                    ft.Container(
                        content=ft.Column([
                            ft.Text("系统状态:", size=16, weight=ft.FontWeight.BOLD),
                            status_display
                        ]),
                        padding=ft.padding.all(10),
                        bgcolor=ft.colors.GREY_50,
                        border_radius=10,
                        margin=ft.margin.only(bottom=20)
                    ),
                    
                    # 输入区域
                    ft.Text("视频信息:", size=16, weight=ft.FontWeight.BOLD),
                    url_input,
                    
                    ft.Container(height=10),
                    
                    key_input,
                    
                    ft.Container(height=20),
                    
                    # 按钮区域
                    ft.Row([
                        ft.ElevatedButton(
                            "测试存储权限",
                            icon=ft.icons.STORAGE,
                            on_click=on_test_permission,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.BLUE_50,
                                color=ft.colors.BLUE_700
                            )
                        ),
                        ft.ElevatedButton(
                            "开始下载",
                            icon=ft.icons.DOWNLOAD,
                            on_click=on_download_click,
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.BLUE_600,
                                color=ft.colors.WHITE
                            )
                        ),
                        ft.OutlinedButton(
                            "清空",
                            icon=ft.icons.CLEAR,
                            on_click=on_clear_logs
                        )
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Container(height=20),
                    
                    # 结果显示
                    ft.Container(
                        content=result_text,
                        padding=ft.padding.all(10),
                        bgcolor=ft.colors.GREY_50,
                        border_radius=10,
                        width=350
                    ),
                    
                    # 帮助文本
                    ft.Container(
                        content=ft.Column([
                            ft.Text("使用说明:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("1. 输入视频的MPD链接", size=12),
                            ft.Text("2. 输入32位解密密钥(64字符)", size=12),
                            ft.Text("3. 点击'开始下载'", size=12),
                            ft.Text("4. 文件将保存到Download文件夹", size=12)
                        ], spacing=5),
                        padding=ft.padding.all(10),
                        bgcolor=ft.colors.BLUE_50,
                        border_radius=10,
                        width=350
                    )
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO)
                
                page.add(main_column)
                page.update()
                debug_log("主界面加载完成")
                
            except Exception as e:
                debug_log(f"加载主界面时出错: {str(e)}")
                # 显示错误页面
                page.controls.clear()
                page.add(
                    ft.Column([
                        ft.Text("❌ 加载失败", size=24, color=ft.colors.RED),
                        ft.Text(f"错误: {str(e)[:100]}", size=12),
                        ft.ElevatedButton("重试", on_click=lambda e: main(page))
                    ], alignment=ft.MainAxisAlignment.CENTER)
                )
                page.update()
        
        # 在新线程中加载主界面
        threading.Thread(target=load_main_interface, daemon=True).start()
        
    except Exception as e:
        debug_log(f"主函数出错: {str(e)}")
        # 最后的保底 - 显示简单界面
        try:
            page.controls.clear()
            page.add(
                ft.Column([
                    ft.Text("DRM下载器", size=24),
                    ft.Text("应用已启动", size=16),
                    ft.Text(f"错误: {str(e)[:50]}", size=12, color=ft.colors.RED)
                ])
            )
            page.update()
        except:
            pass

# 应用启动
if __name__ == "__main__":
    try:
        debug_log("========== 启动应用 ==========")
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            assets_dir="assets"
        )
    except Exception as e:
        debug_log(f"启动失败: {str(e)}")
