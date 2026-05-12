-- Lab5 数据库应用开发大作业：简易朋友圈系统
-- 用法：
--   1. 在 MySQL 中执行本文件，创建数据库、表、视图和触发器。
--   2. 再执行 init_data.sql，插入初始化测试数据。


CREATE DATABASE IF NOT EXISTS lab5_social_platform
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE lab5_social_platform;

DROP VIEW IF EXISTS post_preview_view;
DROP VIEW IF EXISTS own_post_view;
DROP VIEW IF EXISTS friend_post_view;
DROP VIEW IF EXISTS friend_profile_view;
DROP VIEW IF EXISTS user_notification_view;
DROP VIEW IF EXISTS admin_post_view;

DROP TRIGGER IF EXISTS trg_audit_logs_after_insert;
DROP TRIGGER IF EXISTS trg_comments_after_insert;
DROP TRIGGER IF EXISTS trg_friend_requests_after_update;
DROP TRIGGER IF EXISTS trg_friend_requests_after_insert;
DROP TRIGGER IF EXISTS trg_posts_before_update;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS post_visible_users;
DROP TABLE IF EXISTS post_visible_groups;
DROP TABLE IF EXISTS friend_group_memberships;
DROP TABLE IF EXISTS friendships;
DROP TABLE IF EXISTS friend_requests;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS friend_groups;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- 普通用户表
CREATE TABLE users (
    -- user_id 是用户注册时自己设置的账号名，不是系统自增编号。
    -- 规则：3-30 位，以英文字母开头，只能包含英文字母、数字和下划线。
    user_id VARCHAR(30) PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    -- name 是公开展示昵称，不要求唯一。
    name VARCHAR(50),
    gender ENUM('男', '女', '其他'),
    birth_date DATE,
    -- display_age 是用户自己填写的公开展示年龄；birth_date 不对好友公开。
    display_age INT,
    avatar_url VARCHAR(255),
    -- 用户设置自己的朋友圈对好友可见多久；自己和管理员查看时不受该设置影响。
    post_visible_period ENUM('7_days', '3_months', '6_months', 'forever') NOT NULL DEFAULT '3_months',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_users_id_format CHECK (user_id REGEXP '^[A-Za-z][A-Za-z0-9_]{2,29}$'),
    CONSTRAINT chk_users_display_age CHECK (display_age IS NULL OR (display_age >= 0 AND display_age <= 150))
) ENGINE = InnoDB;

-- 管理员表
CREATE TABLE admins (
    admin_id INT PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(50),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB;

-- 好友分组表：每个用户可以拥有多个自己的好友分组
CREATE TABLE friend_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id VARCHAR(30) NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_friend_groups_owner_name UNIQUE (owner_id, group_name),
    CONSTRAINT uk_friend_groups_owner_group UNIQUE (owner_id, group_id),
    CONSTRAINT fk_friend_groups_owner
        FOREIGN KEY (owner_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 朋友圈表
CREATE TABLE posts (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(30) NOT NULL,
    content VARCHAR(500) NOT NULL,
    -- 只支持一张图片；这里保存图片路径或 URL，不直接保存图片二进制内容。
    image_url VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- post_status 是管理员审核状态；blocked 表示管理员审核后屏蔽，和用户自己设置“仅自己可见”不同。
    post_status ENUM('visible', 'blocked') NOT NULL DEFAULT 'visible',
    -- visibility 是用户自己设置的可见范围。
    -- friends: 全部好友可见；groups: 指定分组可见；selected: 指定好友可见；self: 仅自己可见。
    visibility ENUM('friends', 'groups', 'selected', 'self') NOT NULL DEFAULT 'friends',
    CONSTRAINT uk_posts_post_user UNIQUE (post_id, user_id),
    CONSTRAINT chk_posts_content CHECK (CHAR_LENGTH(content) > 0 AND CHAR_LENGTH(content) <= 500),
    CONSTRAINT fk_posts_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 好友申请表
-- 一方发起申请，另一方可以同意或拒绝；拒绝后允许重新申请，因此不对历史申请做唯一约束。
-- 程序中发起申请时，应先检查两人是否已经是好友，以及是否已有 pending 状态的申请。
CREATE TABLE friend_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    requester_id VARCHAR(30) NOT NULL,
    receiver_id VARCHAR(30) NOT NULL,
    request_status ENUM('pending', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME,
    CONSTRAINT fk_friend_requests_requester
        FOREIGN KEY (requester_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_friend_requests_receiver
        FOREIGN KEY (receiver_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 好友关系表
-- 好友关系是双向的，但在表中按“每个人自己的好友列表”存两条记录：
--   A 和 B 成为好友后，插入 A -> B 与 B -> A 两条记录。
--   删除好友时，程序应在事务中同时删除这两条记录。
CREATE TABLE friendships (
    friendship_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id VARCHAR(30) NOT NULL,
    friend_id VARCHAR(30) NOT NULL,
    accepted_request_id INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_friendships_owner_friend UNIQUE (owner_id, friend_id),
    CONSTRAINT fk_friendships_owner
        FOREIGN KEY (owner_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_friendships_friend
        FOREIGN KEY (friend_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_friendships_request
        FOREIGN KEY (accepted_request_id) REFERENCES friend_requests(request_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 好友分组归属表
-- 一个好友可以被放入多个分组，也可以不属于任何分组。
-- 分组只对 owner_id 自己有效，A 给 B 的分组和 B 给 A 的分组互不影响。
CREATE TABLE friend_group_memberships (
    owner_id VARCHAR(30) NOT NULL,
    friend_id VARCHAR(30) NOT NULL,
    group_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (owner_id, friend_id, group_id),
    CONSTRAINT fk_friend_group_memberships_friendship
        FOREIGN KEY (owner_id, friend_id) REFERENCES friendships(owner_id, friend_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_friend_group_memberships_group
        FOREIGN KEY (owner_id, group_id) REFERENCES friend_groups(owner_id, group_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 朋友圈指定分组可见表
-- 当 posts.visibility = 'groups' 时，用本表记录这条朋友圈对作者的哪些好友分组可见。
CREATE TABLE post_visible_groups (
    post_id INT NOT NULL,
    owner_id VARCHAR(30) NOT NULL,
    group_id INT NOT NULL,
    PRIMARY KEY (post_id, group_id),
    CONSTRAINT fk_post_visible_groups_post_owner
        FOREIGN KEY (post_id, owner_id) REFERENCES posts(post_id, user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_post_visible_groups_group
        FOREIGN KEY (owner_id, group_id) REFERENCES friend_groups(owner_id, group_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 朋友圈指定好友可见表
-- 当 posts.visibility = 'selected' 时，用本表记录这条朋友圈对作者的哪些好友可见。
CREATE TABLE post_visible_users (
    post_id INT NOT NULL,
    owner_id VARCHAR(30) NOT NULL,
    viewer_id VARCHAR(30) NOT NULL,
    PRIMARY KEY (post_id, viewer_id),
    CONSTRAINT fk_post_visible_users_post_owner
        FOREIGN KEY (post_id, owner_id) REFERENCES posts(post_id, user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_post_visible_users_friend
        FOREIGN KEY (owner_id, viewer_id) REFERENCES friendships(owner_id, friend_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 评论表
CREATE TABLE comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id VARCHAR(30) NOT NULL,
    content VARCHAR(300) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_comments_content CHECK (CHAR_LENGTH(content) > 0 AND CHAR_LENGTH(content) <= 300),
    CONSTRAINT fk_comments_post
        FOREIGN KEY (post_id) REFERENCES posts(post_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 用户通知表
-- 用于保存好友申请、好友申请处理结果、朋友圈评论、管理员审核等通知。
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_user_id VARCHAR(30) NOT NULL,
    actor_user_id VARCHAR(30),
    related_post_id INT,
    related_comment_id INT,
    related_request_id INT,
    notification_type ENUM(
        'FRIEND_REQUEST',
        'FRIEND_REQUEST_ACCEPTED',
        'FRIEND_REQUEST_REJECTED',
        'POST_COMMENT',
        'POST_BLOCKED',
        'POST_UNBLOCKED'
    ) NOT NULL,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notifications_recipient
        FOREIGN KEY (recipient_user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_actor
        FOREIGN KEY (actor_user_id) REFERENCES users(user_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_comment
        FOREIGN KEY (related_comment_id) REFERENCES comments(comment_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_request
        FOREIGN KEY (related_request_id) REFERENCES friend_requests(request_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 审核日志表
-- target_post_id 和 target_user_id 不强制设置外键，是为了在朋友圈或用户被删除后仍然保留历史日志。
CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    target_post_id INT,
    target_user_id VARCHAR(30),
    action ENUM('BLOCK_POST', 'UNBLOCK_POST', 'DELETE_USER') NOT NULL,
    content_snapshot TEXT,
    action_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_logs_admin
        FOREIGN KEY (admin_id) REFERENCES admins(admin_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 管理员审核朋友圈时使用的视图
-- 注意：该视图只展示朋友圈信息和 user_id，不展示用户姓名、性别、生日等个人基本信息。
CREATE VIEW admin_post_view AS
SELECT
    post_id,
    user_id,
    content,
    image_url,
    created_at,
    updated_at,
    post_status,
    visibility
FROM posts;

-- 用户查看好友资料时使用的视图
-- 好友可以看到账号、昵称、性别、展示年龄、头像和分组名，但不能看到生日、密码等隐私字段。
CREATE VIEW friend_profile_view AS
SELECT
    f.owner_id AS viewer_id,
    f.friend_id,
    u.name,
    u.gender,
    u.display_age,
    u.avatar_url,
    COALESCE(GROUP_CONCAT(fg.group_name ORDER BY fg.group_name SEPARATOR ', '), '未分组') AS group_names,
    f.created_at AS friendship_created_at
FROM friendships AS f
JOIN users AS u
    ON f.friend_id = u.user_id
LEFT JOIN friend_group_memberships AS fgm
    ON f.owner_id = fgm.owner_id
   AND f.friend_id = fgm.friend_id
LEFT JOIN friend_groups AS fg
    ON fgm.group_id = fg.group_id
GROUP BY
    f.owner_id,
    f.friend_id,
    u.name,
    u.gender,
    u.display_age,
    u.avatar_url,
    f.created_at;

-- 用户查看好友朋友圈时使用的视图
-- viewer_id 表示正在查看朋友圈的用户；author_id 表示朋友圈发布者。
-- 该视图遵守作者设置的可见范围和作者设置的可见时长。
CREATE VIEW friend_post_view AS
SELECT
    f.friend_id AS viewer_id,
    p.post_id,
    f.owner_id AS author_id,
    u.name AS author_name,
    u.gender AS author_gender,
    u.display_age AS author_display_age,
    u.avatar_url AS author_avatar_url,
    p.content,
    p.image_url,
    p.created_at,
    p.updated_at,
    p.post_status,
    p.visibility
FROM friendships AS f
JOIN posts AS p
    ON f.owner_id = p.user_id
JOIN users AS u
    ON p.user_id = u.user_id
WHERE p.post_status = 'visible'
  AND (
      u.post_visible_period = 'forever'
      OR (u.post_visible_period = '7_days' AND p.created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY))
      OR (u.post_visible_period = '3_months' AND p.created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 3 MONTH))
      OR (u.post_visible_period = '6_months' AND p.created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH))
  )
  AND (
      p.visibility = 'friends'
      OR (
          p.visibility = 'groups'
          AND EXISTS (
              SELECT 1
              FROM post_visible_groups AS pvg
              JOIN friend_group_memberships AS fgm
                ON pvg.group_id = fgm.group_id
               AND fgm.owner_id = f.owner_id
               AND fgm.friend_id = f.friend_id
              WHERE pvg.post_id = p.post_id
                AND pvg.owner_id = f.owner_id
          )
      )
      OR (
          p.visibility = 'selected'
          AND EXISTS (
              SELECT 1
              FROM post_visible_users AS pvu
              WHERE pvu.post_id = p.post_id
                AND pvu.owner_id = f.owner_id
                AND pvu.viewer_id = f.friend_id
          )
      )
  );

-- 用户查看自己朋友圈时使用的视图
-- 自己可以看到所有状态的朋友圈，包括仅自己可见和被管理员屏蔽的朋友圈。
CREATE VIEW own_post_view AS
SELECT
    p.user_id AS owner_id,
    p.post_id,
    p.content,
    p.image_url,
    p.created_at,
    p.updated_at,
    p.post_status,
    p.visibility,
    CASE
        WHEN p.post_status = 'blocked' THEN '管理员已屏蔽，仅本人和管理员可见'
        WHEN p.visibility = 'self' THEN '仅自己可见'
        WHEN p.visibility = 'groups' THEN '指定分组可见'
        WHEN p.visibility = 'selected' THEN '指定好友可见'
        ELSE '全部好友可见'
    END AS visibility_note
FROM posts AS p;

-- 添加好友时的朋友圈预览视图
-- 预览规则固定为最近 3 个月，不受用户 post_visible_period 设置影响。
-- 预览只展示作者设置为“全部好友可见”的正常朋友圈，不展示分组、指定好友或仅自己可见内容。
CREATE VIEW post_preview_view AS
SELECT
    p.user_id AS target_user_id,
    u.name,
    u.gender,
    u.display_age,
    u.avatar_url,
    p.post_id,
    p.content,
    p.image_url,
    p.created_at,
    p.updated_at
FROM posts AS p
JOIN users AS u
    ON p.user_id = u.user_id
WHERE p.post_status = 'visible'
  AND p.visibility = 'friends'
  AND p.created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 3 MONTH);

-- 用户通知视图
-- Python 菜单可以直接按 recipient_user_id 查询该视图来展示通知列表。
CREATE VIEW user_notification_view AS
SELECT
    n.notification_id,
    n.recipient_user_id,
    n.notification_type,
    n.actor_user_id,
    COALESCE(actor.name, n.actor_user_id) AS actor_name,
    n.related_post_id,
    n.related_comment_id,
    n.related_request_id,
    fr.request_status,
    n.message,
    n.is_read,
    n.created_at
FROM notifications AS n
LEFT JOIN users AS actor
    ON n.actor_user_id = actor.user_id
LEFT JOIN friend_requests AS fr
    ON n.related_request_id = fr.request_id;

DELIMITER //

-- 触发器：修改朋友圈内容、图片、状态或可见范围时，自动刷新最后更新时间。
CREATE TRIGGER trg_posts_before_update
BEFORE UPDATE ON posts
FOR EACH ROW
BEGIN
    IF NOT (NEW.content <=> OLD.content)
       OR NOT (NEW.image_url <=> OLD.image_url)
       OR NEW.post_status <> OLD.post_status
       OR NEW.visibility <> OLD.visibility THEN
        SET NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
END//

-- 触发器：发起好友申请后，自动通知接收方去接受或拒绝。
CREATE TRIGGER trg_friend_requests_after_insert
AFTER INSERT ON friend_requests
FOR EACH ROW
BEGIN
    IF NEW.request_status = 'pending' THEN
        INSERT INTO notifications (
            recipient_user_id,
            actor_user_id,
            related_request_id,
            notification_type,
            message
        ) VALUES (
            NEW.receiver_id,
            NEW.requester_id,
            NEW.request_id,
            'FRIEND_REQUEST',
            CONCAT(
                (SELECT COALESCE(name, user_id) FROM users WHERE user_id = NEW.requester_id),
                '申请添加你为好友，请选择接受或拒绝。'
            )
        );
    END IF;
END//

-- 触发器：好友申请被接受或拒绝后，自动通知申请发起方。
-- 只有状态从 pending 变成 accepted/rejected 时才发通知，避免重复更新造成重复通知。
CREATE TRIGGER trg_friend_requests_after_update
AFTER UPDATE ON friend_requests
FOR EACH ROW
BEGIN
    IF OLD.request_status = 'pending'
       AND NEW.request_status IN ('accepted', 'rejected')
       AND OLD.request_status <> NEW.request_status THEN
        INSERT INTO notifications (
            recipient_user_id,
            actor_user_id,
            related_request_id,
            notification_type,
            message
        ) VALUES (
            NEW.requester_id,
            NEW.receiver_id,
            NEW.request_id,
            IF(NEW.request_status = 'accepted', 'FRIEND_REQUEST_ACCEPTED', 'FRIEND_REQUEST_REJECTED'),
            CONCAT(
                (SELECT COALESCE(name, user_id) FROM users WHERE user_id = NEW.receiver_id),
                IF(NEW.request_status = 'accepted', '已接受你的好友申请。', '已拒绝你的好友申请。')
            )
        );
    END IF;
END//

-- 触发器：新增评论后，自动通知能看到该朋友圈的用户和朋友圈作者。
-- 通知范围 = 朋友圈作者本人 + friend_post_view 中能看到这条朋友圈的用户，排除评论者自己。
CREATE TRIGGER trg_comments_after_insert
AFTER INSERT ON comments
FOR EACH ROW
BEGIN
    DECLARE v_author_id VARCHAR(30);
    DECLARE v_author_name VARCHAR(50);
    DECLARE v_commenter_name VARCHAR(50);

    SELECT p.user_id, COALESCE(u.name, u.user_id)
    INTO v_author_id, v_author_name
    FROM posts AS p
    JOIN users AS u
        ON p.user_id = u.user_id
    WHERE p.post_id = NEW.post_id;

    SELECT COALESCE(name, user_id)
    INTO v_commenter_name
    FROM users
    WHERE user_id = NEW.user_id;

    INSERT INTO notifications (
        recipient_user_id,
        actor_user_id,
        related_post_id,
        related_comment_id,
        notification_type,
        message
    )
    SELECT DISTINCT
        visible_users.recipient_user_id,
        NEW.user_id,
        NEW.post_id,
        NEW.comment_id,
        'POST_COMMENT',
        CONCAT(v_commenter_name, '对', v_author_name, '的朋友圈评论了：', LEFT(NEW.content, 80))
    FROM (
        SELECT v_author_id AS recipient_user_id
        UNION
        SELECT viewer_id AS recipient_user_id
        FROM friend_post_view
        WHERE post_id = NEW.post_id
    ) AS visible_users
    WHERE visible_users.recipient_user_id IS NOT NULL
      AND visible_users.recipient_user_id <> NEW.user_id;
END//

-- 触发器：管理员审核日志写入后，自动通知被屏蔽或恢复的朋友圈作者。
CREATE TRIGGER trg_audit_logs_after_insert
AFTER INSERT ON audit_logs
FOR EACH ROW
BEGIN
    IF NEW.action = 'BLOCK_POST' AND NEW.target_user_id IS NOT NULL THEN
        INSERT INTO notifications (
            recipient_user_id,
            related_post_id,
            notification_type,
            message
        ) VALUES (
            NEW.target_user_id,
            NEW.target_post_id,
            'POST_BLOCKED',
            CONCAT('你的朋友圈已被管理员审核为不可见，朋友圈ID：', NEW.target_post_id)
        );
    ELSEIF NEW.action = 'UNBLOCK_POST' AND NEW.target_user_id IS NOT NULL THEN
        INSERT INTO notifications (
            recipient_user_id,
            related_post_id,
            notification_type,
            message
        ) VALUES (
            NEW.target_user_id,
            NEW.target_post_id,
            'POST_UNBLOCKED',
            CONCAT('你的朋友圈已恢复可见，朋友圈ID：', NEW.target_post_id)
        );
    END IF;
END//

DELIMITER ;
