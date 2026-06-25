# 香港留学课程检索系统 - 部署指南

## 方式一：CloudStudio 静态版（已部署）

公网访问地址：**https://9e30d306f6d2474c8cb7d5b3094ab36d.app.codebuddy.work**

- 任何设备浏览器打开即用
- 数据存储在浏览器 localStorage 中（每个设备独立）
- 无需服务器，无需安装

---

## 方式二：Flask 版（共享数据库，推荐多设备使用）

部署到云平台后，所有设备共享同一个数据库，课程信息一处修改处处生效。

### Railway 部署（免费）

1. 注册 [Railway](https://railway.app/)
2. 安装 Railway CLI 或连接 GitHub
3. 将此项目上传到 GitHub
4. 在 Railway 中新建项目 → Deploy from GitHub repo
5. Railway 自动检测 Python 项目并部署

### Render 部署（免费）

1. 注册 [Render](https://render.com/)
2. Dashboard → New → Web Service
3. 连接 GitHub 仓库
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python app.py`
6. 点击 Create Web Service

### PythonAnywhere 部署（免费，需要手动设置）

1. 注册 [PythonAnywhere](https://www.pythonanywhere.com/)
2. 上传项目文件到 /home/yourname/hk-course-finder/
3. 打开 Web 标签 → Add a new web app → Flask
4. 设置 Source code 路径指向项目目录
5. 在 WSGI 配置文件中设置 app

### Docker 部署

```bash
# 构建镜像
docker build -t hk-course-finder .

# 运行容器
docker run -d -p 5000:5000 -v $(pwd)/data:/app/data --name hkcf hk-course-finder
```

---

## 数据说明

- 数据库文件：`database.db`（SQLite）
- 部署时请确保该文件可写入
- 建议定期备份 `database.db`
