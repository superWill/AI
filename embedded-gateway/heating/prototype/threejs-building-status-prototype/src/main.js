/**
 * PROTOTYPE — The selected stacked-floor building-status view.
 * State is intentionally in-memory only.
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CSS2DObject, CSS2DRenderer } from "three/addons/renderers/CSS2DRenderer.js";

const floorSpacing = 2.25;

const statusMeta = {
  normal: { label: "正常运行", color: 0x19b76b, css: "#19b76b" },
  standby: { label: "待机", color: 0x2878ff, css: "#2878ff" },
  warning: { label: "设备故障", color: 0xf0a11a, css: "#f0a11a" },
  alarm: { label: "报警", color: 0xef4354, css: "#ef4354" },
  offline: { label: "离线", color: 0x7b879b, css: "#7b879b" },
};

const floors = [
  { id: "f3", name: "三层 · 设备间", level: 3 },
  { id: "f2", name: "二层 · 办公区", level: 2 },
  { id: "f1", name: "一层 · 机房", level: 1 },
];

const devices = [
  { id: "cam-03", floor: "f3", type: "camera", icon: "◉", name: "西侧摄像头", ip: "192.168.10.23", status: "normal", x: -4.2, z: -1.8 },
  { id: "smoke-03", floor: "f3", type: "sensor", icon: "◌", name: "烟感 3-08", point: "回路3 / 地址08", status: "normal", x: 2.6, z: 1.6 },
  { id: "cam-02", floor: "f2", type: "camera", icon: "◉", name: "走廊摄像头", ip: "192.168.10.22", status: "warning", x: 3.8, z: -1.6 },
  { id: "door-02", floor: "f2", type: "door", icon: "▯", name: "东侧门禁", point: "DI-02", status: "normal", x: -3.8, z: 1.8 },
  { id: "pump-01", floor: "f1", type: "pump", icon: "↻", name: "循环水泵 1", point: "RS485-1 / 站号01", status: "normal", x: -3.3, z: -1.2 },
  { id: "valve-01", floor: "f1", type: "valve", icon: "◆", name: "调节阀 1", point: "RS485-1 / 站号03", status: "standby", x: 0.3, z: 1.5 },
  { id: "cam-01", floor: "f1", type: "camera", icon: "◉", name: "入口摄像头", ip: "192.168.10.21", status: "normal", x: 4.3, z: 1.7 },
];

const params = new URLSearchParams(location.search);
let selectedFloorId = "f1";
let selectedDeviceId = devices.some((device) => device.id === params.get("device")) ? params.get("device") : "cam-01";
let simulatedAlarm = false;

const app = document.querySelector("#app");

function renderShell() {
  app.innerHTML = `
    <main class="shell variant-a">
      <header class="topbar">
        <div class="brand-mark">◇</div>
        <div class="brand">EdgeAgent One</div>
        <div class="station">黑灯换热站 · 空间监控</div>
        <div class="system-ok"><span class="status-dot"></span>系统正常</div>
      </header>

      <div class="alarm-banner" id="alarm-banner">● 三层烟感 3-08 触发报警，已自动定位</div>
      <aside class="left-panel">
        <p class="eyebrow">Spatial overview</p>
        <h1>楼层总览</h1>
        <p class="subtitle">点击楼层展开，再点击设备查看实时状态。</p>
        <div class="floor-list" id="floor-list"></div>
        <div class="legend">
          ${Object.entries(statusMeta).slice(0, 4).map(([key, meta]) => `
            <div class="legend-item"><span class="mini-dot" style="background:${meta.css}"></span>${meta.label}</div>
          `).join("")}
        </div>
      </aside>

      <section class="viewport" id="viewport"></section>

      <aside class="right-panel">
        <p class="eyebrow">Device status</p>
        <div id="device-details"></div>
      </aside>

      <section class="device-detail-page" id="device-detail-page" aria-hidden="true">
        <div id="device-detail-content"></div>
      </section>

      <div class="tip">拖动旋转 · 滚轮缩放 · 点击楼层或设备</div>
    </main>
  `;
}

renderShell();

const viewport = document.querySelector("#viewport");
const scene = new THREE.Scene();
scene.background = null;
scene.fog = new THREE.Fog(0xedf3fa, 24, 52);

const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 100);
camera.position.set(16, 13, 18);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewport.appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.domElement.className = "label-layer";
viewport.appendChild(labelRenderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 3, 0);
controls.enableDamping = false;
controls.minDistance = 11;
controls.maxDistance = 34;
controls.maxPolarAngle = Math.PI * 0.49;
controls.update();
controls.addEventListener("change", requestRender);

let renderFrameId = 0;

function requestRender() {
  if (!renderFrameId) renderFrameId = requestAnimationFrame(renderFrame);
}

scene.add(new THREE.HemisphereLight(0xffffff, 0x91a3b9, 2.3));
const keyLight = new THREE.DirectionalLight(0xffffff, 3.1);
keyLight.position.set(8, 18, 10);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(1024, 1024);
scene.add(keyLight);

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(13, 64),
  new THREE.MeshStandardMaterial({
    color: 0xdfe9f5,
    transparent: true,
    opacity: 0.7,
    roughness: 0.95,
  }),
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.4;
ground.receiveShadow = true;
scene.add(ground);

const building = new THREE.Group();
building.position.set(-0.9, 0.38, 0);
scene.add(building);
const floorObjects = [];
const deviceObjects = [];
const deviceObjectById = new Map();

function floorY(floor) {
  return (floor.level - 1) * floorSpacing;
}

function makeWall(width, depth, x, z, y) {
  const wall = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.65, depth),
    new THREE.MeshStandardMaterial({
      color: 0xb8cce3,
      transparent: true,
      opacity: 0.82,
      roughness: 0.7,
    }),
  );
  wall.position.set(x, y + 0.42, z);
  wall.castShadow = true;
  return wall;
}

function createFloor(floor) {
  const group = new THREE.Group();
  group.userData = { kind: "floor", floorId: floor.id, baseY: floorY(floor) };
  group.position.y = group.userData.baseY;

  const slab = new THREE.Mesh(
    new THREE.BoxGeometry(13, 0.22, 7.5),
    new THREE.MeshStandardMaterial({
      color: 0xf4f8fd,
      emissive: 0x000000,
      transparent: true,
      opacity: 0.96,
      roughness: 0.72,
      metalness: 0.02,
    }),
  );
  slab.receiveShadow = true;
  slab.castShadow = true;
  slab.userData = { kind: "floor", floorId: floor.id };
  group.add(slab);
  floorObjects.push(slab);

  const edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(slab.geometry),
    new THREE.LineBasicMaterial({ color: 0x7d9abb, transparent: true, opacity: 0.75 }),
  );
  group.add(edge);

  group.add(makeWall(13, 0.12, 0, -3.62, 0));
  group.add(makeWall(0.12, 7.2, -6.35, 0, 0));
  group.add(makeWall(5.2, 0.1, -3.8, 0.2, 0));
  group.add(makeWall(0.1, 3.2, 1.15, 1.9, 0));
  group.add(makeWall(4.1, 0.1, 3.9, -1.5, 0));

  const labelElement = document.createElement("div");
  labelElement.className = "floor-label";
  labelElement.textContent = floor.name;
  labelElement.dataset.floorId = floor.id;
  labelElement.setAttribute("role", "button");
  labelElement.setAttribute("tabindex", "0");
  labelElement.setAttribute("aria-label", `查看${floor.name}`);
  labelElement.addEventListener("click", (event) => {
    event.stopPropagation();
    selectFloor(floor.id);
  });
  labelElement.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectFloor(floor.id);
    }
  });
  const floorLabel = new CSS2DObject(labelElement);
  floorLabel.position.set(-6.8, 0.55, 3.1);
  group.add(floorLabel);

  building.add(group);
  return group;
}

const floorGroupById = new Map(floors.map((floor) => [floor.id, createFloor(floor)]));

function markerGeometry(type) {
  if (type === "camera") return new THREE.ConeGeometry(0.23, 0.55, 16);
  if (type === "pump") return new THREE.CylinderGeometry(0.24, 0.24, 0.5, 16);
  if (type === "door") return new THREE.BoxGeometry(0.35, 0.52, 0.18);
  return new THREE.OctahedronGeometry(0.29, 0);
}

function createDevice(device) {
  const meta = statusMeta[device.status];
  const group = new THREE.Group();
  const floorGroup = floorGroupById.get(device.floor);
  group.position.set(device.x, 0.55, device.z);
  group.userData = { kind: "device", deviceId: device.id };

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.34, 0.47, 32),
    new THREE.MeshBasicMaterial({ color: meta.color, transparent: true, opacity: 0.42, side: THREE.DoubleSide }),
  );
  ring.rotation.x = -Math.PI / 2;
  ring.userData = { kind: "device", deviceId: device.id };
  group.add(ring);

  const marker = new THREE.Mesh(
    markerGeometry(device.type),
    new THREE.MeshStandardMaterial({
      color: meta.color,
      emissive: meta.color,
      emissiveIntensity: 0.2,
      roughness: 0.35,
    }),
  );
  marker.castShadow = true;
  marker.userData = { kind: "device", deviceId: device.id };
  if (device.type === "camera") marker.rotation.z = -Math.PI / 2;
  group.add(marker);

  const labelElement = document.createElement("div");
  labelElement.className = `device-label ${device.status === "alarm" ? "alarm" : ""}`;
  labelElement.dataset.deviceId = device.id;
  labelElement.setAttribute("role", "button");
  labelElement.setAttribute("tabindex", "0");
  labelElement.setAttribute("aria-label", `查看${device.name}详情`);
  labelElement.style.setProperty("--device-color", meta.css);
  labelElement.textContent = `${device.name} · ${meta.label}`;
  labelElement.addEventListener("click", (event) => {
    event.stopPropagation();
    openDeviceDetail(device.id);
  });
  labelElement.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openDeviceDetail(device.id);
    }
  });
  const label = new CSS2DObject(labelElement);
  label.position.set(0, 0.72, 0);
  group.add(label);

  group.userData.marker = marker;
  group.userData.ring = ring;
  group.userData.labelElement = labelElement;
  floorGroup.add(group);
  deviceObjects.push(marker, ring);
  deviceObjectById.set(device.id, group);
}

devices.forEach(createDevice);

function renderFloorList() {
  const list = document.querySelector("#floor-list");
  list.innerHTML = floors.map((floor) => {
    const floorDevices = devices.filter((device) => device.floor === floor.id);
    const severe = floorDevices.find((device) => device.status === "alarm")
      ?? floorDevices.find((device) => device.status === "warning")
      ?? floorDevices.find((device) => device.status === "offline")
      ?? floorDevices[0];
    const color = statusMeta[severe?.status ?? "normal"].css;
    return `
      <button class="floor-button ${floor.id === selectedFloorId ? "active" : ""}" data-floor="${floor.id}">
        <span class="floor-index">${floor.level}F</span>
        <span><span class="floor-name">${floor.name.split(" · ")[1]}</span><br><span class="floor-count">${floorDevices.length}个设备</span></span>
        <span class="mini-dot" style="background:${color}"></span>
      </button>
    `;
  }).join("");
  list.querySelectorAll("[data-floor]").forEach((button) => {
    button.addEventListener("click", () => selectFloor(button.dataset.floor));
  });
}

function selectedDevice() {
  return devices.find((device) => device.id === selectedDeviceId) ?? devices[0];
}

function renderDeviceDetails() {
  const device = selectedDevice();
  const floor = floors.find((item) => item.id === device.floor);
  const meta = statusMeta[device.status];
  const detail = document.querySelector("#device-details");
  detail.innerHTML = `
    <div class="card-title">
      <span class="device-symbol">${device.icon}</span>
      <div><h2>${device.name}</h2></div>
      <span class="state-chip" style="color:${meta.css};background:${meta.css}1c">${meta.label}</span>
    </div>
    <p class="subtitle">${device.type === "camera" ? "视频监控设备" : "现场接入设备"} · 数据每5秒刷新</p>
    <div class="detail-grid">
      <div class="detail-row"><span>所在位置</span><span>主楼 / ${floor.name}</span></div>
      <div class="detail-row"><span>通信地址</span><span>${device.ip ?? device.point}</span></div>
      <div class="detail-row"><span>最后更新</span><span>刚刚</span></div>
      <div class="detail-row"><span>运行状态</span><span style="color:${meta.css}">${meta.label}</span></div>
    </div>
    <div class="actions">
      <button class="action-button primary" id="simulate-status">${simulatedAlarm ? "恢复正常" : "模拟报警"}</button>
      <button class="action-button" id="open-device-detail">查看详情</button>
    </div>
  `;
  document.querySelector("#simulate-status").addEventListener("click", toggleAlarm);
  document.querySelector("#open-device-detail").addEventListener("click", () => openDeviceDetail(device.id));
}

function deviceTelemetry(device) {
  if (device.type === "camera") {
    return [
      ["视频流", "H.264 · 1080P"],
      ["实时码率", "2.8 Mbps"],
      ["画面状态", "持续更新"],
      ["录像计划", "事件录像"],
    ];
  }
  if (device.type === "pump") {
    return [
      ["运行频率", "42.5 Hz"],
      ["出口压力", "0.42 MPa"],
      ["瞬时功率", "2.35 kW"],
      ["累计运行", "1,286 h"],
    ];
  }
  return [
    ["当前值", device.status === "standby" ? "关闭" : "正常"],
    ["采集周期", "5秒"],
    ["信号质量", "98%"],
    ["今日事件", "0条"],
  ];
}

function renderDevicePage() {
  const device = selectedDevice();
  const floor = floors.find((item) => item.id === device.floor);
  const meta = statusMeta[device.status];
  const telemetry = deviceTelemetry(device);
  const content = document.querySelector("#device-detail-content");
  content.innerHTML = `
    <div class="detail-page-header">
      <button class="back-button" id="close-device-detail">← 返回楼层总览</button>
      <div class="detail-breadcrumb">主楼 / ${floor.name} / ${device.name}</div>
      <span class="detail-live"><i style="background:${meta.css}"></i>${meta.label}</span>
    </div>

    <div class="detail-page-grid">
      <article class="detail-hero">
        <div class="detail-hero-copy">
          <p class="eyebrow">Device overview</p>
          <div class="detail-device-heading">
            <span class="detail-device-icon">${device.icon}</span>
            <div>
              <h1>${device.name}</h1>
              <p>${device.type === "camera" ? "视频监控设备" : "现场接入设备"} · ${device.id}</p>
            </div>
          </div>
        </div>

        <div class="device-visual">
          ${device.type === "camera" ? `
            <div class="camera-scene">
              <div class="camera-grid"></div>
              <div class="camera-time">LIVE&nbsp;&nbsp;10:32:18</div>
              <div class="camera-zone">入口监控区域</div>
            </div>
          ` : `
            <div class="equipment-orbit">
              <span>${device.icon}</span>
              <i></i><i></i><i></i>
            </div>
          `}
        </div>
      </article>

      <aside class="detail-info-card">
        <div class="detail-info-title">
          <h2>设备信息</h2>
          <span style="color:${meta.css}">● ${meta.label}</span>
        </div>
        <div class="detail-info-list">
          <div><span>空间位置</span><strong>主楼 / ${floor.name}</strong></div>
          <div><span>通信地址</span><strong>${device.ip ?? device.point}</strong></div>
          <div><span>接入方式</span><strong>${device.type === "camera" ? "RTSP / ONVIF" : "RS485 / Modbus"}</strong></div>
          <div><span>最后更新</span><strong>刚刚</strong></div>
        </div>
        <button class="detail-primary-button">${device.type === "camera" ? "查看实时画面" : "进入设备控制"}</button>
      </aside>

      <section class="telemetry-section">
        <div class="section-heading"><div><p class="eyebrow">Realtime data</p><h2>实时状态</h2></div><span>每5秒刷新</span></div>
        <div class="telemetry-grid">
          ${telemetry.map(([label, value], index) => `
            <div class="telemetry-card">
              <span>${label}</span>
              <strong>${value}</strong>
              <div class="telemetry-bars">${Array.from({ length: 10 }, (_, bar) => `<i style="height:${8 + ((bar * 7 + index * 5) % 24)}px"></i>`).join("")}</div>
            </div>
          `).join("")}
        </div>
      </section>

      <section class="event-section">
        <div class="section-heading"><div><p class="eyebrow">Recent events</p><h2>近期事件</h2></div><button>查看全部</button></div>
        <div class="event-list">
          <div><time>10:32:18</time><i class="event-normal"></i><span>设备状态刷新</span><strong>${meta.label}</strong></div>
          <div><time>09:00:00</time><i class="event-normal"></i><span>每日自检完成</span><strong>通过</strong></div>
          <div><time>昨天 18:24</time><i class="event-info"></i><span>配置同步完成</span><strong>版本 12</strong></div>
        </div>
      </section>
    </div>
  `;
  document.querySelector("#close-device-detail").addEventListener("click", closeDeviceDetail);
}

function openDeviceDetail(deviceId, updateHistory = true) {
  selectDevice(deviceId);
  renderDevicePage();
  const page = document.querySelector("#device-detail-page");
  page.classList.add("visible");
  page.setAttribute("aria-hidden", "false");
  if (updateHistory) {
    const url = new URL(location.href);
    url.searchParams.set("device", deviceId);
    history.pushState({ deviceId }, "", url);
  }
}

function closeDeviceDetail(updateHistory = true) {
  const page = document.querySelector("#device-detail-page");
  page.classList.remove("visible");
  page.setAttribute("aria-hidden", "true");
  if (updateHistory) {
    const url = new URL(location.href);
    url.searchParams.delete("device");
    history.pushState({}, "", url);
  }
}

function selectFloor(floorId) {
  selectedFloorId = floorId;
  const firstDevice = devices.find((device) => device.floor === floorId);
  if (firstDevice) selectedDeviceId = firstDevice.id;

  floorGroupById.forEach((group, id) => {
    const floor = floors.find((item) => item.id === id);
    const baseY = floorY(floor);
    group.userData.targetY = id === floorId ? baseY + 0.48 : baseY;
    group.userData.targetX = id === floorId ? 0.65 : 0;
  });
  renderFloorList();
  renderDeviceDetails();
  requestRender();
}

function selectDevice(deviceId) {
  selectedDeviceId = deviceId;
  const device = devices.find((item) => item.id === deviceId);
  if (device) selectedFloorId = device.floor;
  selectFloor(selectedFloorId);
  selectedDeviceId = deviceId;
  renderDeviceDetails();
}

function applyDeviceStatus(device) {
  const group = deviceObjectById.get(device.id);
  const meta = statusMeta[device.status];
  group.userData.marker.material.color.setHex(meta.color);
  group.userData.marker.material.emissive.setHex(meta.color);
  group.userData.ring.material.color.setHex(meta.color);
  group.userData.labelElement.style.setProperty("--device-color", meta.css);
  group.userData.labelElement.classList.toggle("alarm", device.status === "alarm");
  group.userData.labelElement.textContent = `${device.name} · ${meta.label}`;
  group.userData.ring.material.opacity = device.status === "alarm" ? 0.76 : 0.42;
  group.userData.ring.scale.setScalar(device.status === "alarm" ? 1.18 : 1);
  requestRender();
}

function toggleAlarm() {
  const alarmDevice = devices.find((device) => device.id === "smoke-03");
  simulatedAlarm = !simulatedAlarm;
  alarmDevice.status = simulatedAlarm ? "alarm" : "normal";
  applyDeviceStatus(alarmDevice);
  document.querySelector("#alarm-banner").classList.toggle("visible", simulatedAlarm);
  if (simulatedAlarm) selectDevice(alarmDevice.id);
  renderFloorList();
  renderDeviceDetails();
  if (document.querySelector("#device-detail-page").classList.contains("visible")) renderDevicePage();
}

renderFloorList();
renderDeviceDetails();
selectFloor(selectedFloorId);
if (params.get("device") && devices.some((device) => device.id === params.get("device"))) {
  openDeviceDetail(params.get("device"), false);
}

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let pointerDown = null;

function normalizedPointer(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

renderer.domElement.addEventListener("pointerdown", (event) => {
  pointerDown = { x: event.clientX, y: event.clientY };
});

renderer.domElement.addEventListener("pointerup", (event) => {
  if (!pointerDown || Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y) > 6) return;
  normalizedPointer(event);
  raycaster.setFromCamera(pointer, camera);
  const deviceHits = raycaster.intersectObjects(deviceObjects, false);
  if (deviceHits.length) {
    openDeviceDetail(deviceHits[0].object.userData.deviceId);
    return;
  }
  const floorHits = raycaster.intersectObjects(floorObjects, false);
  if (floorHits.length) selectFloor(floorHits[0].object.userData.floorId);
});

function resize() {
  const width = viewport.clientWidth;
  const height = viewport.clientHeight;
  renderer.setSize(width, height, false);
  labelRenderer.setSize(width, height);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  requestRender();
}

const resizeObserver = new ResizeObserver(resize);
resizeObserver.observe(viewport);
resize();

function renderFrame() {
  renderFrameId = 0;
  let moving = false;
  floorGroupById.forEach((group) => {
    const targetY = group.userData.targetY ?? group.userData.baseY;
    const targetX = group.userData.targetX ?? 0;
    const dy = targetY - group.position.y;
    const dx = targetX - group.position.x;
    if (Math.abs(dy) > 0.002 || Math.abs(dx) > 0.002) {
      group.position.y += dy * 0.16;
      group.position.x += dx * 0.16;
      moving = true;
    } else {
      group.position.y = targetY;
      group.position.x = targetX;
    }
  });

  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
  if (moving) requestRender();
}

window.addEventListener("keydown", (event) => {
  if (["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName) || document.activeElement?.isContentEditable) return;
  if (event.key === "Escape" && document.querySelector("#device-detail-page").classList.contains("visible")) {
    closeDeviceDetail();
  }
});

window.addEventListener("popstate", () => {
  const deviceId = new URLSearchParams(location.search).get("device");
  if (deviceId && devices.some((device) => device.id === deviceId)) openDeviceDetail(deviceId, false);
  else closeDeviceDetail(false);
});
