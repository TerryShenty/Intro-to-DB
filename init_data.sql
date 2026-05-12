-- Lab5 初始化测试数据
-- 用法：
--   先执行 schema.sql，再执行本文件。
--
-- 默认测试账号：
--   普通用户密码均为 123456
--   用户：Alice093427, Bob104582, Carol386915, David582731, Emma640298, Frank719463, Grace805217, Henry924680, Ivy137592, Jack468305
--   管理员：9001 / admin123

USE lab5_social_platform;

INSERT INTO users (user_id, password_hash, name, gender, birth_date, display_age, avatar_url, post_visible_period, created_at) VALUES
    ('Alice093427', SHA2('123456', 256), 'alice', '女', '2004-03-12', 22, 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', '6_months', '2026-05-01 09:00:00'),
    ('Bob104582', SHA2('123456', 256), 'bob', '男', '2003-08-20', 23, 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', '3_months', '2026-05-01 09:02:00'),
    ('Carol386915', SHA2('123456', 256), 'carol', '女', '2004-11-02', 21, 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', 'forever', '2026-05-01 09:04:00'),
    ('David582731', SHA2('123456', 256), 'david', '男', '2002-01-19', 24, 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', '7_days', '2026-05-01 09:06:00'),
    ('Emma640298', SHA2('123456', 256), 'emma', '女', '2005-06-08', 20, 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', '3_months', '2026-05-01 09:08:00'),
    ('Frank719463', SHA2('123456', 256), 'frank', '男', '2003-12-28', 22, 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', '6_months', '2026-05-01 09:10:00'),
    ('Grace805217', SHA2('123456', 256), 'grace', '女', '2004-09-14', 21, 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', 'forever', '2026-05-01 09:12:00'),
    ('Henry924680', SHA2('123456', 256), 'henry', '男', '2002-04-01', 24, 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', '3_months', '2026-05-01 09:14:00'),
    ('Ivy137592', SHA2('123456', 256), 'ivy', '女', '2005-02-23', 21, 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', '6_months', '2026-05-01 09:16:00'),
    ('Jack468305', SHA2('123456', 256), 'jack', '男', '2003-07-07', 22, 'https://images.unsplash.com/photo-1504257432389-52343af06ae3?auto=format&fit=crop&crop=faces&w=160&h=160&q=80', 'forever', '2026-05-01 09:18:00');

INSERT INTO admins (admin_id, password_hash, name, created_at) VALUES
    (9001, SHA2('admin123', 256), 'Admin Terry', '2026-05-01 08:30:00');

INSERT INTO friend_groups (group_id, owner_id, group_name, created_at) VALUES
    (1, 'Alice093427', 'Classmates', '2026-05-01 10:00:00'),
    (2, 'Alice093427', 'Close Friends', '2026-05-01 10:01:00'),
    (3, 'Bob104582', 'Dorm', '2026-05-01 10:02:00'),
    (4, 'Bob104582', 'Project Team', '2026-05-01 10:03:00'),
    (5, 'Carol386915', 'Study Group', '2026-05-01 10:04:00'),
    (6, 'Carol386915', 'Food Friends', '2026-05-01 10:05:00'),
    (7, 'David582731', 'Basketball', '2026-05-01 10:06:00'),
    (8, 'Emma640298', 'Lab Partners', '2026-05-01 10:07:00'),
    (9, 'Frank719463', 'Reading Club', '2026-05-01 10:08:00'),
    (10, 'Grace805217', 'Travel', '2026-05-01 10:09:00'),
    (11, 'Henry924680', 'Old Friends', '2026-05-01 10:10:00'),
    (12, 'Ivy137592', 'Design Team', '2026-05-01 10:11:00'),
    (13, 'Jack468305', 'Sports', '2026-05-01 10:12:00'),
    (14, 'Jack468305', 'Database Lab', '2026-05-01 10:13:00');

-- 好友申请：accepted 会生成双向好友；pending 会自动生成好友申请通知；rejected 后允许再次申请。
INSERT INTO friend_requests (request_id, requester_id, receiver_id, request_status, created_at, responded_at) VALUES
    (1, 'Alice093427', 'Bob104582', 'accepted', '2026-05-01 10:20:00', '2026-05-01 10:22:00'),
    (2, 'Alice093427', 'Carol386915', 'accepted', '2026-05-01 10:21:00', '2026-05-01 10:23:00'),
    (3, 'Alice093427', 'David582731', 'accepted', '2026-05-01 10:22:00', '2026-05-01 10:24:00'),
    (4, 'Bob104582', 'Emma640298', 'accepted', '2026-05-01 10:23:00', '2026-05-01 10:25:00'),
    (5, 'Carol386915', 'Frank719463', 'accepted', '2026-05-01 10:24:00', '2026-05-01 10:26:00'),
    (6, 'David582731', 'Grace805217', 'accepted', '2026-05-01 10:25:00', '2026-05-01 10:27:00'),
    (7, 'Emma640298', 'Ivy137592', 'accepted', '2026-05-01 10:26:00', '2026-05-01 10:28:00'),
    (8, 'Frank719463', 'Jack468305', 'accepted', '2026-05-01 10:27:00', '2026-05-01 10:29:00'),
    (9, 'Grace805217', 'Henry924680', 'accepted', '2026-05-01 10:28:00', '2026-05-01 10:30:00'),
    (10, 'Ivy137592', 'Alice093427', 'accepted', '2026-05-01 10:29:00', '2026-05-01 10:31:00'),
    (11, 'Jack468305', 'Bob104582', 'rejected', '2026-05-01 10:30:00', '2026-05-01 10:32:00'),
    (12, 'Jack468305', 'Bob104582', 'pending', '2026-05-01 10:40:00', NULL),
    (13, 'Henry924680', 'Alice093427', 'rejected', '2026-05-01 10:41:00', '2026-05-01 10:43:00'),
    (14, 'Carol386915', 'Ivy137592', 'pending', '2026-05-01 10:44:00', NULL);

-- 双向好友关系：每对好友两条记录。
INSERT INTO friendships (friendship_id, owner_id, friend_id, accepted_request_id, created_at) VALUES
    (1, 'Alice093427', 'Bob104582', 1, '2026-05-01 10:22:00'),
    (2, 'Bob104582', 'Alice093427', 1, '2026-05-01 10:22:00'),
    (3, 'Alice093427', 'Carol386915', 2, '2026-05-01 10:23:00'),
    (4, 'Carol386915', 'Alice093427', 2, '2026-05-01 10:23:00'),
    (5, 'Alice093427', 'David582731', 3, '2026-05-01 10:24:00'),
    (6, 'David582731', 'Alice093427', 3, '2026-05-01 10:24:00'),
    (7, 'Bob104582', 'Emma640298', 4, '2026-05-01 10:25:00'),
    (8, 'Emma640298', 'Bob104582', 4, '2026-05-01 10:25:00'),
    (9, 'Carol386915', 'Frank719463', 5, '2026-05-01 10:26:00'),
    (10, 'Frank719463', 'Carol386915', 5, '2026-05-01 10:26:00'),
    (11, 'David582731', 'Grace805217', 6, '2026-05-01 10:27:00'),
    (12, 'Grace805217', 'David582731', 6, '2026-05-01 10:27:00'),
    (13, 'Emma640298', 'Ivy137592', 7, '2026-05-01 10:28:00'),
    (14, 'Ivy137592', 'Emma640298', 7, '2026-05-01 10:28:00'),
    (15, 'Frank719463', 'Jack468305', 8, '2026-05-01 10:29:00'),
    (16, 'Jack468305', 'Frank719463', 8, '2026-05-01 10:29:00'),
    (17, 'Grace805217', 'Henry924680', 9, '2026-05-01 10:30:00'),
    (18, 'Henry924680', 'Grace805217', 9, '2026-05-01 10:30:00'),
    (19, 'Ivy137592', 'Alice093427', 10, '2026-05-01 10:31:00'),
    (20, 'Alice093427', 'Ivy137592', 10, '2026-05-01 10:31:00');

-- 好友分组归属：一个好友可以多个分组，也可以未分组。
INSERT INTO friend_group_memberships (owner_id, friend_id, group_id, created_at) VALUES
    ('Alice093427', 'Bob104582', 1, '2026-05-01 10:35:00'),
    ('Alice093427', 'Bob104582', 2, '2026-05-01 10:36:00'),
    ('Alice093427', 'Carol386915', 1, '2026-05-01 10:37:00'),
    ('Alice093427', 'Ivy137592', 2, '2026-05-01 10:38:00'),
    ('Bob104582', 'Alice093427', 3, '2026-05-01 10:39:00'),
    ('Bob104582', 'Emma640298', 4, '2026-05-01 10:40:00'),
    ('Carol386915', 'Alice093427', 5, '2026-05-01 10:41:00'),
    ('Carol386915', 'Frank719463', 6, '2026-05-01 10:42:00'),
    ('David582731', 'Grace805217', 7, '2026-05-01 10:43:00'),
    ('Emma640298', 'Bob104582', 8, '2026-05-01 10:44:00'),
    ('Emma640298', 'Ivy137592', 8, '2026-05-01 10:45:00'),
    ('Frank719463', 'Carol386915', 9, '2026-05-01 10:46:00'),
    ('Grace805217', 'David582731', 10, '2026-05-01 10:47:00'),
    ('Henry924680', 'Grace805217', 11, '2026-05-01 10:48:00'),
    ('Ivy137592', 'Alice093427', 12, '2026-05-01 10:49:00'),
    ('Jack468305', 'Frank719463', 13, '2026-05-01 10:50:00'),
    ('Jack468305', 'Frank719463', 14, '2026-05-01 10:51:00');

INSERT INTO posts (post_id, user_id, content, image_url, created_at, updated_at, post_status, visibility) VALUES
    (1, 'Alice093427', '周六早上去附近咖啡店坐了一会儿，窗边的位置很舒服。', 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80', '2026-05-02 09:00:00', '2026-05-02 09:00:00', 'visible', 'friends'),
    (2, 'Alice093427', '和同学约了晚饭，饭后沿着校园散步，风很舒服。', 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80', '2026-05-02 10:00:00', '2026-05-02 10:00:00', 'visible', 'groups'),
    (3, 'Alice093427', '给自己留个小目标：这个月保持早睡。', NULL, '2026-05-02 11:00:00', '2026-05-02 11:00:00', 'visible', 'self'),
    (4, 'Bob104582', '午饭吃了一碗热汤面，整个人都被治愈了。', 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=80', '2026-05-02 12:00:00', '2026-05-02 12:00:00', 'visible', 'friends'),
    (5, 'Bob104582', '项目组下午一起去买奶茶，顺便把周末计划定了。', NULL, '2026-05-02 13:00:00', '2026-05-02 13:00:00', 'visible', 'groups'),
    (6, 'Carol386915', '晚上在图书馆看完一本小说，回宿舍路上月亮很亮。', 'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=900&q=80', '2026-05-02 18:30:00', '2026-05-02 18:30:00', 'visible', 'friends'),
    (7, 'Carol386915', '只给 alice 看：这家甜品店下次一起去。', NULL, '2026-05-02 19:10:00', '2026-05-02 19:10:00', 'visible', 'selected'),
    (8, 'David582731', '傍晚去操场跑了几圈，夕阳很好看。', 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=900&q=80', '2026-05-03 17:30:00', '2026-05-03 17:30:00', 'visible', 'friends'),
    (9, 'David582731', '这条内容被管理员屏蔽，用来演示审核功能。', NULL, '2026-05-03 18:00:00', '2026-05-03 18:30:00', 'blocked', 'friends'),
    (10, 'Emma640298', '周日整理房间，换了新的床单，心情一下变好。', 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80', '2026-05-04 09:20:00', '2026-05-04 09:20:00', 'visible', 'friends'),
    (11, 'Emma640298', '只给 bob 和 ivy 看：明天一起去看展吗？', NULL, '2026-05-04 10:30:00', '2026-05-04 10:30:00', 'visible', 'selected'),
    (12, 'Frank719463', '午后在小公园晒太阳，听了一会儿播客。', 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=80', '2026-05-04 12:20:00', '2026-05-04 12:20:00', 'visible', 'friends'),
    (13, 'Frank719463', '阅读小组今晚聊了一本短篇集，大家推荐都很有趣。', NULL, '2026-05-04 20:00:00', '2026-05-04 20:00:00', 'visible', 'groups'),
    (14, 'Grace805217', '下课后去江边走了走，风景很安静。', 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=900&q=80', '2026-05-05 18:45:00', '2026-05-05 18:45:00', 'visible', 'friends'),
    (15, 'Henry924680', '今天在家做了简单的早餐，煎蛋刚刚好。', 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=900&q=80', '2026-05-05 21:00:00', '2026-05-05 21:00:00', 'visible', 'friends'),
    (16, 'Ivy137592', '和朋友去看了新展，颜色和灯光都很漂亮。', 'https://images.unsplash.com/photo-1518998053901-5348d3961a04?auto=format&fit=crop&w=900&q=80', '2026-05-06 09:10:00', '2026-05-06 09:10:00', 'visible', 'friends'),
    (17, 'Jack468305', '运动后买了杯冰美式，感觉整个人都醒了。', 'https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=900&q=80', '2026-05-06 16:00:00', '2026-05-06 16:00:00', 'visible', 'friends'),
    (18, 'Jack468305', '只给 frank 看：周末篮球场见。', NULL, '2026-05-06 16:40:00', '2026-05-06 16:40:00', 'visible', 'selected');

INSERT INTO post_visible_groups (post_id, owner_id, group_id) VALUES
    (2, 'Alice093427', 1),
    (5, 'Bob104582', 4),
    (13, 'Frank719463', 9);

INSERT INTO post_visible_users (post_id, owner_id, viewer_id) VALUES
    (7, 'Carol386915', 'Alice093427'),
    (11, 'Emma640298', 'Bob104582'),
    (11, 'Emma640298', 'Ivy137592'),
    (18, 'Jack468305', 'Frank719463');

INSERT INTO comments (comment_id, post_id, user_id, content, created_at) VALUES
    (1, 1, 'Bob104582', '这家咖啡看起来不错。', '2026-05-02 09:20:00'),
    (2, 1, 'Carol386915', '窗边座位真的很适合放空。', '2026-05-02 09:30:00'),
    (3, 2, 'Bob104582', '下次散步叫我。', '2026-05-02 10:20:00'),
    (4, 4, 'Alice093427', '看起来太香了。', '2026-05-02 12:15:00'),
    (5, 4, 'Emma640298', '深夜看到会饿。', '2026-05-02 12:40:00'),
    (6, 5, 'Emma640298', '奶茶我投芋泥。', '2026-05-02 13:30:00'),
    (7, 6, 'Alice093427', '小说名字发我一下。', '2026-05-02 18:45:00'),
    (8, 7, 'Alice093427', '甜品店收藏了。', '2026-05-02 19:30:00'),
    (9, 8, 'Alice093427', '夕阳这张很好看。', '2026-05-03 18:00:00'),
    (10, 8, 'Grace805217', '跑完步很舒服。', '2026-05-03 18:10:00'),
    (11, 10, 'Bob104582', '整理房间真的有成就感。', '2026-05-04 09:40:00'),
    (12, 10, 'Ivy137592', '这颜色好温柔。', '2026-05-04 10:00:00'),
    (13, 11, 'Ivy137592', '可以，明天我有空。', '2026-05-04 10:45:00'),
    (14, 12, 'Carol386915', '公园晒太阳很治愈。', '2026-05-04 12:40:00'),
    (15, 12, 'Jack468305', '这个角落看起来很安静。', '2026-05-04 13:00:00'),
    (16, 13, 'Carol386915', '这本我也想看。', '2026-05-04 20:30:00'),
    (17, 14, 'David582731', '江边散步好舒服。', '2026-05-05 19:00:00'),
    (18, 14, 'Henry924680', '这张很有夏天的感觉。', '2026-05-05 19:10:00'),
    (19, 16, 'Alice093427', '展览名字发我。', '2026-05-06 09:40:00'),
    (20, 18, 'Frank719463', '周末见，记得带球。', '2026-05-06 17:00:00');

-- 插入审核日志后，trg_audit_logs_after_insert 会自动给 david 生成通知。
INSERT INTO audit_logs (log_id, admin_id, target_post_id, target_user_id, action, content_snapshot, action_time) VALUES
    (1, 9001, 9, 'David582731', 'BLOCK_POST', '这条内容被管理员屏蔽，用来演示审核功能。', '2026-05-03 18:30:00');
