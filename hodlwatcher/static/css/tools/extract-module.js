#!/usr/bin/env node

/**
 * Script para ayudar a extraer componentes CSS de styles.css a módulos separados
 *
 * Uso: node extract-module.js SELECTOR MÓDULO_DESTINO
 *
 * Ejemplos:
 *   node extract-module.js ".btn" components.css    # Extrae las reglas de botones
 *   node extract-module.js ".navbar" components.css  # Extrae las reglas de navbar
 *   node extract-module.js ".container" grid.css     # Extrae las reglas de grid
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const STYLES_PATH = path.join(__dirname, '..', 'styles.css');
const MODULES_PATH = path.join(__dirname, '..', 'modules');

// Verificar argumentos
if (process.argv.length < 4) {
  console.error('Uso: node extract-module.js SELECTOR MÓDULO_DESTINO');
  process.exit(1);
}

const selector = process.argv[2];
const targetModule = process.argv[3];
const targetPath = path.join(MODULES_PATH, targetModule);

// Verificar que el módulo de destino exista
if (!fs.existsSync(targetPath)) {
  console.error(`El módulo de destino ${targetModule} no existe en ${MODULES_PATH}`);
  process.exit(1);
}

// Leer el archivo de estilos
const cssContent = fs.readFileSync(STYLES_PATH, 'utf8');

// Encontrar las reglas CSS que coinciden con el selector
function findCssRules(css, selector) {
  const rules = [];
  const lines = css.split('\n');
  let inRule = false;
  let currentRule = '';
  let braceCount = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Si estamos dentro de una regla
    if (inRule) {
      currentRule += line + '\n';
      braceCount += (line.match(/{/g) || []).length;
      braceCount -= (line.match(/}/g) || []).length;

      // Si cerramos todas las llaves, la regla ha terminado
      if (braceCount === 0) {
        rules.push(currentRule);
        inRule = false;
        currentRule = '';
      }
    }
    // Si encontramos el selector, comenzamos una nueva regla
    else if (line.includes(selector)) {
      inRule = true;
      currentRule = line + '\n';
      braceCount += (line.match(/{/g) || []).length;
      braceCount -= (line.match(/}/g) || []).length;

      // Si la regla se abre y cierra en la misma línea
      if (braceCount === 0 && line.includes('{') && line.includes('}')) {
        rules.push(currentRule);
        inRule = false;
        currentRule = '';
      }
    }
  }

  return rules;
}

// Encontrar las reglas
const matchedRules = findCssRules(cssContent, selector);

if (matchedRules.length === 0) {
  console.error(`No se encontraron reglas para el selector "${selector}"`);
  process.exit(1);
}

// Mostrar las reglas encontradas
console.log(`Se encontraron ${matchedRules.length} reglas para el selector "${selector}":`);
matchedRules.forEach((rule, index) => {
  console.log(`\n--- Regla ${index + 1} ---\n${rule}`);
});

// Preguntar si queremos añadir las reglas al módulo
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.question(`\n¿Añadir estas reglas a ${targetModule}? (s/n): `, (answer) => {
  if (answer.toLowerCase() === 's') {
    // Añadir las reglas al módulo
    const moduleContent = fs.readFileSync(targetPath, 'utf8');
    const updatedContent = moduleContent + '\n/* Reglas extraídas de styles.css */\n' + matchedRules.join('\n');
    fs.writeFileSync(targetPath, updatedContent);
    console.log(`Reglas añadidas a ${targetModule}`);

    // Preguntar si queremos comentar las reglas en styles.css
    rl.question('\n¿Comentar estas reglas en styles.css? (s/n): ', (answer) => {
      if (answer.toLowerCase() === 's') {
        let updatedStyles = cssContent;
        matchedRules.forEach(rule => {
          const commentedRule = rule.split('\n').map(line => '/* ' + line + ' */').join('\n');
          updatedStyles = updatedStyles.replace(rule, commentedRule);
        });
        fs.writeFileSync(STYLES_PATH, updatedStyles);
        console.log('Reglas comentadas en styles.css');
      }
      rl.close();
    });
  } else {
    rl.close();
  }
});
