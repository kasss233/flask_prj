import os
from flask import current_app # 用于访问 app.config
from flask_login import current_user

def get_user_base_upload_path(user_id_to_use=None):
    """
    获取指定用户或当前认证用户的专属上传根目录。
    如果 user_id_to_use 提供，则使用该用户ID。否则，使用 current_user.id。
    """
    actual_user_id = None
    if user_id_to_use:
        actual_user_id = user_id_to_use
    elif current_user.is_authenticated:
        actual_user_id = current_user.id
    else:
        # 对于分享链接的匿名访问，如果 user_id_to_use 未提供，这是一个问题
        raise ValueError("无法确定用户ID以获取专属目录（未提供user_id且用户未认证）。")
    
    # 使用用户ID作为子目录名，确保唯一性
    user_specific_folder_name = str(actual_user_id)
    
    if 'UPLOAD_FOLDER' not in current_app.config or not current_app.config['UPLOAD_FOLDER']:
        current_app.logger.error("UPLOAD_FOLDER 未在应用配置中定义或为空。")
        raise ValueError("应用配置错误：上传目录未设置。")

    user_base_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user_specific_folder_name)
    
    if not os.path.exists(user_base_path):
        try:
            os.makedirs(user_base_path)
            current_app.logger.info(f"为用户 {actual_user_id} 创建目录: {user_base_path}")
        except OSError as e:
            # 更具体的错误处理或日志记录
            current_app.logger.error(f"无法创建用户目录 {user_base_path} (用户ID: {actual_user_id}): {e}")
            raise ValueError(f"无法创建用户专属目录: {e}")
    return os.path.abspath(user_base_path)

def get_safe_absolute_path(relative_path="", user_id_to_use=None):
    """
    安全地将指定用户或当前用户的专属上传根目录与提供的相对路径连接起来。
    防止路径遍历攻击。
    """
    try:
        # Pass user_id_to_use to get_user_base_upload_path
        base_path = get_user_base_upload_path(user_id_to_use=user_id_to_use)
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
        user_info = f"User ID: {user_id_to_use}" if user_id_to_use else f"Current User: {current_user.id if current_user.is_authenticated else 'Anonymous'}"
        current_app.logger.warning(
            f"路径遍历尝试或受限区域访问被阻止。 "
            f"Base: '{base_path}', Target: '{target_path}', Relative: '{relative_path}'. {user_info}"
        )
        raise ValueError("试图进行路径遍历或访问受限区域")
    return target_path
