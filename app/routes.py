import os
import shutil
from flask import Blueprint, request, redirect, url_for, render_template, send_from_directory, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .utils import get_safe_absolute_path # 从 utils.py 导入

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/files/') # 添加一个明确的 /files/ 路径
@bp.route('/files/<path:path>')
@login_required
def manage_files(path=""):
    try:
        current_dir_normalized = path.strip('/\\')
        current_full_path = get_safe_absolute_path(current_dir_normalized)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for('main.manage_files'))

    if not os.path.isdir(current_full_path):
        flash(f"路径 '{current_dir_normalized}' 不是一个有效的目录。", "error")
        return redirect(url_for('main.manage_files'))

    items_list = []
    try:
        for item_name in os.listdir(current_full_path):
            item_full_path = os.path.join(current_full_path, item_name)
            item_relative_path = os.path.relpath(item_full_path, current_app.config['UPLOAD_FOLDER'])
            items_list.append({
                'name': item_name,
                'path': item_relative_path.replace(os.sep, '/'),
                'is_dir': os.path.isdir(item_full_path)
            })
    except OSError as e:
        flash(f"无法读取目录 '{current_dir_normalized}': {e}", "error")
        return redirect(url_for('main.manage_files'))
    
    items_list.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

    parent_dir = ""
    if current_dir_normalized:
        parent_dir = os.path.dirname(current_dir_normalized).replace(os.sep, '/')
    
    current_dir_display = current_dir_normalized if current_dir_normalized else "根目录"
    parent_dir_display = os.path.basename(parent_dir) if parent_dir else "根目录"
    if current_dir_normalized and not parent_dir:
        parent_dir_display = "根目录"

    return render_template('file_manager.html', 
                           items=items_list, 
                           current_dir_normalized=current_dir_normalized,
                           current_dir_display=current_dir_display,
                           parent_dir=parent_dir,
                           parent_dir_display=parent_dir_display,
                           title="文件管理器")

@bp.route('/upload/', defaults={'current_path_segment': ''}, methods=['POST'])
@bp.route('/upload/<path:current_path_segment>', methods=['POST'])
@login_required
def upload_file(current_path_segment):
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
        filename = secure_filename(file.filename)
        if not filename:
            flash('无效的文件名。', 'error')
            return redirect(redirect_url)
        try:
            upload_destination_folder = get_safe_absolute_path(current_path_segment)
            if not os.path.isdir(upload_destination_folder):
                 flash(f"目标目录 '{current_path_segment}' 不存在。", "error")
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
    item_path_normalized = item_path.strip('/\\')
    parent_dir_of_item = os.path.dirname(item_path_normalized).replace(os.sep, '/')
    redirect_url = url_for('main.manage_files', path=parent_dir_of_item)

    try:
        full_item_path = get_safe_absolute_path(item_path_normalized)
        item_name = os.path.basename(item_path_normalized)

        if not os.path.exists(full_item_path):
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
            
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for('main.manage_files'))
    except OSError as e:
        flash(f"删除 '{item_name}' 时出错: {e}", "error")
    
    return redirect(redirect_url)

@bp.route('/download/<path:file_path>')
@login_required
def download_file_route(file_path):
    file_path_normalized = file_path.strip('/\\')
    parent_dir_of_item = os.path.dirname(file_path_normalized).replace(os.sep, '/')
    
    try:
        abs_file_path_to_check = get_safe_absolute_path(file_path_normalized)
        
        if not os.path.isfile(abs_file_path_to_check):
            flash("请求的文件不存在或不是一个文件。", "error")
            return redirect(url_for('main.manage_files', path=parent_dir_of_item))

        return send_from_directory(current_app.config['UPLOAD_FOLDER'], 
                                   file_path_normalized, 
                                   as_attachment=True)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for('main.manage_files'))
    except Exception as e:
        flash(f"下载文件时出错: {e}", "error")
        return redirect(url_for('main.manage_files', path=parent_dir_of_item))

