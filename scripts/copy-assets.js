const fs = require("fs");
const path = require("path");

const root = process.cwd();
const cssDir = path.join(root, "app", "static", "css");
const fontsDir = path.join(root, "app", "static", "fonts");
const cssFontsDir = path.join(root, "app", "static", "css", "fonts");

fs.mkdirSync(cssDir, { recursive: true });
fs.mkdirSync(fontsDir, { recursive: true });
fs.mkdirSync(cssFontsDir, { recursive: true });

fs.copyFileSync(
  path.join(root, "node_modules", "bootstrap", "dist", "css", "bootstrap.min.css"),
  path.join(cssDir, "bootstrap.min.css")
);

fs.copyFileSync(
  path.join(root, "node_modules", "bootstrap-icons", "font", "bootstrap-icons.css"),
  path.join(cssDir, "bootstrap-icons.css")
);

const iconsSrc = path.join(root, "node_modules", "bootstrap-icons", "font", "fonts");
for (const file of fs.readdirSync(iconsSrc)) {
  fs.copyFileSync(path.join(iconsSrc, file), path.join(fontsDir, file));
  fs.copyFileSync(path.join(iconsSrc, file), path.join(cssFontsDir, file));
}
