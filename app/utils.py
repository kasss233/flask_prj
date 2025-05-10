import os
from flask import current_app # 用于访问 app.config
from flask_login import current_user

def get_user_base_upload_path():
    """获取当前认证用户的专属上传根目录，如果不存在则创建它。"""
    if not current_user.is_authenticated:
        # 这个异常理论上不应该被未认证用户触发，因为路由有 @login_required
        raise ValueError("用户未认证，无法获取用户专属目录。")
    
    # 使用用户ID作为子目录名，确保唯一性
    user_specific_folder_name = str(current_user.id)
    user_base_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user_specific_folder_name)
    
    if not os.path.exists(user_base_path):
        try:
            os.makedirs(user_base_path)
        except OSError as e:
            # 更具体的错误处理或日志记录
            current_app.logger.error(f"无法创建用户目录 {user_base_path}: {e}")
            raise ValueError(f"无法创建用户专属目录: {e}")
    return os.path.abspath(user_base_path)

def get_safe_absolute_path(relative_path=""):
    """
    安全地将用户专属的上传根目录与提供的相对路径连接起来。
    防止路径遍历攻击。
    """
    try:
        base_path = get_user_base_upload_path()
    except ValueError as e: # 来自 get_user_base_upload_path 的错误
        raise # 重新抛出，让调用者处理

    cleaned_relative_path = relative_path.lstrip('/\\')
    
    # 进一步清理，防止相对路径中包含 ".." 等导致跳出用户目录
    # os.path.normpath 会处理一些情况，但额外的检查可能需要
    # 例如，确保 cleaned_relative_path 在拼接和规范化后仍在 base_path 内
    # cleaned_relative_path = os.path.normpath("/" + cleaned_relative_path).lstrip("/") # 确保是纯粹的相对路径

    target_path = os.path.normpath(os.path.join(base_path, cleaned_relative_path))
    
    # 关键安全检查：确保最终路径在用户专属的根目录之下
    if not target_path.startswith(base_path):
        raise ValueError("试图进行路径遍历或访问受限区域")
    return target_path
