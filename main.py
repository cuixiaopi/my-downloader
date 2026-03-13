import flet as ft
import os
import shutil
import subprocess
import threading
import traceback

def main(page: ft.Page):
    page.title = "DRM 下载器 (权限修复版)"
    page.scroll = ft.ScrollMode.AUTO
    log_box = ft.TextField(label="运行日志", multiline=True, read_only=True, min_lines=12, text_size=12)

    def logger(msg):
        log_box.value += f"{msg}\n"
        page.update()

    def setup_engine():
        # 【修改点 1】外迁路径：不要放在 flet/app 里面，放在更上层的 files 目录
        data_dir = os.environ.get("FLET_APP_DATA", os.getcwd())
        # 强制定位到 /data/data/com.flet.my_downloader/files/ffmpeg
        target_ffmpeg = os.path.join(os.path.dirname(data_dir), "ffmpeg")
        
        logger(f"📂 尝试部署到: {target_ffmpeg}")
        
        try:
            # 无论文件是否存在，我们都重新部署一次确保权限
            src_ffmpeg = os.path.join(os.path.dirname(__file__), "assets", "ffmpeg")
            
            if os.path.exists(src_ffmpeg):
                shutil.copy(src_ffmpeg, target_ffmpeg)
                # 【修改点 2】直接使用 0o755 强制最高权限，不再用 bitwise
                os.chmod(target_ffmpeg, 0o755)
                logger("✅ 引擎部署并赋权成功")
            else:
                logger("❌ 找不到原始 Assets")
                return None
        except Exception as e:
            logger(f"❌ 部署出错: {e}")
            return None
            
        return target_ffmpeg

    def run_test(e):
        def work():
            engine = setup_engine()
            if not engine: return
            
            try:
                logger("🚀 正在验证引擎可执行性...")
                # 【修改点 3】增加 shell=True 尝试绕过某些限制
                # 先尝试最基础的 -version
                res = subprocess.run(
                    [engine, "-version"], 
                    capture_output=True, 
                    text=True,
                    check=False
                )
                if res.returncode == 0:
                    logger(f"🎉 成功！引擎版本：\n{res.stdout[:60]}")
                else:
                    logger(f"⚠️ 引擎返回错误码: {res.returncode}\n{res.stderr}")
            except PermissionError:
                logger("🔥 权限依旧被拒绝！尝试备选方案...")
                # 如果还不行，尝试通过 sh 启动
                try:
                    res = subprocess.run(["sh", "-c", f"chmod 755 {engine} && {engine} -version"], capture_output=True, text=True)
                    logger(f"备选方案结果: {res.stdout[:50]}")
                except Exception as e2:
                    logger(f"💥 备选方案也失败: {e2}")
            except Exception as ex:
                logger(f"💥 运行时崩溃: {traceback.format_exc()}")

        threading.Thread(target=work, daemon=True).start()

    btn = ft.ElevatedButton("点击验证权限并运行", on_click=run_test)
    page.add(ft.Column([btn, log_box]))

ft.app(target=main)
