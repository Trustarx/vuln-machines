"use strict";
const express = require("express");
const cors    = require("cors");
const bodyParser = require("body-parser");
const jwt = require("jsonwebtoken");
const { ApolloServer } = require("@apollo/server");
const { expressMiddleware } = require("@apollo/server/express4");
const gql = require("graphql-tag");
const crypto = require("crypto");

const JWT_SECRET = crypto.randomBytes(32).toString("hex");
const PORT = 4000;

// ─── In-memory data ──────────────────────────────────────────────────────────
let nextUserId = 1;
const USERS = [];
const ARTICLES = [];

function makeUser({ username, email, password, role = "author" }) {
  const u = {
    id: String(nextUserId++),
    username, email, password, role,
    recoveryToken: crypto.randomBytes(16).toString("hex"),
    recoveryExpires: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
    internalNotes: "",
  };
  USERS.push(u);
  return u;
}

const admin = makeUser({
  username: "admin", email: "admin@nebulacms.io",
  password: "N3bul@_Adm1n!2024", role: "admin",
});
admin.internalNotes = "ROOT EDITORIAL — flag: FLAG{graphql_field_level_authz_bypass_recovery_token}";

makeUser({ username: "alice",   email: "alice@nebulacms.io",   password: "alice-2024",   role: "author" });
makeUser({ username: "bob",     email: "bob@nebulacms.io",     password: "bob-2024",     role: "author" });
makeUser({ username: "charlie", email: "charlie@nebulacms.io", password: "charlie-2024", role: "reader" });

ARTICLES.push({ id: "1", authorId: "1", title: "Welcome to NebulaCMS", excerpt: "Editorial platform notes", publishedAt: "2024-08-22" });
ARTICLES.push({ id: "2", authorId: "2", title: "Drafting tips for newsroom",   excerpt: "How alice writes",      publishedAt: "2024-08-19" });
ARTICLES.push({ id: "3", authorId: "3", title: "Embargoes and you",            excerpt: "Bob's column",          publishedAt: "2024-08-12" });

// ─── Schema ──────────────────────────────────────────────────────────────────
const typeDefs = gql`
  type User {
    id: ID!
    username: String!
    email: String!
    role: String!
    articles: [Article!]!

    # ── Legacy fields kept for v1 mobile API compatibility ──
    # TICKET-NEB-441: remove after mobile v1 sunset
    recoveryToken: String
    recoveryExpires: String
    internalNotes: String
  }

  type Article {
    id: ID!
    title: String!
    excerpt: String
    publishedAt: String
    author: User!
  }

  type AuthPayload {
    token: String!
    user: User!
  }

  type Query {
    me: User
    user(id: ID!): User
    users: [User!]!
  }

  type Mutation {
    login(username: String!, password: String!): AuthPayload!
    register(username: String!, email: String!, password: String!): AuthPayload!
    resetPassword(token: String!, newPassword: String!): Boolean!
  }
`;

// ─── Auth helpers ────────────────────────────────────────────────────────────
function authedUser(ctx) {
  if (!ctx.user) throw new Error("Not authenticated");
  return ctx.user;
}
function adminOnly(ctx) {
  const u = authedUser(ctx);
  if (u.role !== "admin") throw new Error("Forbidden");
  return u;
}

// ─── Resolvers ───────────────────────────────────────────────────────────────
const resolvers = {
  Query: {
    me: (_, __, ctx) => {
      authedUser(ctx);
      return USERS.find(u => u.id === ctx.user.id);
    },
    // VULN: requires authentication, but no per-field authz —
    // any logged-in user can look up any other user including admin
    // and pull `recoveryToken` / `internalNotes`.
    user: (_, { id }, ctx) => {
      authedUser(ctx);
      return USERS.find(u => u.id === String(id));
    },
    users: (_, __, ctx) => {
      adminOnly(ctx);
      return USERS;
    },
  },

  Mutation: {
    login: (_, { username, password }) => {
      const u = USERS.find(x => x.username === username && x.password === password);
      if (!u) throw new Error("Invalid credentials");
      const token = jwt.sign({ id: u.id, username: u.username, role: u.role }, JWT_SECRET, { expiresIn: "8h" });
      return { token, user: u };
    },
    register: (_, { username, email, password }) => {
      if (USERS.some(u => u.username === username)) throw new Error("Username taken");
      const u = makeUser({ username, email, password, role: "author" });
      const token = jwt.sign({ id: u.id, username: u.username, role: u.role }, JWT_SECRET, { expiresIn: "8h" });
      return { token, user: u };
    },
    // VULN: trusts any valid recoveryToken regardless of who's calling.
    // Combined with field-level authz bypass above, attacker can read admin's
    // recoveryToken via Q user(id: "1") and pass it here.
    resetPassword: (_, { token, newPassword }) => {
      const u = USERS.find(x => x.recoveryToken === token);
      if (!u) throw new Error("Invalid recovery token");
      u.password = newPassword;
      // Rotate the recovery token after use (real apps do this)
      u.recoveryToken = crypto.randomBytes(16).toString("hex");
      return true;
    },
  },

  User: {
    articles: (parent) => ARTICLES.filter(a => a.authorId === parent.id),
  },
  Article: {
    author: (parent) => USERS.find(u => u.id === parent.authorId),
  },
};

// ─── Server bootstrap ────────────────────────────────────────────────────────
async function start() {
  const app = express();
  app.use(cors());
  app.use(bodyParser.json());

  const server = new ApolloServer({
    typeDefs,
    resolvers,
    introspection: false,                       // forces use of JS-leaked field names
    formatError: (formattedError) => ({         // hide stack traces
      message: formattedError.message,
    }),
  });
  await server.start();

  app.use("/graphql", expressMiddleware(server, {
    context: async ({ req }) => {
      const auth = req.headers.authorization || "";
      const token = auth.replace("Bearer ", "");
      if (!token) return {};
      try {
        const user = jwt.verify(token, JWT_SECRET);
        return { user };
      } catch {
        return {};
      }
    },
  }));

  app.get("/health", (_, res) => res.json({ status: "ok" }));

  app.listen(PORT, () => console.log(`[graphql-lab] backend on :${PORT}`));
}

start();
