self.addEventListener("push", (event) => {
  let alertId;
  try {
    alertId = event.data ? event.data.json().alertId : undefined;
  } catch {
    alertId = undefined;
  }

  event.waitUntil(
    self.registration.showNotification("New patient alert", {
      body: "A new care-team alert needs review. Open the secure inbox.",
      icon: "./icon.svg",
      badge: "./icon.svg",
      tag: alertId ? `care-alert-${alertId}` : "care-alert",
      data: { url: alertId ? `./?alertId=${encodeURIComponent(alertId)}` : "./" },
      requireInteraction: true,
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = new URL(event.notification.data?.url || "./", self.registration.scope).href;
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
      const existing = windows.find((client) => new URL(client.url).origin === self.location.origin);
      if (existing) {
        existing.navigate(target);
        return existing.focus();
      }
      return clients.openWindow(target);
    }),
  );
});
