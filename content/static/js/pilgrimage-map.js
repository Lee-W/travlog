(function() {
  const map = L.map('map').setView([35.03, 135.77], 14);

  L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    {
      attribution: '&copy; OpenStreetMap & Carto',
      subdomains: 'abcd',
      maxZoom: 20
    }
  ).addTo(map);

  fetch("/places.geojson")
    .then(r => r.json())
    .then(data => {
      L.geoJSON(data, {
        onEachFeature: function(feature, layer) {
          let popup = `<b>${feature.properties.title}</b><br>${feature.properties.anime}`;
          layer.bindPopup(popup);
        }
      }).addTo(map);

      const bounds = L.geoJSON(data).getBounds();
      if (bounds.isValid()) map.fitBounds(bounds);
    })
    .catch(err => console.error("GeoJSON load error:", err));
})();
