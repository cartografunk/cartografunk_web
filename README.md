# Cartografunk Web

Sitio estatico para el portafolio y presentacion de proyectos de Cartografunk.

## Ejecutar localmente

Desde esta carpeta:

```powershell
py -m http.server 8000
```

Abrir:

```text
http://localhost:8000
```

## Ambientes

Este repositorio publica el mismo sitio estatico en dos ambientes:

```text
main
  -> staging / prueba
  -> GitHub Pages
  -> https://cartografunk.github.io/cartografunk_web/

production
  -> produccion
  -> Cloudflare Pages
  -> https://cartografunk.com/
```

El repo usa un build estatico minimo para produccion. No compila frontend: solo prepara `dist/` con los archivos publicos y excluye GeoJSON fuente demasiado pesados para Cloudflare.

Los metadatos SEO (`canonical`, Open Graph, sitemap y robots) apuntan a `https://cartografunk.com/`, porque ese es el dominio publico de produccion. GitHub Pages queda como URL de revision.

## Estructura

```text
cartografunk_web/
|-- index.html
|-- assets/
|   |-- img/
|   |-- css/
|   `-- js/
`-- README.md
```

## GitHub Pages para staging

1. En GitHub: Settings -> Pages.
4. En "Build and deployment", elegir:
   - Source: Deploy from a branch
   - Branch: main
   - Folder: /root
5. Guardar y esperar a que GitHub publique la URL de prueba.

No agregar `CNAME` en esta rama. GitHub Pages debe conservarse como staging en `cartografunk.github.io/cartografunk_web`.

## Cloudflare Pages para produccion

Crear un proyecto en Cloudflare Pages conectado a GitHub:

```text
Repository: cartografunk/cartografunk_web
Production branch: production
Framework preset: None
Build command: npm run build
Build output directory: dist
```

Agregar los custom domains:

```text
cartografunk.com
www.cartografunk.com
```

Cuando Cloudflare pida activar el dominio, cambiar en Akky los nameservers del dominio por los dos nameservers que entregue Cloudflare. Akky queda solo como registrador; Cloudflare queda como DNS y hosting de produccion.

## Promover a produccion

Trabajar y probar en `main`. Cuando este listo para publicar:

```powershell
.\scripts\deploy-production.ps1
```

El script hace `fetch`, actualiza `main`, cambia a `production`, exige fast-forward desde `main`, empuja `production` y vuelve a la rama original. Cloudflare Pages despliega automaticamente desde `production` y corre `npm run build`.

## Pitch tecnico

"Lo estoy manejando como un sitio estatico versionado en Git. Ahorita lo corro localmente para iterar rapido y el siguiente paso es conectarlo a GitHub Pages para convertirlo en un portafolio vivo con deploy continuo."
