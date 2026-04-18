// Application logic
document.addEventListener("DOMContentLoaded", () => {
  const originSelect = document.getElementById("origin-select");
  const destSelect = document.getElementById("dest-select");
  const swapBtn = document.getElementById("swap-btn");
  const findBtn = document.getElementById("find-btn");
  const loadingState = document.getElementById("loading-state");
  const resultsSection = document.getElementById("results-section");
  const routesContainer = document.getElementById("routes-container");
  const errorMsg = document.getElementById("error-msg");
  const errorText = document.getElementById("error-text");
  const emptyState = document.getElementById("empty-state");
  const resultsCount = document.getElementById("results-count");

  // Swap button functionality
  swapBtn.addEventListener("click", () => {
    const temp = originSelect.value;
    originSelect.value = destSelect.value;
    destSelect.value = temp;

    // Trigger change events to update map
    originSelect.dispatchEvent(new Event("change"));
    destSelect.dispatchEvent(new Event("change"));

    // Animation
    swapBtn.style.transform = "rotate(180deg)";
    setTimeout(() => (swapBtn.style.transform = "rotate(0deg)"), 300);
  });

  // Select change handlers for map highlighting
  originSelect.addEventListener("change", (e) => {
    if (e.target.value && markers[e.target.value]) {
      highlightMarker(e.target.value);
    }
  });

  destSelect.addEventListener("change", (e) => {
    if (e.target.value && markers[e.target.value]) {
      highlightMarker(e.target.value);
    }
  });

  // Find routes button
  findBtn.addEventListener("click", async () => {
    const origin = originSelect.value;
    const dest = destSelect.value;
    const preference = document.querySelector(
      'input[name="preference"]:checked',
    ).value;

    // Reset UI
    errorMsg.classList.add("hidden");
    resultsSection.classList.add("hidden");
    emptyState.classList.add("hidden");

    // Validation
    if (!origin || !dest) {
      showError("Please select both origin and destination");
      return;
    }

    if (origin === dest) {
      showError("Origin and destination cannot be the same");
      return;
    }

    // Show loading
    loadingState.classList.remove("hidden");
    findBtn.disabled = true;

    try {
      const response = await fetch("/api/routes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origin, destination: dest, preference }),
      });

      const data = await response.json();

      if (data.error) {
        showError(
          Array.isArray(data.error) ? data.error.join(", ") : data.error,
        );
        return;
      }

      if (data.routes && data.routes.length > 0) {
        displayRoutes(data.routes);
        resultsCount.textContent = `${data.count} route${data.count !== 1 ? "s" : ""} found`;

        // Auto-draw first route on map
        if (data.routes[0]) {
          drawRouteOnMap(data.routes[0].stop_sequence, data.routes[0].segments);
        }
      } else {
        showError(data.message || "No routes found between these stops");
      }
    } catch (err) {
      showError("Network error. Please try again.");
      console.error(err);
    } finally {
      loadingState.classList.add("hidden");
      findBtn.disabled = false;
    }
  });

  function showError(msg) {
    errorText.textContent = msg;
    errorMsg.classList.remove("hidden");
    emptyState.classList.remove("hidden");
  }

  function displayRoutes(routes) {
    routesContainer.innerHTML = "";

    routes.forEach((route, index) => {
      const card = createRouteCard(route, index);
      routesContainer.appendChild(card);
    });

    resultsSection.classList.remove("hidden");

    // Scroll to results on mobile
    if (window.innerWidth < 1024) {
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function createRouteCard(route, index) {
    const div = document.createElement("div");
    div.className =
      "route-card bg-white border border-slate-200 rounded-xl p-4 cursor-pointer hover:border-blue-400";

    // Determine badge color based on rank
    const rankColors = [
      "bg-yellow-100 text-yellow-800 border-yellow-200",
      "bg-slate-100 text-slate-700 border-slate-200",
      "bg-orange-100 text-orange-800 border-orange-200",
    ];
    const rankBadge =
      index < 3
        ? rankColors[index]
        : "bg-slate-100 text-slate-600 border-slate-200";

    // Build segments HTML
    const segmentsHtml = route.segments
      .map(
        (seg, idx) => `
            <div class="timeline-item relative pl-6 pb-4 last:pb-0">
                <div class="absolute left-0 top-1 w-3 h-3 rounded-full border-2 border-white shadow-sm z-10 
                            ${seg.mode === "walk" ? "bg-gray-400" : "bg-blue-500"}"></div>
                
                <div class="flex items-center justify-between mb-1">
                    <span class="text-sm font-medium text-slate-900">${seg.from_stop}</span>
                    <span class="text-xs text-slate-500">${seg.duration} min</span>
                </div>
                
                <div class="flex items-center gap-2 mb-2">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getModeBadgeClass(seg.mode)}">
                        <i class="fas fa-${seg.icon} mr-1"></i>
                        ${seg.mode}
                    </span>
                    <span class="text-xs text-slate-500">${seg.route_name}</span>
                </div>
                
                ${
                  idx === route.segments.length - 1
                    ? `
                <div class="flex items-center justify-between pt-1">
                    <span class="text-sm font-medium text-slate-900">${seg.to_stop}</span>
                </div>
                `
                    : ""
                }
            </div>
        `,
      )
      .join("");

    div.innerHTML = `
            <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-2">
                    <span class="px-2.5 py-1 rounded-lg text-xs font-bold border ${rankBadge}">
                        #${route.rank}
                    </span>
                    <div>
                        <div class="text-sm text-slate-500">${route.total_duration} mins • ${route.num_transfers} transfers</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-lg font-bold text-slate-900">HK$ ${route.total_cost.toFixed(1)}</div>
                </div>
            </div>
            
            <div class="border-l-2 border-slate-200 ml-1.5 space-y-0">
                ${segmentsHtml}
            </div>
            
            <div class="mt-3 pt-3 border-t border-slate-100 flex justify-end">
                <button class="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1" onclick="event.stopPropagation(); showRouteDetail(${route.id})">
                    View Details <i class="fas fa-arrow-right text-xs"></i>
                </button>
            </div>
        `;

    div.addEventListener("click", () => {
      drawRouteOnMap(route.stop_sequence, route.segments);
      // Highlight selected card
      document
        .querySelectorAll(".route-card")
        .forEach((c) => c.classList.remove("ring-2", "ring-blue-500"));
      div.classList.add("ring-2", "ring-blue-500");
    });

    return div;
  }

  function getModeBadgeClass(mode) {
    const classes = {
      bus: "bg-red-100 text-red-700 border-red-200",
      shuttle: "bg-green-100 text-green-700 border-green-200",
      walk: "bg-gray-100 text-gray-700 border-gray-200",
      walking: "bg-gray-100 text-gray-700 border-gray-200",
      minibus: "bg-yellow-100 text-yellow-800 border-yellow-200",
    };
    return (
      classes[mode.toLowerCase()] || "bg-blue-100 text-blue-700 border-blue-200"
    );
  }

  // Modal functionality
  window.showRouteDetail = function (routeId) {
    const modal = document.getElementById("route-modal");
    const content = document.getElementById("modal-content");
    const route = routes.find((r) => r.id === routeId);

    if (!route) return;

    // Build detailed view
    content.innerHTML = `
            <div class="space-y-4">
                <div class="bg-slate-50 rounded-lg p-4 flex justify-between items-center">
                    <div>
                        <div class="text-sm text-slate-500">Total Time</div>
                        <div class="text-2xl font-bold text-slate-900">${route.total_duration} <span class="text-sm font-normal text-slate-500">min</span></div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm text-slate-500">Total Cost</div>
                        <div class="text-2xl font-bold text-green-600">HK$ ${route.total_cost.toFixed(1)}</div>
                    </div>
                </div>
                
                <div class="space-y-3">
                    ${route.segments
                      .map(
                        (seg, idx) => `
                        <div class="flex gap-3 p-3 bg-white border border-slate-200 rounded-lg">
                            <div class="shrink-0 w-10 h-10 rounded-full ${getModeBgClass(seg.mode)} flex items-center justify-center">
                                <i class="fas fa-${seg.icon} text-white"></i>
                            </div>
                            <div class="flex-1">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <div class="font-semibold text-slate-900">${seg.from_stop} → ${seg.to_stop}</div>
                                        <div class="text-sm text-slate-500">${seg.route_name}</div>
                                    </div>
                                    <div class="text-right text-sm">
                                        <div class="font-medium text-slate-900">${seg.duration} min</div>
                                        <div class="text-slate-500">HK$ ${seg.cost.toFixed(1)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `,
                      )
                      .join("")}
                </div>
                
                <button onclick="drawRouteOnMap(${JSON.stringify(route.stop_sequence)}, ${JSON.stringify(route.segments)}); closeModal();" 
                        class="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors">
                    Show on Map
                </button>
            </div>
        `;

    modal.classList.remove("hidden");
  };

  function getModeBgClass(mode) {
    const classes = {
      bus: "bg-red-500",
      shuttle: "bg-green-500",
      walk: "bg-gray-500",
      walking: "bg-gray-500",
      minibus: "bg-yellow-500",
    };
    return classes[mode.toLowerCase()] || "bg-blue-500";
  }

  // Close modal handlers
  document.getElementById("close-modal").addEventListener("click", closeModal);
  document
    .getElementById("modal-backdrop")
    .addEventListener("click", closeModal);

  function closeModal() {
    document.getElementById("route-modal").classList.add("hidden");
  }

  // Mobile panel drag handling
  const panel = document.getElementById("control-panel");
  const handle = document.getElementById("panel-handle");
  let isExpanded = false;

  handle.addEventListener("click", () => {
    if (isExpanded) {
      panel.style.transform = "translateY(0)";
    } else {
      panel.style.transform = "translateY(-30%)";
    }
    isExpanded = !isExpanded;
  });

  // Locate me button (mock functionality)
  document.getElementById("locate-btn").addEventListener("click", () => {
    // In real app, use geolocation API
    alert("GPS location would be used here to find nearest stop");
  });
});
