---
name: hk-course-finder
description: 香港留学课程检索系统。纯前端单文件应用，用于快速检索、筛选、管理香港高校的留学课程信息。支持学校名录管理（18所香港高校）、课程多维度筛选（11个维度）、课程详情查看、以及完整的增删改查与审计日志。数据通过浏览器 localStorage 持久化存储。适用于留学咨询顾问为客户匹配合适的香港留学课程。
---

# 香港留学课程检索系统 (HK Course Finder)

## 功能概述

纯前端单文件应用，数据存储在浏览器 localStorage，无需服务器，开箱即用。

## 使用方式

### 方式一：CloudStudio 公网访问（推荐）
直接浏览器打开：
```
https://9e30d306f6d2474c8cb7d5b3094ab36d.app.codebuddy.work/hk-course-finder.html
```
任何设备、任何网络均可访问，数据存储在浏览器 localStorage。

### 方式二：本地打开
直接打开 `hk-course-finder.html` 即可使用（双击文件在浏览器中打开）。

文件路径：
```
/Users/allenlautik/WorkBuddy/2026-06-25-21-17-17/hk-course-finder/hk-course-finder.html
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

- **纯前端**：HTML + CSS + JavaScript
- **数据存储**：浏览器 localStorage（JSON格式）
- **无依赖**：零外部库，单文件即可运行

## 备选方案

如需后端数据库支持（多用户、大量数据），可使用 Flask 版本：
```bash
cd /Users/allenlautik/WorkBuddy/2026-06-25-21-17-17/hk-course-finder && /Users/allenlautik/.workbuddy/binaries/python/envs/hk-course-finder/bin/python app.py
```
