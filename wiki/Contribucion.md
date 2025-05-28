# Contribución

¡Las contribuciones son bienvenidas y fundamentales para la comunidad de código abierto! Si tienes ideas para mejorar HodlWatcher Web o deseas corregir algún problema, siéntete libre de participar.

## ¿Cómo Contribuir?

1.  **Haz un Fork del Proyecto:**
    Comienza por crear tu propia copia (fork) del repositorio `KrogZetsBit/HodlWatcher_web` en tu cuenta de GitHub.

2.  **Crea una Rama para tu Característica o Corrección:**
    Desde tu fork, crea una nueva rama descriptiva para tus cambios.
    ```bash
    git checkout -b feature/NuevaCaracteristicaIncreible
    # o para una corrección:
    # git checkout -b fix/CorreccionErrorMenor
    ```

3.  **Realiza tus Cambios:**
    Implementa tu nueva característica o corrige el error. Asegúrate de seguir el estilo de código existente y añadir comentarios claros donde sea necesario.

4.  **Añade Pruebas (si aplica):**
    Si estás añadiendo una nueva funcionalidad o modificando una existente de forma significativa, por favor, incluye pruebas unitarias o de integración que cubran tus cambios. Las pruebas ayudan a asegurar la estabilidad y calidad del código. Para ejecutar las pruebas:
    ```bash
    pytest
    ```
    Para verificar la cobertura de las pruebas:
    ```bash
    coverage run -m pytest
    coverage html
    # Luego abre htmlcov/index.html en tu navegador
    ```

5.  **Confirma tus Cambios (Commit):**
    Usa mensajes de commit claros y descriptivos.
    ```bash
    git commit -m "Añade nueva característica X que hace Y"
    # o
    # git commit -m "Corrige error Z en el módulo W"
    ```

6.  **Empuja tus Cambios a tu Rama (Push):**
    Sube los cambios a tu repositorio fork.
    ```bash
    git push origin feature/NuevaCaracteristicaIncreible
    ```

7.  **Abre un Pull Request (PR):**
    Ve al repositorio original `KrogZetsBit/HodlWatcher_web` en GitHub y abre un Pull Request desde tu rama hacia la rama principal del proyecto (generalmente `main` o `master`).
    *   Describe claramente los cambios que has realizado en el PR.
    *   Si tu PR está relacionado con un "Issue" existente, menciónalo.

## Estilo de Código y Calidad

*   Intenta seguir el estilo de código existente en el proyecto.
*   El proyecto utiliza `Ruff` para el formateo y linting. Considera configurarlo en tu editor o ejecutarlo antes de hacer commit.
*   Asegúrate de que las pruebas pasen después de tus cambios.

## Reporte de Errores o Sugerencias

Si no deseas contribuir con código directamente pero has encontrado un error o tienes una idea para una nueva funcionalidad, por favor:
*   **Abre un "Issue"** en el repositorio de GitHub.
*   Describe el problema o la sugerencia con el mayor detalle posible.

¡Gracias por tu interés en mejorar HodlWatcher Web!
