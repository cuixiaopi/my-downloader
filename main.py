import flet as ft
import time
import sys

# 简单日志
def log(msg):
    print(f"[APP] {msg}", file=sys.stderr, flush=True)

def main(page: ft.Page):
    log("应用启动")
    
    # 基本页面设置
    page.title = "DRM下载大师"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    # 立即显示内容
    page.add(
        ft.Column([
            ft.Text("DRM下载大师", 
                   size=28, 
                   weight=ft.FontWeight.BOLD,
                   color=ft.colors.BLUE_700,
                   text_align=ft.TextAlign.CENTER),
            
            ft.Divider(height=20),
            
            ft.Text("状态: 应用已启动", 
                   size=18, 
                   color=ft.colors.GREEN,
                   text_align=ft.TextAlign.CENTER),
            
            ft.Text("欢迎使用DRM下载工具", 
                   size=16,
                   text_align=ft.TextAlign.CENTER),
            
            ft.Divider(height=20),
            
            ft.TextField(
                label="MPD链接",
                hint_text="输入视频的.mpd文件链接",
                width=350,
                border_color=ft.colors.BLUE_400
            ),
            
            ft.TextField(
                label="解密密钥 (32位)",
                hint_text="输入64个字符的解密密钥",
                width=350,
                password=True,
                border_color=ft.colors.BLUE_400
            ),
            
            ft.Divider(height=20),
            
            ft.ElevatedButton(
                "测试应用",
                icon=ft.icons.PLAY_ARROW,
                on_click=lambda e: on_test_click(page),
                width=200
            ),
            
            ft.Text("提示: 这是一个测试版本", 
                   size=12, 
                   color=ft.colors.GREY_600,
                   text_align=ft.TextAlign.CENTER)
        ], 
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    
    log("UI构建完成")

def on_test_click(page):
    # 更新状态
    page.controls[2].value = "状态: 测试中..."
    page.controls[2].color = ft.colors.ORANGE
    page.update()
    
    time.sleep(1)
    
    page.controls[2].value = "状态: 测试完成 ✓"
    page.controls[2].color = ft.colors.GREEN
    page.update()

# 启动应用
if __name__ == "__main__":
    ft.app(target=main)
