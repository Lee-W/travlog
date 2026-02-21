(async function () {
  const DEFAULT_VIEW = { center: [23.7, 121], zoom: 7 };
  const mapContainerId = "map";

  // 1️⃣ 安全移除舊 map
  const mapEl = document.getElementById(mapContainerId);
  if (!mapEl) {
    console.error(`#${mapContainerId} not found`);
    return;
  }
  if (window._pilgrimageMapInstance) {
    window._pilgrimageMapInstance.remove();
    window._pilgrimageMapInstance = null;
  }
  mapEl.innerHTML = "";
  mapEl._leaflet_id = null;

  // 2️⃣ 初始化 map
  const map = L.map(mapContainerId, {
    center: DEFAULT_VIEW.center,
    zoom: DEFAULT_VIEW.zoom,
  });
  window._pilgrimageMapInstance = map;

  // 3️⃣ 全局存 marker
  window._pilgrimageAllMarkers = [];

  // 4️⃣ tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  // 5️⃣ Fullscreen
  if (typeof L.Control.FullScreen === "function") {
    map.addControl(new L.Control.FullScreen());
  }

  // 6️⃣ 等 map 尺寸穩定再加 marker
  function waitForMapSize(cb) {
    const check = () => {
      const size = map.getSize();
      if (size.x > 0 && size.y > 0) {
        map.invalidateSize();
        cb?.();
      } else {
        requestAnimationFrame(check);
      }
    };
    check();
  }

  waitForMapSize(async () => {
    try {
      const res = await fetch(`/static/places.geojson?ts=${Date.now()}`, {
        cache: "no-cache",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const geojson = await res.json();

      if (!geojson.features?.length) {
        console.warn("GeoJSON has no features");
        map.setView(DEFAULT_VIEW.center, DEFAULT_VIEW.zoom);
        return;
      }

      // 清除舊 marker
      window._pilgrimageAllMarkers.forEach((m) => m.remove());
      window._pilgrimageAllMarkers = [];

      const animeLayers = {};

      geojson.features.forEach((f) => {
        const coords = f.geometry?.coordinates;

        // ❌ 嚴格檢查座標
        if (
          !Array.isArray(coords) ||
          coords.length < 2 ||
          coords.some((c) => c == null)
        ) {
          console.warn("Skipping invalid coordinates", f);
          return;
        }

        let [lon, lat] = coords.map(Number);
        if (
          isNaN(lat) ||
          isNaN(lon) ||
          lat < -90 ||
          lat > 90 ||
          lon < -180 ||
          lon > 180
        ) {
          console.warn("Skipping out-of-range coordinates", f);
          return;
        }

        const p = f.properties || {};
        const anime = p.anime || "Unknown";

        // ❌ Layer group 先加 map
        if (!animeLayers[anime]) animeLayers[anime] = L.layerGroup().addTo(map);

        const color = p.visited ? "green" : "orange";

        try {
          const marker = L.circleMarker([lat, lon], {
            radius: 6,
            color,
            weight: 2,
            fillOpacity: 0.9,
          }).bindPopup(buildPilgrimagePopup(p, lat, lon));

          // ❌ 等 map ready 再加 marker
          map.whenReady(() => {
            marker.addTo(animeLayers[anime]);
            window._pilgrimageAllMarkers.push(marker);
          });
        } catch (e) {
          console.warn("Failed to create marker", f, e);
        }
      });

      // fitBounds
      if (window._pilgrimageAllMarkers.length) {
        const bounds = L.featureGroup(window._pilgrimageAllMarkers).getBounds();
        if (bounds.isValid && bounds.isValid()) {
          map.fitBounds(bounds, { padding: [30, 30] });
        } else {
          map.setView(DEFAULT_VIEW.center, DEFAULT_VIEW.zoom);
        }
      } else {
        console.warn("No valid markers, fallback to default view");
        map.setView(DEFAULT_VIEW.center, DEFAULT_VIEW.zoom);
      }

      // Layer control
      L.control.layers(null, animeLayers, { collapsed: true }).addTo(map);

      console.log("Markers loaded:", window._pilgrimageAllMarkers.length);
    } catch (err) {
      console.error("Error loading GeoJSON:", err);
      map.setView(DEFAULT_VIEW.center, DEFAULT_VIEW.zoom);
    }
  });
})();

// Popup function
function buildPilgrimagePopup(p, lat, lon) {
  const badge = p.visited
    ? '<span style="background:#16a34a;color:white;padding:2px 6px;border-radius:6px;font-size:12px;">已訪問</span>'
    : '<span style="background:#ea580c;color:white;padding:2px 6px;border-radius:6px;font-size:12px;">未訪問</span>';

  let photosHtml = "";
  if (p.photos?.length) {
    photosHtml = p.photos
      .map(
        (src) =>
          `<img src="${src}" style="max-width:240px;border-radius:8px;margin-bottom:6px;">`,
      )
      .join("");
  }

  const osmUrl = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=18/${lat}/${lon}`;
  const gmapUrl = `https://maps.google.com/?q=${lat},${lon}`;

  return `
    <div style="min-width:220px;max-width:260px;">
      <div style="font-weight:700;font-size:15px;margin-bottom:4px;">${p.title || ""}</div>
      <div style="margin-bottom:6px;">${badge}</div>
      ${photosHtml}
      <div style="font-size:13px;line-height:1.4;">
        <b>作品：</b>${p.anime || ""}<br>
        <b>地點：</b>${p.city || ""} ${p.country || ""}<br>
        ${p.category ? `<b>分類：</b>${p.category}<br>` : ""}
        ${p.date ? `<b>日期：</b>${p.date}<br>` : ""}
        ${p.notes ? `<div style="margin-top:4px;">${p.notes}</div>` : ""}
      </div>
      <div style="margin-top:6px;font-size:12px;">
        🔗 <a href="${osmUrl}" target="_blank">OSM</a> |
        <a href="${gmapUrl}" target="_blank">Google</a>
      </div>
    </div>
  `;
}
