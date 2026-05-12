# Lab5 简易朋友圈系统

这是实验五“数据库应用开发大作业”的简易朋友圈系统。项目使用 Python + MySQL 实现，提供网页前端和命令行菜单两种交互方式。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `schema.sql` | 创建数据库、表、完整性约束、视图、触发器 |
| `init_data.sql` | 插入初始化测试数据 |
| `app.py` | Python 后端服务，提供网页接口和数据库操作逻辑 |
| `frontend.html` | 简易前端页面 |
| `cli_app.py` | 最小命令行菜单版，便于讲解代码逻辑 |
| `实验五报告.md` | 实验报告 Markdown 版本 |
| `lab5_er_first_layout_text_only_final.png` | ER 图 |

## 数据库对象说明

执行 `SHOW FULL TABLES;` 时会看到 18 个对象，其中并不全是基本表：

- 基本表：12 张
- 视图：6 个

基本表如下：

```text
users
admins
friend_groups
friend_requests
friendships
friend_group_memberships
posts
post_visible_groups
post_visible_users
comments
notifications
audit_logs
```

视图如下：

```text
admin_post_view
friend_profile_view
friend_post_view
own_post_view
post_preview_view
user_notification_view
```

## 环境要求

- Python 3
- MySQL 8.0 或以上
- 浏览器

本项目的 Python 后端通过本机 MySQL 命令行工具连接数据库，不需要额外安装 Python 第三方包。

## 初始化数据库

本项目默认使用 MySQL login-path：`lab5root`。如果本机还没有配置，可以先执行：

```bash
mysql_config_editor set --login-path=lab5root --host=localhost --user=root --password
```

执行后输入 MySQL root 密码。配置完成后，可以用下面命令测试：

```bash
mysql --login-path=lab5root -e "SELECT 1;"
```

然后进入项目文件夹：

```bash
cd /path/to/lab5
```

先创建数据库、表、视图和触发器：

```bash
mysql --login-path=lab5root < schema.sql
```

再导入初始化测试数据：

```bash
mysql --login-path=lab5root < init_data.sql
```

`schema.sql` 会创建数据库 `lab5_social_platform`，并创建所有表、约束、视图和触发器。`init_data.sql` 开头有：

```sql
USE lab5_social_platform;
```

所以第二条命令会把测试用户、管理员、好友关系、朋友圈、评论、通知等初始数据插入到该数据库中。

也可以在 MySQL 交互界面里手动执行：

```sql
SOURCE /path/to/lab5/schema.sql;
SOURCE /path/to/lab5/init_data.sql;
```

## 启动网页端

在项目文件夹中执行：

```bash
python3 app.py
```

浏览器打开：

```text
http://127.0.0.1:8005
```

网页端支持普通用户和管理员登录、朋友圈浏览、好友管理、通知、管理员审核等功能。

## 启动命令行版

```bash
python3 cli_app.py
```

命令行版复用 `app.py` 里的数据库操作函数，方便按菜单理解每个功能对应的插入、删除、修改和查询逻辑。

## 默认账号

普通用户密码均为：

```text
123456
```

常用普通用户：

```text
Alice093427
Bob104582
Carol386915
David582731
Emma640298
Frank719463
Grace805217
Henry924680
Ivy137592
Jack468305
```

管理员：

```text
9001 / admin123
```

## 查看数据库原始数据

进入数据库：

```bash
mysql --login-path=lab5root -D lab5_social_platform
```

常用检查语句：

```sql
SHOW FULL TABLES;
SELECT * FROM users;
SELECT * FROM admins;
SELECT * FROM posts;
SELECT * FROM comments;
SELECT * FROM friendships;
SELECT * FROM notifications;
SELECT * FROM admin_post_view;
SELECT * FROM friend_post_view;
```

查看表结构：

```sql
DESCRIBE users;
DESCRIBE posts;
DESCRIBE notifications;
```

## 演示重点

- 注册登录与资料：注册新用户、登录、修改姓名、性别、出生日期、展示年龄、头像、朋友圈可见时长。
- 好友申请通知：发送好友申请后，对方会收到通知；接受或拒绝后，申请人也会收到通知。
- 好友管理：搜索用户并申请添加好友；接受申请后自动建立双向好友关系；删除好友时双方关系一起删除。
- 分组管理：创建分组，把好友加入或移出分组；一个好友可以属于多个分组。
- 朋友圈管理：发表、修改、删除自己的朋友圈；删除朋友圈时评论会级联删除。
- 朋友圈权限：支持全部好友、指定分组、指定好友、仅自己可见。
- 评论通知：评论后，系统自动通知朋友圈作者和可见范围内相关用户。
- 管理员审核：管理员可以查看所有朋友圈、屏蔽或恢复朋友圈、注销用户。
- 视图检查：前端“验收视图”页面可以直接查看各个数据库视图的结果。

## GitHub 使用说明

可以把本项目上传到 GitHub，但 GitHub Pages 不能直接运行完整系统。原因是本系统依赖 Python 后端和 MySQL 数据库，GitHub Pages 只能托管静态网页。

助教或其他同学如果要运行完整系统，需要把仓库拉到本地，然后按上面的步骤初始化 MySQL 数据库并运行 `python3 app.py`。

如果使用命令行上传到 GitHub，可以先在 GitHub 网站上新建一个空仓库，例如 `lab5-social-platform`，然后在本地执行：

```bash
cd /path/to/lab5
git init
git add schema.sql init_data.sql app.py frontend.html cli_app.py README.md 实验五报告.md lab5_er_first_layout_text_only_final.png .gitignore
git commit -m "Add lab5 social platform project"
git branch -M main
git remote add origin https://github.com/你的用户名/lab5-social-platform.git
git push -u origin main
```

如果使用 GitHub 网页上传，也只需要上传下面列出的项目文件，不要上传缓存文件。

建议上传的文件：

```text
schema.sql
init_data.sql
app.py
frontend.html
cli_app.py
README.md
实验五报告.md
lab5_er_first_layout_text_only_final.png
```

不要上传：

```text
.DS_Store
__pycache__/
*.pyc
```
