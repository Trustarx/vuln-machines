/**
 * Intentionally Vulnerable REST API
 * -----------------------------------
 * FOR EDUCATIONAL / PENTESTING PRACTICE ONLY.
 * DO NOT deploy on any network accessible to untrusted users.
 *
 * Vulnerabilities:
 *   1. IDOR           - GET /api/users/:id, GET /api/users/:id/notes
 *   2. Mass assignment - PUT /api/users/:id
 *   3. JWT alg:none   - Bearer tokens with algorithm "none" accepted
 *   4. Weak JWT secret - Secret is "secret", easily brute-forced
 *   5. Broken auth    - Admin endpoints only check token presence, not validity
 *   6. SQLi           - GET /api/products/search?q=
 *   7. Excessive data - Responses include password hashes & internal fields
 */

const express    = require("express");
const jwt        = require("jsonwebtoken");
const bcrypt     = require("bcryptjs");
const bodyParser = require("body-parser");
const Database   = require("better-sqlite3");

const app = express();
const JWT_SECRET = "secret"; // VULN: weak secret, brutable with hashcat/john

app.use(bodyParser.json());

// Access logger
app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    const ms = Date.now() - start;
    const status = res.statusCode;
    const flag = status >= 200 && status < 300 ? "✅" : status >= 400 ? "❌" : "➡️";
    console.log(`${flag} ${status} ${req.method} ${req.path} (${ms}ms) ip=${req.ip} body=${JSON.stringify(req.body || {}).slice(0,120)}`);
  });
  next();
});

// ─── Database seed ────────────────────────────────────────────────────────────
const db = new Database(":memory:");

db.exec(`
  CREATE TABLE users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email    TEXT NOT NULL,
    role     TEXT DEFAULT 'user',
    balance  INTEGER DEFAULT 0,
    api_key  TEXT
  );

  CREATE TABLE notes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL
  );

  CREATE TABLE products (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT,
    price REAL
  );
`);

// Seed users
const hash = (p) => bcrypt.hashSync(p, 8);
db.prepare("INSERT INTO users (username, password, email, role, balance, api_key) VALUES (?, ?, ?, ?, ?, ?)")
  .run("admin",   hash("AdminP@ss2024"), "admin@corp.internal",  "admin", 99999, "sk-admin-f3a1b2c3d4e5f6a7");
db.prepare("INSERT INTO users (username, password, email, role, balance, api_key) VALUES (?, ?, ?, ?, ?, ?)")
  .run("alice",   hash("alice123"),      "alice@corp.internal",  "user",  500,   "sk-alice-aabbccddeeff");
db.prepare("INSERT INTO users (username, password, email, role, balance, api_key) VALUES (?, ?, ?, ?, ?, ?)")
  .run("bob",     hash("bob123"),        "bob@corp.internal",    "user",  250,   "sk-bob-112233445566");
db.prepare("INSERT INTO users (username, password, email, role, balance, api_key) VALUES (?, ?, ?, ?, ?, ?)")
  .run("charlie", hash("charlie123"),    "charlie@corp.internal","user",  100,   "sk-charlie-99887766");

// Seed notes
db.prepare("INSERT INTO notes (user_id, content) VALUES (?, ?)").run(1, "TODO: rotate the prod DB password (current: Sup3rS3cr3t_DB_2024!)");
db.prepare("INSERT INTO notes (user_id, content) VALUES (?, ?)").run(1, "AWS key backup: AKIAIOSFODNN7EXAMPLE / wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY");
db.prepare("INSERT INTO notes (user_id, content) VALUES (?, ?)").run(2, "My personal note - only I should see this");
db.prepare("INSERT INTO notes (user_id, content) VALUES (?, ?)").run(3, "Bob's private note");

// Seed products
["Widget A","Widget B","Gadget Pro","SuperTool"].forEach((name, i) =>
  db.prepare("INSERT INTO products (name, price) VALUES (?, ?)").run(name, (i + 1) * 9.99)
);

// ─── Helpers ──────────────────────────────────────────────────────────────────

// VULN: accepts alg:none — no signature verification if header says "none"
function parseToken(token) {
  try {
    const [headerB64] = token.split(".");
    const header = JSON.parse(Buffer.from(headerB64, "base64").toString());
    if (header.alg && header.alg.toLowerCase() === "none") {
      // alg:none — decode payload without verifying signature
      const payloadB64 = token.split(".")[1];
      return JSON.parse(Buffer.from(payloadB64, "base64").toString());
    }
    return jwt.verify(token, JWT_SECRET);
  } catch {
    return null;
  }
}

function authMiddleware(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth) return res.status(401).json({ error: "No token provided" });
  const token = auth.replace("Bearer ", "");
  const payload = parseToken(token);
  if (!payload) return res.status(401).json({ error: "Invalid token" });
  req.user = payload;
  next();
}

// VULN: broken admin check — only checks that a token exists, not that role===admin
function adminMiddleware(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth) return res.status(403).json({ error: "Admin only" });
  // Missing: actual role check!
  next();
}

// ─── Routes ───────────────────────────────────────────────────────────────────

// POST /api/register
app.post("/api/register", (req, res) => {
  const { username, password, email } = req.body;
  if (!username || !password || !email)
    return res.status(400).json({ error: "username, password, email required" });
  try {
    db.prepare("INSERT INTO users (username, password, email) VALUES (?, ?, ?)")
      .run(username, hash(password), email);
    res.json({ message: "Registered successfully" });
  } catch {
    res.status(409).json({ error: "Username taken" });
  }
});

// POST /api/login
app.post("/api/login", (req, res) => {
  const { username, password } = req.body;
  const user = db.prepare("SELECT * FROM users WHERE username = ?").get(username);
  if (!user || !bcrypt.compareSync(password, user.password))
    return res.status(401).json({ error: "Invalid credentials" });

  // VULN: weak secret used for signing
  const token = jwt.sign(
    { id: user.id, username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: "24h" }
  );

  // VULN: excessive data exposure — returns hash and api_key on login
  res.json({ token, user });
});

// GET /api/users  — requires auth
app.get("/api/users", authMiddleware, (req, res) => {
  // VULN: excessive data exposure — returns password hashes
  const users = db.prepare("SELECT * FROM users").all();
  res.json(users);
});

// GET /api/users/:id  — VULN: IDOR, no ownership check
app.get("/api/users/:id", authMiddleware, (req, res) => {
  const user = db.prepare("SELECT * FROM users WHERE id = ?").get(req.params.id);
  if (!user) return res.status(404).json({ error: "Not found" });
  res.json(user); // VULN: also returns password hash and api_key
});

// PUT /api/users/:id  — VULN: mass assignment + IDOR
app.put("/api/users/:id", authMiddleware, (req, res) => {
  const user = db.prepare("SELECT * FROM users WHERE id = ?").get(req.params.id);
  if (!user) return res.status(404).json({ error: "Not found" });

  // VULN: no ownership check (IDOR) + directly merges user-supplied fields (mass assignment)
  // Attacker can set role:"admin" or balance:999999
  const fields = req.body;
  const updates = Object.keys(fields).map(k => `${k} = ?`).join(", ");
  const values  = [...Object.values(fields), req.params.id];

  try {
    db.prepare(`UPDATE users SET ${updates} WHERE id = ?`).run(...values);
    res.json({ message: "Updated", user: db.prepare("SELECT * FROM users WHERE id = ?").get(req.params.id) });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

// GET /api/users/:id/notes  — VULN: IDOR, no ownership check
app.get("/api/users/:id/notes", authMiddleware, (req, res) => {
  const notes = db.prepare("SELECT * FROM notes WHERE user_id = ?").all(req.params.id);
  res.json(notes);
});

// GET /api/products/search?q=  — VULN: SQLi
app.get("/api/products/search", (req, res) => {
  const q = req.query.q || "";
  try {
    // VULN: raw string interpolation into SQL
    const results = db.prepare(`SELECT * FROM products WHERE name LIKE '%${q}%'`).all();
    res.json(results);
  } catch (e) {
    res.status(500).json({ error: e.message, query: q }); // VULN: leaks query in error
  }
});

// GET /api/admin/users  — VULN: broken admin check
app.get("/api/admin/users", adminMiddleware, (req, res) => {
  const users = db.prepare("SELECT * FROM users").all();
  res.json({ message: "Admin panel", users });
});

// POST /api/admin/flag  — the root flag, guarded by broken admin check
app.get("/api/admin/flag", adminMiddleware, (req, res) => {
  res.json({ flag: "FLAG{api_fully_pwned_idor_mass_jwt_sqli}" });
});

// GET /  — API index
app.get("/", (req, res) => {
  res.json({
    name: "CorpAPI v2.1",
    endpoints: [
      "POST /api/register",
      "POST /api/login",
      "GET  /api/users            [auth]",
      "GET  /api/users/:id        [auth]",
      "PUT  /api/users/:id        [auth]",
      "GET  /api/users/:id/notes  [auth]",
      "GET  /api/products/search?q=",
      "GET  /api/admin/users      [admin]",
      "GET  /api/admin/flag       [admin]"
    ]
  });
});

app.listen(3000, "0.0.0.0", () => {
  console.log("CorpAPI v2.1 running on :3000");
  console.log("FLAG location: GET /api/admin/flag");
});
