const POLL_MS = 3000;
const UNITS = { celsius: "°C", percent: "%" };

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).detail;
    } catch (e) {}
    throw new Error(detail || "HTTP " + res.status);
  }
  return res.status === 204 ? null : res.json();
}

function ago(iso) {
  // SQLite CURRENT_TIMESTAMP is UTC without a timezone suffix.
  const seconds = Math.max(0, Math.round((Date.now() - new Date(iso + "Z")) / 1000));
  if (seconds < 60) return seconds + " giây trước";
  if (seconds < 3600) return Math.round(seconds / 60) + " phút trước";
  return Math.round(seconds / 3600) + " giờ trước";
}

function setMessage(text) {
  document.getElementById("msg").textContent = text || "";
}

function renderDevices(devices, roomNames) {
  const box = document.getElementById("devices");
  box.replaceChildren();
  if (!devices.length) box.append(el("div", "empty", "Chưa có thiết bị."));

  for (const device of devices) {
    const card = el("div", "card");
    card.append(el("div", "name", device.name));
    card.append(el("div", "meta", (roomNames[device.room_id] || "?") + " · " + device.device_id));
    card.append(el("div", "online" + (device.is_online ? " up" : ""), device.is_online ? "● Online" : "○ Offline"));

    if (device.device_type === "light") {
      const isOn = device.state === "on";
      card.append(el("div", "state" + (isOn ? " on" : ""), isOn ? "ĐANG BẬT" : "ĐANG TẮT"));

      const button = el("button", "", isOn ? "Tắt" : "Bật");
      button.addEventListener("click", () => sendCommand(device, isOn ? "off" : "on", button));
      card.append(button);
    }
    box.append(card);
  }
}

function renderSensors(sensors, latest, devices) {
  const deviceById = Object.fromEntries(devices.map((d) => [d.id, d]));
  const box = document.getElementById("sensors");
  box.replaceChildren();
  if (!sensors.length) box.append(el("div", "empty", "Chưa có cảm biến."));

  sensors.forEach((sensor, i) => {
    const reading = latest[i] && latest[i][0];
    const card = el("div", "card");
    card.append(el("div", "name", sensor.name));

    const parent = deviceById[sensor.device_id];
    if (parent && !parent.is_online) card.append(el("div", "online", "○ Thiết bị offline"));

    if (reading) {
      const unit = UNITS[sensor.unit] || sensor.unit;
      card.append(el("div", "value", reading.value.toFixed(1) + " " + unit));
      card.append(el("div", "meta", "Cập nhật " + ago(reading.recorded_at)));
    } else {
      card.append(el("div", "meta", "Chưa có dữ liệu"));
    }
    box.append(card);
  });
}

async function sendCommand(device, command, button) {
  button.disabled = true;
  setMessage("");
  try {
    await api("/devices/" + device.id + "/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command }),
    });
    // The state changes only after the ESP32 confirms it over MQTT.
    setTimeout(refresh, 800);
  } catch (err) {
    setMessage("Không gửi được lệnh: " + err.message);
    button.disabled = false;
  }
}

async function refresh() {
  const status = document.getElementById("status");
  try {
    const [rooms, devices, sensors] = await Promise.all([
      api("/rooms"),
      api("/devices"),
      api("/sensors"),
    ]);
    const latest = await Promise.all(
      sensors.map((s) => api("/sensors/" + s.id + "/readings?limit=1"))
    );

    const roomNames = Object.fromEntries(rooms.map((r) => [r.id, r.name]));
    renderDevices(devices, roomNames);
    renderSensors(sensors, latest, devices);

    status.className = "";
    status.textContent = "Cập nhật lúc " + new Date().toLocaleTimeString();
  } catch (err) {
    status.className = "error";
    status.textContent = "Mất kết nối backend";
  }
}

refresh();
setInterval(refresh, POLL_MS);
