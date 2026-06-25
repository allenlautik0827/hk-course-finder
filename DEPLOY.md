# 香港留学课程检索系统 — 公网部署指南

---

## 当前状态

### ✅ 方式一：CloudStudio 静态版（已上线，立即可用）

🔗 **https://9e30d306f6d2474c8cb7d5b3094ab36d.app.codebuddy.work/hk-course-finder.html**

- 任何设备、任何网络均可访问
- 数据存储在浏览器本地，每台设备独立

---

## 🚀 方式二：Flask 共享数据库版（推荐）

部署后所有设备共享同一个数据库，一处修改处处生效。

### 最快路径：Railway（3 分钟，免费）

**第一步：推送代码到 GitHub**

1. 打开 https://github.com/new ，仓库名填 `hk-course-finder`，选 Public
2. 在终端中执行：
   ```bash
   cd /Users/allenlautik/WorkBuddy/2026-06-25-21-17-17/hk-course-finder
   git remote add origin https://github.com/你的用户名/hk-course-finder.git
   git push -u origin main
   ```

**第二步：Railway 自动部署**

3. 打开 https://railway.app/ ，用 GitHub 账号登录
4. 点击「New Project」→「Deploy from GitHub repo」
5. 选择 `hk-course-finder` 仓库
6. Railway 自动检测 Python 项目 → 1 分钟后获得公网 URL ✅

项目已有 `Procfile` 和 `requirements.txt`，Railway 会自动识别。

---

### 备选平台

| 平台 | 说明 |
|------|------|
| [Render](https://render.com/) | 免费，同样支持 GitHub 自动部署 |
| [PythonAnywhere](https://www.pythonanywhere.com/) | 免费，手动上传文件 |
| 自有服务器 | `docker build -t hkcf . && docker run -d -p 5000:5000 hkcf` |

---

## 📦 项目文件说明

| 文件 | 用途 |
|------|------|
| `app.py` | Flask 后端（API + 数据库） |
| `hk-course-finder.html` | 纯前端备用版本 |
| `templates/index.html` | Flask 前端页面 |
| `requirements.txt` | Python 依赖（flask, waitress） |
| `Procfile` | Railway/Render 启动配置 |
| `Dockerfile` | Docker 容器配置 |
| `deploy.sh` | 一键部署辅助脚本 |

---

## ⚠️ 数据备份提醒

SQLite 数据库文件 `database.db` 存储在服务器上。建议定期从 Railway Dashboard 下载备份。
