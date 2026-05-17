// NebulaCMS — main UI controller
"use strict";

const App = {
  tab(which) {
    const showLogin = which === "login";
    document.getElementById("form-login").classList.toggle("d-none", !showLogin);
    document.getElementById("form-register").classList.toggle("d-none", showLogin);
    document.getElementById("tab-login").classList.toggle("active", showLogin);
    document.getElementById("tab-register").classList.toggle("active", !showLogin);
  },

  async login() {
    const username = document.getElementById("li-user").value;
    const password = document.getElementById("li-pass").value;
    const r = await Api.gql(Api.M_LOGIN, { username, password });
    if (r.errors) {
      document.getElementById("auth-err").textContent = r.errors[0].message;
      return;
    }
    localStorage.setItem("nebula_token", r.data.login.token);
    this.showApp();
  },

  async register() {
    const username = document.getElementById("rg-user").value;
    const email    = document.getElementById("rg-email").value;
    const password = document.getElementById("rg-pass").value;
    const r = await Api.gql(Api.M_REGISTER, { username, email, password });
    if (r.errors) {
      document.getElementById("auth-err").textContent = r.errors[0].message;
      return;
    }
    localStorage.setItem("nebula_token", r.data.register.token);
    this.showApp();
  },

  async showApp() {
    const me = await Api.gql(Api.Q_ME);
    if (me.errors || !me.data || !me.data.me) { this.logout(); return; }
    document.getElementById("nav-user").textContent =
      `${me.data.me.username} (${me.data.me.role})`;
    document.getElementById("view-auth").classList.add("d-none");
    document.getElementById("view-app").classList.remove("d-none");

    const arts = await Api.gql(Api.Q_MY_ARTICLES);
    const list = (arts.data && arts.data.me && arts.data.me.articles) || [];
    document.getElementById("article-list").innerHTML = list.length
      ? `<ul class="list-group">${list.map(a =>
          `<li class="list-group-item"><strong>${a.title}</strong>
           <br><small class="text-muted">${a.excerpt || "(no excerpt)"}</small></li>`
        ).join("")}</ul>`
      : `<p class="text-muted">No articles yet.</p>`;
  },

  logout() {
    localStorage.removeItem("nebula_token");
    location.reload();
  },
};

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("nebula_token")) App.showApp();
});
