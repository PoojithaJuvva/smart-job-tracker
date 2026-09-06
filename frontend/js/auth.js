document.addEventListener("DOMContentLoaded", () => {
  // If already logged in, skip straight to the dashboard.
  if (TokenStore.getAccess()) {
    window.location.href = "dashboard.html";
    return;
  }

  const tabButtons = document.querySelectorAll(".tab-btn");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const tab = btn.dataset.tab;
      loginForm.classList.toggle("hidden", tab !== "login");
      registerForm.classList.toggle("hidden", tab !== "register");
    });
  });

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("login-error");
    errorEl.textContent = "";
    try {
      const data = await Api.login({
        email: document.getElementById("login-email").value.trim(),
        password: document.getElementById("login-password").value,
      });
      TokenStore.set(data.access_token, data.refresh_token);
      TokenStore.setUser(data.user);
      window.location.href = "dashboard.html";
    } catch (err) {
      errorEl.textContent = err.message || "Login failed.";
    }
  });

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("register-error");
    errorEl.textContent = "";
    try {
      const data = await Api.register({
        name: document.getElementById("register-name").value.trim(),
        email: document.getElementById("register-email").value.trim(),
        password: document.getElementById("register-password").value,
      });
      TokenStore.set(data.access_token, data.refresh_token);
      TokenStore.setUser(data.user);
      window.location.href = "dashboard.html";
    } catch (err) {
      errorEl.textContent = err.message || "Registration failed.";
    }
  });
});
