# ============================================================
#  warren.py  —  Motor de cálculo: Armadura Tipo Warren
#  Método de secciones | Factor de seguridad FS = 1.67
# ============================================================

import math
import json
import os
from datetime import datetime
from typing import Optional

HISTORY_FILE = os.path.join(os.getcwd(), "history.json")

MATERIALS: dict[str, dict] = {
    "Acero A36":     {"Fy_MPa": 250.0},
    "Acero A572":    {"Fy_MPa": 345.0},
    "Aluminio 6061": {"Fy_MPa": 276.0},
}


# ── MOTOR DE CÁLCULO ────────────────────────────────────────────────────────
class WarrenTruss:
    """
    Armadura simétrica tipo Warren.

    Parámetros
    ----------
    L       : Longitud total (m)
    H       : Altura (m)
    panels  : Número de paneles (2-20)
    P_total : Carga total aplicada en nodos superiores (kN)
    """

    def __init__(self, L: float, H: float, panels: int, P_total: float) -> None:
        self.L = L
        self.H = H
        self.panels = panels
        self.P_total = P_total
        self.results: dict = {}
        self._analyze()

    # ── análisis por método de secciones ────────────────────────────────────
    def _analyze(self) -> None:
        L, H, n, Pt = self.L, self.H, self.panels, self.P_total

        d          = L / n                          # longitud de panel
        diag_len   = math.hypot(d, H)               # longitud diagonal
        sin_a      = H / diag_len
        angle_deg  = math.degrees(math.atan2(H, d))
        load_nodes = n - 1                          # nodos interiores con carga
        P_node     = Pt / load_nodes                # carga por nodo
        Ra = Rb    = Pt / 2                         # reacciones simétricas

        # diagrama de cortante
        V, shear = [], Ra
        for i in range(n):
            V.append(shear)
            if i < load_nodes:
                shear -= P_node

        # fuerzas en cordón inferior (tensión positiva)
        bot_forces: list[float] = []
        for i in range(n):
            x_right = (i + 1) * d
            M = Ra * x_right
            if i > 0:
                for j in range(1, i + 1):
                    M -= P_node * (j * d)
            bot_forces.append(M / H)

        # fuerzas en cordón superior (compresión negativa)
        top_forces: list[float] = []
        for i in range(n):
            x_mid = (i + 0.5) * d
            M = Ra * x_mid - sum(
                P_node * (j * d)
                for j in range(1, i + 1)
                if j * d < x_mid
            )
            top_forces.append(-M / H)

        # fuerzas en diagonales
        diag_forces: list[float] = [V[i] / sin_a for i in range(n)]

        # construir lista de miembros
        members: list[dict] = []

        for i, f in enumerate(top_forces):
            members.append({
                "id":          f"CS{i+1}",
                "name":        f"Cordón Superior {i+1}",
                "type":        "top_chord",
                "force":       round(f, 3),
                "length":      round(d, 3),
                "stress_type": "Compresión" if f < 0 else "Tensión",
            })

        for i, f in enumerate(bot_forces):
            members.append({
                "id":          f"CI{i+1}",
                "name":        f"Cordón Inferior {i+1}",
                "type":        "bot_chord",
                "force":       round(f, 3),
                "length":      round(d, 3),
                "stress_type": "Tensión" if f > 0 else "Compresión",
            })

        for i, f in enumerate(diag_forces):
            members.append({
                "id":          f"D{i+1}",
                "name":        f"Diagonal {i+1}",
                "type":        "diagonal",
                "force":       round(f, 3),
                "length":      round(diag_len, 3),
                "stress_type": "Tensión" if f > 0 else "Compresión",
            })

        self.results = {
            "L":         L,
            "H":         H,
            "panels":    n,
            "P_total":   Pt,
            "P_node":    round(P_node, 3),
            "Ra":        round(Ra, 3),
            "Rb":        round(Rb, 3),
            "d":         round(d, 3),
            "diag":      round(diag_len, 3),
            "angle_deg": round(angle_deg, 2),
            "members":   members,
            "max_force": round(max(abs(m["force"]) for m in members), 3),
            "n_members": len(members),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ── evaluación de seguridad ──────────────────────────────────────────────
    def evaluate_safety(
        self,
        material: str = "Acero A36",
        section_area_cm2: float = 50.0,
    ) -> dict:
        """
        Verifica esfuerzos admisibles con FS = 1.67.

        Retorna dict con veredicto, evaluaciones por miembro y sugerencias.
        """
        Fy_MPa       = MATERIALS.get(material, MATERIALS["Acero A36"])["Fy_MPa"]
        allowable_MPa = Fy_MPa / 1.67
        A_mm2         = section_area_cm2 * 100.0   # cm² → mm²

        member_evals: list[dict] = []
        critical: list[str]      = []
        warnings: list[str]      = []

        for m in self.results["members"]:
            F_N       = abs(m["force"]) * 1000.0        # kN → N
            sigma_MPa = F_N / A_mm2
            ratio     = sigma_MPa / allowable_MPa

            if ratio > 1.0:
                status, color = "FALLA",  "danger"
                critical.append(m["id"])
            elif ratio > 0.85:
                status, color = "LÍMITE", "warn"
                warnings.append(m["id"])
            else:
                status, color = "SEGURO", "safe"

            member_evals.append({
                **m,
                "sigma_MPa":      round(sigma_MPa, 2),
                "allowable_MPa":  round(allowable_MPa, 2),
                "ratio":          round(ratio, 3),
                "status":         status,
                "color":          color,
            })

        if critical:
            verdict, v_level = "PELIGROSO",  "danger"
        elif warnings:
            verdict, v_level = "PRECAUCIÓN", "warn"
        else:
            verdict, v_level = "SEGURO",     "safe"

        suggestions = self._suggestions(
            critical, warnings, member_evals,
            section_area_cm2, allowable_MPa, material
        )

        return {
            "verdict":           verdict,
            "v_level":           v_level,
            "material":          material,
            "section_area_cm2":  round(section_area_cm2, 1),
            "Fy_MPa":            round(Fy_MPa, 0),
            "allowable_MPa":     round(allowable_MPa, 1),
            "critical_members":  critical,
            "warning_members":   warnings,
            "member_evals":      member_evals,
            "suggestions":       suggestions,
        }

    # ── sugerencias de diseño ────────────────────────────────────────────────
    def _suggestions(
        self,
        critical: list[str],
        warnings: list[str],
        evals: list[dict],
        area_cm2: float,
        allowable_MPa: float,
        material: str,
    ) -> list[str]:
        s: list[str] = []
        hl = self.results["H"] / self.results["L"]

        if critical:
            F_max_N   = max(abs(e["force"]) for e in evals) * 1000.0
            A_min_cm2 = (F_max_N / allowable_MPa / 100.0) * 1.15
            s.append(f"Aumentar sección transversal a mínimo {A_min_cm2:.1f} cm²")
            s.append("Considerar material de mayor resistencia (mayor Fy)")
            if self.results["panels"] < 8:
                s.append("Aumentar número de paneles para reducir fuerzas por miembro")
            if hl < 0.10:
                s.append("Aumentar altura del puente (relación H/L ≥ 0.10 recomendada)")
            if material != "Acero A572":
                s.append("Cambiar a Acero A572 (mayor resistencia que A36)")
        elif warnings:
            s.append("Miembros cercanos al límite — revisar cargas de servicio")
            s.append("Aumentar sección en 15-20% para mayor margen de seguridad")
        else:
            s.append("✅ Diseño dentro de parámetros admisibles")
            max_r     = max(e["ratio"] for e in evals) if evals else 0
            area_opt  = area_cm2 * max_r * 1.10
            if area_opt < area_cm2 * 0.80:
                s.append(
                    f"💡 Puede optimizar la sección a ~{area_opt:.1f} cm² (ahorro de material)"
                )

        if hl < 0.08:
            s.append(f"⚠️ Relación H/L = {hl:.2f} muy baja — riesgo de pandeo lateral")
        elif hl > 0.20:
            s.append(f"⚠️ Relación H/L = {hl:.2f} elevada — revisar cargas de viento")

        return s


# ── HISTORIAL ────────────────────────────────────────────────────────────────
class HistoryManager:
    """Lee y escribe el historial en history.json."""

    def __init__(self, fp: str = HISTORY_FILE) -> None:
        self.fp      = fp
        self.records = self._load()

    def _load(self) -> list[dict]:
        if os.path.exists(self.fp):
            try:
                with open(self.fp, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save(self, entry: dict) -> None:
        self.records.append(entry)
        with open(self.fp, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2, ensure_ascii=False)

    def clear(self) -> None:
        self.records = []
        if os.path.exists(self.fp):
            os.remove(self.fp)

    def get_all(self) -> list[dict]:
        return list(reversed(self.records))
