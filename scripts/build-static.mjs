import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const dist = path.join(root, "dist");

const rootFiles = [
  "404.html",
  "_redirects",
  "desaparecidos.html",
  "google5b9223c756063cb5.html",
  "index.html",
  "actualidad.html",
  "daft-metro.html",
  "cursos.html",
  "servicios.html",
  "proyectos.html",
  "nosotros.html",
  "marcas.html",
  "privacidad.html",
  "reporte-agua.html",
  "robots.txt",
  "sitemap.xml",
];

const directories = [
  "assets",
  "cartography",
  "samples",
];

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

for (const file of rootFiles) {
  if (existsSync(path.join(root, file))) {
    await cp(path.join(root, file), path.join(dist, file));
  }
}

for (const dir of directories) {
  if (existsSync(path.join(root, dir))) {
    await cp(path.join(root, dir), path.join(dist, dir), { recursive: true });
  }
}

const browserMapsKey = process.env.GOOGLE_MAPS_BROWSER_KEY?.trim();
if (browserMapsKey) {
  const waterConfigPath = path.join(dist, "assets/js/reporte-agua-config.js");
  const waterConfig = await readFile(waterConfigPath, "utf8");
  const keyAssignment = "window.CARTOGRAFUNK_GOOGLE_MAPS_BROWSER_KEY = '';";
  if (!waterConfig.includes(keyAssignment)) {
    throw new Error("No se encontró la configuración de Google Maps en reporte-agua-config.js.");
  }
  await writeFile(
    waterConfigPath,
    waterConfig.replace(keyAssignment, `window.CARTOGRAFUNK_GOOGLE_MAPS_BROWSER_KEY = ${JSON.stringify(browserMapsKey)};`),
  );
}

await mkdir(path.join(dist, "data"), { recursive: true });
await cp(path.join(root, "data", "estados-hero.geojson"), path.join(dist, "data", "estados-hero.geojson"));
await cp(path.join(root, "data", "division_estatal.geojson"), path.join(dist, "data", "division_estatal.geojson"));

console.log("Built static site into dist/");
