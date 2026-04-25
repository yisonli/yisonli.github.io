#!/usr/bin/env python3
"""
Hugo 博客迁移脚本
将 blogMD 目录下的文章迁移到 Hugo 站点的 content/posts 目录
"""

import os
import re
import shutil
import yaml
from datetime import datetime
from pathlib import Path

# 配置路径
BLOG_MD_DIR = Path("/app/working/workspaces/iZdgLi/yison/blogMD")
HUGO_CONTENT_DIR = Path("/app/working/workspaces/iZdgLi/yison/hugo-site/content/posts")
STATIC_IMAGES_DIR = Path("/app/working/workspaces/iZdgLi/yison/hugo-site/static/images")

def parse_frontmatter(content):
    """解析 YAML front matter"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}, content
    
    frontmatter_str = match.group(1)
    body = content[len(match.group(0)):].lstrip('\n')
    
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError:
        frontmatter = {}
    
    return frontmatter, body

def fix_image_paths(content):
    """修复图片路径为 Hugo 相对路径"""
    # 匹配常见图片引用格式
    patterns = [
        # Markdown 图片: ![alt](url)
        (r'!\[([^\]]*)\]\(([^)]+\.(?:png|jpg|jpeg|gif|webp))\)', 
         lambda m: f'![{m.group(1)}](/images/{os.path.basename(m.group(2))})'),
        # HTML img: <img src="url">
        (r'<img\s+[^>]*src=["\']([^"\']+\.(?:png|jpg|jpeg|gif|webp))["\']', 
         lambda m: re.sub(r'(?:src=["\'])([^"\']+\.(?:png|jpg|jpeg|gif|webp))(["\'])', 
                         r'\g<1>' if os.path.basename(m.group(1)) else r'/images/' + os.path.basename(m.group(1)), 
                         m.group(0))),
    ]
    
    # 简化处理：直接替换 /images/ 为 /images/
    content = re.sub(r'\(/images/', '/images/', content)
    content = re.sub(r'!\[\]\(/images/', '![](/images/', content)
    
    # 替换静态资源路径为 /images/
    content = re.sub(r'!\[([^\]]*)\]\(([^)]*)\)', 
                     lambda m: f'![{m.group(1)}](/images/{os.path.basename(m.group(2))})' 
                     if any(ext in m.group(2).lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'])
                     else m.group(0),
                     content)
    
    return content

def generate_slug(filename):
    """从文件名生成 slug"""
    # 移除日期前缀 (YYYY-MM-DD-)
    name = os.path.basename(filename)
    name = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', name)
    # 移除 .md 扩展名
    name = re.sub(r'\.md(?:\.md)?$', '', name)
    # 替换特殊字符为连字符
    name = re.sub(r'[#【】\[\]（）\(\)《》<>]', '-', name)
    name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name.lower()

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
    
    # 保留 lastmod
    if 'lastmod' in frontmatter:
        new_frontmatter['lastmod'] = frontmatter['lastmod']
    
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
    # 确保目标目录存在
    HUGO_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取所有 md 文件
    md_files = list(BLOG_MD_DIR.glob("*.md"))
    md_files.extend(list(BLOG_MD_DIR.glob("*.md.md")))  # 处理 .md.md 文件
    
    print(f"找到 {len(md_files)} 篇文章")
    
    success_count = 0
    error_files = []
    
    for filepath in md_files:
        try:
            slug, new_content = process_post(filepath)
            
            # 生成新文件名: slug.md
            output_file = HUGO_CONTENT_DIR / f"{slug}.md"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            success_count += 1
            print(f"✓ {filepath.name} -> {slug}.md")
            
        except Exception as e:
            error_files.append((filepath.name, str(e)))
            print(f"✗ {filepath.name}: {e}")
    
    print(f"\n处理完成: {success_count} 成功, {len(error_files)} 失败")
    
    if error_files:
        print("\n失败文件:")
        for name, err in error_files:
            print(f"  - {name}: {err}")

if __name__ == "__main__":
    main()
