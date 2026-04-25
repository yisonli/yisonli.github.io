---
categories:
- 编程
date: 2018-07-25
description: PHP OpenSSL 扩展详解：对称加密、非对称加密、数字签名完整指南
image: /images/cover-programming.svg
lastmod: 2018-07-25
tags:
- PHP
- OpenSSL
- 加密解密
- 安全
title: PHP的OpenSSL加密扩展使用小结
---

> 互联网的发展史上，安全性一直是开发者们相当重视的主题。为了实现数据传输安全，我们需要保证：数据来源（防伪造）、数据完整性（防篡改）、数据私密性（防窃听）。

## 加密基础

### 加密算法分类

```
┌─────────────────────────────────────────────────────────────┐
│                      加密算法分类                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────┐         ┌─────────────────┐           │
│   │   对称加密      │         │   非对称加密    │           │
│   ├─────────────────┤         ├─────────────────┤           │
│   │ • DES           │         │ • RSA           │           │
│   │ • AES           │         │ • DSA           │           │
│   │ • 3DES          │         │ • ECC           │           │
│   │ • Blowfish      │         │ • DH             │           │
│   └─────────────────┘         └─────────────────┘           │
│                                                             │
│   ┌─────────────────────────────────────────────────┐       │
│   │                   数字签名                      │       │
│   ├─────────────────────────────────────────────────┤       │
│   │ • MD5 (已不安全) • SHA-1 (已不安全)            │       │
│   │ • SHA-256 • SHA-512 • HMAC                      │       │
│   └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 对称加密

**特点**：
- 加密和解密使用同一密钥
- 速度快，适合大量数据
- 加密前后文件大小变化不大
- 密钥管理是难题

**常见算法**：DES、AES、3DES、Blowfish

### 非对称加密

**特点**：
- 使用公钥和私钥一对密钥
- 公钥加密，私钥解密（或反之）
- 计算量大，速度慢
- 适合密钥交换和数字签名

**常见算法**：RSA、DSA、ECC

### 数字签名

**特点**：
- 无论原始数据多大，输出长度固定
- 输入相同，输出相同
- 微小改变导致输出巨大变化
- 不可逆，无法从哈希值恢复原始数据

**常见算法**：MD5、SHA-1、SHA-256、HMAC

## PHP OpenSSL 扩展

### 安装检查

```php
<?php
// 检查 OpenSSL 扩展是否启用
if (extension_loaded('openssl')) {
    echo "OpenSSL 已启用";
    
    // 查看支持的加密算法
    print_r(openssl_get_cipher_methods());
    print_r(openssl_get_md_methods());
} else {
    echo "OpenSSL 未启用";
}
```

## 对称加密

### AES 加密

```php
<?php

/**
 * AES-256-CBC 加密
 * 
 * @param string $data 待加密数据
 * @param string $key 密钥（32字节）
 * @param string $iv 初始化向量（16字节）
 * @return string 加密后的数据（base64编码）
 */
function aes_encrypt(string $data, string $key, string $iv = ''): string
{
    // 密钥必须是 32 字节（AES-256）
    $key = hash('sha256', $key, true);
    
    // IV 必须是 16 字节（AES 块大小）
    if (strlen($iv) !== 16) {
        $iv = openssl_random_pseudo_bytes(16);
    }
    
    $encrypted = openssl_encrypt(
        $data,
        'AES-256-CBC',
        $key,
        OPENSSL_RAW_DATA,  // 返回原始数据
        $iv
    );
    
    // 返回 IV + 密文（便于解密）
    return base64_encode($iv . $encrypted);
}

/**
 * AES-256-CBC 解密
 * 
 * @param string $encrypted 加密数据（base64编码）
 * @param string $key 密钥
 * @return string 解密后的数据
 */
function aes_decrypt(string $encrypted, string $key): string
{
    $key = hash('sha256', $key, true);
    $data = base64_decode($encrypted);
    
    // 提取 IV（前 16 字节）
    $iv = substr($data, 0, 16);
    $ciphertext = substr($data, 16);
    
    return openssl_decrypt(
        $ciphertext,
        'AES-256-CBC',
        $key,
        OPENSSL_RAW_DATA,
        $iv
    );
}

// 使用示例
$key = 'your-secret-key-here';
$data = 'Hello, World! 你好世界！';

$encrypted = aes_encrypt($data, $key);
echo "加密后: " . $encrypted . "\n";

$decrypted = aes_decrypt($encrypted, $key);
echo "解密后: " . $decrypted . "\n";
```

### 其他对称加密算法

```php
<?php

$key = hash('sha256', 'password', true);

// AES-128-CBC（密钥 16 字节）
$encrypted = openssl_encrypt($data, 'AES-128-CBC', $key, OPENSSL_RAW_DATA, $iv);

// AES-128-ECB（无需 IV，但不安全）
$encrypted = openssl_encrypt($data, 'AES-128-ECB', $key);

// DES（不安全，不推荐）
$encrypted = openssl_encrypt($data, 'DES-ECB', $key);
```

## 非对称加密

### 生成 RSA 密钥对

```php
<?php

/**
 * 生成 RSA 密钥对
 * 
 * @param int $bits 密钥位数（推荐 2048 或 4096）
 * @return array ['private_key' => string, 'public_key' => string]
 */
function generate_rsa_keypair(int $bits = 2048): array
{
    $config = [
        'private_key_bits' => $bits,
        'private_key_type' => OPENSSL_KEYTYPE_RSA,
    ];
    
    // 生成密钥对
    $keyPair = openssl_pkey_new($config);
    
    // 导出私钥
    openssl_pkey_export($keyPair, $privateKey);
    
    // 导出公钥
    $publicKeyDetails = openssl_pkey_get_details($keyPair);
    $publicKey = $publicKeyDetails['key'];
    
    return [
        'private_key' => $privateKey,
        'public_key' => $publicKey,
    ];
}

// 生成密钥对
$keyPair = generate_rsa_keypair(2048);

echo "私钥:\n" . $keyPair['private_key'] . "\n\n";
echo "公钥:\n" . $keyPair['public_key'] . "\n";

// 保存到文件
file_put_contents('private.key', $keyPair['private_key']);
file_put_contents('public.key', $keyPair['public_key']);

// 设置权限（Linux）
chmod('private.key', 0600);
```

### RSA 加密解密

```php
<?php

/**
 * RSA 加密（使用公钥）
 * 
 * @param string $data 待加密数据
 * @param string $publicKey 公钥
 * @return string 加密后的数据（base64编码）
 */
function rsa_encrypt(string $data, string $publicKey): string
{
    $publicKey = openssl_pkey_get_public($publicKey);
    
    openssl_public_encrypt($data, $encrypted, $publicKey);
    
    return base64_encode($encrypted);
}

/**
 * RSA 解密（使用私钥）
 * 
 * @param string $encrypted 加密数据（base64编码）
 * @param string $privateKey 私钥
 * @return string 解密后的数据
 */
function rsa_decrypt(string $encrypted, string $privateKey): string
{
    $privateKey = openssl_pkey_get_private($privateKey);
    
    $data = base64_decode($encrypted);
    openssl_private_decrypt($data, $decrypted, $privateKey);
    
    return $decrypted;
}

// 使用示例
$keyPair = generate_rsa_keypair();

$data = 'Hello, RSA!';

$encrypted = rsa_encrypt($data, $keyPair['public_key']);
echo "加密后: " . $encrypted . "\n";

$decrypted = rsa_decrypt($encrypted, $keyPair['private_key']);
echo "解密后: " . $decrypted . "\n";
```

> ⚠️ **限制**：RSA 加密的数据长度有限制（密钥位数 / 8 - 11 字节）

### 分块加密大文件

```php
<?php

/**
 * RSA 分块加密（用于大数据）
 * 
 * @param string $data 待加密数据
 * @param string $publicKey 公钥
 * @return string 加密后的数据（base64编码）
 */
function rsa_encrypt_large(string $data, string $publicKey): string
{
    $res = openssl_pkey_get_public($publicKey);
    if ($res === false) {
        throw new InvalidArgumentException('Invalid public key');
    }
    $details = openssl_pkey_get_details($res);
    $maxChunk = (int) ($details['bits'] / 8) - 11; // PKCS#1 填充占用 11 字节
    if ($maxChunk <= 0) {
        throw new RuntimeException('Key size too small');
    }

    $cipherRaw = '';
    $len = strlen($data);
    for ($i = 0; $i < $len; $i += $maxChunk) {
        $chunk = substr($data, $i, $maxChunk);
        $out = '';
        if (!openssl_public_encrypt($chunk, $out, $res, OPENSSL_PKCS1_PADDING)) {
            throw new RuntimeException('openssl_public_encrypt failed');
        }
        $cipherRaw .= $out;
    }
    return base64_encode($cipherRaw);
}

/**
 * RSA 分块解密
 *
 * @param string $encrypted 公钥加密且经 base64 编码的密文
 * @param string $privateKey 私钥
 * @return string 原文
 */
function rsa_decrypt_large(string $encrypted, string $privateKey): string
{
    $res = openssl_pkey_get_private($privateKey);
    if ($res === false) {
        throw new InvalidArgumentException('Invalid private key');
    }
    $details = openssl_pkey_get_details($res);
    $block = (int) ($details['bits'] / 8);
    $raw = base64_decode($encrypted, true);
    if ($raw === false) {
        throw new InvalidArgumentException('Invalid base64 cipher');
    }

    $plain = '';
    $len = strlen($raw);
    for ($i = 0; $i < $len; $i += $block) {
        $chunk = substr($raw, $i, $block);
        $out = '';
        if (!openssl_private_decrypt($chunk, $out, $res, OPENSSL_PKCS1_PADDING)) {
            throw new RuntimeException('openssl_private_decrypt failed');
        }
        $plain .= $out;
    }
    return $plain;
}

/*
 * 小结：超长明文请优先使用「RSA 协商对称密钥 + AES」的混合加密；本节分块 RSA 适用于必须纯 RSA 的场景，
 * 实现时注意密钥位数与性能开销。
 */

```