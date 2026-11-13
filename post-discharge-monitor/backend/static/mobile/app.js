const API = "../api/mobile";
const tokenKey = "minearena-doctor-token";
const loginPanel = document.querySelector("#login-panel");
const inboxPanel = document.querySelector("#inbox-panel");
const alertsContainer = document.querySelector("#alerts");
const statusMessage = document.querySelector("#status-message");
const newAlertBanner = document.querySelector("#new-alert-banner");
let accessToken = sessionStorage.getItem(tokenKey) || "";
let knownAlertIds = null;

function authHeaders() {
  return { Authorization: `Bearer ${accessToken}` };
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function setSignedIn(signedIn) {
  loginPanel.classList.toggle("hidden", signedIn);
  inboxPanel.classList.toggle("hidden", !signedIn);
  document.querySelector("#sign-out").classList.toggle("hidden", !signedIn);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function localTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? escapeHtml(value) : escapeHtml(date.toLocaleString());
}

function renderAlerts(items) {
  const alertIds = new Set(items.map((item) => String(item.id)));
  if (knownAlertIds !== null) {
    const newAlerts = items.filter((item) => !knownAlertIds.has(String(item.id)));
    if (newAlerts.length) {
      newAlertBanner.textContent = newAlerts.length === 1
        ? `New ${newAlerts[0].severity} alert received. Review the inbox below.`
        : `${newAlerts.length} new alerts received. Review the inbox below.`;
      newAlertBanner.classList.remove("hidden");
    }
  }
  knownAlertIds = alertIds;

  const openCount = items.filter((item) => !item.acknowledged_at).length;
  document.querySelector("#open-count").textContent = String(openCount);
  document.querySelector("#total-count").textContent = String(items.length);
  if (!items.length) {
    alertsContainer.innerHTML = '<div class="empty-state">No alerts yet. New monitor alerts will appear here.</div>';
    return;
  }
  alertsContainer.innerHTML = items.map((item) => {
    const id = Number(item.id);
    const severity = escapeHtml(item.severity);
    const acknowledged = item.acknowledged_at
      ? `<p class="acknowledged">Acknowledged · ${localTime(item.acknowledged_at)}</p>`
      : `<button class="quiet-button acknowledge-button" data-acknowledge="${id}" type="button">Acknowledge</button>`;
    return `
      <article class="alert-card" data-severity="${severity}" id="alert-${id}">
        <div class="alert-heading">
          <h3>${escapeHtml(item.patient_name)} · ${escapeHtml(item.patient_id)}</h3>
          <span class="badge">${severity}</span>
        </div>
        <p>${escapeHtml(item.message)}</p>
        <p class="action">Suggested next step: ${escapeHtml(item.recommended_action)}</p>
        <span class="alert-meta">Rule ${escapeHtml(item.rule_id)} · ${localTime(item.created_at)}</span>
        ${acknowledged}
      </article>`;
  }).join("");

  alertsContainer.querySelectorAll("[data-acknowledge]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await apiRequest(`/doctor/alerts/${button.dataset.acknowledge}/acknowledge`, { method: "PATCH" });
        await refreshAlerts();
      } catch (error) {
        button.disabled = false;
        statusMessage.textContent = error.message;
      }
    });
  });

  const targetId = new URLSearchParams(location.search).get("alertId");
  if (targetId) {
    document.querySelector(`#alert-${CSS.escape(targetId)}`)?.scrollIntoView({ behavior: "smooth" });
    history.replaceState({}, "", location.pathname);
  }
}

async function refreshAlerts() {
  const result = await apiRequest("/doctor/alerts");
  renderAlerts(result.alerts);
}

function base64UrlToBytes(base64Url) {
  const padding = "=".repeat((4 - base64Url.length % 4) % 4);
  const base64 = (base64Url + padding).replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(base64), (character) => character.charCodeAt(0));
}

async function enablePush() {
  if (!window.isSecureContext) {
    throw new Error("Phone notifications require HTTPS. This local Wi-Fi address can show the inbox, but cannot enable push.");
  }
  if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
    throw new Error("Web Push is unavailable in this browser. The inbox still updates while open. On iPhone or iPad, add the app to your Home Screen and open it there.");
  }
  const permission = await Notification.requestPermission();
  if (permission !== "granted") throw new Error("Notification permission was not granted.");

  const { public_key: publicKey } = await apiRequest("/doctor/push-key");
  const registration = await navigator.serviceWorker.register("./service-worker.js");
  await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: base64UrlToBytes(publicKey),
    });
  }
  await apiRequest("/doctor/push-subscriptions", {
    method: "POST",
    body: JSON.stringify(subscription),
  });
  statusMessage.textContent = "Phone alerts are enabled on this device.";
}

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const errorMessage = document.querySelector("#login-error");
  const code = document.querySelector("#access-code").value;
  try {
    const response = await fetch(`${API}/doctor/session`, {
      method: "POST",
      headers: { Authorization: `Bearer ${code}` },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Could not sign in.");
    }
    accessToken = code;
    sessionStorage.setItem(tokenKey, accessToken);
    errorMessage.textContent = "";
    setSignedIn(true);
    await refreshAlerts();
  } catch (error) {
    errorMessage.textContent = error.message;
    accessToken = "";
    sessionStorage.removeItem(tokenKey);
  }
});

document.querySelector("#sign-out").addEventListener("click", () => {
  accessToken = "";
  knownAlertIds = null;
  newAlertBanner.classList.add("hidden");
  sessionStorage.removeItem(tokenKey);
  setSignedIn(false);
  alertsContainer.replaceChildren();
});

document.querySelector("#enable-push").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  statusMessage.textContent = "";
  try {
    await enablePush();
  } catch (error) {
    statusMessage.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

if (accessToken) {
  apiRequest("/doctor/session", { method: "POST" })
    .then(() => {
      setSignedIn(true);
      return refreshAlerts();
    })
    .catch(() => {
      accessToken = "";
      sessionStorage.removeItem(tokenKey);
      setSignedIn(false);
    });
} else {
  setSignedIn(false);
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./service-worker.js").catch((error) => {
    console.error("Service worker registration failed", error);
  });
}

window.setInterval(() => {
  if (accessToken) refreshAlerts().catch((error) => {
    statusMessage.textContent = error.message;
  });
}, 30000);
