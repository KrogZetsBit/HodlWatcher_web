# Sistema CSS Modular para HodlWatcher

Este directorio contiene el sistema CSS refactorizado de HodlWatcher, diseñado para ser modular, ligero y fácil de mantener.

## Estructura

```
css/
├── modules/
│   ├── variables.css    # Variables CSS (colores, fuentes, etc.)
│   ├── base.css         # Estilos base (body, headings, etc.)
│   ├── grid.css         # Sistema de grid
│   ├── components.css   # Componentes (botones, tarjetas, etc.)
│   ├── utilities.css    # Utilidades (margenes, padding, etc.)
│   └── ...              # Otros módulos que puedas añadir
├── styles.css           # Archivo CSS original (legado/en refactorización)
├── main.css             # Archivo principal que importa los módulos
└── README.md            # Este archivo
```

## Cómo usar

En tus plantillas HTML, simplemente incluye el archivo `main.css`:

```html
<link rel="stylesheet" href="/static/css/main.css">
```

Si solo necesitas ciertos componentes, puedes editar `main.css` y comentar las importaciones que no necesites.

## Personalización

### Variables

Todas las variables CSS están definidas en `modules/variables.css`. Puedes modificar este archivo para cambiar colores, fuentes y otros valores globales.

### Componentes

Los componentes principales como botones, tarjetas y barras de navegación están en `modules/components.css`. Si necesitas añadir un nuevo componente personalizado, agrégalo a este archivo o crea un nuevo módulo.

### Utilidades

Las clases de utilidad (como márgenes, padding, flexbox, etc.) están en `modules/utilities.css`. Estas clases siguen la nomenclatura de Bootstrap 5.

## Migración desde styles.css

El archivo `styles.css` original sigue disponible pero está siendo refactorizado progresivamente. Para contribuir a la refactorización:

1. Identifica un conjunto relacionado de estilos en `styles.css`
2. Crea un nuevo módulo o añádelos a un módulo existente
3. Elimina o comenta los estilos en `styles.css` que ya hayas migrado
4. Actualiza este README si es necesario

## Principios de diseño

1. **Modularidad**: Cada módulo debe tener un propósito claro
2. **Ligereza**: Solo carga lo que necesitas
3. **Claridad**: Nombres de clases descriptivos y consistentes
4. **Compatibilidad**: Manteniendo compatibilidad con Bootstrap 5
