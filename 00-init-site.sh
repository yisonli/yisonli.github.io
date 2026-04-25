#!/bin/bash
#===============================================================================
# Hugo 博客站点一键初始化脚本
# 适用于: Ubuntu/Linux 环境
# 
# 使用方法:
#   1. 下载 Hugo Extended (>=0.160.1): 
#      wget https://github.com/gohugoio/hugo/releases/download/v0.160.1/hugo_extended_0.160.1_linux-amd64.tar.gz
#   2. 解压并安装: tar -xzf hugo_extended_*.tar.gz && mv hugo /usr/local/bin/
#   3. 运行本脚本: chmod +x 00-init-site.sh && ./00-init-site.sh
#===============================================================================

set -e

HUGO_SITE_DIR="/app/working/workspaces/iZdgLi/yison/hugo-site"
BLOG_MD_DIR="/app/working/workspaces/iZdgLi/yison/blogMD"

echo "=========================================="
echo "  Hugo 博客站点一键初始化"
echo "=========================================="

# 1. 安装 Hugo (如果未安装)
if ! command -v hugo &> /dev/null; then
    echo "[1/8] 安装 Hugo Extended..."
    cd /tmp
    wget -q https://github.com/gohugoio/hugo/releases/download/v0.160.1/hugo_extended_0.160.1_linux-amd64.tar.gz
    tar -xzf hugo_extended_*.tar.gz
    mv hugo /usr/local/bin/
    chmod +x /usr/local/bin/hugo
fi

# 2. 创建站点目录
echo "[2/8] 创建 Hugo 站点..."
cd "$(dirname "$HUGO_SITE_DIR")"
if [ ! -d "$HUGO_SITE_DIR" ]; then
    mkdir -p "$HUGO_SITE_DIR"
    cd "$HUGO_SITE_DIR"
    hugo new site . --force
fi

# 3. 安装主题
echo "[3/8] 安装 hugo-theme-stack 主题..."
cd "$HUGO_SITE_DIR"
if [ ! -d "themes/hugo-theme-stack" ]; then
    git init
    git clone --depth 1 https://github.com/CaiJimmy/hugo-theme-stack.git themes/hugo-theme-stack
fi

# 4. 复制主题资源
echo "[4/8] 复制主题资源..."
mkdir -p assets/icons assets/scss assets/ts
cp -r themes/hugo-theme-stack/assets/icons/* assets/icons/
cp -r themes/hugo-theme-stack/assets/scss/* assets/scss/
cp -r themes/hugo-theme-stack/assets/ts/* assets/ts/

# 5. 复制 i18n
echo "[5/8] 配置多语言支持..."
mkdir -p i18n
cp themes/hugo-theme-stack/i18n/zh.toml i18n/

# 6. 复制博客内容
echo "[6/8] 复制博客文章..."
if [ -d "$BLOG_MD_DIR" ]; then
    # 复制图片
    mkdir -p static/images
    cp -r "$BLOG_MD_DIR/images/"* static/images/
    
    # 复制文章 (需手动运行 01-import-posts.py)
    echo "  请运行: python3 01-import-posts.py"
fi

# 7. 初始化完成
echo "[7/8] 清理临时文件..."
rm -f import_posts.py hugo.mod 2>/dev/null || true

# 8. 启动服务
echo "[8/8] 启动 Hugo 服务器..."
hugo server --bind 0.0.0.0 --port 1313

echo ""
echo "=========================================="
echo "  初始化完成!"
echo "  访问地址: http://localhost:1313"
echo "=========================================="
