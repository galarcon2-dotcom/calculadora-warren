# 🌉 Calculadora de Puente de Armadura Tipo Warren

Aplicación web de análisis estructural para armaduras tipo Warren, desarrollada con **Streamlit** y **Plotly**. Calcula fuerzas internas, reacciones en apoyos, evalúa la seguridad de cada miembro y genera sugerencias de diseño.

---

## 🖥️ Demo en vivo

> Despliega tu propia instancia en **Streamlit Cloud** siguiendo los pasos de la sección [Despliegue](#-despliegue-en-streamlit-cloud).

---

## ✨ Funcionalidades

| Módulo | Descripción |
|---|---|
| **Análisis estructural** | Método de secciones para armadura Warren simétrica |
| **Reacciones** | Ra = Rb (carga simétrica distribuida en nodos superiores) |
| **Cordón superior** | Fuerzas en todos los elementos del cordón superior |
| **Cordón inferior** | Fuerzas en todos los elementos del cordón inferior |
| **Diagonales** | Fuerzas en todas las diagonales (patrón W alternado) |
| **Evaluación de seguridad** | Verificación contra esfuerzo admisible (FS = 1.67) |
| **Sugerencias de diseño** | Recomendaciones automáticas según el estado |
| **Diagrama interactivo** | Visualización Plotly con colores por tipo de esfuerzo |
| **Historial** | Registro persistente en JSON con exportación CSV |

---

## 📐 Materiales soportados

| Material | Fy (MPa) | σ_adm (MPa) |
|---|---|---|
| Acero A36 | 250 | 149.7 |
| Acero A572 | 345 | 206.6 |
| Aluminio 6061 | 276 | 165.3 |

---

## 📁 Estructura del proyecto

```
calculadora-warren/
│
├── app.py            # Interfaz Streamlit (UI + lógica de presentación)
├── warren.py         # Motor de cálculo estructural (sin dependencias de UI)
├── requirements.txt  # Dependencias Python
├── README.md         # Este archivo
└── history.json      # Historial generado automáticamente (no versionar)
```

---

## 🚀 Ejecutar localmente

### Requisitos previos
- Python 3.11 o superior
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/calculadora-warren.git
cd calculadora-warren

# 2. Crear entorno virtual (recomendado)
python -m venv venv

# En Windows:
venv\Scripts\activate

# En macOS / Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`.

---

## ☁️ Despliegue en Streamlit Cloud

### Paso 1 — Crear repositorio en GitHub

1. Ve a [github.com](https://github.com) e inicia sesión.
2. Haz clic en **"New repository"**.
3. Nombre sugerido: `calculadora-warren`.
4. Selecciona **Public** (necesario para el plan gratuito de Streamlit Cloud).
5. **No** inicialices con README (ya lo tienes).
6. Haz clic en **"Create repository"**.

### Paso 2 — Subir los archivos

**Opción A — Desde la línea de comandos (recomendado):**

```bash
# Dentro de la carpeta calculadora-warren/
git init
git add app.py warren.py requirements.txt README.md
git commit -m "feat: calculadora Warren en Streamlit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/calculadora-warren.git
git push -u origin main
```

**Opción B — Desde la interfaz web de GitHub:**

1. Abre el repositorio recién creado.
2. Haz clic en **"uploading an existing file"**.
3. Arrastra los 4 archivos (`app.py`, `warren.py`, `requirements.txt`, `README.md`).
4. Haz clic en **"Commit changes"**.

> ⚠️ **Importante:** NO subas `history.json` al repositorio. El historial se genera en tiempo de ejecución.

### Paso 3 — Conectar GitHub con Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io).
2. Inicia sesión con tu cuenta de GitHub.
3. Haz clic en **"New app"**.
4. En el formulario:
   - **Repository:** `TU_USUARIO/calculadora-warren`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Haz clic en **"Deploy!"**.

### Paso 4 — Verificar el despliegue

- Streamlit Cloud instalará automáticamente las dependencias del `requirements.txt`.
- El proceso tarda entre 1 y 3 minutos.
- Al terminar obtendrás una URL pública con el formato:
  `https://TU_USUARIO-calculadora-warren-app-HASH.streamlit.app`

---

## 🔧 Resolución de errores comunes

### Error: `ModuleNotFoundError: No module named 'warren'`
**Causa:** `warren.py` no está en el repositorio o en la misma carpeta que `app.py`.  
**Solución:** Asegúrate de que ambos archivos están en la raíz del repositorio y fueron subidos correctamente.

---

### Error: `ModuleNotFoundError: No module named 'plotly'`
**Causa:** El `requirements.txt` no se subió o tiene errores de sintaxis.  
**Solución:**
1. Verifica que `requirements.txt` existe en la raíz.
2. Comprueba que no tiene espacios ni caracteres especiales.
3. En Streamlit Cloud, abre **"Manage app" → "Reboot app"** para forzar reinstalación.

---

### Error: `StreamlitAPIException` o pantalla en blanco
**Causa:** Error de sintaxis en `app.py`.  
**Solución:** Revisa los logs en Streamlit Cloud (botón **"Manage app"**) para ver el error exacto.

---

### El historial no persiste entre sesiones en Streamlit Cloud
**Causa:** Streamlit Cloud reinicia los procesos periódicamente.  
**Solución:** Esto es comportamiento esperado en el plan gratuito. Para persistencia real, puedes:
- Usar `st.session_state` (ya implementado para la sesión activa).
- Integrar una base de datos (Supabase, Firebase) en futuras versiones.

---

### Error de permisos al escribir `history.json`
**Causa:** El sistema de archivos de Streamlit Cloud puede ser de solo lectura en algunos directorios.  
**Solución:** El código ya maneja esta excepción — el historial funcionará en memoria durante la sesión activa aunque no se persista en disco.

---

## 🔬 Metodología de cálculo

- **Modelo:** Armadura plana simplemente apoyada, carga puntual distribuida uniformemente en los **nodos intermedios del cordón superior**.
- **Método:** Secciones (Ritter). La fuerza en cada miembro se calcula por equilibrio de momentos o fuerzas en la sección cortada.
- **Factor de seguridad:** FS = 1.67 (AISC ASD — Allowable Stress Design).
- **Esfuerzo admisible:** σ_adm = Fy / 1.67
- **Criterio de falla:** ratio = σ / σ_adm > 1.0 → FALLA
- **Criterio de advertencia:** ratio > 0.85 → LÍMITE

---

## 📊 Parámetros de entrada

| Parámetro | Símbolo | Rango | Unidad |
|---|---|---|---|
| Longitud total | L | 2 – 500 | m |
| Altura | H | 0.5 – 100 | m |
| Número de paneles | n | 2 – 20 | — |
| Carga total | P | 1 – 1,000,000 | kN |
| Área de sección | A | 1 – 5000 | cm² |
| Material | — | A36 / A572 / Al6061 | — |

---

## 📜 Licencia

MIT License — libre para uso educativo y profesional.

---

## 👤 Autor

Desarrollado como herramienta de análisis estructural para puentes de armadura tipo Warren.  
Conversión de Tkinter a Streamlit manteniendo toda la lógica de cálculo original.
