# Lunch Microcentro — instrucciones de instalación

App de gestión completa: pedidos, recetario con rendimientos, costos, packaging, gastos, clientes.

---

## Paso 1: Instalar Python (una sola vez)

### En Mac
1. Abrí la Terminal (Cmd + Espacio → escribí "Terminal")
2. Tipeá `python3 --version` y presioná Enter
   - Si te muestra una versión (ej: `Python 3.11.x`) → **ya lo tenés, pasá al Paso 2**
   - Si dice "command not found" → seguí abajo
3. Instalá Python desde https://www.python.org/downloads/ (botón amarillo "Download Python")
4. Abrí el `.pkg` descargado y dale "Continuar" hasta el final

### En Windows
1. Andá a https://www.python.org/downloads/
2. Apretá el botón amarillo "Download Python"
3. **MUY IMPORTANTE:** al abrir el instalador, **marcá la casilla "Add Python to PATH"** antes de instalar
4. "Install Now" → esperá a que termine

---

## Paso 2: Abrir la app

### En Mac
- Doble click en **`Abrir Lunch.command`**
- La primera vez puede aparecer un aviso de seguridad: click derecho → "Abrir" → "Abrir igualmente"
- Va a tardar 1-2 minutos la primera vez (instala las librerías)
- Se abre solo en el navegador en `http://localhost:8501`

### En Windows
- Doble click en **`Abrir Lunch.bat`**
- Si Windows pide permiso ("Windows protegió tu PC") → "Más información" → "Ejecutar de todos modos"
- Tarda 1-2 minutos la primera vez
- Se abre solo en el navegador en `http://localhost:8501`

---

## Uso diario

A partir de la segunda vez, el doble click abre la app en menos de 10 segundos.

**Para cerrar:** simplemente cerrá la ventana negra (terminal) que queda abierta de fondo.

---

## Los datos: dónde se guardan

Todos los datos viven en el archivo `data/lunch.db` (una base de datos SQLite local).
Hacer **backup** = copiar ese archivo a otro lado.

Si querés empezar desde cero: borrá `data/lunch.db` y la app se regenera con los datos iniciales al próximo arranque.

---

## Las 10 pantallas

1. **Dashboard** — KPIs de la semana (ingresos, costos, ganancia, ranking de platos)
2. **Pedidos** — listado y carga de nuevos pedidos
3. **Producción del día** — qué cocinar hoy + lista de ingredientes totales en peso crudo
4. **Costos por plato** — costo real desglosado (comida + packaging) y margen
5. **Recetario** — editar cantidades y rendimientos por plato
6. **Insumos** — maestro de ingredientes. Si cambia el precio del pollo, lo cambiás acá y se actualiza en TODOS los platos
7. **Packaging** — descartables (bandejas, potes, film, rollo)
8. **Gastos** — todas las compras con totales por categoría
9. **Clientes** — cartera con historial
10. **Configuración** — parámetros del negocio, precios de platos

---

## Problemas comunes

**"Mac dice que no puede verificar el desarrollador"**
→ Click derecho sobre `Abrir Lunch.command` → "Abrir" → "Abrir igualmente". Solo una vez.

**"Windows protegió tu PC"**
→ "Más información" → "Ejecutar de todos modos". Solo una vez.

**No se abre el navegador automáticamente**
→ Abrilo manualmente y andá a `http://localhost:8501`

**Quiero llevarme los datos a otra computadora**
→ Copiá el archivo `data/lunch.db` y pegalo en la carpeta `data/` de la otra compu.

---

¿Dudas? Avisame.
