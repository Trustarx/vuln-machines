"use strict";
const express = require("express");
const jwt     = require("jsonwebtoken");

const app = express();
app.use(express.json());

// ── Must match the secret leaked in app.js + app.js.map ──────────────────────
const JWT_SECRET = "nexus-jwt-hs256-pr0d-k3y-2024!";

const USERS = [
  { id: 1, username: "admin",  password: "Nexus@dm1n2024!",  role: "admin"  },
  { id: 2, username: "alice",  password: "alice123",          role: "user"   },
  { id: 3, username: "bob",    password: "bob123",            role: "user"   },
  { id: 4, username: "deploy", password: "d3pl0y-svc-pass!",  role: "service"},
];

function auth(req, res, next) {
  const header = req.headers.authorization || "";
  const token  = header.replace("Bearer ", "");
  if (!token) return res.status(401).json({ error: "No token" });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: "Invalid token" });
  }
}

function adminOnly(req, res, next) {
  if (req.user.role !== "admin") return res.status(403).json({ error: "Admin only" });
  next();
}

// ── Public ────────────────────────────────────────────────────────────────────
app.post("/api/v1/auth/login", (req, res) => {
  const { username, password } = req.body;
  const user = USERS.find(u => u.username === username && u.password === password);
  if (!user) return res.status(401).json({ error: "Invalid credentials" });
  const token = jwt.sign(
    { id: user.id, username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: "8h" }
  );
  res.json({ token });
});

// ── Authenticated ─────────────────────────────────────────────────────────────
app.get("/api/v1/users/me", auth, (req, res) => {
  const user = USERS.find(u => u.id === req.user.id);
  const { password, ...safe } = user;
  res.json(safe);
});

app.get("/api/v1/users", auth, (req, res) => {
  res.json(USERS.map(({ password, ...u }) => u));
});

// ── Admin ─────────────────────────────────────────────────────────────────────
app.get("/api/v1/admin/users", auth, adminOnly, (req, res) => {
  // Returns passwords — only accessible with valid admin JWT
  res.json(USERS);
});

app.get("/api/v1/admin/flag", auth, adminOnly, (req, res) => {
  res.json({
    flag: "FLAG{spa_js_source_analysis_jwt_secret_leaked}",
    note: "Found via JWT secret in app.js / app.js.map → forge admin token → hit this endpoint"
  });
});

// ── Finding: debug dump endpoint never removed (SEC-388) ─────────────────────
// No auth — leaks all users including service account password
app.get("/api/v1/debug/dump", (req, res) => {
  res.json({
    warning: "DEBUG ENDPOINT — disable in production",
    users: USERS,
    env: {
      NODE_ENV: process.env.NODE_ENV || "development",
      jwt_secret: JWT_SECRET,
    }
  });
});

app.get("/api/v1/health", (req, res) => res.json({ status: "ok" }));

app.listen(3000, () => console.log("[spa-lab] backend listening on :3000"));
