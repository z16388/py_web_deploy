# py_web_deploy

一个基于 Python 3 + web.py 的轻量级 Web 交付工具，无需 App Store，通过浏览器即可分发 APK / AAB / OBB 安装包文件。

---

## 功能特性

- 📁 **多目录管理**：自动扫描 `deploy/` 下所有子目录，每个目录独立展示
- 📦 **多格式支持**：支持 `.apk`、`.aab`、`.obb` 等格式，按修改时间倒序展示，最新版本自动标注
- 🔒 **目录密码保护**：通过配置文件为指定目录设置访问密码，密码验证通过后会话内持续有效
- 🌙 **夜间模式 UI**：CSS 变量驱动的深色主题，响应式设计，手机端友好
- 🛡️ **路径穿越防护**：所有文件路径经过严格校验，防止目录遍历攻击

---

## 环境要求

- Python 3.8+
- pip

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/z16388/py_web_deploy.git
cd py_web_deploy
```

### 2. 搭建环境

**Linux / macOS：**

```bash
chmod +x setup.sh && ./setup.sh
```

**Windows：**

```bat
setup.bat
```

或手动执行：

```bash
pip install -r requirements.txt
mkdir deploy/android   # Windows: mkdir deploy\android
```

### 3. 放入安装包文件

在 `deploy/` 下创建子目录，将安装包放入对应目录：

```
deploy/
├── android/          # 公开目录
│   ├── myapp-1.0.apk
│   └── myapp-1.1.apk
└── internal/         # 可设置密码保护
    └── myapp-debug.apk
```

### 4. 启动服务

```bash
# Linux / macOS
python3 deploy.py 8888

# Windows
python deploy.py 8888
```

或使用启动脚本（默认端口 8888）：

```bash
./start.sh [端口]     # Linux / macOS
start.bat [端口]      # Windows
```

### 5. 访问下载页面

```
http://<服务器IP>:8888/
```

---

## 目录密码配置

编辑 `config/dir_passwords.json`，为指定目录设置访问密码：

```json
{
  "android": "",
  "internal": "your-password"
}
```

- 值为空字符串或不填 → **公开访问**（无需密码）
- 值为非空字符串 → **需要输入密码**才能进入

> 修改配置文件后**无需重启**服务，下次请求时自动生效。

首次启动若 `dir_passwords.json` 不存在，会自动创建一个空配置（所有目录公开）。

---

## 目录结构

```
py_web_deploy/
├── deploy.py                    # 主程序
├── requirements.txt             # Python 依赖
├── setup.sh / setup.bat         # 环境搭建脚本
├── start.sh / start.bat         # 启动脚本
├── config/
│   └── dir_passwords.json       # 目录密码配置（首次启动自动生成）
├── sessions/                    # Session 存储（自动生成）
├── deploy/
│   └── android/                 # 默认示例目录，存放安装包
└── templates/
    ├── layout.html              # 页面基础布局（夜间主题 CSS）
    ├── dir_index.html           # 目录列表页
    ├── file_list.html           # 文件下载列表页
    └── dir_auth.html            # 目录密码验证页
```

---

## License

[MIT License](LICENSE)
