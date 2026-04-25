---
categories:
- 编程
date: 2017-12-08
description: 使用 PHP GD 库为图片批量添加平铺水印的完整方案
image: /images/cover-programming.svg
lastmod: 2017-12-08
tags:
- PHP
- GD库
- 图片处理
title: 使用GD库给图片铺满水印
---

> PHP 使用 GD 库生成平铺水印的方法，可以将水印图片铺满整个图片。

## 原理说明

平铺水印的核心思想是：
1. 读取原图和水印图片
2. 循环遍历原图的每一个区域
3. 将水印图片复制到每个区域
4. 处理边界情况（水印超出原图边界）

## 完整代码实现

```php
<?php

/**
 * 图片平铺水印
 * 
 * @param string $dst_file 处理完成后保存的文件路径
 * @param string $src_file 待处理的图片文件路径
 * @param string $logo_file 水印图片文件路径
 * @param int $top 上间距（水印之间的垂直间距）
 * @param int $left 左间距（水印之间的水平间距）
 * @param int|false $alpha 透明度 0-100，false 表示不透明
 * @return bool
 */
function fullFillLogos($dst_file, $src_file, $logo_file, $top = 0, $left = 0, $alpha = false) {
    try {
        // 检查文件是否存在
        if (!file_exists($src_file)) {
            throw new Exception("源图片不存在: $src_file");
        }
        if (!file_exists($logo_file)) {
            throw new Exception("水印图片不存在: $logo_file");
        }
        
        // 检查 GD 库是否支持
        if (!extension_loaded('gd')) {
            throw new Exception("GD 库未安装");
        }
        
        // 创建图片资源
        $dst = imagecreatefromstring(file_get_contents($src_file));
        $logo = imagecreatefrompng($logo_file); // PNG 保留透明度
        
        if (!$dst || !$logo) {
            throw new Exception("图片创建失败");
        }
        
        // 获取尺寸
        $logo_w = imagesx($logo);
        $logo_h = imagesy($logo);
        $dst_w = imagesx($dst);
        $dst_h = imagesy($dst);
        
        // 循环铺上水印
        for ($off_y = $top; $off_y < $dst_h; $off_y += $logo_h + $top) {
            for ($off_x = $left; $off_x < $dst_w; $off_x += $logo_w + $left) {
                // 计算边界：如果水印超出原图边界，需要裁剪
                $width = ($off_x + $logo_w > $dst_w) ? ($dst_w - $off_x) : $logo_w;
                $height = ($off_y + $logo_h > $dst_h) ? ($dst_h - $off_y) : $logo_h;
                
                // 如果超出边界，从水印图片的 (0,0) 开始裁剪
                $src_x = 0;
                $src_y = 0;
                if ($off_x + $logo_w > $dst_w) {
                    $src_x = $logo_w - $width;
                }
                if ($off_y + $logo_h > $dst_h) {
                    $src_y = $logo_h - $height;
                }
                
                // 根据透明度选择复制方式
                if ($alpha === false) {
                    // 不透明复制（忽略 PNG 原有透明度）
                    imagecopy($dst, $logo, $off_x, $off_y, $src_x, $src_y, $width, $height);
                } else {
                    // 带透明度复制（PNG 透明度会被忽略）
                    imagecopymerge($dst, $logo, $off_x, $off_y, $src_x, $src_y, $width, $height, $alpha);
                }
            }
        }
        
        // 获取原图格式
        $mime = mime_content_type($src_file);
        $ext = strtolower(pathinfo($src_file, PATHINFO_EXTENSION));
        
        // 保存图片
        switch ($ext) {
            case 'jpg':
            case 'jpeg':
                imagejpeg($dst, $dst_file, 90);
                break;
            case 'png':
                imagepng($dst, $dst_file, 9);
                break;
            case 'gif':
                imagegif($dst, $dst_file);
                break;
            default:
                imagejpeg($dst, $dst_file, 90);
        }
        
        // 释放内存
        imagedestroy($dst);
        imagedestroy($logo);
        
        return true;
    } catch (Exception $e) {
        error_log($e->getMessage());
        return false;
    }
}
```

## 使用示例

```php
<?php

// 示例1：最基本的用法
$result = fullFillLogos(
    '/path/to/output.jpg',      // 输出文件
    '/path/to/source.jpg',      // 源图片
    '/path/to/watermark.png',   // 水印图片
    10,                         // 垂直间距
    10,                         // 水平间距
    50                          // 50% 透明度
);

// 示例2：不透明水印
$result = fullFillLogos(
    '/path/to/output.jpg',
    '/path/to/source.jpg',
    '/path/to/logo.png',
    20,      // 更大的间距
    20,
    false    // 不透明
);

// 示例3：API 形式调用
if (fullFillLogos($dst, $src, $logo, 0, 0, 30)) {
    echo "水印添加成功";
} else {
    echo "水印添加失败";
}
```

## 进阶版本：支持水印位置

```php
/**
 * 带位置参数的水印函数
 * 
 * @param string $dst_file 输出文件
 * @param string $src_file 源文件
 * @param string $logo_file 水印文件
 * @param string $position 水印位置：center/tiled/single
 * @param int $margin 边距（single 模式下有效）
 * @param int|false $alpha 透明度
 */
function watermark($dst_file, $src_file, $logo_file, $position = 'tiled', $margin = 10, $alpha = false) {
    $dst = imagecreatefromstring(file_get_contents($src_file));
    $logo = imagecreatefrompng($logo_file);
    
    $logo_w = imagesx($logo);
    $logo_h = imagesy($logo);
    $dst_w = imagesx($dst);
    $dst_h = imagesy($dst);
    
    if ($position === 'tiled') {
        // 平铺模式
        for ($off_y = 0; $off_y < $dst_h; $off_y += $logo_h) {
            for ($off_x = 0; $off_x < $dst_w; $off_x += $logo_w) {
                imagecopy($dst, $logo, $off_x, $off_y, 0, 0, $logo_w, $logo_h);
            }
        }
    } elseif ($position === 'center') {
        // 居中模式
        $x = ($dst_w - $logo_w) / 2;
        $y = ($dst_h - $logo_h) / 2;
        imagecopy($dst, $logo, $x, $y, 0, 0, $logo_w, $logo_h);
    } elseif ($position === 'bottom-right') {
        // 右下角
        $x = $dst_w - $logo_w - $margin;
        $y = $dst_h - $logo_h - $margin;
        imagecopy($dst, $logo, $x, $y, 0, 0, $logo_w, $logo_h);
    }
    
    imagepng($dst, $dst_file);
    imagedestroy($dst);
    imagedestroy($logo);
}
```

## 水印图片制作建议

### 1. 使用 PNG 格式

PNG 格式支持透明背景，适合做水印：

```bash
# 使用 ImageMagick 创建水印图片
convert -size 100x50 xc:none -fill black \n        -pointsize 20 -gravity center \n        -annotate +0+0 "© YISON" logo.png
```

### 2. 保持水印图片尺寸适中

- 水印太小：看不清
- 水印太大：影响原图观赏

建议水印尺寸为原图的 **5%-15%**

### 3. 半透明效果

使用 PNG-24 格式并设置透明度：

```php
// 使用 imagecopymerge 可以保留 PNG 的透明通道
imagecopymerge($dst, $logo, $x, $y, 0, 0, $logo_w, $logo_h, 50);
```

## 注意事项

1. **内存消耗**：处理大图片时注意 PHP 内存限制
    ```php
    ini_set('memory_limit', '256M'); // 根据需要调整
    ```

2. **GD 库与格式**：确认 PHP 已启用 GD（`php -m | grep -i gd`）。JPEG、PNG、GIF、WebP 需分别使用 `imagecreatefromjpeg` / `imagecreatefrompng` / `imagecreatefromgif` / `imagecreatefromwebp` 创建画布；保存时对应使用 `imagejpeg`、`imagepng` 等，并对透明 PNG 选用 `imagesavealpha($im, true)`，避免透明通道丢失。

3. **压缩与画质**：对大图先做适当缩放再叠水印以节省内存。JPEG 保存时可指定质量参数，例如 `imagejpeg($dst, $path, 90);`，在体积与观感之间折中；尽量避免对同一文件反复解码—编码多次，以免画质明显下降。

## 小结

铺满水印本质是「遍历网格 + `imagecopy`/`imagecopymerge`」。实现时注意内存、格式与透明度处理，并在批量任务里做好异常与日志，便于线上排查。