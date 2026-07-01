import { initPixelSoftUtilityApp } from "../../../design-system/app-shell.js";
import { bindRegisterWindow } from "../../../design-system/setup-flow.js";

const config = {
  app_id: "pulliku",
  app_name: "Pulliku",
  app_subtitle: "Medien herunterladen",
  app_symbol: "download",
  app_logo: {
    src: "../../assets/logos/example-pulliku-logo.svg",
    favicon: "../../assets/logos/example-pulliku-logo.svg",
    alt: ""
  },
  default_theme: "lavender",
  default_mode: "system"
};

async function injectIcons() {
  const target = document.getElementById("icon-sprite");
  if (!target) return;
  const response = await fetch("../../../icons/psu-icons.svg");
  target.innerHTML = await response.text();
}

await injectIcons();
initPixelSoftUtilityApp(config);

bindRegisterWindow(document.querySelector("[data-psu-register-form]"), {
  appId: config.app_id,
  appName: config.app_name,
  async onSubmit(formData, form) {
    // Template only: real apps must submit to the backend.
    // The backend must validate setup_secret against the Docker secret server-side,
    // hash the admin password, create the first admin, mark setup complete, and close registration.
    form.querySelector("button[type='submit']").disabled = true;
  }
});
