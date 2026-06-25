---
name: hk-course-finder
description: 香港留学课程检索系统。纯前端单文件应用，用于快速检索、筛选、管理香港高校的留学课程信息。支持学校名录管理（18所香港高校）、课程多维度筛选（11个维度）、课程详情查看、以及完整的增删改查与审计日志。数据通过浏览器 localStorage 持久化存储。适用于留学咨询顾问为客户匹配合适的香港留学课程。
---

# 香港留学课程检索系统 (HK Course Finder)

## 功能概述

纯前端单文件应用，数据存储在浏览器 localStorage，无需服务器，开箱即用。

## 使用方式

### 方式一：Render 共享数据库版（推荐）✨
公网访问，多设备数据同步：
```
https://hk-course-finder.onrender.com
```
- Flask + SQLite 后端，多设备共享同一数据库
- 办公室添加课程，外面手机也能看到
- 所有数据持久化保存在服务器
- ⚠️ 首次访问可能需等待几秒唤醒（免费版休眠机制）

### 方式二：CloudStudio 静态版（备用）
纯前端，每设备数据独立：
```
https://9e30d306f6d2474c8cb7d5b3094ab36d.app.codebuddy.work/hk-course-finder.html
```
- 无需服务器，双击文件即可打开
- 数据存储在浏览器 localStorage

### 方式三：本地运行
```bash
cd /Users/allenlautik/WorkBuddy/2026-06-25-21-17-17/hk-course-finder && /Users/allenlautik/.workbuddy/binaries/python/envs/hk-course-finder/bin/python app.py
```

## 三个功能面板

### 1. 学校名录
- 18所香港高校预设数据
- 支持添加、编辑、删除学校
- 显示课程数量统计（授课式/研究式）
- 修改自动记录审计日志

### 2. 课程检索
- **11个筛选维度**：课程编号 / 学校名称（下拉） / 学科分类（下拉） / 授课方式（下拉） / 课程名称（关键词） / 学制（下拉） / 学年（下拉） / 身份（下拉） / 学费范围 / 截止日期排序
- 点击课程名称查看完整详情
- 支持添加、编辑、删除课程

### 3. 操作日志
- 所有增删改操作自动记录
- 包含修改内容、日期、时间
- 按表名筛选（学校/课程）

## 技术架构

- **后端**：Flask + SQLite（gunicorn 部署）
- **前端**：HTML + CSS + JavaScript
- **部署**：Render.com（免费，自动从 GitHub 部署）
- **数据库**：SQLite（courses / schools / audit_log 三张表）
