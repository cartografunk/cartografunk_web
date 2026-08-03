import { cp, mkdir, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const dist = path.join(root, "dist");

const rootFiles = [
  "404.html",
  "desaparecidos.html",
  "google5b9223c756063cb5.html",
  "index.html",
  "marcas.html",
  "robots.txt",
  "seccion-futbol-desaparecidos.html",
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

await mkdir(path.join(dist, "data"), { recursive: true });
await cp(path.join(root, "data", "estados-hero.geojson"), path.join(dist, "data", "estados-hero.geojson"));
await cp(path.join(root, "data", "division_estatal.geojson"), path.join(dist, "data", "division_estatal.geojson"));

console.log("Built static site into dist/");
