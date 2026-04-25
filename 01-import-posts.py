#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugo 博客文章导入脚本
功能:
  1. 从 blogMD 目录读取 Markdown 文章
  2. 转换 frontmatter 格式
  3. 修复图片路径为相对路径
  4. 根据分类自动分配渐变封面
  5. 输出到 hugo-site/content/posts/

使用方法:
  python3 01-import-posts.py
"""

import os
import re
import shutil
import yaml
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================
BLOG_MD_DIR = Path("/app/working/workspaces/iZdgLi/yison/blogMD")
HUGO_CONTENT_DIR = Path("/app/working/workspaces/iZdgLi/yison/hugo-site/content/posts")
STATIC_IMAGES_DIR = Path("/app/working/workspaces/iZdgLi/yison/hugo-site/static/images")

# 分类到封面的映射
CATEGORY_COVERS = {
    "编程": "/images/cover-programming.svg",
    "数据库": "/images/cover-database.svg",
    "操作系统": "/images/cover-os.svg",
    "版本控制": "/images/cover-vcs.svg",
    "读书": "/images/cover-reading.svg",
    "DevOps": "/images/cover-devops.svg",
}

# ==================== 函数 ====================

def parse_frontmatter(content):
    """解析 YAML front matter"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}, content
    
    frontmatter_str = match.group(1)
    body = content[len(match.group(0)):].lstrip('\n')
    
    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        frontmatter = {}
    
    return frontmatter, body

def fix_image_paths(content):
    """修复图片路径为 Hugo 相对路径"""
    # 处理 /images/ 路径，保留原文件名
    def replace_image(match):
        path = match.group(2)
        if any(ext in path.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            # 提取文件名并构建新路径
            basename = os.path.basename(path)
            return f'![{match.group(1)}](/images/{basename})'
        return match.group(0)
    
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+\.(?:png|jpg|jpeg|gif|webp))\)', replace_image, content)
    return content

def generate_slug(filename):
    """从文件名生成 slug"""
    name = os.path.basename(filename)
    # 移除日期前缀
    name = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', name)
    # 移除扩展名
    name = re.sub(r'\.md(?:\.md)?$', '', name)
    # 特殊字符转连字符
    name = re.sub(r'[#【】\[\]（）\(\)《》<>]', '-', name)
    name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-').lower()

def process_post(filepath):
    """处理单篇文章"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析 front matter
    frontmatter, body = parse_frontmatter(content)
    
    # 提取日期
    date_str = os.path.basename(filepath)[:10]
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        date = datetime.now()
    
    # 生成 slug
    slug = generate_slug(filepath)
    
    # 构建新的 front matter
    new_frontmatter = {
        'title': frontmatter.get('title', slug),
        'date': date.isoformat(),
        'draft': False,
    }
    
    # 保留分类和标签
    if 'categories' in frontmatter:
        new_frontmatter['categories'] = frontmatter['categories']
    if 'tags' in frontmatter:
        new_frontmatter['tags'] = frontmatter['tags']
    if 'description' in frontmatter:
        new_frontmatter['description'] = frontmatter['description']
    if 'lastmod' in frontmatter:
        new_frontmatter['lastmod'] = frontmatter['lastmod']
    
    # 根据分类添加封面
    if 'categories' in frontmatter and frontmatter['categories']:
        category = frontmatter['categories'][0] if frontmatter['categories'] else '编程'
        cover = CATEGORY_COVERS.get(category, CATEGORY_COVERS['编程'])
        new_frontmatter['image'] = cover
    
    # 修复图片路径
    new_body = fix_image_paths(body)
    
    # 生成新内容
    new_content = '---\n'
    new_content += yaml.dump(new_frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    new_content += '---\n'
    new_content += new_body
    
    return slug, new_content

def main():
    """主函数"""
    HUGO_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取所有 md 文件
    md_files = list(BLOG_MD_DIR.glob("*.md"))
    md_files.extend(list(BLOG_MD_DIR.glob("*.md.md")))
    
    print(f"找到 {len(md_files)} 篇文章")
    
    success_count = 0
    error_files = []
    
    for filepath in md_files:
        try:
            slug, new_content = process_post(filepath)
            output_file = HUGO_CONTENT_DIR / f"{slug}.md"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            success_count += 1
            print(f"✓ {filepath.name} -> {slug}.md")
            
        except Exception as e:
            error_files.append((filepath.name, str(e)))
            print(f"✗ {filepath.name}: {e}")
    
    print(f"\n处理完成: {success_count} 成功, {len(error_files)} 失败")

if __name__ == "__main__":
    main()
