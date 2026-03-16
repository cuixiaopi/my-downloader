# android_permissions.py
import os
from pathlib import Path

def request_storage_permission():
    """请求存储权限"""
    try:
        from android.permissions import Permission, request_permission, check_permission
        
        permissions = [
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
        ]
        
        granted = []
        for perm in permissions:
            if check_permission(perm):
                granted.append(perm)
            else:
                if request_permission(perm):
                    granted.append(perm)
        
        return len(granted) == len(permissions)
    except ImportError:
        # 非 Android 环境
        return True
    except Exception as e:
        print(f"权限请求失败: {e}")
        return False

def get_download_path():
    """获取下载路径"""
    try:
        # Android 路径
        paths = [
            "/storage/emulated/0/Download",
            "/sdcard/Download",
            str(Path.home() / "Download"),
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        # 创建下载目录
        download_path = "/storage/emulated/0/Download"
        os.makedirs(download_path, exist_ok=True)
        return download_path
        
    except Exception:
        # 回退到当前目录
        return os.getcwd()

def check_android_permissions():
    """检查 Android 权限"""
    try:
        from android import mActivity
        from android.permissions import Permission, check_permission
        
        # 检查必要的权限
        needed_perms = [
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
        ]
        
        missing_perms = []
        for perm in needed_perms:
            if not check_permission(perm):
                missing_perms.append(perm)
        
        return missing_perms
    except ImportError:
        return []  # 非 Android 环境
