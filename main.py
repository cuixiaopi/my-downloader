import flet as ft
import time

def main(page: ft.Page):
    # 1. 立即设置页面属性
    page.title = "DRM下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.bgcolor = ft.colors.WHITE
    
    # 2. 立即显示加载界面
    page.add(
        ft.Column([
            ft.Text("正在启动...", size=20, color=ft.colors.BLUE),
            ft.ProgressBar(width=300)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    page.update()
    
    # 3. 1秒后显示主界面
    def show_main():
        time.sleep(1)
        
        # 清空页面
        page.controls.clear()
        
        # 添加主界面
        page.add(
            ft.Column([
                # 标题
                ft.Container(
                    content=ft.Column([
                        ft.Text("DRM下载大师", 
                               size=28, 
                               weight=ft.FontWeight.BOLD,
                               color=ft.colors.BLUE_700,
                               text_align=ft.TextAlign.CENTER),
                        ft.Text("Android版 v1.0", 
                               size=12, 
                               color=ft.colors.GREY_600,
                               text_align=ft.TextAlign.CENTER)
                    ]),
                    alignment=ft.alignment.center
                ),
                
                # 分隔线
                ft.Divider(height=20),
                
                # 输入区域
                ft.Text("MPD链接:", size=16, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    hint_text="例如: https://example.com/video.mpd",
                    border_color=ft.colors.BLUE_400,
                    width=350
                ),
                
                ft.Text("32位KEY:", size=16, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    hint_text="64个字符的解密密钥",
                    border_color=ft.colors.BLUE_400,
                    width=350,
                    password=True,
                    can_reveal_password=True
                ),
                
                # 分隔线
                ft.Divider(height=20),
                
                # 按钮
                ft.Container(
                    content=ft.ElevatedButton(
                        "开始下载",
                        icon=ft.icons.DOWNLOAD,
                        on_click=lambda e: on_download_click(page),
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE
                        )
                    ),
                    alignment=ft.alignment.center
                ),
                
                # 状态显示
                ft.Text("就绪", 
                       size=14, 
                       color=ft.colors.GREEN,
                       text_align=ft.TextAlign.CENTER)
            ], 
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()
    
    # 异步显示主界面
    import threading
    threading.Thread(target=show_main, daemon=True).start()

def on_download_click(page):
    # 简单的下载模拟
    page.controls[-1].value = "下载中..."
    page.controls[-1].color = ft.colors.ORANGE
    page.update()
    
    time.sleep(2)
    
    page.controls[-1].value = "下载完成！"
    page.controls[-1].color = ft.colors.GREEN
    page.update()

# 启动应用 - 使用最简配置
if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP
    )
