const BRAND = "Xpression NextGen (demo)";
const LINKS = [["workbench", "Demand Workbench", "workbench.html"], ["inventory", "Inventory Policy", "inventory.html"],
  ["replenishment", "Replenishment", "replenishment.html"], ["scenarios", "Scenarios", "scenarios.html"]];
function shell(active) { if (!requireAuth()) return false; renderShell(active, LINKS, BRAND);
  if (API.user().role === "VIEWER") document.body.classList.add("read-only"); return true; }
const isViewer = () => (API.user() || {}).role === "VIEWER";
