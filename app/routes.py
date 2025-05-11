import os
import shutil
from flask import Blueprint, request, redirect, url_for, render_template, send_from_directory, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .utils import get_safe_absolute_path, get_user_base_upload_path # 从 utils.py 导入
from .models import Share, User # 导入 Share 和 User 模型
from . import db # 导入 db 实例

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/files/') # 添加一个明确的 /files/ 路径
@bp.route('/files/<path:path>')
@login_required
def manage_files(path=""):
    try:
        # path 现在是相对于用户目录的路径
        current_dir_normalized = path.strip('/\\')
        # get_safe_absolute_path 内部会使用 current_user.id 来构建基础路径
        current_full_path = get_safe_absolute_path(current_dir_normalized)
        user_base_dir = get_user_base_upload_path() # 获取用户专属根目录
    except ValueError as e:
        flash(str(e), "error")
        # 如果是用户目录创建失败等，可能需要重定向到错误页或登出
        return redirect(url_for('main.manage_files')) # 重定向到用户根目录

    if not os.path.isdir(current_full_path):
        flash(f"路径 '{current_dir_normalized}' 不是一个有效的目录。", "error")
        return redirect(url_for('main.manage_files'))

    items_list = []
    try:
        for item_name in os.listdir(current_full_path):
            item_full_path = os.path.join(current_full_path, item_name)
            # item_relative_path 现在是相对于用户专属根目录的路径
            item_relative_path_to_user_dir = os.path.relpath(item_full_path, user_base_dir)
            items_list.append({
                'name': item_name,
                'path': item_relative_path_to_user_dir.replace(os.sep, '/'),
                'is_dir': os.path.isdir(item_full_path)
            })
    except OSError as e:
        flash(f"无法读取目录 '{current_dir_normalized}': {e}", "error")
        return redirect(url_for('main.manage_files'))
    
    items_list.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

    parent_dir = ""
    if current_dir_normalized: # current_dir_normalized 是相对于用户目录的
        parent_dir = os.path.dirname(current_dir_normalized).replace(os.sep, '/')
    
    current_dir_display = current_dir_normalized if current_dir_normalized else "根目录" # 用户个人空间的根目录
    parent_dir_display = os.path.basename(parent_dir) if parent_dir else "根目录"
    if current_dir_normalized and not parent_dir: # 如果在用户根目录的子目录，但父目录是用户根目录
        parent_dir_display = "根目录"

    return render_template('file_manager.html', 
                           items=items_list, 
                           current_dir_normalized=current_dir_normalized, # 相对于用户目录
                           current_dir_display=current_dir_display,
                           parent_dir=parent_dir, # 相对于用户目录
                           parent_dir_display=parent_dir_display,
                           title="文件管理器")

@bp.route('/upload/', defaults={'current_path_segment': ''}, methods=['POST'])
@bp.route('/upload/<path:current_path_segment>', methods=['POST'])
@login_required
def upload_file(current_path_segment):
    # current_path_segment 是相对于用户目录的路径
    current_path_segment = current_path_segment.strip('/\\')
    redirect_url = url_for('main.manage_files', path=current_path_segment)

    if 'file' not in request.files:
        flash('没有文件部分', 'error')
        return redirect(redirect_url)
    
    file = request.files['file']
    if file.filename == '':
        flash('未选择文件', 'error')
        return redirect(redirect_url)

    if file:
        filename = file.filename
        if not filename:
            flash('无效的文件名。', 'error')
            return redirect(redirect_url)
        try:
            # get_safe_absolute_path 会处理用户特定的路径
            upload_destination_folder = get_safe_absolute_path(current_path_segment)
            if not os.path.isdir(upload_destination_folder):
                 flash(f"目标目录 '{current_path_segment}' 不存在。", "error")
                 # 此处应重定向到用户根目录，因为 current_path_segment 可能无效
                 return redirect(url_for('main.manage_files'))

            file_save_path = os.path.join(upload_destination_folder, filename)
            if os.path.exists(file_save_path):
                flash(f"文件 '{filename}' 已存在。请重命名或删除现有文件。", "error")
            else:
                file.save(file_save_path)
                flash(f"文件 '{filename}' 上传成功。", "success")
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"上传文件时出错: {e}", "error")
    else:
        flash('文件上传失败。', 'error')
        
    return redirect(redirect_url)

@bp.route('/create_folder/', defaults={'current_path_segment': ''}, methods=['POST'])
@bp.route('/create_folder/<path:current_path_segment>', methods=['POST'])
@login_required
def create_folder_route(current_path_segment):
    # current_path_segment 是相对于用户目录的路径
    current_path_segment = current_path_segment.strip('/\\')
    redirect_url = url_for('main.manage_files', path=current_path_segment)

    folder_name = request.form.get('folder_name')
    if not folder_name:
        flash("文件夹名称不能为空。", "error")
        return redirect(redirect_url)

    safe_folder_name = secure_filename(folder_name)
    if not safe_folder_name or safe_folder_name in [".", ".."]:
        flash("无效的文件夹名称。", "error")
        return redirect(redirect_url)
        
    try:
        # get_safe_absolute_path 会处理用户特定的路径
        target_folder_base = get_safe_absolute_path(current_path_segment)
        if not os.path.isdir(target_folder_base):
            flash(f"目标目录 '{current_path_segment}' 不存在。", "error")
            return redirect(url_for('main.manage_files'))

        new_folder_path = os.path.join(target_folder_base, safe_folder_name)
        
        if os.path.exists(new_folder_path):
            flash(f"文件夹 '{safe_folder_name}' 已存在。", "error")
        else:
            os.makedirs(new_folder_path)
            flash(f"文件夹 '{safe_folder_name}' 创建成功。", "success")
    except ValueError as e:
        flash(str(e), "error")
    except OSError as e:
        flash(f"创建文件夹时出错: {e}", "error")
        
    return redirect(redirect_url)

@bp.route('/delete/<path:item_path>', methods=['GET']) # 保持 GET 为简单起见
@login_required
def delete_item(item_path):
    # item_path 是相对于用户目录的路径
    item_path_normalized = item_path.strip('/\\')
    parent_dir_of_item = os.path.dirname(item_path_normalized).replace(os.sep, '/')
    redirect_url = url_for('main.manage_files', path=parent_dir_of_item)

    try:
        # get_safe_absolute_path 会处理用户特定的路径
        full_item_path = get_safe_absolute_path(item_path_normalized)
        # item_name 从 item_path_normalized 获取，因为它是相对路径中的最后一节
        item_name = os.path.basename(item_path_normalized)

        if not os.path.exists(full_item_path): # full_item_path 已经是绝对安全的路径
            flash(f"项目 '{item_name}' 未找到。", "error")
            return redirect(redirect_url)

        if os.path.isfile(full_item_path):
            os.remove(full_item_path)
            flash(f"文件 '{item_name}' 删除成功。", "success")
        elif os.path.isdir(full_item_path):
            shutil.rmtree(full_item_path)
            flash(f"文件夹 '{item_name}' 及其内容删除成功。", "success")
        else:
            flash(f"'{item_name}' 不是有效的文件或目录。", "error") 
            
    except ValueError as e: # 来自 get_safe_absolute_path 的错误
        flash(str(e), "error")
        return redirect(url_for('main.manage_files')) # 重定向到用户根目录
    except OSError as e:
        flash(f"删除 '{item_name}' 时出错: {e}", "error")
    
    return redirect(redirect_url)

@bp.route('/download/<path:file_path>')
@login_required
def download_file_route(file_path):
    # file_path 是相对于用户目录的路径
    file_path_normalized = file_path.strip('/\\')
    parent_dir_of_item = os.path.dirname(file_path_normalized).replace(os.sep, '/')
    
    try:
        # 检查文件是否存在于用户目录中
        abs_file_path_to_check = get_safe_absolute_path(file_path_normalized)
        
        if not os.path.isfile(abs_file_path_to_check):
            flash("请求的文件不存在或不是一个文件。", "error")
            return redirect(url_for('main.manage_files', path=parent_dir_of_item))

        user_base_upload_dir = get_user_base_upload_path()
        # file_path_normalized 是相对于 user_base_upload_dir 的路径
        return send_from_directory(user_base_upload_dir, 
                                   file_path_normalized, 
                                   as_attachment=True)
    except ValueError as e: # 来自 get_safe_absolute_path 或 get_user_base_upload_path
        flash(str(e), "error")
        return redirect(url_for('main.manage_files'))
    except Exception as e:
        flash(f"下载文件时出错: {e}", "error")
        return redirect(url_for('main.manage_files', path=parent_dir_of_item))

@bp.route('/share_item/<path:item_path>', methods=['POST'])
@login_required
def create_share_link(item_path):
    item_path_normalized = item_path.strip('/\\')
    redirect_path = os.path.dirname(item_path_normalized).replace(os.sep, '/')
    redirect_url = url_for('main.manage_files', path=redirect_path)

    try:
        # 确认项目存在且属于当前用户
        abs_item_path = get_safe_absolute_path(item_path_normalized) # uses current_user.id by default
        
        if not os.path.exists(abs_item_path):
            flash("要分享的项目不存在。", "error")
            return redirect(redirect_url)

        is_file = os.path.isfile(abs_item_path)
        
        # 检查是否已为此项目创建过分享链接 (可选，或允许重复分享)
        existing_share = Share.query.filter_by(user_id=current_user.id, item_path=item_path_normalized).first()
        if existing_share:
            share_url = url_for('main.access_shared_item', share_token=existing_share.share_token, _external=True)
            flash(f"此项目已分享。分享链接: {share_url}", "info")
            return redirect(redirect_url)

        token = Share.generate_token()
        new_share = Share(
            user_id=current_user.id,
            item_path=item_path_normalized,
            share_token=token,
            is_file=is_file
        )
        db.session.add(new_share)
        db.session.commit()

        share_url = url_for('main.access_shared_item', share_token=token, _external=True)
        flash(f"分享链接已创建: {share_url}", "success")
        # Consider using a clipboard copy functionality on the frontend
        current_app.logger.info(f"User {current_user.id} shared item {item_path_normalized} with token {token}")

    except ValueError as e: # From get_safe_absolute_path
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash(f"创建分享链接时出错: {e}", "error")
        current_app.logger.error(f"Error creating share link for {item_path} by user {current_user.id}: {e}")
        
    return redirect(redirect_url)

@bp.route('/shared/<share_token>')
@bp.route('/shared/<share_token>/<path:sub_path>')
def access_shared_item(share_token, sub_path=""):
    share_record = Share.query.filter_by(share_token=share_token).first()

    if not share_record:
        flash("分享链接无效或已过期。", "error")
        return redirect(url_for('main.manage_files' if current_user.is_authenticated else 'auth.login'))

    owner_id = share_record.user_id
    # item_path_in_share is the root of the share, relative to owner's space
    item_path_in_share = share_record.item_path 
    
    # current_relative_path is sub_path within the shared item_path_in_share
    current_relative_path_within_share = sub_path.strip('/\\')

    # full_relative_path_to_owner_root is the path from the owner's root
    full_relative_path_to_owner_root = os.path.join(item_path_in_share, current_relative_path_within_share).replace(os.sep, '/')
    
    try:
        # Get owner's base upload directory
        owner_base_dir = get_user_base_upload_path(user_id_to_use=owner_id)
        # Get the absolute path of the item to be accessed (file or directory)
        # This uses the full path relative to the owner's root.
        abs_item_path = get_safe_absolute_path(full_relative_path_to_owner_root, user_id_to_use=owner_id)

        if not os.path.exists(abs_item_path):
            flash("分享的项目中的指定路径不存在。", "error")
            return redirect(url_for('main.manage_files' if current_user.is_authenticated else 'auth.login'))

        # If the original share was a file, sub_path should typically be empty or not used for navigation
        if share_record.is_file:
            if sub_path: # Trying to access a sub_path of a shared file doesn't make sense
                flash("无效的分享访问。", "error")
                return redirect(url_for('main.manage_files' if current_user.is_authenticated else 'auth.login'))
            # Send the file for download
            # send_from_directory needs path relative to its first argument (owner_base_dir)
            return send_from_directory(owner_base_dir, item_path_in_share, as_attachment=True)
        
        # If it's a shared directory
        else:
            # If a download is requested for a file within the shared directory
            if request.args.get('download') == 'true' and os.path.isfile(abs_item_path):
                # full_relative_path_to_owner_root is already the correct path relative to owner_base_dir
                return send_from_directory(owner_base_dir, full_relative_path_to_owner_root, as_attachment=True)
            elif not os.path.isdir(abs_item_path): # Trying to "view" a file as a directory
                flash("分享的项目中的指定路径不是一个目录。", "error")
                return redirect(url_for('main.access_shared_item', share_token=share_token))


            # List directory contents
            items_list = []
            for item_name_in_dir in os.listdir(abs_item_path):
                # item_sub_path_in_share is the path of this item relative to the *root of the share*
                item_sub_path_in_share = os.path.join(current_relative_path_within_share, item_name_in_dir).replace(os.sep, '/')
                
                # full_abs_path_of_item_in_dir is its absolute path on disk
                full_abs_path_of_item_in_dir = os.path.join(abs_item_path, item_name_in_dir)
                
                items_list.append({
                    'name': item_name_in_dir,
                    'path': item_sub_path_in_share, # This path is used for links within the shared view
                    'is_dir': os.path.isdir(full_abs_path_of_item_in_dir)
                })
            items_list.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            shared_item_base_name = os.path.basename(item_path_in_share) if item_path_in_share else "根分享"
            
            current_display_path_in_share = current_relative_path_within_share if current_relative_path_within_share else shared_item_base_name
            
            parent_dir_in_share = None
            parent_dir_display_in_share = None
            if current_relative_path_within_share:
                parent_dir_in_share = os.path.dirname(current_relative_path_within_share).replace(os.sep, '/')
                if parent_dir_in_share == ".": parent_dir_in_share = "" # Top level of share
                parent_dir_display_in_share = os.path.basename(parent_dir_in_share) if parent_dir_in_share else shared_item_base_name

            owner = User.query.get(owner_id)

            return render_template('shared_item_view.html',
                                   items=items_list,
                                   share_token=share_token,
                                   shared_item_name=shared_item_base_name, # The name of the originally shared folder/file
                                   current_dir_normalized=current_relative_path_within_share, # Path relative to shared root
                                   current_dir_display=current_display_path_in_share,
                                   parent_dir=parent_dir_in_share,
                                   parent_dir_display=parent_dir_display_in_share or shared_item_base_name,
                                   owner_username=owner.username if owner else "未知用户",
                                   creation_date=share_record.created_at,
                                   title=f"分享: {shared_item_base_name}")

    except ValueError as e: # From get_safe_absolute_path or get_user_base_upload_path
        flash(str(e), "error")
        current_app.logger.error(f"Error accessing shared item {share_token} (sub_path: {sub_path}): {e}")
        return redirect(url_for('main.manage_files' if current_user.is_authenticated else 'auth.login'))
    except Exception as e:
        flash(f"访问分享内容时发生错误: {e}", "error")
        current_app.logger.error(f"Generic error accessing shared item {share_token} (sub_path: {sub_path}): {e}")
        return redirect(url_for('main.manage_files' if current_user.is_authenticated else 'auth.login'))

@bp.route('/my_shares')
@login_required
def my_shares():
    user_shares = Share.query.filter_by(user_id=current_user.id).order_by(Share.created_at.desc()).all()
    shares_data = []
    for share in user_shares:
        item_name = os.path.basename(share.item_path) if share.item_path else "根目录项"
        # Ensure item_name is set, especially if item_path could be empty or just '/'
        if not item_name and share.item_path == '/': # Or some other logic for root shares
            item_name = "用户根目录"
        elif not item_name: # Default for any other unexpected empty basename
             item_name = "未知项目"

        shares_data.append({
            'token': share.share_token,
            'item_name': item_name,
            'item_path': share.item_path,
            'is_file': share.is_file,
            'created_at': share.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'url': url_for('main.access_shared_item', share_token=share.share_token, _external=True)
        })
    return render_template('my_shares.html', shares=shares_data, title="我的分享")

@bp.route('/delete_share/<share_token>', methods=['POST'])
@login_required
def delete_share(share_token):
    share_to_delete = Share.query.filter_by(share_token=share_token, user_id=current_user.id).first()
    if share_to_delete:
        try:
            db.session.delete(share_to_delete)
            db.session.commit()
            flash("分享链接已成功删除。", "success")
            current_app.logger.info(f"User {current_user.id} deleted share token {share_token}")
        except Exception as e:
            db.session.rollback()
            flash(f"删除分享链接时出错: {e}", "error")
            current_app.logger.error(f"Error deleting share token {share_token} by user {current_user.id}: {e}")
    else:
        flash("未找到要删除的分享链接，或您无权删除它。", "error")
    return redirect(url_for('main.my_shares'))

