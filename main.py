import flet as ft
import os
import shutil
import subprocess
import threading
import traceback
import sys

def main(page: ft.Page):
    page.title = "DRM 视频大师 - 核心修复版"
    page.scroll = ft.ScrollMode.AUTO
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=15, text_size=12)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    def setup_engine():
        # 【核心修正】彻底离开 flet 子目录，前往安卓应用最根部的 files 目录
        # data_dir 通常是 /data/data/包名/files/flet/app
        flet_app_data = os.environ.get("FLET_APP_DATA", os.getcwd())
        
        # 尝试逐级向上寻找真正的 files 根目录
        # 目标：/data/data/com.flet.my_downloader/files/ffmpeg
        base_files_dir = flet_app_data
        for _ in range(2): 
            base_files_dir = os.path.dirname(base_files_dir)
        
        target_ffmpeg = os.path.join(base_files_dir, "ffmpeg")
        
        logger(f"📂 目标引擎路径: {target_ffmpeg}")
        
        try:
            # 1. 定位 Assets 资源
            src_ffmpeg = os.path.join(os.path.dirname(__file__), "assets", "ffmpeg")
            
            # 2. 部署文件
            if os.path.exists(src_ffmpeg):
                shutil.copy(src_ffmpeg, target_ffmpeg)
                # 3. 强制赋予 777 权限
                os.chmod(target_ffmpeg, 0o777)
                
                size_kb = os.path.getsize(target_ffmpeg) / 1024
                logger(f"✅ 引擎部署成功 (大小: {size_kb:.1f} KB)")
            else:
                logger("❌ 致命错误：安装包内找不到 assets/ffmpeg")
                return None
        except Exception as e:
            logger(f"❌ 部署失败: {e}")
            return None
            
        return target_ffmpeg

    def run_logic(e):
        def work():
            engine = setup_engine()
            if not engine: return
            
            try:
                logger("🚀 正在穿透安卓防火墙启动引擎...")
                
                # 【核心方案】使用 sh 代理执行，避开直接调用的权限拦截
                # 这一行命令完成了：设置执行权限 + 运行版本检测
                cmd = f"chmod 777 {engine} && {engine} -version"
                
                process = subprocess.run(
                    ["/system/bin/sh", "-c", cmd],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if "ffmpeg version" in process.stdout:
                    logger(f"🎉 突破成功！引擎已激活：\n{process.stdout[:80]}...")
                    logger("\n[提示] 现在你可以填入链接开始下载了！")
                else:
                    logger(f"⚠️ 启动受限，Stdout: {process.stdout}")
                    logger(f"🛑 报错详情: {process.stderr}")
                    
            except Exception as ex:
                logger(f"💥 运行时崩溃: {traceback.format_exc()}")

        threading.Thread(target=work, daemon=True).start()

    btn = ft.ElevatedButton("验证环境并激活引擎", on_click=run_logic, icon=ft.icons.SHIELD_MOON)
    page.add(ft.Column([
        ft.Text("DRM 下载器 - 权限穿透模式", size=18, weight="bold"),
        btn, 
        log_box
    ]))

ft.app(target=main)
