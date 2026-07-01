import { initPixelSoftUtilityApp } from "../../../design-system/app-shell.js";
import { setPixelSoftUtilityTheme, setPixelSoftUtilityMode } from "../../../design-system/theme-controller.js";

function readEmbeddedConfig() {
  const script = document.querySelector("script[type='application/json'][data-psu-app-config]");
  if (!script) {
    return {
      app_id: "pulliku",
      app_name: "Pulliku",
      app_subtitle: "Medien herunterladen",
      app_symbol: "download",
      app_logo: {
        src: "../../assets/logos/example-pulliku-logo.svg",
        favicon: "../../assets/logos/example-pulliku-logo.svg",
        alt: "",
        use_as_header_symbol: true,
        use_as_favicon: true,
        use_as_about_symbol: true,
        use_as_profile_sheet_symbol: true,
        use_as_empty_state_symbol: true
      },
      default_theme: "lavender",
      default_mode: "system"
    };
  }
  return JSON.parse(script.textContent);
}

const config = readEmbeddedConfig();

async function injectIcons() {
  const target = document.getElementById("icon-sprite");
  if (!target) return;
  const response = await fetch("../../../icons/psu-icons.svg");
  target.innerHTML = await response.text();
}

await injectIcons();
initPixelSoftUtilityApp(config);

document.querySelectorAll("[data-theme-choice]").forEach((button) => {
  button.addEventListener("click", () => setPixelSoftUtilityTheme(button.dataset.themeChoice));
});

document.querySelectorAll("[data-mode-choice]").forEach((button) => {
  button.addEventListener("click", () => setPixelSoftUtilityMode(button.dataset.modeChoice));
});

window.addEventListener("psu:themechange", (event) => {
  const { theme, mode } = event.detail;
  document.querySelectorAll("[data-theme-choice]").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.themeChoice === theme);
    button.setAttribute("aria-pressed", String(button.dataset.themeChoice === theme));
  });
  document.querySelectorAll("[data-mode-choice]").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.modeChoice === mode);
    button.setAttribute("aria-pressed", String(button.dataset.modeChoice === mode));
  });
});
