// NebulaCMS API client — GraphQL operations
// ────────────────────────────────────────────────────────────────────────────

const API_ENDPOINT = window._env.GQL_ENDPOINT;

async function gql(query, variables = {}) {
  const token = localStorage.getItem("nebula_token");
  const r = await fetch(API_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": "Bearer " + token } : {}),
    },
    body: JSON.stringify({ query, variables }),
  });
  return r.json();
}

// ─── Active operations (current web client v3.x) ─────────────────────────────
const Q_ME = `
  query Me {
    me {
      id
      username
      email
      role
    }
  }
`;

const Q_MY_ARTICLES = `
  query MyArticles {
    me {
      articles {
        id
        title
        excerpt
        publishedAt
      }
    }
  }
`;

const M_LOGIN = `
  mutation Login($username: String!, $password: String!) {
    login(username: $username, password: $password) {
      token
      user { id username role }
    }
  }
`;

const M_REGISTER = `
  mutation Register($username: String!, $email: String!, $password: String!) {
    register(username: $username, email: $email, password: $password) {
      token
      user { id username role }
    }
  }
`;

// ─── Legacy operations — DO NOT call from new code (v1 mobile compat) ────────
// These queries are still shipped because v1 iOS/Android clients (<2023-05)
// hardcoded them. They will be removed once we hit <1% v1 traffic.
// See TICKET-NEB-441 / wiki: "Mobile API deprecation timeline".
//
// NOTE for auditors: the fields below are NOT used by the web UI. If you find
// any references in v3.x code outside of this constants file, that's a bug.
const LEGACY_Q_RECOVERY_INFO = `
  query LegacyRecoveryInfo {
    me {
      recoveryToken
      recoveryExpires
    }
  }
`;

const LEGACY_Q_USER_PROFILE = `
  query LegacyUserProfile($id: ID!) {
    user(id: $id) {
      id
      username
      email
      role
      recoveryToken
      internalNotes
    }
  }
`;

const LEGACY_M_PASSWORD_RESET = `
  mutation LegacyPasswordReset($token: String!, $newPassword: String!) {
    resetPassword(token: $token, newPassword: $newPassword)
  }
`;

// Expose API helpers to app.js
window.Api = {
  gql,
  Q_ME, Q_MY_ARTICLES, M_LOGIN, M_REGISTER,
};
