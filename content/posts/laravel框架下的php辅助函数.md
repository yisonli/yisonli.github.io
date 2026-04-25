---
title: Laravel框架下的PHP辅助函数
date: '2019-03-22T00:00:00'
draft: false
categories:
- 编程
tags:
- PHP
- Laravel
- 辅助函数
description: Laravel 框架内置 PHP 辅助函数详解：数组、字符串、路径、URL 函数
lastmod: 2019-03-22
image: /images/cover-programming.svg
---
> Laravel 框架自带了一系列 PHP 辅助函数，很多被框架自身使用。了解这些函数方便我们在代码中善用它们。

## 数组函数

### array_add()

添加给定键值对到数组（如果给定键不存在）：

```php
// 如果键不存在则添加
$array = array_add(['name' => 'Desk'], 'price', 100);
// ['name' => 'Desk', 'price' => 100]

// 如果键已存在则不添加
$array = array_add(['name' => 'Desk', 'price' => 50], 'price', 100);
// ['name' => 'Desk', 'price' => 50]  价格保持 50
```

### array_collapse()

将多个数组合并成一个：

```php
$array = array_collapse([[1, 2, 3], [4, 5, 6], [7, 8, 9]]);
// [1, 2, 3, 4, 5, 6, 7, 8, 9]

// 实际应用：分组数据合并
$postsByCategory = [
    'tech' => [['title' => 'Post 1'], ['title' => 'Post 2']],
    'life' => [['title' => 'Post 3']],
];
$allPosts = array_collapse($postsByCategory);
// [['title' => 'Post 1'], ['title' => 'Post 2'], ['title' => 'Post 3']]
```

### array_divide()

分离数组的键和值：

```php
[$keys, $values] = array_divide(['name' => 'Desk', 'price' => 100]);
// $keys = ['name', 'price']
// $values = ['Desk', 100]
```

### array_dot()

将多维数组转为一维（使用点号分隔键）：

```php
$array = [
    'products' => [
        'desk' => [
            'price' => 100,
        ],
    ],
];

$flattened = array_dot($array);
// [
//     'products.desk.price' => 100,
// ]
```

### array_except() / array_only()

```php
// 排除指定键
$array = ['name' => 'Desk', 'price' => 100, 'orders' => 10];
$except = array_except($array, ['price']);
// ['name' => 'Desk', 'orders' => 10]

// 只保留指定键
$array = ['name' => 'Desk', 'price' => 100, 'orders' => 10];
$only = array_only($array, ['name', 'price']);
// ['name' => 'Desk', 'price' => 100]
```

### array_first() / array_last()

```php
$array = [100, 200, 300];

// 返回第一个匹配的元素
$first = array_first($array, function ($value) {
    return $value >= 150;
});
// 200

// 返回最后一个匹配的元素
$last = array_last($array, function ($value) {
    return $value >= 150;
});
// 300

// 支持默认值
$first = array_first($array, function ($value) {
    return $value >= 500;
}, 'default');
// 'default'
```

### array_flatten()

多维数组转一维：

```php
$array = [['id' => 1], ['id' => 2], [['id' => 3]]];
$flattened = array_flatten($array);
// [1, 2, 3]
```

### array_forget()

使用点号语法删除数组元素：

```php
$array = ['products' => ['desk' => ['price' => 100]]];
array_forget($array, 'products.desk.price');

// $array = ['products' => ['desk' => []]]
```

### array_get()

使用点号语法获取数组值：

```php
$array = [
    'products' => [
        'desk' => ['price' => 100],
    ],
];

$price = array_get($array, 'products.desk.price');
// 100

// 支持默认值
$price = array_get($array, 'products.chair.price', 200);
// 200
```

### array_has()

检查数组是否有指定键：

```php
$array = ['products' => ['desk' => ['price' => 100]]];

array_has($array, 'products.desk');
// true

array_has($array, 'products.chair');
// false

// 支持检查多个键
array_has($array, ['products.desk', 'products.chair']);
// false
```

### array_pluck()

提取数组中指定键的值：

```php
$array = [
    ['product' => 'Desk', 'price' => 100],
    ['product' => 'Chair', 'price' => 50],
];

$products = array_pluck($array, 'product');
// ['Desk', 'Chair']

// 带键
$products = array_pluck($array, 'product', 'price');
// [100 => 'Desk', 50 => 'Chair']
```

### array_pull()

弹出数组元素并删除：

```php
$array = ['name' => 'Desk', 'price' => 100];

$name = array_pull($array, 'name');
// $name = 'Desk'
// $array = ['price' => 100]
```

### array_set()

使用点号语法设置数组值：

```php
$array = [];
array_set($array, 'products.desk.price', 100);

// $array = ['products' => ['desk' => ['price' => 100]]]
```

### array_sort()

按值排序：

```php
$array = [
    ['name' => 'Desk', 'price' => 100],
    ['name' => 'Chair', 'price' => 50],
    ['name' => 'Table', 'price' => 75],
];

$sorted = array_values(array_sort($array, function ($item) {
    return $item['price'];
}));
// [
//     ['name' => 'Chair', 'price' => 50],
//     ['name' => 'Table', 'price' => 75],
//     ['name' => 'Desk', 'price' => 100],
// ]
```

### array_where()

条件过滤数组：

```php
$array = [100, 200, 300, 400, 500];

$filtered = array_where($array, function ($value, $key) {
    return $value >= 200;
});
// [1 => 200, 2 => 300, 3 => 400, 4 => 500]
```

### head() / last()

```php
$array = [100, 200, 300];

head($array);  // 100 - 返回第一个元素
last($array);  // 300 - 返回最后一个元素
```

## 字符串函数

### str_contains()

检查字符串是否包含指定内容：

```php
str_contains('Hello World', 'World');
// true

str_contains('Hello World', ['World', 'PHP']);
// true

str_contains('Hello World', ['World', 'PHP']);
// true - 任一匹配即返回 true
```

### str_start()

确保字符串以指定内容开头：

```php
str_start('World', 'Hello ');
// 'Hello World'

str_start('Hello World', 'Hello ');
// 'Hello World' - 已经是则不变
```

### str_finish()

确保字符串以指定内容结尾：

```php
str_finish('Hello', ' World');
// 'Hello World'

str_finish('Hello World', ' World');
// 'Hello World' - 已经是则不变
```

### str_limit()

截断字符串：

```php
str_limit('The quick brown fox jumps over the lazy dog', 20);
// 'The quick brown fox...'

str_limit('The quick brown fox', 20, ' (...)');
// 'The quick brown (...)'
```

### str_plural() / str_singular()

单复数转换：

```php
str_plural('child');
// 'children'

str_plural('child', 1);
// 'child'

str_plural('children');
// 'children'

str_singular('children');
// 'child'
```

### str_slug()

生成 URL 友好的字符串：

```php
str_slug('Hello World');
// 'hello-world'

str_slug('Hello World!', '_');
// 'hello_world'

str_slug('日本語');
// 'ri-ben-yu'
```

### str_replace_array()

批量替换字符串：

```php
$string = 'The framework has :count widgets';

str_replace_array(':count', [5], $string);
// 'The framework has 5 widgets'
```

### str_replace_first() / str_replace_last()

```php
str_replace_first('the', 'a', 'the quick the fox');
// 'a quick the fox'

str_replace_last('the', 'a', 'the quick the fox');
// 'the quick a fox'

// 对应门面（文件顶部需：use Illuminate\Support\Str;）
// Str::replaceLast('world', 'PHP', 'Hello world'); // Hello PHP
```

> `str_replace_*` 系列常用于日志脱敏、路径规范化等场景；新版本 Laravel 亦可使用 `Illuminate\Support\Str` 门面，请以当前版本文档为准。