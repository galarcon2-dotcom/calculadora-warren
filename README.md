# 🏗️ Calculadora — Puente Armadura Tipo Warren

**Proyecto Integrador · Ingeniería · UNICA**

Aplicación web desarrollada con **Streamlit** para el análisis estructural de armaduras planas simétricas tipo Warren, usando el **método de secciones** con verificación de esfuerzos admisibles.

---

## ✨ Funcionalidades

| Módulo | Descripción |
|---|---|
| **Portada** | Página de bienvenida con diagrama animado y botón de ingreso |
| **Cálculo** | Fuerzas internas: cordón superior, inferior y diagonales |
| **Reacciones** | Ra y Rb por equilibrio estático |
| **Seguridad** | Verificación con FS = 1.67, estados SEGURO / LÍMITE / FALLA |
| **Diagrama** | Visualización interactiva con Plotly (tensión vs. compresión) |
| **Historial** | Registro persistente en JSON, descarga CSV |
| **Sugerencias** | Recomendaciones automáticas de diseño |

---

## 🚀 Ejecución local

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/calculadora-warren.git
cd calculadora-warren

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`.

---

## 📁 Estructura del proyecto

```
calculadora-warren/
├── app.py            ← Interfaz Streamlit (portada + calculadora)
├── warren.py         ← Motor de cálculo (WarrenTruss, HistoryManager)
├── requirements.txt  ← Dependencias para Streamlit Cloud
├── history.json      ← Historial de cálculos (auto-generado)
└── README.md
```

---

## 🧮 Parámetros de entrada

| Parámetro | Rango | Por defecto |
|---|---|---|
| Longitud total L | 1 – 500 m | 20 m |
| Altura H | 0.5 – 100 m | 3 m |
| Número de paneles | 2 – 20 | 6 |
| Carga total P | > 0 kN | 500 kN |
| Área de sección | > 0 cm² | 50 cm² |
| Material | A36 / A572 / Al 6061 | Acero A36 |

---

## 🔩 Materiales soportados

| Material | Fy (MPa) | σ_adm (MPa) |
|---|---|---|
| Acero A36 | 250 | 149.7 |
| Acero A572 | 345 | 206.6 |
| Aluminio 6061 | 276 | 165.3 |

---

## 📐 Método de cálculo

1. **Geometría**: se divide la longitud total `L` en `n` paneles de longitud `d = L/n`.
2. **Cargas**: la carga total `P` se distribuye uniformemente en los `n-1` nodos interiores superiores.
3. **Reacciones**: `Ra = Rb = P/2` (simetría).
4. **Cordón inferior** (tensión): `F = M / H` por equilibrio de momentos.
5. **Cordón superior** (compresión): `F = -M / H`.
6. **Diagonales**: `F = V / sin(α)` con `V` la fuerza cortante en cada panel.
7. **Esfuerzo**: `σ = F / A`; se compara con `σ_adm = Fy / 1.67`.

---

## ☁️ Despliegue en Streamlit Cloud

Ver la sección de despliegue al final del README.

1. Subir este repositorio a **GitHub** (público o privado).
2. Ir a [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Seleccionar repositorio, rama `main` y archivo `app.py`.
4. Hacer clic en **Deploy**.

---

## 👤 Autores

Proyecto Integrador — Facultad de Ingeniería · UNICA  
Universidad Cardenal Miguel Obando Bravo

---

## 📄 Licencia

MIT License — libre para uso académico.
