---
categories:
- 编程
date: 2017-05-03
description: WordPress 接入腾讯云 COS 实现图片外链的完整配置教程
lastmod: 2017-05-03
tags:
- WordPress
- 腾讯云
- COS
- 对象存储
title: WordPress如何使用腾讯云COS
---

> COS 是腾讯云的对象存储服务，免费 50G 存储空间，按外网流量收费，内网调用免流量。本文介绍如何让 WordPress 使用 COS 存储图片并享受内网流量。

## 一、COS 开通与配置

### 1. 开通对象存储服务

登录 [腾讯云控制台](https://console.cloud.tencent.com/cos5)，按照提示开通 COS 服务。

### 2. 创建 Bucket

> ⚠️ **重要**：Bucket 所属地域必须与 ECS 服务器一致，否则无法享受内网流量！

在 COS 控制台创建存储桶：
- 选择与 ECS 相同地域（如广州、上海等）
- 设置访问权限（建议私有读写）
- 记录 Bucket 名称和地域

### 3. 获取密钥

在 [访问密钥管理](https://console.cloud.tencent.com/cam/capi) 页面获取：
- SecretId
- SecretKey

## 二、安装 COS 插件

本文采用 [cos-sync 插件](https://www.slmwp.com/cos-sync-plugins.html)，上传图片时自动同步到 COS。

### 安装步骤

1. 下载插件并解压
2. 上传到 WordPress 插件目录
3. 在 WordPress 后台启用插件
4. 配置插件参数（SecretId、SecretKey、Bucket、地域等）

### 插件配置

```php
// 插件配置参数示例
cos_options = [
    'secretId' => '你的SecretId',
    'secretKey' => '你的SecretKey',
    'bucket' => 'your-bucket-1250000000',
    'regional' => 'ap-guangzhou',  // 地域代码
    'domain' => 'https://your-bucket.cos.ap-guangzhou.myqcloud.com'
];
```

## 三、享受 COS 内网流量

### 方法 A：自建代理服务

在服务器上实现一个读取 COS 图片的服务：

```php
<?php
// proxy.php - COS 代理服务
if (empty($_GET["file"])) {
    die('no access');
}

require_once __DIR__ . '/../../../wp-blog-header.php';
require_once 'vendor/autoload.php';

use Qcloud\Cos\Client;
use Qcloud\Cos\Exception\ServiceResponseException;

$cos_options = get_option('cos_options', true);
$secretId = $cos_options['secretId'];
$secretKey = $cos_options['secretKey'];
$bucket = $cos_options['bucket'];
$region = $cos_options['regional'];

$client = new Client([
    'region' => $region,
    'credentials' => [
        'secretId' => $secretId,
        'secretKey' => $secretKey,
    ],
]);

$file = $_GET["file"];

try {
    $result = $client->getObject([
        'Bucket' => $bucket,
        'Key' => ltrim($file, '/'),
    ]);
    
    // 设置 Content-Type
    $contentType = $result['ContentType'] ?? 'application/octet-stream';
    header('Content-Type: ' . $contentType);
    echo $result['Body'];
} catch (ServiceResponseException $e) {
    http_response_code(404);
    die('File not found');
}
```

**评价**：
- ✅ 实现灵活，可自定义缓存、压缩等
- ❌ 需要处理 COS 的 keep-alive 问题
- ❌ 需要设置合理的超时时间

### 方法 B：Nginx 反向代理（推荐）

使用 Nginx 代理 COS 请求，实现内网访问：

```nginx
server {
    listen 80;
    server_name your-blog.com;
    
    # WordPress 其他请求
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
    
    # COS 图片代理
    location ^~ /cos/ {
        # 去掉 /cos/ 前缀，重写为实际 COS 路径
        rewrite ^/cos/(.*) /$1 break;
        
        # 代理到 COS
        proxy_pass https://your-bucket.cos.ap-guangzhou.myqcloud.com/;
        
        # 代理配置
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
        
        # 缓存设置
        proxy_cache cache;
        proxy_cache_valid 200 7d;
        add_header X-Cache-Status $upstream_cache_status;
    }
    
    location ~ \.php$ {
        fastcgi_pass unix:/run/php/php-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }
}
```

**访问方式**：`http://your-blog.com/cos/uploads/2023/01/image.jpg`

**评价**：
- ✅ 实现简单，配置灵活
- ✅ 响应及时，支持缓存
- ✅ 可复用 Nginx 的各种优化

## 四、插件优化配置

### 问题 A：媒体库缩略图显示异常

> **现象**：不勾选"本地保存"后，媒体库缩略图显示不正确

**原因**：服务器不存储图片，无法获取尺寸，默认宽高为 1px

**解决**：修改 WordPress 核心文件最小尺寸

```php
// wp-includes/media.php，约 444 行
// 将 $w 和 $h 的最小值改为 150
$w = max(150, (int) round($current_width * $ratio));
$h = max(150, (int) round($current_height * $ratio));
```

```php
// wp-admin/includes/image-edit.php，约 606 行
$w2 = max(150, $w * $ratio);
$h2 = max(150, $h * $ratio);
```

### 问题 B：预览看不到图片

**解决**：修改媒体模板文件

```php
// wp-includes/media-template.php，约 680 行和 931 行
// 在 else 分支中设置 size 为 full
<# } else { #>
    <label class="setting">
        <input type="hidden" name="size" value="full" />
    </label>
<# } #>
```

## 五、完整配置示例

### docker-compose.yml

```yaml
version: '3.8'

services:
  wordpress:
    image: wordpress:latest
    ports:
      - "8080:80"
    volumes:
      - ./wp-content:/var/www/html/wp-content
    environment:
      - WORDPRESS_DB_HOST=db
      - WORDPRESS_DB_NAME=wordpress
      - WORDPRESS_DB_USER=wp_user
      - WORDPRESS_DB_PASSWORD=wp_password

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=wordpress
      - MYSQL_USER=wp_user
      - MYSQL_PASSWORD=wp_password
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```

### Nginx 配置（生产环境）

```nginx
upstream wordpress {
    server 127.0.0.1:8080;
}

server {
    listen 443 ssl http2;
    server_name your-blog.com;
    
    ssl_certificate /etc/ssl/certs/your-blog.crt;
    ssl_certificate_key /etc/ssl/private/your-blog.key;
    
    root /var/www/html;
    index index.php index.html;
    
    # COS 代理
    location ^~ /cos/ {
        rewrite ^/cos/(.*) /$1 break;
        proxy_pass https://your-bucket.cos.ap-guangzhou.myqcloud.com/;
        proxy_cache_valid 200 30d;
        expires 30d;
    }
    
    # WordPress
    location / {
        proxy_pass http://wordpress;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location ~ \.php$ {
        proxy_pass http://wordpress;
        fastcgi_pass unix:/run/php/php-fpm.sock;
        include fastcgi_params;
    }
}
```

## 六、常见问题

### Q: Bucket 地域选错了怎么办？

A: 可以删除重建，或在插件中手动指定地域参数。

### Q: 内网流量仍然收费？

A: 检查 ECS 和 COS 是否同地域，确保使用内网域名访问。

### Q: 图片加载很慢？

A: 建议开启 CDN 加速，配合 Nginx 缓存优化。

## 七、费用说明

| 项目 | 说明 |
|:---|:---|
| 存储空间 | 免费 50GB |
| 内网流量 | 免费 |
| 外网下行流量 | 按量计费 |
| 请求次数 | 按量计费 |

> 💡 **建议**：将 ECS 和 COS 放在同一地域，使用 **内网 Endpoint（内网域名）** 访问存储与回源，可省去外网下行流量费用并降低访问延迟。若站点必须对公网用户分发图片，可在 COS 或 CDN 侧单独配置外网访问与缓存策略，按业务场景权衡成本与性能。

## 八、小结

按本文完成 COS 对接与域名配置后，媒体资源可走对象存储承载流量，ECS 专注计算；后续若有访问热点，再结合 CDN 与缓存策略进一步优化即可。