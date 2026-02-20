(function () {
  // initialize map
  const map = L.map('map').setView([35.03, 135.77], 13);
  map.addControl(new L.Control.FullScreen());
  L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    {
      attribution: '&copy; OpenStreetMap & Carto',
      subdomains: 'abcd',
      maxZoom: 20
    }
  ).addTo(map);

  // load GeoJSON
  fetch("/places.geojson")
    .then(r => r.json())
    .then(geojson => {

      const animeLayers = {};
      const group = L.featureGroup();

      geojson.features.forEach(f => {
        const p = f.properties;
        const anime = p.anime || "Unknown";

        if (!animeLayers[anime]) {
          animeLayers[anime] = L.layerGroup().addTo(map);
        }

        const color = p.visited ? 'green' : 'orange';
        const lat = f.geometry.coordinates[1];
        const lon = f.geometry.coordinates[0];

        const marker = L.circleMarker(
          [lat, lon],
          {
            radius: 6,
            color: color,
            weight: 2,
            fillOpacity: 0.9
          }
        ).bindPopup(buildPilgrimagePopup(p, lat, lon));

        marker.addTo(animeLayers[anime]);
        group.addLayer(marker);
      });

      if (group.getLayers().length > 0) {
        group.addTo(map);
        map.fitBounds(group.getBounds(), { padding: [30, 30] });
      }

      L.control.layers(null, animeLayers, { collapsed: false }).addTo(map);
    })
    .catch(e => console.error("Error loadding GeoJSON:", e));
})();


function buildPilgrimagePopup(p, lat, lon) {
  // ===== visited badge =====
  const badge = p.visited
    ? '<span style="background:#16a34a;color:white;padding:2px 6px;border-radius:6px;font-size:12px;">已訪問</span>'
    : '<span style="background:#ea580c;color:white;padding:2px 6px;border-radius:6px;font-size:12px;">未訪問</span>';

  let photosHtml = '';

  if (p.photos && p.photos.length) {
    photosHtml = p.photos
      .map(src =>
        `<img src="${src}" style="max-width:240px;border-radius:8px;margin-bottom:6px;">`
      )
      .join('');
  } else if (p.photo) {
    photosHtml =
      `<img src="${p.photo}" style="max-width:240px;border-radius:8px;margin-bottom:6px;">`;
  }

  const osmUrl = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=18/${lat}/${lon}`;
  const gmapUrl = `https://maps.google.com/?q=${lat},${lon}`;

  return `
    <div style="min-width:220px;max-width:260px;">

      <div style="font-weight:700;font-size:15px;margin-bottom:4px;">
        ${p.title || ''}
      </div>

      <div style="margin-bottom:6px;">${badge}</div>

      ${photosHtml}

      <div style="font-size:13px;line-height:1.4;">
        <b>作品：</b>${p.anime || ''}<br>
        <b>地點：</b>${p.city || ''} ${p.country || ''}<br>
        ${p.category ? `<b>分類：</b>${p.category}<br>` : ''}
        ${p.date ? `<b>日期：</b>${p.date}<br>` : ''}
        ${p.notes ? `<div style="margin-top:4px;">${p.notes}</div>` : ''}
      </div>

      <div style="margin-top:6px;font-size:12px;">
        🔗 <a href="${osmUrl}" target="_blank">OSM</a> |
        <a href="${gmapUrl}" target="_blank">Google</a>
      </div>

    </div>
  `;
}
