#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import csv
import io
import json
import re
import subprocess


DB_NAME = "lab5_social_platform"
LOGIN_PATH = "lab5root"
HOST = "127.0.0.1"
PORT = 8005
USER_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,29}$")
FRONTEND_PATH = Path(__file__).with_name("frontend.html")


def sql_literal(value):
    if value is None:
        return "NULL"
    text = str(value)
    text = text.replace("\\", "\\\\").replace("'", "''")
    return f"'{text}'"


def run_sql(sql, expect_rows=True):
    cmd = [
        "mysql",
        f"--login-path={LOGIN_PATH}",
        "-D",
        DB_NAME,
        "--batch",
        "--raw",
        "--default-character-set=utf8mb4",
        "-e",
        sql,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "MySQL command failed")
    if not expect_rows:
        return []
    output = result.stdout.strip("\n")
    if not output:
        return []
    reader = csv.DictReader(io.StringIO(output), delimiter="\t")
    rows = []
    for row in reader:
        rows.append({key: (None if value == "NULL" else value) for key, value in row.items()})
    return rows


def execute(sql):
    run_sql(sql, expect_rows=False)


def execute_change(sql):
    rows = run_sql(f"""
        {sql.rstrip(';')}
        ;
        SELECT ROW_COUNT() AS affected_rows
    """)
    return int(rows[0]["affected_rows"]) if rows else 0


def execute_transaction(statements):
    clean_statements = [statement.strip().rstrip(";") for statement in statements if statement.strip()]
    sql = "START TRANSACTION;\n" + ";\n".join(clean_statements) + ";\nCOMMIT;"
    execute(sql)


def require_exists(sql, message):
    if not run_sql(sql):
        raise ValueError(message)


def require_not_exists(sql, message):
    if run_sql(sql):
        raise ValueError(message)


def get_json_body(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw)


def require_value(data, key):
    value = data.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"Missing required field: {key}")
    return str(value).strip()


def validate_user_id(user_id):
    if not USER_ID_PATTERN.fullmatch(user_id):
        raise ValueError("user_id 必须为 3-30 位，以英文字母开头，只能包含英文字母、数字和下划线")


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lab5 朋友圈数据库演示</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #172033;
      --muted: #657084;
      --line: #d9deea;
      --blue: #2866d8;
      --green: #10845d;
      --red: #bd2f36;
      --amber: #a16000;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 260px 1fr;
    }
    aside {
      background: #111827;
      color: #e5e7eb;
      padding: 20px 16px;
      position: sticky;
      top: 0;
      height: 100vh;
    }
    .brand {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 18px;
    }
    .user-box {
      border: 1px solid #2d3748;
      background: #1f2937;
      padding: 12px;
      margin-bottom: 16px;
    }
    label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }
    aside label { color: #aab3c2; }
    select, input, textarea, button {
      font: inherit;
    }
    select, input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 9px;
      background: #fff;
      color: var(--text);
    }
    aside select {
      background: #0f172a;
      color: #f8fafc;
      border-color: #334155;
    }
    .nav {
      display: grid;
      gap: 6px;
    }
    .nav button {
      text-align: left;
      border: 0;
      background: transparent;
      color: #cbd5e1;
      padding: 10px 11px;
      border-radius: 6px;
      cursor: pointer;
    }
    .nav button.active, .nav button:hover {
      background: #243044;
      color: #fff;
    }
    main {
      padding: 22px;
      max-width: 1380px;
      width: 100%;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }
    h1 {
      margin: 0;
      font-size: 22px;
    }
    .subtitle {
      color: var(--muted);
      margin-top: 5px;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: end;
      gap: 10px;
    }
    .toolbar > div { min-width: 170px; }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(170px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .stat, .panel, .post, .person, .note {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .stat {
      padding: 16px;
    }
    .stat .value {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 3px;
    }
    .stat .label {
      color: var(--muted);
    }
    .panel {
      padding: 14px;
      margin-bottom: 14px;
    }
    .panel h2 {
      font-size: 16px;
      margin: 0 0 12px;
    }
    .list {
      display: grid;
      gap: 12px;
    }
    .people-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 12px;
    }
    .person, .note {
      padding: 12px;
    }
    .person-head {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .avatar {
      width: 46px;
      height: 46px;
      border-radius: 50%;
      object-fit: cover;
      background: #e7ebf3;
      flex: 0 0 auto;
    }
    .muted { color: var(--muted); }
    .badge {
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      color: var(--muted);
      margin: 4px 4px 0 0;
      background: #fafbff;
    }
    .badge.green { color: var(--green); border-color: #c8eadb; background: #effaf5; }
    .badge.red { color: var(--red); border-color: #f3c5ca; background: #fff3f3; }
    .badge.amber { color: var(--amber); border-color: #f2d8a7; background: #fff8e8; }
    .post {
      overflow: hidden;
    }
    .post img.post-image {
      width: 100%;
      height: 210px;
      object-fit: cover;
      display: block;
      background: #e7ebf3;
    }
    .post-body {
      padding: 12px;
    }
    .post-meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }
    .post-content {
      line-height: 1.6;
      margin-bottom: 10px;
    }
    .post-actions {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: start;
    }
    .post-actions textarea {
      resize: vertical;
      min-height: 38px;
    }
    .btn {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      padding: 8px 10px;
      cursor: pointer;
    }
    .btn:hover { border-color: #9aabc7; }
    .btn.primary {
      background: var(--blue);
      color: #fff;
      border-color: var(--blue);
    }
    .btn.danger {
      background: var(--red);
      color: #fff;
      border-color: var(--red);
    }
    .btn.good {
      background: var(--green);
      color: #fff;
      border-color: var(--green);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    th, td {
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      vertical-align: top;
    }
    th {
      background: #f0f3fa;
      font-weight: 600;
      color: #374151;
    }
    tr:last-child td { border-bottom: 0; }
    .empty {
      padding: 30px;
      text-align: center;
      color: var(--muted);
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .error {
      background: #fff3f3;
      color: #a61924;
      border: 1px solid #f0b8bf;
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 14px;
      white-space: pre-wrap;
    }
    .ok {
      background: #effaf5;
      color: #0b6b4b;
      border: 1px solid #bee5d2;
      padding: 10px 12px;
      border-radius: 8px;
      margin-bottom: 14px;
    }
    @media (max-width: 860px) {
      .app { grid-template-columns: 1fr; }
      aside { position: static; height: auto; }
      .grid { grid-template-columns: repeat(2, 1fr); }
      header { display: block; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">Lab5 朋友圈演示</div>
      <div class="user-box">
        <label for="currentUser">当前用户</label>
        <select id="currentUser"></select>
      </div>
      <div class="nav" id="nav">
        <button data-view="overview" class="active">总览</button>
        <button data-view="account">注册登录与资料</button>
        <button data-view="users">用户资料</button>
        <button data-view="friends">好友与分组</button>
        <button data-view="posts">朋友圈</button>
        <button data-view="notifications">通知</button>
        <button data-view="requests">好友申请</button>
        <button data-view="admin">管理员审核视图</button>
        <button data-view="raw">数据库视图检查</button>
      </div>
    </aside>
    <main>
      <header>
        <div>
          <h1 id="title">总览</h1>
          <div class="subtitle" id="subtitle">查看当前数据库的核心数据量和演示入口。</div>
        </div>
        <div class="toolbar" id="toolbar"></div>
      </header>
      <div id="message"></div>
      <section id="content"></section>
    </main>
  </div>

  <script>
    const state = { users: [], currentUser: "", view: "overview" };
    const titles = {
      overview: ["总览", "查看当前数据库的核心数据量和演示入口。"],
      account: ["注册登录与资料", "注册、登录，并修改当前用户的个人基本信息。"],
      users: ["用户资料", "普通用户的公开资料，生日和密码不会显示。"],
      friends: ["好友与分组", "查看当前用户的好友资料，支持未分组和多分组。"],
      posts: ["朋友圈", "按当前用户查看好友朋友圈、自己的朋友圈或添加好友预览。"],
      notifications: ["通知", "查看好友申请、评论和管理员审核通知。"],
      requests: ["好友申请", "处理当前用户收到的 pending 好友申请，或发起新申请。"],
      admin: ["管理员审核视图", "管理员可以浏览所有朋友圈，但不显示用户个人基本信息。"],
      raw: ["数据库视图检查", "直接查看 SQL 视图结果，便于验收时解释设计。"]
    };

    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }

    async function api(path, options = {}) {
      const res = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || res.statusText);
      return data;
    }

    function setMessage(text, type = "ok") {
      document.getElementById("message").innerHTML = text ? `<div class="${type}">${esc(text)}</div>` : "";
    }

    function setToolbar(html = "") {
      document.getElementById("toolbar").innerHTML = html;
    }

    function setHeader(view) {
      const [title, subtitle] = titles[view] || titles.overview;
      document.getElementById("title").textContent = title;
      document.getElementById("subtitle").textContent = subtitle;
      document.querySelectorAll("#nav button").forEach(btn => btn.classList.toggle("active", btn.dataset.view === view));
    }

    function table(rows) {
      if (!rows || rows.length === 0) return `<div class="empty">暂无数据</div>`;
      const keys = Object.keys(rows[0]);
      return `<table><thead><tr>${keys.map(k => `<th>${esc(k)}</th>`).join("")}</tr></thead><tbody>${
        rows.map(row => `<tr>${keys.map(k => `<td>${esc(row[k])}</td>`).join("")}</tr>`).join("")
      }</tbody></table>`;
    }

    async function loadUsers() {
      const data = await api("/api/users");
      state.users = data.rows;
      const select = document.getElementById("currentUser");
      select.innerHTML = state.users.map(u => `<option value="${esc(u.user_id)}">${esc(u.name)} (${esc(u.user_id)})</option>`).join("");
      state.currentUser = state.currentUser || (state.users[0] && state.users[0].user_id) || "";
      select.value = state.currentUser;
    }

    async function render() {
      setMessage("");
      setHeader(state.view);
      try {
        if (state.view === "overview") await renderOverview();
        if (state.view === "account") await renderAccount();
        if (state.view === "users") await renderUsers();
        if (state.view === "friends") await renderFriends();
        if (state.view === "posts") await renderPosts();
        if (state.view === "notifications") await renderNotifications();
        if (state.view === "requests") await renderRequests();
        if (state.view === "admin") await renderAdmin();
        if (state.view === "raw") await renderRaw();
      } catch (err) {
        document.getElementById("content").innerHTML = "";
        setMessage(err.message, "error");
      }
    }

    async function renderOverview() {
      setToolbar(`<button class="btn primary" onclick="render()">刷新</button>`);
      const data = await api("/api/overview");
      document.getElementById("content").innerHTML = `
        <div class="grid">${data.counts.map(item => `
          <div class="stat"><div class="value">${esc(item.row_count)}</div><div class="label">${esc(item.table_name)}</div></div>
        `).join("")}</div>
        <div class="panel">
          <h2>演示建议</h2>
          <p class="muted">先切换用户，再依次查看“好友与分组”“朋友圈”“通知”“好友申请”。管理员审核视图用于说明管理员不能看用户生日等个人信息。</p>
        </div>
        <div class="panel">
          <h2>通知类型统计</h2>
          ${table(data.notifications)}
        </div>`;
    }

    async function renderUsers() {
      setToolbar(`<div><label>搜索用户</label><input id="userSearch" placeholder="账号或昵称"></div><button class="btn primary" onclick="renderUsers()">搜索</button>`);
      const search = document.getElementById("userSearch")?.value || "";
      const data = await api(`/api/users?search=${encodeURIComponent(search)}`);
      document.getElementById("content").innerHTML = `<div class="people-grid">${
        data.rows.map(u => `<div class="person">
          <div class="person-head">
            <img class="avatar" src="${esc(u.avatar_url)}" alt="">
            <div><strong>${esc(u.name)}</strong><div class="muted">${esc(u.user_id)}</div></div>
          </div>
          <div style="margin-top:10px">
            <span class="badge">${esc(u.gender)}</span>
            <span class="badge">展示年龄 ${esc(u.display_age)}</span>
            <span class="badge">朋友圈 ${esc(u.post_visible_period)}</span>
          </div>
          ${u.user_id !== state.currentUser ? `<div style="margin-top:10px"><button class="btn primary" onclick="sendRequestTo('${esc(u.user_id)}')">申请添加好友</button></div>` : ""}
        </div>`).join("")
      }</div>`;
    }

    async function renderFriends() {
      setToolbar(`
        <div><label>新分组名</label><input id="newGroupName" placeholder="例如 Lab Partners"></div>
        <button class="btn primary" onclick="createGroup()">创建分组</button>
      `);
      const data = await api(`/api/friends?user=${encodeURIComponent(state.currentUser)}`);
      const groups = await api(`/api/groups?user=${encodeURIComponent(state.currentUser)}`);
      const groupOptions = groups.rows.map(g => `<option value="${esc(g.group_id)}">${esc(g.group_name)}</option>`).join("");
      document.getElementById("content").innerHTML = `<div class="people-grid">${
        data.rows.map(f => `<div class="person">
          <div class="person-head">
            <img class="avatar" src="${esc(f.avatar_url)}" alt="">
            <div><strong>${esc(f.name)}</strong><div class="muted">${esc(f.friend_id)}</div></div>
          </div>
          <div style="margin-top:10px">
            <span class="badge">${esc(f.gender)}</span>
            <span class="badge">展示年龄 ${esc(f.display_age)}</span>
            <span class="badge green">${esc(f.group_names)}</span>
          </div>
          <div style="margin-top:10px; display:grid; gap:8px">
            <select id="group-${esc(f.friend_id)}">${groupOptions}</select>
            <div>
              <button class="btn" onclick="addFriendToGroup('${esc(f.friend_id)}')">加入分组</button>
              <button class="btn" onclick="removeFriendFromGroup('${esc(f.friend_id)}')">移出分组</button>
              <button class="btn danger" onclick="deleteFriend('${esc(f.friend_id)}')">删除好友</button>
            </div>
          </div>
        </div>`).join("")
      }</div><div class="panel"><h2>我的分组</h2>${table(groups.rows)}</div>`;
    }

    async function renderPosts(scope = "friend") {
      setToolbar(`
        <div><label>朋友圈范围</label><select id="postScope" onchange="renderPosts(this.value)">
          <option value="friend">当前用户可见的好友朋友圈</option>
          <option value="own">当前用户自己的朋友圈</option>
          <option value="preview">添加好友预览</option>
          <option value="all">管理员查看全部</option>
        </select></div>
      `);
      const scopeSelect = document.getElementById("postScope");
      if (scopeSelect) scopeSelect.value = scope;
      const data = await api(`/api/posts?user=${encodeURIComponent(state.currentUser)}&scope=${encodeURIComponent(scope)}`);
      const composer = scope === "own" ? postComposer() : "";
      document.getElementById("content").innerHTML = `${composer}<div class="list">${
        data.rows.length ? data.rows.map(postCard).join("") : `<div class="empty">暂无朋友圈</div>`
      }</div>`;
    }

    function postComposer() {
      return `<div class="panel">
        <h2>发表朋友圈</h2>
        <div style="display:grid; gap:10px">
          <textarea id="newPostContent" placeholder="输入朋友圈内容，最多 500 字"></textarea>
          <input id="newPostImage" placeholder="图片 URL，可为空">
          <div class="toolbar">
            <div><label>可见范围</label><select id="newPostVisibility">
              <option value="friends">全部好友可见</option>
              <option value="groups">指定分组可见</option>
              <option value="selected">指定好友可见</option>
              <option value="self">仅自己可见</option>
            </select></div>
            <div><label>分组 ID，逗号分隔</label><input id="newPostGroups" placeholder="例如 1,2"></div>
            <div><label>好友 user_id，逗号分隔</label><input id="newPostUsers" placeholder="例如 bob,carol"></div>
            <button class="btn primary" onclick="createPost()">发表</button>
          </div>
        </div>
      </div>`;
    }

    function postCard(p) {
      const author = p.author_name || p.name || p.author_id || p.user_id || p.owner_id || p.target_user_id || "";
      const image = p.image_url ? `<img class="post-image" src="${esc(p.image_url)}" alt="">` : "";
      const canComment = p.post_status !== "blocked" && p.visibility !== "self";
      const isOwn = p.owner_id === state.currentUser || p.user_id === state.currentUser;
      return `<article class="post">
        ${image}
        <div class="post-body">
          <div class="post-meta">
            <strong>${esc(author)}</strong>
            <span>${esc(p.created_at)}</span>
            <span class="badge ${p.post_status === "blocked" ? "red" : "green"}">${esc(p.post_status || "visible")}</span>
            <span class="badge">${esc(p.visibility || "")}</span>
            <span class="badge">评论 ${esc(p.comment_count || 0)}</span>
          </div>
          <div class="post-content">${esc(p.content)}</div>
          ${isOwn ? `<div class="post-actions" style="margin-bottom:8px">
            <textarea id="edit-${esc(p.post_id)}">${esc(p.content)}</textarea>
            <div style="display:grid; gap:6px">
              <button class="btn" onclick="updatePost(${esc(p.post_id)})">修改</button>
              <button class="btn danger" onclick="deletePost(${esc(p.post_id)})">删除</button>
            </div>
          </div>` : ""}
          ${canComment ? `<div class="post-actions">
            <textarea id="comment-${esc(p.post_id)}" placeholder="写一条评论，用于测试评论通知"></textarea>
            <button class="btn primary" onclick="addComment(${esc(p.post_id)})">评论</button>
          </div>` : ""}
        </div>
      </article>`;
    }

    async function addComment(postId) {
      const input = document.getElementById(`comment-${postId}`);
      const content = input.value.trim();
      if (!content) return setMessage("评论不能为空", "error");
      await api("/api/comments", {
        method: "POST",
        body: JSON.stringify({ post_id: postId, user_id: state.currentUser, content })
      });
      setMessage("评论已添加，相关用户会自动收到通知");
      input.value = "";
      await renderPosts(document.getElementById("postScope")?.value || "friend");
    }

    async function loginUser() {
      const user_id = document.getElementById("loginUserId").value.trim();
      const password = document.getElementById("loginPassword").value;
      await api("/api/login", { method: "POST", body: JSON.stringify({ user_id, password }) });
      state.currentUser = user_id;
      await loadUsers();
      setMessage("登录成功");
      await renderAccount();
    }

    async function registerUser() {
      const user_id = document.getElementById("regUserId").value.trim();
      const password = document.getElementById("regPassword").value;
      const name = document.getElementById("regName").value.trim() || user_id;
      await api("/api/register", { method: "POST", body: JSON.stringify({ user_id, password, name }) });
      state.currentUser = user_id;
      await loadUsers();
      setMessage("注册成功，已切换到新用户");
      await renderAccount();
    }

    async function updateProfile() {
      await api("/api/users/update", {
        method: "POST",
        body: JSON.stringify({
          user_id: state.currentUser,
          name: document.getElementById("profileName").value.trim(),
          gender: document.getElementById("profileGender").value,
          birth_date: document.getElementById("profileBirth").value,
          display_age: document.getElementById("profileAge").value,
          avatar_url: document.getElementById("profileAvatar").value.trim(),
          post_visible_period: document.getElementById("profilePeriod").value
        })
      });
      await loadUsers();
      setMessage("个人信息已更新");
      await renderAccount();
    }

    async function createPost() {
      await api("/api/posts/create", {
        method: "POST",
        body: JSON.stringify({
          user_id: state.currentUser,
          content: document.getElementById("newPostContent").value.trim(),
          image_url: document.getElementById("newPostImage").value.trim(),
          visibility: document.getElementById("newPostVisibility").value,
          group_ids: document.getElementById("newPostGroups").value.trim(),
          viewer_ids: document.getElementById("newPostUsers").value.trim()
        })
      });
      setMessage("朋友圈已发表");
      await renderPosts("own");
    }

    async function updatePost(postId) {
      await api("/api/posts/update", {
        method: "POST",
        body: JSON.stringify({
          user_id: state.currentUser,
          post_id: postId,
          content: document.getElementById(`edit-${postId}`).value.trim()
        })
      });
      setMessage("朋友圈已修改，updated_at 已由触发器自动更新");
      await renderPosts("own");
    }

    async function deletePost(postId) {
      if (!confirm("确定删除这条朋友圈吗？相关评论会自动级联删除。")) return;
      await api("/api/posts/delete", { method: "POST", body: JSON.stringify({ user_id: state.currentUser, post_id: postId }) });
      setMessage("朋友圈已删除，相关评论已自动删除");
      await renderPosts("own");
    }

    async function renderAccount() {
      setToolbar("");
      const profileData = await api(`/api/profile?user=${encodeURIComponent(state.currentUser)}`);
      const profile = profileData.row || {};
      document.getElementById("content").innerHTML = `
        <div class="panel">
          <h2>用户登录</h2>
          <div class="toolbar">
            <div><label>user_id</label><input id="loginUserId" value="${esc(state.currentUser)}"></div>
            <div><label>密码</label><input id="loginPassword" type="password" value="123456"></div>
            <button class="btn primary" onclick="loginUser()">登录</button>
          </div>
        </div>
        <div class="panel">
          <h2>用户注册</h2>
          <div class="toolbar">
            <div><label>user_id</label><input id="regUserId" placeholder="英文开头，只含字母数字下划线"></div>
            <div><label>密码</label><input id="regPassword" type="password" placeholder="初始密码"></div>
            <div><label>昵称</label><input id="regName" placeholder="昵称"></div>
            <button class="btn primary" onclick="registerUser()">注册</button>
          </div>
        </div>
        <div class="panel">
          <h2>修改个人信息</h2>
          <div class="toolbar">
            <div><label>昵称</label><input id="profileName" value="${esc(profile.name || "")}"></div>
            <div><label>性别</label><select id="profileGender">
              <option value="男">男</option><option value="女">女</option><option value="其他">其他</option>
            </select></div>
            <div><label>出生日期</label><input id="profileBirth" type="date" value="${esc(profile.birth_date || "")}"></div>
            <div><label>展示年龄</label><input id="profileAge" type="number" value="${esc(profile.display_age || "")}"></div>
            <div><label>头像 URL</label><input id="profileAvatar" value="${esc(profile.avatar_url || "")}"></div>
            <div><label>朋友圈可见时长</label><select id="profilePeriod">
              <option value="7_days">7 天</option><option value="3_months">3 个月</option><option value="6_months">6 个月</option><option value="forever">永久</option>
            </select></div>
            <button class="btn primary" onclick="updateProfile()">保存资料</button>
          </div>
        </div>`;
      document.getElementById("profileGender").value = profile.gender || "其他";
      document.getElementById("profilePeriod").value = profile.post_visible_period || "3_months";
    }

    async function renderNotifications() {
      setToolbar(`<button class="btn primary" onclick="render()">刷新</button>`);
      const data = await api(`/api/notifications?user=${encodeURIComponent(state.currentUser)}`);
      document.getElementById("content").innerHTML = `<div class="list">${
        data.rows.length ? data.rows.map(n => `<div class="note">
          <div>
            <span class="badge ${n.is_read === "0" ? "amber" : "green"}">${n.is_read === "0" ? "未读" : "已读"}</span>
            <span class="badge">${esc(n.notification_type)}</span>
            ${n.request_status ? `<span class="badge">${esc(n.request_status)}</span>` : ""}
          </div>
          <p>${esc(n.message)}</p>
          <div class="muted">${esc(n.created_at)}</div>
          ${n.is_read === "0" ? `<button class="btn" onclick="markRead(${esc(n.notification_id)})">标记已读</button>` : ""}
        </div>`).join("") : `<div class="empty">暂无通知</div>`
      }</div>`;
    }

    async function markRead(id) {
      await api("/api/notifications/read", { method: "POST", body: JSON.stringify({ notification_id: id }) });
      await renderNotifications();
    }

    async function renderRequests() {
      setToolbar(`
        <div><label>申请对象 user_id</label><input id="receiverId" placeholder="例如 jack"></div>
        <button class="btn primary" onclick="sendRequest()">发起申请</button>
      `);
      const data = await api(`/api/requests?user=${encodeURIComponent(state.currentUser)}`);
      document.getElementById("content").innerHTML = `<div class="panel"><h2>收到的申请</h2>${table(data.received)}</div>
        <div class="list">${data.received.filter(r => r.request_status === "pending").map(r => `
          <div class="note">
            <strong>${esc(r.requester_id)}</strong> 申请添加你为好友
            <div style="margin-top:8px">
              <button class="btn good" onclick="respondRequest(${esc(r.request_id)}, 'accept')">接受</button>
              <button class="btn danger" onclick="respondRequest(${esc(r.request_id)}, 'reject')">拒绝</button>
            </div>
          </div>
        `).join("")}</div>
        <div class="panel"><h2>发出的申请</h2>${table(data.sent)}</div>`;
    }

    async function sendRequest() {
      const receiver = document.getElementById("receiverId").value.trim();
      if (!receiver) return setMessage("请输入申请对象 user_id", "error");
      await api("/api/requests", { method: "POST", body: JSON.stringify({ requester_id: state.currentUser, receiver_id: receiver }) });
      setMessage("好友申请已发送，对方会收到通知");
      await renderRequests();
    }

    async function sendRequestTo(receiver) {
      await api("/api/requests", { method: "POST", body: JSON.stringify({ requester_id: state.currentUser, receiver_id: receiver }) });
      setMessage(`已向 ${receiver} 发送好友申请`);
    }

    async function respondRequest(id, action) {
      await api("/api/requests/respond", { method: "POST", body: JSON.stringify({ request_id: id, user_id: state.currentUser, action }) });
      setMessage(action === "accept" ? "已接受申请，双方成为好友" : "已拒绝申请");
      await renderRequests();
    }

    async function createGroup() {
      const group_name = document.getElementById("newGroupName").value.trim();
      if (!group_name) return setMessage("分组名不能为空", "error");
      await api("/api/groups", { method: "POST", body: JSON.stringify({ owner_id: state.currentUser, group_name }) });
      setMessage("分组已创建");
      await renderFriends();
    }

    async function addFriendToGroup(friendId) {
      const group_id = document.getElementById(`group-${friendId}`).value;
      await api("/api/groups/membership", { method: "POST", body: JSON.stringify({ owner_id: state.currentUser, friend_id: friendId, group_id, action: "add" }) });
      setMessage("好友已加入分组");
      await renderFriends();
    }

    async function removeFriendFromGroup(friendId) {
      const group_id = document.getElementById(`group-${friendId}`).value;
      await api("/api/groups/membership", { method: "POST", body: JSON.stringify({ owner_id: state.currentUser, friend_id: friendId, group_id, action: "remove" }) });
      setMessage("好友已从分组移出");
      await renderFriends();
    }

    async function deleteFriend(friendId) {
      if (!confirm(`确定删除好友 ${friendId} 吗？双方好友关系都会删除。`)) return;
      await api("/api/friends/delete", { method: "POST", body: JSON.stringify({ user_id: state.currentUser, friend_id: friendId }) });
      setMessage("好友已删除，双方关系和分组归属已清理");
      await renderFriends();
    }

    async function loginAdmin() {
      await api("/api/admin/login", {
        method: "POST",
        body: JSON.stringify({
          admin_id: document.getElementById("adminId").value.trim(),
          password: document.getElementById("adminPassword").value
        })
      });
      setMessage("管理员登录成功");
    }

    async function updateAdmin() {
      await api("/api/admin/update", {
        method: "POST",
        body: JSON.stringify({
          admin_id: document.getElementById("adminId").value.trim(),
          name: document.getElementById("adminName").value.trim()
        })
      });
      setMessage("管理员信息已更新");
    }

    async function blockPost(postId) {
      await api("/api/admin/block_post", {
        method: "POST",
        body: JSON.stringify({ admin_id: document.getElementById("adminId").value.trim(), post_id: postId })
      });
      setMessage("朋友圈已被管理员屏蔽，并已生成审核通知");
      await renderAdmin();
    }

    async function unblockPost(postId) {
      await api("/api/admin/unblock_post", {
        method: "POST",
        body: JSON.stringify({ admin_id: document.getElementById("adminId").value.trim(), post_id: postId })
      });
      setMessage("朋友圈已恢复可见，并已生成通知");
      await renderAdmin();
    }

    async function deleteUserByAdmin() {
      const target_user_id = document.getElementById("deleteUserId").value.trim();
      if (!target_user_id) return setMessage("请输入要注销的 user_id", "error");
      if (!confirm(`确定注销用户 ${target_user_id} 吗？这会删除系统中所有相关信息。`)) return;
      await api("/api/admin/delete_user", {
        method: "POST",
        body: JSON.stringify({ admin_id: document.getElementById("adminId").value.trim(), target_user_id })
      });
      await loadUsers();
      setMessage("用户已注销，相关数据已级联删除");
      await renderAdmin();
    }

    async function renderAdmin() {
      setToolbar(`
        <div><label>管理员 ID</label><input id="adminId" value="9001"></div>
        <div><label>密码</label><input id="adminPassword" type="password" value="admin123"></div>
        <button class="btn primary" onclick="loginAdmin()">管理员登录</button>
        <div><label>管理员昵称</label><input id="adminName" placeholder="新昵称"></div>
        <button class="btn" onclick="updateAdmin()">修改管理员信息</button>
        <div><label>注销用户 user_id</label><input id="deleteUserId" placeholder="例如 david"></div>
        <button class="btn danger" onclick="deleteUserByAdmin()">注销用户</button>
      `);
      const data = await api("/api/admin/posts");
      document.getElementById("content").innerHTML = `<div class="list">${
        data.rows.map(p => `<div class="note">
          <div><strong>Post #${esc(p.post_id)}</strong> <span class="badge ${p.post_status === "blocked" ? "red" : "green"}">${esc(p.post_status)}</span> <span class="badge">${esc(p.visibility)}</span></div>
          <p>${esc(p.content)}</p>
          <div class="muted">作者 user_id: ${esc(p.user_id)} | 更新时间: ${esc(p.updated_at)} | 评论 ${esc(p.comment_count)}</div>
          <div style="margin-top:8px">
            <button class="btn danger" onclick="blockPost(${esc(p.post_id)})">审核删除/屏蔽</button>
            <button class="btn good" onclick="unblockPost(${esc(p.post_id)})">恢复可见</button>
          </div>
        </div>`).join("")
      }</div>`;
    }

    async function renderRaw(viewName = "friend_post_view") {
      setToolbar(`
        <div><label>选择视图</label><select id="rawView" onchange="renderRaw(this.value)">
          <option>friend_profile_view</option>
          <option>friend_post_view</option>
          <option>own_post_view</option>
          <option>post_preview_view</option>
          <option>user_notification_view</option>
          <option>admin_post_view</option>
        </select></div>
      `);
      document.getElementById("rawView").value = viewName;
      const data = await api(`/api/raw?view=${encodeURIComponent(viewName)}&user=${encodeURIComponent(state.currentUser)}`);
      document.getElementById("content").innerHTML = table(data.rows);
    }

    document.getElementById("currentUser").addEventListener("change", event => {
      state.currentUser = event.target.value;
      render();
    });
    document.getElementById("nav").addEventListener("click", event => {
      const btn = event.target.closest("button[data-view]");
      if (!btn) return;
      state.view = btn.dataset.view;
      render();
    });

    loadUsers().then(render).catch(err => setMessage(err.message, "error"));
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_html(self):
        if FRONTEND_PATH.exists():
            data = FRONTEND_PATH.read_bytes()
        else:
            data = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/":
                return self.send_html()
            if parsed.path == "/api/overview":
                return self.send_json(api_overview())
            if parsed.path == "/api/users":
                return self.send_json({"rows": users(query.get("search", [""])[0])})
            if parsed.path == "/api/profile":
                return self.send_json(user_profile(query.get("user", [""])[0]))
            if parsed.path == "/api/friends":
                return self.send_json({"rows": friends(query.get("user", [""])[0])})
            if parsed.path == "/api/groups":
                return self.send_json({"rows": groups(query.get("user", [""])[0])})
            if parsed.path == "/api/posts":
                return self.send_json({"rows": posts(query.get("user", [""])[0], query.get("scope", ["friend"])[0])})
            if parsed.path == "/api/post-preview":
                return self.send_json({"rows": post_preview(query.get("target", [""])[0])})
            if parsed.path == "/api/comments":
                return self.send_json({"rows": comments_for_posts(query.get("post_ids", [""])[0])})
            if parsed.path == "/api/notifications":
                return self.send_json({"rows": notifications(query.get("user", [""])[0])})
            if parsed.path == "/api/requests":
                return self.send_json(requests(query.get("user", [""])[0]))
            if parsed.path == "/api/admin/posts":
                return self.send_json({"rows": admin_posts()})
            if parsed.path == "/api/raw":
                return self.send_json({"rows": raw_view(query.get("view", ["friend_post_view"])[0], query.get("user", [""])[0])})
            self.send_json({"error": "Not found"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            data = get_json_body(self)
            if parsed.path == "/api/login":
                return self.send_json(login_user(data))
            if parsed.path == "/api/register":
                return self.send_json(register_user(data))
            if parsed.path == "/api/users/update":
                return self.send_json(update_user(data))
            if parsed.path == "/api/comments":
                return self.send_json(add_comment(data))
            if parsed.path == "/api/notifications/read":
                return self.send_json(mark_notification_read(data))
            if parsed.path == "/api/requests":
                return self.send_json(send_friend_request(data))
            if parsed.path == "/api/requests/respond":
                return self.send_json(respond_friend_request(data))
            if parsed.path == "/api/friends/delete":
                return self.send_json(delete_friend(data))
            if parsed.path == "/api/groups":
                return self.send_json(create_group(data))
            if parsed.path == "/api/groups/membership":
                return self.send_json(update_group_membership(data))
            if parsed.path == "/api/posts/create":
                return self.send_json(create_post(data))
            if parsed.path == "/api/posts/update":
                return self.send_json(update_post(data))
            if parsed.path == "/api/posts/delete":
                return self.send_json(delete_post(data))
            if parsed.path == "/api/admin/login":
                return self.send_json(login_admin(data))
            if parsed.path == "/api/admin/update":
                return self.send_json(update_admin(data))
            if parsed.path == "/api/admin/block_post":
                return self.send_json(admin_set_post_status(data, "blocked"))
            if parsed.path == "/api/admin/unblock_post":
                return self.send_json(admin_set_post_status(data, "visible"))
            if parsed.path == "/api/admin/delete_user":
                return self.send_json(admin_delete_user(data))
            self.send_json({"error": "Not found"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)

    def log_message(self, fmt, *args):
        return


def api_overview():
    counts = run_sql("""
        SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
        UNION ALL SELECT 'friend_requests', COUNT(*) FROM friend_requests
        UNION ALL SELECT 'friendships', COUNT(*) FROM friendships
        UNION ALL SELECT 'posts', COUNT(*) FROM posts
        UNION ALL SELECT 'comments', COUNT(*) FROM comments
        UNION ALL SELECT 'notifications', COUNT(*) FROM notifications
    """)
    notification_counts = run_sql("""
        SELECT notification_type, COUNT(*) AS row_count
        FROM notifications
        GROUP BY notification_type
        ORDER BY notification_type
    """)
    return {"counts": counts, "notifications": notification_counts}


def users(search=""):
    where = ""
    if search:
        pattern = f"%{search}%"
        where = f"WHERE user_id LIKE {sql_literal(pattern)} OR name LIKE {sql_literal(pattern)}"
    return run_sql("""
        SELECT user_id, name, gender, display_age, avatar_url, post_visible_period, created_at
        FROM users
        {where}
        ORDER BY user_id
    """.format(where=where))


def user_profile(user_id):
    user_id = str(user_id).strip()
    rows = run_sql(f"""
        SELECT user_id, name, gender, birth_date, display_age, avatar_url, post_visible_period, created_at
        FROM users
        WHERE user_id = {sql_literal(user_id)}
        LIMIT 1
    """)
    if not rows:
        raise ValueError("用户不存在")
    return {"row": rows[0]}


def login_user(data):
    user_id = require_value(data, "user_id")
    password = require_value(data, "password")
    rows = run_sql(f"""
        SELECT user_id
        FROM users
        WHERE user_id = {sql_literal(user_id)}
          AND password_hash = SHA2({sql_literal(password)}, 256)
        LIMIT 1
    """)
    if not rows:
        raise ValueError("用户 ID 或密码错误")
    return {"ok": True, "user_id": user_id}


def register_user(data):
    user_id = require_value(data, "user_id")
    validate_user_id(user_id)
    password = require_value(data, "password")
    name = data.get("name") or user_id
    require_not_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(user_id)} LIMIT 1",
        "user_id 已存在，请换一个账号名",
    )
    execute(f"""
        INSERT INTO users (user_id, password_hash, name, avatar_url)
        VALUES (
            {sql_literal(user_id)},
            SHA2({sql_literal(password)}, 256),
            {sql_literal(name)},
            {sql_literal('https://i.pravatar.cc/160?u=' + user_id)}
        )
    """)
    return {"ok": True, "user_id": user_id}


def update_user(data):
    user_id = require_value(data, "user_id")
    require_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(user_id)} LIMIT 1",
        "用户不存在，无法修改资料",
    )
    execute(f"""
        UPDATE users
        SET name = {sql_literal(data.get("name") or user_id)},
            gender = {sql_literal(data.get("gender") or None)},
            birth_date = {sql_literal(data.get("birth_date") or None)},
            display_age = {sql_literal(data.get("display_age") or None)},
            avatar_url = {sql_literal(data.get("avatar_url") or None)},
            post_visible_period = {sql_literal(data.get("post_visible_period") or "3_months")}
        WHERE user_id = {sql_literal(user_id)}
    """)
    return {"ok": True}


def friends(user_id):
    return run_sql(f"""
        SELECT friend_id, name, gender, display_age, avatar_url, group_names, friendship_created_at
        FROM friend_profile_view
        WHERE viewer_id = {sql_literal(user_id)}
        ORDER BY friend_id
    """)


def groups(user_id):
    return run_sql(f"""
        SELECT group_id, group_name, created_at
        FROM friend_groups
        WHERE owner_id = {sql_literal(user_id)}
        ORDER BY group_id
    """)


def create_group(data):
    owner_id = require_value(data, "owner_id")
    group_name = require_value(data, "group_name")
    require_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(owner_id)} LIMIT 1",
        "用户不存在，无法创建分组",
    )
    require_not_exists(
        f"""
        SELECT 1 AS ok
        FROM friend_groups
        WHERE owner_id = {sql_literal(owner_id)}
          AND group_name = {sql_literal(group_name)}
        LIMIT 1
        """,
        "该用户已经有同名分组",
    )
    execute(f"""
        INSERT INTO friend_groups (owner_id, group_name)
        VALUES ({sql_literal(owner_id)}, {sql_literal(group_name)})
    """)
    return {"ok": True}


def update_group_membership(data):
    owner_id = require_value(data, "owner_id")
    friend_id = require_value(data, "friend_id")
    group_id = require_value(data, "group_id")
    action = require_value(data, "action")
    require_exists(
        f"""
        SELECT 1 AS ok
        FROM friendships
        WHERE owner_id = {sql_literal(owner_id)}
          AND friend_id = {sql_literal(friend_id)}
        LIMIT 1
        """,
        "只能把已经是好友的用户加入分组",
    )
    require_exists(
        f"""
        SELECT 1 AS ok
        FROM friend_groups
        WHERE owner_id = {sql_literal(owner_id)}
          AND group_id = {sql_literal(group_id)}
        LIMIT 1
        """,
        "分组不存在，无法修改分组归属",
    )
    if action == "add":
        execute(f"""
            INSERT IGNORE INTO friend_group_memberships (owner_id, friend_id, group_id)
            VALUES ({sql_literal(owner_id)}, {sql_literal(friend_id)}, {sql_literal(group_id)})
        """)
    elif action == "remove":
        affected = execute_change(f"""
            DELETE FROM friend_group_memberships
            WHERE owner_id = {sql_literal(owner_id)}
              AND friend_id = {sql_literal(friend_id)}
              AND group_id = {sql_literal(group_id)}
        """)
        if affected == 0:
            raise ValueError("该好友原本不在这个分组中")
    else:
        raise ValueError("action must be add or remove")
    return {"ok": True}


def posts(user_id, scope):
    if scope == "own":
        return run_sql(f"""
            SELECT p.*, (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comment_count
            FROM own_post_view p
            WHERE owner_id = {sql_literal(user_id)}
            ORDER BY created_at DESC
        """)
    if scope == "preview":
        return run_sql("""
            SELECT p.*, (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comment_count
            FROM post_preview_view p
            ORDER BY created_at DESC
            LIMIT 60
        """)
    if scope == "all":
        return admin_posts()
    return run_sql(f"""
        SELECT p.*, (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comment_count
        FROM friend_post_view p
        WHERE viewer_id = {sql_literal(user_id)}
        ORDER BY created_at DESC
    """)


def split_csv(value):
    if not value:
        return []
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value).split(",")
    return [item.strip() for item in raw if item and item.strip()]


def create_post(data):
    user_id = require_value(data, "user_id")
    content = require_value(data, "content")
    image_url = data.get("image_url") or None
    visibility = data.get("visibility") or "friends"
    if visibility not in {"friends", "groups", "selected", "self"}:
        raise ValueError("visibility 不合法")
    require_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(user_id)} LIMIT 1",
        "用户不存在，无法发表朋友圈",
    )
    if visibility == "groups" and not split_csv(data.get("group_ids")):
        raise ValueError("指定分组可见时，至少需要填写一个分组 ID")
    if visibility == "selected" and not split_csv(data.get("viewer_ids")):
        raise ValueError("指定好友可见时，至少需要填写一个好友 user_id")
    statements = [
        f"""
        INSERT INTO posts (user_id, content, image_url, visibility)
        VALUES ({sql_literal(user_id)}, {sql_literal(content)}, {sql_literal(image_url)}, {sql_literal(visibility)})
        """,
        "SET @new_post_id = LAST_INSERT_ID()",
    ]
    if visibility == "groups":
        for group_id in split_csv(data.get("group_ids")):
            statements.append(f"""
                INSERT INTO post_visible_groups (post_id, owner_id, group_id)
                VALUES (@new_post_id, {sql_literal(user_id)}, {sql_literal(group_id)})
            """)
    if visibility == "selected":
        for viewer_id in split_csv(data.get("viewer_ids")):
            statements.append(f"""
                INSERT INTO post_visible_users (post_id, owner_id, viewer_id)
                VALUES (@new_post_id, {sql_literal(user_id)}, {sql_literal(viewer_id)})
            """)
    execute_transaction(statements)
    return {"ok": True}


def update_post(data):
    user_id = require_value(data, "user_id")
    post_id = require_value(data, "post_id")
    content = require_value(data, "content")
    require_exists(
        f"""
        SELECT 1 AS ok
        FROM posts
        WHERE post_id = {sql_literal(post_id)}
          AND user_id = {sql_literal(user_id)}
        LIMIT 1
        """,
        "朋友圈不存在，或你不是这条朋友圈的作者",
    )
    execute(f"""
        UPDATE posts
        SET content = {sql_literal(content)}
        WHERE post_id = {sql_literal(post_id)}
          AND user_id = {sql_literal(user_id)}
    """)
    return {"ok": True}


def delete_post(data):
    user_id = require_value(data, "user_id")
    post_id = require_value(data, "post_id")
    affected = execute_change(f"""
        DELETE FROM posts
        WHERE post_id = {sql_literal(post_id)}
          AND user_id = {sql_literal(user_id)}
    """)
    if affected == 0:
        raise ValueError("朋友圈不存在，或你不是这条朋友圈的作者")
    return {"ok": True}


def notifications(user_id):
    return run_sql(f"""
        SELECT notification_id, notification_type, actor_user_id, actor_name, related_post_id,
               related_comment_id, related_request_id, request_status, message, is_read, created_at
        FROM user_notification_view
        WHERE recipient_user_id = {sql_literal(user_id)}
        ORDER BY is_read ASC, created_at DESC, notification_id DESC
    """)


def requests(user_id):
    received = run_sql(f"""
        SELECT request_id, requester_id, receiver_id, request_status, created_at, responded_at
        FROM friend_requests
        WHERE receiver_id = {sql_literal(user_id)}
        ORDER BY created_at DESC
    """)
    sent = run_sql(f"""
        SELECT request_id, requester_id, receiver_id, request_status, created_at, responded_at
        FROM friend_requests
        WHERE requester_id = {sql_literal(user_id)}
        ORDER BY created_at DESC
    """)
    return {"received": received, "sent": sent}


def comments_for_posts(post_ids):
    ids = split_csv(post_ids)
    if not ids:
        return []
    id_list = ", ".join(sql_literal(post_id) for post_id in ids)
    return run_sql(f"""
        SELECT
            c.comment_id,
            c.post_id,
            c.user_id,
            COALESCE(u.name, c.user_id) AS user_name,
            u.avatar_url,
            c.content,
            c.created_at
        FROM comments AS c
        JOIN users AS u
            ON c.user_id = u.user_id
        WHERE c.post_id IN ({id_list})
        ORDER BY c.post_id, c.created_at, c.comment_id
    """)


def post_preview(target_user_id):
    target_user_id = str(target_user_id).strip()
    require_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(target_user_id)} LIMIT 1",
        "要预览的用户不存在",
    )
    return run_sql(f"""
        SELECT p.*, (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comment_count
        FROM post_preview_view p
        WHERE target_user_id = {sql_literal(target_user_id)}
        ORDER BY created_at DESC
        LIMIT 20
    """)


def admin_posts():
    return run_sql("""
        SELECT
            p.*,
            COALESCE(u.name, p.user_id) AS author_name,
            u.avatar_url AS author_avatar_url,
            (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comment_count
        FROM admin_post_view p
        JOIN users u
            ON p.user_id = u.user_id
        ORDER BY created_at DESC
    """)


def raw_view(view_name, user_id):
    allowed = {
        "friend_profile_view",
        "friend_post_view",
        "own_post_view",
        "post_preview_view",
        "user_notification_view",
        "admin_post_view",
    }
    if view_name not in allowed:
        raise ValueError("Unsupported view")
    if view_name == "friend_profile_view":
        where = f" WHERE viewer_id = {sql_literal(user_id)}"
    elif view_name == "friend_post_view":
        where = f" WHERE viewer_id = {sql_literal(user_id)}"
    elif view_name == "own_post_view":
        where = f" WHERE owner_id = {sql_literal(user_id)}"
    elif view_name == "user_notification_view":
        where = f" WHERE recipient_user_id = {sql_literal(user_id)}"
    else:
        where = ""
    return run_sql(f"SELECT * FROM {view_name}{where} LIMIT 80")


def add_comment(data):
    user_id = require_value(data, "user_id")
    post_id = require_value(data, "post_id")
    content = require_value(data, "content")
    access = run_sql(f"""
        SELECT 1 AS ok
        FROM own_post_view
        WHERE owner_id = {sql_literal(user_id)}
          AND post_id = {sql_literal(post_id)}
        UNION
        SELECT 1 AS ok
        FROM friend_post_view
        WHERE viewer_id = {sql_literal(user_id)}
          AND post_id = {sql_literal(post_id)}
        LIMIT 1
    """)
    if not access:
        raise ValueError("当前用户不能评论这条朋友圈")
    execute(f"""
        INSERT INTO comments (post_id, user_id, content)
        VALUES ({sql_literal(post_id)}, {sql_literal(user_id)}, {sql_literal(content)})
    """)
    return {"ok": True}


def mark_notification_read(data):
    notification_id = require_value(data, "notification_id")
    require_exists(
        f"SELECT 1 AS ok FROM notifications WHERE notification_id = {sql_literal(notification_id)} LIMIT 1",
        "通知不存在，无法标记已读",
    )
    execute(f"""
        UPDATE notifications
        SET is_read = TRUE
        WHERE notification_id = {sql_literal(notification_id)}
    """)
    return {"ok": True}


def send_friend_request(data):
    requester_id = require_value(data, "requester_id")
    receiver_id = require_value(data, "receiver_id")
    if requester_id == receiver_id:
        raise ValueError("不能添加自己为好友")
    require_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(requester_id)} LIMIT 1",
        "申请发起用户不存在",
    )
    require_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(receiver_id)} LIMIT 1",
        "申请对象不存在",
    )
    existing = run_sql(f"""
        SELECT 1 AS ok
        FROM friendships
        WHERE owner_id = {sql_literal(requester_id)}
          AND friend_id = {sql_literal(receiver_id)}
        UNION
        SELECT 1 AS ok
        FROM friend_requests
        WHERE requester_id = {sql_literal(requester_id)}
          AND receiver_id = {sql_literal(receiver_id)}
          AND request_status = 'pending'
        UNION
        SELECT 1 AS ok
        FROM friend_requests
        WHERE requester_id = {sql_literal(receiver_id)}
          AND receiver_id = {sql_literal(requester_id)}
          AND request_status = 'pending'
        LIMIT 1
    """)
    if existing:
        raise ValueError("已经是好友，或已有待处理申请")
    execute(f"""
        INSERT INTO friend_requests (requester_id, receiver_id)
        VALUES ({sql_literal(requester_id)}, {sql_literal(receiver_id)})
    """)
    return {"ok": True}


def delete_friend(data):
    user_id = require_value(data, "user_id")
    friend_id = require_value(data, "friend_id")
    require_exists(
        f"""
        SELECT 1 AS ok
        FROM friendships
        WHERE owner_id = {sql_literal(user_id)}
          AND friend_id = {sql_literal(friend_id)}
        LIMIT 1
        """,
        "这两个用户当前不是好友关系",
    )
    execute_transaction([
        f"""
        DELETE FROM friendships
        WHERE (owner_id = {sql_literal(user_id)} AND friend_id = {sql_literal(friend_id)})
           OR (owner_id = {sql_literal(friend_id)} AND friend_id = {sql_literal(user_id)})
        """
    ])
    return {"ok": True}


def respond_friend_request(data):
    request_id = require_value(data, "request_id")
    user_id = require_value(data, "user_id")
    action = require_value(data, "action")
    if action not in {"accept", "reject"}:
        raise ValueError("action must be accept or reject")
    rows = run_sql(f"""
        SELECT requester_id, receiver_id
        FROM friend_requests
        WHERE request_id = {sql_literal(request_id)}
          AND receiver_id = {sql_literal(user_id)}
          AND request_status = 'pending'
    """)
    if not rows:
        raise ValueError("没有找到可处理的 pending 好友申请")
    requester = rows[0]["requester_id"]
    receiver = rows[0]["receiver_id"]
    if action == "reject":
        execute(f"""
            UPDATE friend_requests
            SET request_status = 'rejected', responded_at = CURRENT_TIMESTAMP
            WHERE request_id = {sql_literal(request_id)}
        """)
        return {"ok": True}
    execute_transaction([
        f"""
        UPDATE friend_requests
        SET request_status = 'accepted', responded_at = CURRENT_TIMESTAMP
        WHERE request_id = {sql_literal(request_id)}
        """,
        f"""
        INSERT INTO friendships (owner_id, friend_id, accepted_request_id)
        VALUES ({sql_literal(requester)}, {sql_literal(receiver)}, {sql_literal(request_id)})
        ON DUPLICATE KEY UPDATE accepted_request_id = VALUES(accepted_request_id)
        """,
        f"""
        INSERT INTO friendships (owner_id, friend_id, accepted_request_id)
        VALUES ({sql_literal(receiver)}, {sql_literal(requester)}, {sql_literal(request_id)})
        ON DUPLICATE KEY UPDATE accepted_request_id = VALUES(accepted_request_id)
        """,
    ])
    return {"ok": True}


def login_admin(data):
    admin_id = require_value(data, "admin_id")
    password = require_value(data, "password")
    rows = run_sql(f"""
        SELECT admin_id
        FROM admins
        WHERE admin_id = {sql_literal(admin_id)}
          AND password_hash = SHA2({sql_literal(password)}, 256)
        LIMIT 1
    """)
    if not rows:
        raise ValueError("管理员 ID 或密码错误")
    return {"ok": True, "admin_id": admin_id}


def update_admin(data):
    admin_id = require_value(data, "admin_id")
    name = require_value(data, "name")
    require_exists(
        f"SELECT 1 AS ok FROM admins WHERE admin_id = {sql_literal(admin_id)} LIMIT 1",
        "管理员不存在，无法修改资料",
    )
    execute(f"""
        UPDATE admins
        SET name = {sql_literal(name)}
        WHERE admin_id = {sql_literal(admin_id)}
    """)
    return {"ok": True}


def admin_set_post_status(data, post_status):
    admin_id = require_value(data, "admin_id")
    post_id = require_value(data, "post_id")
    if post_status not in {"visible", "blocked"}:
        raise ValueError("post_status 不合法")
    require_exists(
        f"SELECT 1 AS ok FROM admins WHERE admin_id = {sql_literal(admin_id)} LIMIT 1",
        "管理员不存在，无法审核朋友圈",
    )
    rows = run_sql(f"""
        SELECT user_id, content
        FROM posts
        WHERE post_id = {sql_literal(post_id)}
        LIMIT 1
    """)
    if not rows:
        raise ValueError("朋友圈不存在")
    target_user_id = rows[0]["user_id"]
    content_snapshot = rows[0]["content"]
    action = "BLOCK_POST" if post_status == "blocked" else "UNBLOCK_POST"
    execute_transaction([
        f"""
        UPDATE posts
        SET post_status = {sql_literal(post_status)}
        WHERE post_id = {sql_literal(post_id)}
        """,
        f"""
        INSERT INTO audit_logs (admin_id, target_post_id, target_user_id, action, content_snapshot)
        VALUES (
            {sql_literal(admin_id)},
            {sql_literal(post_id)},
            {sql_literal(target_user_id)},
            {sql_literal(action)},
            {sql_literal(content_snapshot)}
        )
        """,
    ])
    return {"ok": True}


def admin_delete_user(data):
    admin_id = require_value(data, "admin_id")
    target_user_id = require_value(data, "target_user_id")
    require_exists(
        f"SELECT 1 AS ok FROM admins WHERE admin_id = {sql_literal(admin_id)} LIMIT 1",
        "管理员不存在，无法注销用户",
    )
    require_exists(
        f"SELECT 1 AS ok FROM users WHERE user_id = {sql_literal(target_user_id)} LIMIT 1",
        "要注销的用户不存在",
    )
    execute_transaction([
        f"""
        INSERT INTO audit_logs (admin_id, target_user_id, action, content_snapshot)
        VALUES ({sql_literal(admin_id)}, {sql_literal(target_user_id)}, 'DELETE_USER', '管理员注销用户')
        """,
        f"""
        DELETE FROM users
        WHERE user_id = {sql_literal(target_user_id)}
        """,
    ])
    return {"ok": True}


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Lab5 demo server: http://{HOST}:{PORT}")
    server.serve_forever()
