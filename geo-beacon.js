/*
 * geo-beacon.js — alwayshave.fun visitor map beacon.
 *
 * Fires once per browser session. Sends only the current path; the location
 * itself is derived server-side from Cloudflare's edge (no IP, no precise
 * client geolocation prompt). See /functions/api/geo.js.
 *
 * Exclude yourself / friends:
 *   visit any page with ?geo_optout=1  → this device stops being counted.
 *   visit with        ?geo_optout=0    → re-enable counting.
 * The choice is remembered in localStorage on that device.
 */
(function () {
  try {
    var params = new URLSearchParams(window.location.search);
    if (params.has("geo_optout")) {
      if (params.get("geo_optout") === "0") localStorage.removeItem("geo_optout");
      else localStorage.setItem("geo_optout", "1");
    }
    if (localStorage.getItem("geo_optout") === "1") return; // self/friends excluded
    if (sessionStorage.getItem("geo_logged") === "1") return; // once per session
    sessionStorage.setItem("geo_logged", "1");

    var payload = JSON.stringify({ path: location.pathname });
    var send = function () {
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/api/geo", new Blob([payload], { type: "application/json" }));
      } else {
        fetch("/api/geo", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: payload,
          keepalive: true,
        }).catch(function () {});
      }
    };
    // Don't compete with page load.
    if (document.readyState === "complete") setTimeout(send, 1200);
    else window.addEventListener("load", function () { setTimeout(send, 1200); });
  } catch (e) {
    /* never let the beacon break the page */
  }
})();
