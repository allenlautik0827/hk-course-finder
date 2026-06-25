#!/bin/bash
# HK Course Finder - Railway 一键部署脚本
# 用法: bash deploy.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "============================================"
echo "  香港留学课程检索系统 - 部署工具"
echo "============================================"
echo ""

# Step 1: Check git
if ! command -v git &> /dev/null; then
  echo "❌ 需要安装 git: https://git-scm.com/downloads"
  exit 1
fi

# Step 2: Initialize git if needed
if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "📦 初始化 git..."
  cd "$PROJECT_DIR" && git init
fi

# Step 3: Commit all files
cd "$PROJECT_DIR"
git add -A
git commit -m "HK Course Finder - Ready for Railway deploy" 2>/dev/null || echo "   (无新变更，跳过 commit)"

# Step 4: Check if gh CLI is available
if command -v gh &> /dev/null; then
  echo "✅ 检测到 GitHub CLI"
  if gh auth status &> /dev/null; then
    # Create repo and push
    echo "📤 创建 GitHub 仓库并推送..."
    gh repo create hk-course-finder --public --source=. --push --remote=origin 2>/dev/null || true
    REPO_URL=$(gh repo view --json url -q .url 2>/dev/null || echo "")
    if [ -n "$REPO_URL" ]; then
      echo "✅ 代码已推送到: $REPO_URL"
    fi
  else
    echo "⚠️  GitHub CLI 未登录，正在打开浏览器..."
    gh auth login --web
    echo "登录后请重新运行此脚本。"
  fi
else
  echo ""
  echo "📋 请手动完成以下步骤："
  echo ""
  echo "  1. 打开 https://github.com/new"
  echo "     仓库名填入: hk-course-finder"
  echo "     选择 Public（公开），点击 Create"
  echo ""
  echo "  2. 在终端中运行以下命令推送代码："
  echo "     cd $PROJECT_DIR"
  echo "     git remote add origin https://github.com/YOUR_USERNAME/hk-course-finder.git"
  echo "     git push -u origin main"
  echo ""
fi

# Step 5: Railway deploy guide
echo ""
echo "============================================"
echo "  🚀 Railway 部署指南"
echo "============================================"
echo ""
echo "  1. 打开 https://railway.app/ 并注册/登录"
echo "  2. 点击 New Project → Deploy from GitHub repo"
echo "  3. 选择 hk-course-finder 仓库"
echo "  4. Railway 自动检测 Python 项目并部署"
echo "  5. 等待 1-2 分钟，获得公网 URL"
echo ""
echo "  系统已预装 18 所香港高校数据"
echo "  所有课程数据保存在 SQLite 数据库"
echo "  多设备共享同一个数据库 ✅"
echo "============================================"
