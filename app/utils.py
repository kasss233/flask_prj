import os
from flask import current_app # 用于访问 app.config

def get_safe_absolute_path(relative_path=""):
    """
    安全地将 UPLOAD_FOLDER 与提供的相对路径连接起来。
    防止路径遍历攻击。
    """
    base_path = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
    cleaned_relative_path = relative_path.lstrip('/\\')
    target_path = os.path.normpath(os.path.join(base_path, cleaned_relative_path))
    
    if not target_path.startswith(base_path):
        raise ValueError("试图进行路径遍历或访问受限区域")
    return target_path
