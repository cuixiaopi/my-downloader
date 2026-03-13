import flet as ft
import os
import shutil
import stat
import subprocess
import threading
import traceback
import sys

def main(page: ft.Page):
    # 1. 基础配置
    page.title = "DRM 诊断版"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    
    # 2. 准备一个大号的错误显示框
    error_text = ft.Text(color="red", weight="bold", selectable=True)
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=10, text_size=12)
    
    def show_crash(err):
        """强行在屏幕上显示错误"""
        log_box.value = f"💥 发生致命错误！\n\n{err}"
        error_text.value = "程序已崩溃，请截图发给 AI 进行分析 👇"
        page.update()

    # 3. 核心业务逻辑包装在 Try 里
    try:
        url_input = ft.TextField(label="MPD 链接", border_radius=10)
        key_input = ft.TextField(label="32位 Key", border_radius=10)
        pb = ft.ProgressBar(visible=False)

        def logger(msg):
            log_box.value += f"{msg}\n"
            page.update()

        def run_task(e):
            def process():
                try:
                    # 路径检测
                    data_dir = os.environ.get("FLET_APP_DATA", os.getcwd())
                    ffmpeg_bin = os.path.join(data_dir, "ffmpeg")
                    
                    if not os.path.exists(ffmpeg_bin):
                        logger("正在从 Assets 部署引擎...")
                        src = os.path.join(os.path.dirname(__file__), "assets", "ffmpeg")
                        if os.path.exists(src):
                            shutil.copy(src, ffmpeg_bin)
                            os.chmod(ffmpeg_bin, os.stat(ffmpeg_bin).st_mode | stat.S_IEXEC)
                            logger("✅ 引擎就绪")
                        else:
                            logger("❌ 找不到 assets/ffmpeg 文件！")
                            return

                    logger("🚀 启动 FFmpeg...")
                    # 执行最简单的版本检测，看引擎能不能动
                    res = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True)
                    logger(f"检测结果: {res.stdout[:50]}...")
                    
                except Exception as ex:
                    logger(f"🔥 运行时出错: {traceback.format_exc()}")
            
            threading.Thread(target=process, daemon=True).start()

        btn = ft.ElevatedButton("验证环境", on_click=run_task)
        
        # 页面装载
        page.add(
            ft.Column([
                ft.Text("DRM 下载器 - 诊断模式", size=20, weight="bold"),
                error_text,
                url_input,
                key_input,
                btn,
                pb,
                log_box
            ])
        )
        logger("系统启动成功，等待操作...")

    except Exception:
        # 捕获 UI 初始化阶段的错误
        show_crash(traceback.format_exc())

# 启动全方位保护
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception:
        # 最后的防线：如果 ft.app 都起不来
        print(traceback.format_exc())
