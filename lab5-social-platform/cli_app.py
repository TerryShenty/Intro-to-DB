#!/usr/bin/env python3
"""
Lab5 minimal command-line interface.

This file intentionally reuses the database functions in app.py.
It is a thin menu layer: input -> app.py function -> MySQL changes.
"""

from getpass import getpass

import app as db


def ask(prompt, default=""):
    suffix = f" [{default}]" if default not in (None, "") else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def pause():
    input("\n按回车继续...")


def print_rows(rows, columns=None):
    if not rows:
        print("暂无数据")
        return
    columns = columns or list(rows[0].keys())
    widths = {col: min(max(len(str(col)), *(len(str(row.get(col, ""))) for row in rows)), 28) for col in columns}
    header = " | ".join(str(col).ljust(widths[col]) for col in columns)
    print(header)
    print("-" * len(header))
    for row in rows:
        values = []
        for col in columns:
            text = str(row.get(col, ""))
            if len(text) > widths[col]:
                text = text[: widths[col] - 1] + "..."
            values.append(text.ljust(widths[col]))
        print(" | ".join(values))


def choose_one(rows, title, label_func):
    if not rows:
        print(f"{title}：暂无可选项")
        return None
    print(f"\n{title}")
    for i, row in enumerate(rows, 1):
        print(f"{i}. {label_func(row)}")
    raw = ask("输入编号，留空取消")
    if not raw:
        return None
    idx = int(raw)
    if idx < 1 or idx > len(rows):
        raise ValueError("编号不合法")
    return rows[idx - 1]


def choose_many(rows, title, label_func):
    if not rows:
        print(f"{title}：暂无可选项")
        return []
    print(f"\n{title}")
    for i, row in enumerate(rows, 1):
        print(f"{i}. {label_func(row)}")
    raw = ask("输入编号，可用逗号多选，留空取消")
    if not raw:
        return []
    result = []
    for item in raw.split(","):
        idx = int(item.strip())
        if idx < 1 or idx > len(rows):
            raise ValueError("编号不合法")
        result.append(rows[idx - 1])
    return result


def print_posts(posts):
    if not posts:
        print("暂无朋友圈")
        return
    for post in posts:
        author = post.get("author_name") or post.get("user_id") or post.get("owner_id") or post.get("author_id")
        print(f"\nPost #{post.get('post_id')} | {author} | {post.get('post_status')} | {post.get('visibility')}")
        print(f"创建: {post.get('created_at')}  更新: {post.get('updated_at')}")
        print(post.get("content", ""))
        if post.get("image_url"):
            print(f"图片: {post.get('image_url')}")
        if post.get("comment_count") is not None:
            print(f"评论数: {post.get('comment_count')}")


def show_comments_for(post_ids):
    if not post_ids:
        return
    rows = db.comments_for_posts(",".join(str(post_id) for post_id in post_ids))
    if not rows:
        print("\n暂无评论")
        return
    print("\n评论：")
    for row in rows:
        print(f"- Post #{row['post_id']} {row['user_name']}({row['user_id']}): {row['content']} [{row['created_at']}]")


def register_user_flow():
    user_id = ask("设置 user_id（英文开头，可含字母数字下划线）")
    password = getpass("设置初始密码: ")
    name = ask("昵称", user_id)
    db.register_user({"user_id": user_id, "password": password, "name": name})
    print("注册成功")
    return user_id


def login_user_flow():
    user_id = ask("user_id")
    password = getpass("密码: ")
    db.login_user({"user_id": user_id, "password": password})
    print("登录成功")
    return user_id


def update_profile_flow(user_id):
    profile = db.user_profile(user_id)["row"]
    print_rows([profile], ["user_id", "name", "gender", "birth_date", "display_age", "avatar_url", "post_visible_period"])
    data = {
        "user_id": user_id,
        "name": ask("昵称", profile.get("name") or ""),
        "gender": ask("性别（男/女/其他）", profile.get("gender") or "其他"),
        "birth_date": ask("出生日期 YYYY-MM-DD", profile.get("birth_date") or ""),
        "display_age": ask("展示年龄", profile.get("display_age") or ""),
        "avatar_url": ask("头像 URL", profile.get("avatar_url") or ""),
        "post_visible_period": ask("朋友圈可见时长 7_days/3_months/6_months/forever", profile.get("post_visible_period") or "3_months"),
    }
    db.update_user(data)
    print("资料已更新")


def search_and_request_flow(user_id):
    keyword = ask("搜索账号或昵称")
    rows = [row for row in db.users(keyword) if row["user_id"] != user_id]
    print_rows(rows, ["user_id", "name", "gender", "display_age", "post_visible_period"])
    target = ask("输入要申请添加的 user_id，留空返回")
    if target:
        db.send_friend_request({"requester_id": user_id, "receiver_id": target})
        print("好友申请已发送，对方会收到通知")


def request_flow(user_id):
    data = db.requests(user_id)
    print("\n收到的申请：")
    print_rows(data["received"], ["request_id", "requester_id", "request_status", "created_at", "responded_at"])
    print("\n发出的申请：")
    print_rows(data["sent"], ["request_id", "receiver_id", "request_status", "created_at", "responded_at"])
    pending = [row for row in data["received"] if row["request_status"] == "pending"]
    row = choose_one(pending, "选择要处理的待处理申请", lambda r: f"{r['request_id']} - {r['requester_id']}")
    if not row:
        return
    action = ask("accept 接受 / reject 拒绝", "accept")
    db.respond_friend_request({"request_id": row["request_id"], "user_id": user_id, "action": action})
    print("好友申请已处理")


def friend_group_flow(user_id):
    while True:
        print("\n好友与分组")
        print("1. 查看好友")
        print("2. 创建分组")
        print("3. 好友加入分组")
        print("4. 好友移出分组")
        print("5. 删除好友")
        print("0. 返回")
        choice = ask("请选择")
        if choice == "0":
            return
        friends = db.friends(user_id)
        groups = db.groups(user_id)
        if choice == "1":
            print_rows(friends, ["friend_id", "name", "gender", "display_age", "group_names"])
        elif choice == "2":
            group_name = ask("新分组名")
            db.create_group({"owner_id": user_id, "group_name": group_name})
            print("分组已创建")
        elif choice in {"3", "4"}:
            friend = choose_one(friends, "选择好友", lambda f: f"{f['name']} ({f['friend_id']})")
            group = choose_one(groups, "选择分组", lambda g: f"{g['group_name']} (group_id={g['group_id']})")
            if friend and group:
                db.update_group_membership({
                    "owner_id": user_id,
                    "friend_id": friend["friend_id"],
                    "group_id": group["group_id"],
                    "action": "add" if choice == "3" else "remove",
                })
                print("分组关系已更新")
        elif choice == "5":
            friend = choose_one(friends, "选择要删除的好友", lambda f: f"{f['name']} ({f['friend_id']})")
            if friend and ask("确认删除？yes/no", "no") == "yes":
                db.delete_friend({"user_id": user_id, "friend_id": friend["friend_id"]})
                print("好友已删除，双方好友关系都会删除")


def view_friend_posts_flow(user_id):
    rows = db.posts(user_id, "friend")
    print_posts(rows)
    show_comments_for([row["post_id"] for row in rows])
    post_id = ask("输入要评论的 post_id，留空返回")
    if post_id:
        content = ask("评论内容")
        db.add_comment({"post_id": post_id, "user_id": user_id, "content": content})
        print("评论已发布，相关通知由触发器自动生成")


def create_post_flow(user_id):
    content = ask("朋友圈内容（最多 500 字）")
    image_url = ask("图片 URL，可为空")
    print("可见范围：1 全部好友  2 指定分组  3 指定好友  4 仅自己")
    choice = ask("请选择", "1")
    visibility_map = {"1": "friends", "2": "groups", "3": "selected", "4": "self"}
    visibility = visibility_map.get(choice, "friends")
    group_ids = ""
    viewer_ids = ""
    if visibility == "groups":
        selected = choose_many(db.groups(user_id), "选择可见分组", lambda g: f"{g['group_name']} (group_id={g['group_id']})")
        group_ids = ",".join(row["group_id"] for row in selected)
    elif visibility == "selected":
        selected = choose_many(db.friends(user_id), "选择可见好友", lambda f: f"{f['name']} ({f['friend_id']})")
        viewer_ids = ",".join(row["friend_id"] for row in selected)
    db.create_post({
        "user_id": user_id,
        "content": content,
        "image_url": image_url,
        "visibility": visibility,
        "group_ids": group_ids,
        "viewer_ids": viewer_ids,
    })
    print("朋友圈已发表")


def manage_own_posts_flow(user_id):
    rows = db.posts(user_id, "own")
    print_posts(rows)
    show_comments_for([row["post_id"] for row in rows])
    print("\n1. 修改朋友圈  2. 删除朋友圈  0. 返回")
    choice = ask("请选择")
    if choice == "1":
        post_id = ask("post_id")
        content = ask("新的内容")
        db.update_post({"user_id": user_id, "post_id": post_id, "content": content})
        print("朋友圈已修改，updated_at 由触发器自动更新")
    elif choice == "2":
        post_id = ask("post_id")
        if ask("确认删除？yes/no", "no") == "yes":
            db.delete_post({"user_id": user_id, "post_id": post_id})
            print("朋友圈已删除，相关评论会由外键级联删除")


def notification_flow(user_id):
    rows = db.notifications(user_id)
    unread = [row for row in rows if str(row["is_read"]) == "0"]
    print(f"未读通知数：{len(unread)}")
    print_rows(rows, ["notification_id", "is_read", "notification_type", "message", "created_at"])
    notification_id = ask("输入要标记已读的 notification_id，留空返回")
    if notification_id:
        db.mark_notification_read({"notification_id": notification_id})
        print("通知已标记为已读")


def view_check_flow(user_id):
    options = ["friend_profile_view", "friend_post_view", "own_post_view", "post_preview_view", "user_notification_view"]
    for i, name in enumerate(options, 1):
        print(f"{i}. {name}")
    idx = int(ask("选择视图", "1"))
    rows = db.raw_view(options[idx - 1], user_id)
    print_rows(rows)


def user_menu(user_id):
    while True:
        print(f"\n用户端：{user_id}")
        print("1. 修改个人资料")
        print("2. 搜索用户并发送好友申请")
        print("3. 处理好友申请")
        print("4. 好友与分组管理")
        print("5. 查看好友朋友圈并评论")
        print("6. 发表朋友圈")
        print("7. 修改/删除自己的朋友圈")
        print("8. 通知")
        print("9. 验收视图")
        print("0. 退出登录")
        choice = ask("请选择")
        try:
            if choice == "0":
                return
            if choice == "1":
                update_profile_flow(user_id)
            elif choice == "2":
                search_and_request_flow(user_id)
            elif choice == "3":
                request_flow(user_id)
            elif choice == "4":
                friend_group_flow(user_id)
            elif choice == "5":
                view_friend_posts_flow(user_id)
            elif choice == "6":
                create_post_flow(user_id)
            elif choice == "7":
                manage_own_posts_flow(user_id)
            elif choice == "8":
                notification_flow(user_id)
            elif choice == "9":
                view_check_flow(user_id)
        except Exception as exc:
            print(f"操作失败：{exc}")
        pause()


def login_admin_flow():
    admin_id = ask("管理员 ID")
    password = getpass("密码: ")
    db.login_admin({"admin_id": admin_id, "password": password})
    print("管理员登录成功")
    return admin_id


def update_admin_flow(admin_id):
    name = ask("新的管理员昵称")
    db.update_admin({"admin_id": admin_id, "name": name})
    print("管理员资料已更新")


def admin_review_flow(admin_id):
    rows = db.raw_view("admin_post_view", admin_id)
    print_rows(rows, ["post_id", "user_id", "content", "post_status", "visibility", "created_at", "updated_at"])
    post_id = ask("输入要审核的 post_id，留空返回")
    if not post_id:
        return
    print("1. 审核删除/屏蔽  2. 恢复可见")
    choice = ask("请选择", "1")
    db.admin_set_post_status({"admin_id": admin_id, "post_id": post_id}, "blocked" if choice == "1" else "visible")
    print("审核状态已更新，并写入 audit_logs；通知由触发器生成")


def admin_delete_user_flow(admin_id):
    target_user_id = ask("要注销的 user_id")
    if ask("确认注销？yes/no", "no") == "yes":
        db.admin_delete_user({"admin_id": admin_id, "target_user_id": target_user_id})
        print("用户已注销，相关信息由外键级联删除")


def admin_view_check_flow(admin_id):
    rows = db.raw_view("admin_post_view", admin_id)
    print_rows(rows)


def admin_menu(admin_id):
    while True:
        print(f"\n管理员端：{admin_id}")
        print("1. 修改管理员资料")
        print("2. 浏览/审核所有朋友圈")
        print("3. 注销用户")
        print("4. 验收视图 admin_post_view")
        print("0. 退出登录")
        choice = ask("请选择")
        try:
            if choice == "0":
                return
            if choice == "1":
                update_admin_flow(admin_id)
            elif choice == "2":
                admin_review_flow(admin_id)
            elif choice == "3":
                admin_delete_user_flow(admin_id)
            elif choice == "4":
                admin_view_check_flow(admin_id)
        except Exception as exc:
            print(f"操作失败：{exc}")
        pause()


def main():
    while True:
        print("\nLab5 简易朋友圈系统（命令行版）")
        print("1. 用户登录")
        print("2. 用户注册")
        print("3. 管理员登录")
        print("0. 退出")
        choice = ask("请选择")
        try:
            if choice == "0":
                break
            if choice == "1":
                user_menu(login_user_flow())
            elif choice == "2":
                user_menu(register_user_flow())
            elif choice == "3":
                admin_menu(login_admin_flow())
        except Exception as exc:
            print(f"操作失败：{exc}")
            pause()


if __name__ == "__main__":
    main()
