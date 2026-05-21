# Cartografunk Web

Sitio estatico local para portafolio y presentacion de proyectos de Cartografunk.

## Ejecutar localmente

Desde esta carpeta:

```powershell
py -m http.server 8000
```

Abrir:

```text
http://localhost:8000
```

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

## Deploy con GitHub Pages

1. Crear un repositorio en GitHub.
2. Subir este proyecto al repositorio.
3. En GitHub: Settings -> Pages.
4. En "Build and deployment", elegir:
   - Source: Deploy from a branch
   - Branch: main
   - Folder: /root
5. Guardar y esperar a que GitHub publique la URL.

## Pitch tecnico

"Lo estoy manejando como un sitio estatico versionado en Git. Ahorita lo corro localmente para iterar rapido y el siguiente paso es conectarlo a GitHub Pages para convertirlo en un portafolio vivo con deploy continuo."
