// Map initialization and management
let map;
let markers = {};
let routeLines = [];

// HKU Main Campus coordinates (approximate center)
const HKU_CENTER = [22.283, 114.137];
const DEFAULT_ZOOM = 16;

function initMap() {
  // Initialize map
  map = L.map("map", {
    zoomControl: false,
    attributionControl: false,
  }).setView(HKU_CENTER, DEFAULT_ZOOM);

  // Add zoom control to top right
  L.control
    .zoom({
      position: "topright",
    })
    .addTo(map);

  // Add attribution
  L.control
    .attribution({
      position: "bottomright",
      prefix: "© OpenStreetMap contributors",
    })
    .addTo(map);

  // Add tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap",
  }).addTo(map);

  // Load stops onto map
  loadStopsToMap();
}

function loadStopsToMap() {
  fetch("/api/stops")
    .then((r) => r.json())
    .then((stops) => {
      let validStops = 0;
      let missingCoords = [];

      stops.forEach((stop) => {
        // Parse coordinates defensively to avoid skipping valid numeric values (e.g. 0)
        const lat = Number(stop.lat);
        const lng = Number(stop.lng);

        // Skip stops with missing or invalid coordinates instead of faking them
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
          missingCoords.push(stop.name);
          return;
        }

        validStops++;

        const marker = L.circleMarker([lat, lng], {
          radius: 8,
          fillColor: "#3b82f6",
          color: "#ffffff",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8,
        }).addTo(map);

        marker.bindPopup(`
                    <div class="font-sans">
                        <h3 class="font-bold text-slate-900">${stop.name}</h3>
                        <p class="text-xs text-slate-500">${stop.campus}</p>
                        <p class="text-xs text-slate-400 mt-1">ID: ${stop.id}</p>
                        <div class="mt-2 flex gap-2">
                            <button onclick="selectStopFromMap('${stop.id}', 'origin')" 
                                    class="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700">
                                Set as Origin
                            </button>
                            <button onclick="selectStopFromMap('${stop.id}', 'dest')" 
                                    class="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">
                                Set as Dest
                            </button>
                        </div>
                    </div>
                `);

        marker.on("click", () => {
          highlightMarker(stop.id);
        });

        markers[stop.id] = { marker, lat, lng, name: stop.name };
      });

      // Fit map to show all stops if we have valid ones
      if (validStops > 0) {
        const group = new L.featureGroup(
          Object.values(markers).map((m) => m.marker),
        );
        map.fitBounds(group.getBounds().pad(0.1));
      }

      // Warn about missing coordinates
      if (missingCoords.length > 0) {
        console.warn(`Missing coordinates for: ${missingCoords.join(", ")}`);
        // Optional: Show warning in UI
        const hint = document.getElementById("map-hint");
        if (hint && missingCoords.length > 0) {
          hint.innerHTML = `<i class="fas fa-exclamation-triangle mr-2 text-yellow-500"></i> ${missingCoords.length} stops missing coordinates`;
          hint.classList.remove("hidden");
        }
      }
    });
}

function highlightMarker(stopId) {
  // Reset all markers
  Object.values(markers).forEach((m) => {
    m.marker.setStyle({ fillColor: "#3b82f6", radius: 8 });
  });

  // Highlight selected
  if (markers[stopId]) {
    markers[stopId].marker.setStyle({ fillColor: "#ef4444", radius: 10 });
  }
}

function selectStopFromMap(stopId, type) {
  const select = document.getElementById(
    type === "origin" ? "origin-select" : "dest-select",
  );
  select.value = stopId;

  // Trigger change event
  select.dispatchEvent(new Event("change"));

  // Visual feedback
  highlightMarker(stopId);

  // Close popup
  map.closePopup();
}

function drawRouteOnMap(stopSequence, segments) {
  // Clear existing routes
  clearRoutes();

  if (!stopSequence || stopSequence.length < 2) return;

  // Draw lines between stops
  const latlngs = [];
  for (let i = 0; i < stopSequence.length; i++) {
    const stopId = stopSequence[i];
    if (markers[stopId]) {
      latlngs.push([markers[stopId].lat, markers[stopId].lng]);
    }
  }

  if (latlngs.length >= 2) {
    const polyline = L.polyline(latlngs, {
      color: "#3b82f6",
      weight: 4,
      opacity: 0.8,
      lineJoin: "round",
      dashArray: segments && segments[0]?.mode === "walk" ? "10, 10" : null,
    }).addTo(map);

    routeLines.push(polyline);
    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
  }

  // Highlight origin and destination
  if (markers[stopSequence[0]]) {
    markers[stopSequence[0]].marker.setStyle({
      fillColor: "#22c55e",
      radius: 12,
    });
  }
  if (markers[stopSequence[stopSequence.length - 1]]) {
    markers[stopSequence[stopSequence.length - 1]].marker.setStyle({
      fillColor: "#ef4444",
      radius: 12,
    });
  }
}

function clearRoutes() {
  routeLines.forEach((line) => map.removeLayer(line));
  routeLines = [];

  // Reset marker colors
  Object.values(markers).forEach((m) => {
    m.marker.setStyle({ fillColor: "#3b82f6", radius: 8 });
  });
}

// Initialize map when DOM is ready
document.addEventListener("DOMContentLoaded", initMap);
