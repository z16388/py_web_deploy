#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import web
import os
import json
import logging
import urllib.parse
from datetime import datetime

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DEPLOY_ROOT   = os.path.join(BASE_DIR, 'deploy')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
CONFIG_DIR    = os.path.join(BASE_DIR, 'config')
PASSWORDS_FILE = os.path.join(CONFIG_DIR, 'dir_passwords.json')

SUPPORTED_EXTS = ('.apk', '.aab', '.obb', '.ipa')
MIME_TYPES = {
    '.apk': 'application/vnd.android.package-archive',
    '.aab': 'application/octet-stream',
    '.obb': 'application/octet-stream',
    '.ipa': 'application/octet-stream',
}

web.config.debug = False  # 禁用 autoreload，防止模块被加载两次导致 Session 错误

urls = (
    '/',                       'dir_index',
    '/files/([^/]+)',          'file_list',
    '/auth/([^/]+)',           'dir_auth',
    '/download/([^/]+)/(.+)', 'file_download',
)

app    = web.application(urls, globals())
store  = web.session.DiskStore(os.path.join(BASE_DIR, 'sessions'))
session = web.session.Session(app, store, initializer={'unlocked': []})

render = web.template.render(TEMPLATES_DIR, base='layout')

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# 目录密码
# ──────────────────────────────────────────────────────────────

def load_passwords():
    """读取目录密码配置。格式：{"目录名": "密码"}，值为空串表示公开。"""
    if not os.path.exists(PASSWORDS_FILE):
        return {}
    with open(PASSWORDS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def dir_password(dirname):
    """返回目录密码，空字符串表示无需密码。"""
    return load_passwords().get(dirname, '')


def is_unlocked(dirname):
    """检查当前会话是否已解锁该目录。无密码目录始终返回 True。"""
    pwd = dir_password(dirname)
    if not pwd:
        return True
    unlocked = session.get('unlocked') or []
    return dirname in unlocked


# ──────────────────────────────────────────────────────────────
# 文件扫描
# ──────────────────────────────────────────────────────────────

def scan_dirs(deploy_root):
    if not os.path.isdir(deploy_root):
        return []
    passwords = load_passwords()
    dirs = []
    for name in sorted(os.listdir(deploy_root)):
        full = os.path.join(deploy_root, name)
        if not os.path.isdir(full):
            continue
        try:
            # 递归统计所有子目录中的文件
            count = 0
            for root, _, files in os.walk(full):
                for fn in files:
                    if fn.lower().endswith(SUPPORTED_EXTS):
                        count += 1
        except Exception as e:
            logger.warning(f'无法扫描目录 {name}: {e}')
            count = 0
        dirs.append(web.storage(
            name=name,
            url_name=urllib.parse.quote(name, safe=''),
            count=count,
            locked=bool(passwords.get(name))
        ))
    return dirs


def build_file_tree(directory):
    """构建文件树结构"""
    tree = {'dirs': {}, 'files': []}
    
    if not os.path.isdir(directory):
        return tree
    
    # 收集所有文件
    all_files = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(SUPPORTED_EXTS):
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, directory)
                all_files.append((rel_path, file_path))
    
    # 按修改时间排序
    all_files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
    
    # 构建树状结构
    for rel_path, file_path in all_files:
        parts = rel_path.split(os.sep)
        file_name = parts[-1]
        ext = os.path.splitext(file_name)[1].lower()
        
        file_info = web.storage(
            name=file_name,
            rel_path=rel_path,
            url_path=urllib.parse.quote(rel_path.replace(os.sep, '/'), safe=''),
            size=_format_size(os.path.getsize(file_path)),
            mtime=datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M'),
            ext=ext,
            full_path=file_path,
        )
        
        # 如果在根目录
        if len(parts) == 1:
            tree['files'].append(file_info)
        else:
            # 在子目录中
            current = tree
            for i, part in enumerate(parts[:-1]):
                if part not in current['dirs']:
                    current['dirs'][part] = {'dirs': {}, 'files': [], 'name': part}
                current = current['dirs'][part]
            current['files'].append(file_info)
    
    return tree


def flatten_tree_for_display(tree, indent=0, file_index=[0]):
    """将树结构扁平化为显示列表"""
    result = []
    
    # 先添加当前层级的文件
    if tree.get('files'):
        for f in tree['files']:
            item = web.storage(
                type='file',
                data=f,
                indent=indent,
                is_newest=(file_index[0] == 0)
            )
            result.append(item)
            file_index[0] += 1
    
    # 再递归处理子目录（逆序排列）
    if tree.get('dirs'):
        for dir_name in sorted(tree['dirs'].keys(), reverse=True):
            # 添加文件夹标题
            result.append(web.storage(
                type='folder',
                name=dir_name,
                indent=indent
            ))
            # 递归添加子目录内容
            subtree = tree['dirs'][dir_name]
            result.extend(flatten_tree_for_display(subtree, indent + 1, file_index))
    
    return result


def scan_files(directory):
    """扫描文件并返回扁平化的显示列表"""
    tree = build_file_tree(directory)
    return flatten_tree_for_display(tree)


def _format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return '{:.1f} {}'.format(size, unit)
        size /= 1024.0
    return '{:.1f} TB'.format(size)


def download_file(file_name, file_path):
    ext      = os.path.splitext(file_name)[1].lower()
    mime     = MIME_TYPES.get(ext, 'application/octet-stream')
    BUF_SIZE = 1024 * 1024
    try:
        web.header('Content-Type', mime)
        web.header('Content-Length', os.path.getsize(file_path))
        web.header('Content-Disposition', 'attachment; filename="{}"'.format(file_name))
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(BUF_SIZE)
                if chunk:
                    yield chunk
                else:
                    break
    except Exception as e:
        logger.error('下载出错: %s', e)
        yield b'Error reading file'


# ──────────────────────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────────────────────

class dir_index:
    def GET(self):
        dirs = scan_dirs(DEPLOY_ROOT)
        return render.dir_index(dirs)


class file_list:
    def GET(self, dirname):
        safe_dir = os.path.basename(dirname)
        if not is_unlocked(safe_dir):
            raise web.seeother('/auth/' + urllib.parse.quote(safe_dir, safe=''))
        dir_path  = os.path.join(DEPLOY_ROOT, safe_dir)
        real_path = os.path.realpath(dir_path)
        if not real_path.startswith(os.path.realpath(DEPLOY_ROOT)):
            raise web.forbidden()
        files = scan_files(dir_path)
        return render.file_list(safe_dir, files)


class dir_auth:
    def GET(self, dirname):
        safe_dir = os.path.basename(dirname)
        if is_unlocked(safe_dir):
            raise web.seeother('/files/' + urllib.parse.quote(safe_dir, safe=''))
        return render.dir_auth(safe_dir, '')

    def POST(self, dirname):
        safe_dir = os.path.basename(dirname)
        password = web.input(password='').password
        correct  = dir_password(safe_dir)
        if correct and password == correct:
            unlocked = list(session.get('unlocked') or [])
            if safe_dir not in unlocked:
                unlocked.append(safe_dir)
            session.unlocked = unlocked
            raise web.seeother('/files/' + urllib.parse.quote(safe_dir, safe=''))
        return render.dir_auth(safe_dir, '密码错误，请重试')


class file_download:
    def GET(self, dirname, filename):
        safe_dir = os.path.basename(dirname)
        if not is_unlocked(safe_dir):
            raise web.seeother('/auth/' + urllib.parse.quote(safe_dir, safe=''))
        
        # 将URL路径转换回系统路径（处理/和\的差异）
        file_rel_path = urllib.parse.unquote(filename).replace('/', os.sep)
        
        # 安全检查：确保不包含路径遍历攻击（如 ../）
        if '..' in file_rel_path or file_rel_path.startswith(os.sep):
            raise web.forbidden()
        
        # 检查文件扩展名
        if not file_rel_path.lower().endswith(SUPPORTED_EXTS):
            raise web.forbidden()
        
        dir_path = os.path.join(DEPLOY_ROOT, safe_dir)
        file_path = os.path.join(dir_path, file_rel_path)
        
        # 安全检查：确保最终路径在部署根目录下
        real_file = os.path.realpath(file_path)
        real_root = os.path.realpath(DEPLOY_ROOT)
        if not real_file.startswith(real_root + os.sep):
            raise web.forbidden()
        
        if not os.path.isfile(file_path):
            raise web.notfound()
        
        # 下载时使用原始文件名（不包含路径）
        download_name = os.path.basename(file_rel_path)
        return download_file(download_name, file_path)


if __name__ == '__main__':
    os.makedirs(os.path.join(DEPLOY_ROOT, 'android'), exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'sessions'), exist_ok=True)
    if not os.path.exists(PASSWORDS_FILE):
        with open(PASSWORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
        logger.info('已创建 config/dir_passwords.json，所有目录默认公开访问')
    app.run()
