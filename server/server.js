/**
 * 轻盈工作台 · 数据同步后端（账号版）
 * 每个用户注册独立账号，数据按用户分文件存储，互不可见。
 * 密码用 scrypt 哈希，登录后发 token（存在 sessions.json，重启不丢）。
 * 依赖仅 express + cors，密码哈希用 Node 内置 crypto，无需额外依赖。
 */
const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const USERS_FILE = path.join(__dirname, 'users.json');
const SESSIONS_FILE = path.join(__dirname, 'sessions.json');
const DATA_DIR = path.join(__dirname, 'data');

function ensureFiles() {
  for (const f of [USERS_FILE, SESSIONS_FILE]) {
    if (!fs.existsSync(f)) fs.writeFileSync(f, JSON.stringify({}));
  }
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}
function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (e) { return {}; }
}
function writeJson(file, obj) {
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

app.use(cors());
app.use(express.json({ limit: '2mb' }));
// 前端静态文件（与后端同源，避免 HTTPS 页面访问 HTTP 接口被浏览器拦截）
app.use(express.static(path.join(__dirname, 'public')));

/* ---------- 密码哈希（scrypt + 随机盐） ---------- */
function hashPassword(pw, salt) {
  return crypto.scryptSync(String(pw), salt, 32).toString('hex');
}
function newSalt() { return crypto.randomBytes(16).toString('hex'); }
function newToken() { return crypto.randomBytes(24).toString('hex'); }

/* ---------- 用户操作 ---------- */
function userExists(name) { return !!readJson(USERS_FILE)[name]; }
function createUser(name, pw) {
  const users = readJson(USERS_FILE);
  const salt = newSalt();
  users[name] = { salt, hash: hashPassword(pw, salt) };
  writeJson(USERS_FILE, users);
}
function verifyUser(name, pw) {
  const users = readJson(USERS_FILE);
  const u = users[name];
  if (!u) return false;
  return hashPassword(pw, u.salt) === u.hash;
}
function loginToken(name) {
  const t = newToken();
  const sessions = readJson(SESSIONS_FILE);
  sessions[t] = name;
  writeJson(SESSIONS_FILE, sessions);
  return t;
}
function userByToken(token) {
  if (!token) return null;
  return readJson(SESSIONS_FILE)[token] || null;
}
function logoutToken(token) {
  const sessions = readJson(SESSIONS_FILE);
  if (sessions[token]) { delete sessions[token]; writeJson(SESSIONS_FILE, sessions); }
}
function userDataFile(name) { return path.join(DATA_DIR, name + '.json'); }
function loadData(name) {
  try { return JSON.parse(fs.readFileSync(userDataFile(name), 'utf8')); }
  catch (e) { return {}; }
}
function saveData(name, data) {
  fs.writeFileSync(userDataFile(name), JSON.stringify(data, null, 2));
}

ensureFiles();

/* ---------- 公开接口 ---------- */
app.get('/health', (req, res) => res.json({ ok: true }));

/* 注册 */
app.post('/api/register', (req, res) => {
  const name = String(req.body.username || '').trim().toLowerCase();
  const pw = String(req.body.password || '');
  if (!/^[a-z0-9_]{2,20}$/.test(name)) return res.status(400).json({ error: '用户名需为 2-20 位字母/数字/下划线' });
  if (pw.length < 6) return res.status(400).json({ error: '密码至少 6 位' });
  if (userExists(name)) return res.status(409).json({ error: '该用户名已被注册' });
  createUser(name, pw);
  res.json({ ok: true, token: loginToken(name), username: name });
});

/* 登录 */
app.post('/api/login', (req, res) => {
  const name = String(req.body.username || '').trim().toLowerCase();
  const pw = String(req.body.password || '');
  if (!verifyUser(name, pw)) return res.status(401).json({ error: '用户名或密码不对' });
  res.json({ ok: true, token: loginToken(name), username: name });
});

/* 登出 */
app.post('/api/logout', (req, res) => {
  logoutToken(String(req.headers['x-token'] || ''));
  res.json({ ok: true });
});

/* ---------- 需要登录的接口 ---------- */
app.use('/api', (req, res, next) => {
  const user = userByToken(String(req.headers['x-token'] || ''));
  if (!user) return res.status(401).json({ error: '未登录或登录已过期' });
  req.user = user;
  next();
});

app.get('/api/data', (req, res) => {
  res.json(loadData(req.user));
});
app.put('/api/data', (req, res) => {
  const data = req.body;
  if (!data || typeof data !== 'object') return res.status(400).json({ error: '数据格式不对' });
  saveData(req.user, data);
  res.json({ ok: true, updatedAt: Date.now() });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ 同步服务（账号版）已启动: http://0.0.0.0:${PORT}`);
  console.log(`   用户文件: ${USERS_FILE}`);
  console.log(`   数据目录: ${DATA_DIR}`);
});
