"""Generate clean standard fixtures for all 15 problems in samples/fixtures/."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "samples" / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

PROBLEM_FIXTURES = {
    "phy-ohm-01": [
        {"id": 1, "text": "V = I * R", "confidence": 0.98, "needs_confirmation": False},
        {"id": 2, "text": "V = 0.5 * 20", "confidence": 0.95, "needs_confirmation": False},
        {"id": 3, "text": "V = 10 V", "confidence": 0.96, "needs_confirmation": False},
    ],
    "phy-res-02": [
        {"id": 1, "text": "1/R_p = 1/R_1 + 1/R_2", "confidence": 0.97, "needs_confirmation": False},
        {"id": 2, "text": "1/R_p = 1/6 + 1/3 = 1/2 => R_p = 2", "confidence": 0.95, "needs_confirmation": False},
        {"id": 3, "text": "I = V / R_p", "confidence": 0.98, "needs_confirmation": False},
        {"id": 4, "text": "I = 12 / 2 = 6 A", "confidence": 0.96, "needs_confirmation": False},
    ],
    "phy-lens-03": [
        {"id": 1, "text": "1/f = 1/v + 1/u", "confidence": 0.96, "needs_confirmation": False},
        {"id": 2, "text": "1/(-20) = 1/v + 1/(-30)", "confidence": 0.94, "needs_confirmation": False},
        {"id": 3, "text": "1/v = -1/20 + 1/30 = -1/60", "confidence": 0.93, "needs_confirmation": False},
        {"id": 4, "text": "v = -60 cm", "confidence": 0.96, "needs_confirmation": False},
    ],
    "phy-kin-04": [
        {"id": 1, "text": "v = u + a * t", "confidence": 0.98, "needs_confirmation": False},
        {"id": 2, "text": "v = 0 + 2.5 * 8", "confidence": 0.96, "needs_confirmation": False},
        {"id": 3, "text": "v = 20 m/s", "confidence": 0.97, "needs_confirmation": False},
    ],
    "phy-kin-05": [
        {"id": 1, "text": "s = u * t + 0.5 * a * t**2", "confidence": 0.97, "needs_confirmation": False},
        {"id": 2, "text": "s = 0 * 10 + 0.5 * 1.2 * 10**2", "confidence": 0.95, "needs_confirmation": False},
        {"id": 3, "text": "s = 0.6 * 100 = 60 m", "confidence": 0.96, "needs_confirmation": False},
    ],
    "phy-work-06": [
        {"id": 1, "text": "W = 0.5 * m * (v**2 - u**2)", "confidence": 0.96, "needs_confirmation": False},
        {"id": 2, "text": "W = 0.5 * 4 * (0**2 - 5**2)", "confidence": 0.94, "needs_confirmation": False},
        {"id": 3, "text": "W = 2 * (-25) = -50 J", "confidence": 0.96, "needs_confirmation": False},
    ],
    "phy-trap-07": [
        {"id": 1, "text": "A = 25 cm^2 = 25 * 10^-4 m^2 = 0.0025 m^2", "confidence": 0.95, "needs_confirmation": False},
        {"id": 2, "text": "P = F / A", "confidence": 0.98, "needs_confirmation": False},
        {"id": 3, "text": "P = 50 / 0.0025 = 20000", "confidence": 0.94, "needs_confirmation": False},
        {"id": 4, "text": "P = 20000 Pa", "confidence": 0.97, "needs_confirmation": False},
    ],
    "phy-power-08": [
        {"id": 1, "text": "R = V**2 / P", "confidence": 0.96, "needs_confirmation": False},
        {"id": 2, "text": "R = 220**2 / 100 = 484", "confidence": 0.94, "needs_confirmation": False},
        {"id": 3, "text": "P = V**2 / R", "confidence": 0.96, "needs_confirmation": False},
        {"id": 4, "text": "P = 110**2 / 484 = 25 W", "confidence": 0.95, "needs_confirmation": False},
    ],
    "math-quad-01": [
        {"id": 1, "text": "x = (-b + sqrt(b**2 - 4*a*c))/(2*a)", "confidence": 0.96, "needs_confirmation": False},
        {"id": 2, "text": "a = 2, b = -7, c = 3", "confidence": 0.97, "needs_confirmation": False},
        {"id": 3, "text": "D = (-7)**2 - 4*2*3 = 25", "confidence": 0.95, "needs_confirmation": False},
        {"id": 4, "text": "x = (7 + 5)/4 = 3, x = 0.5", "confidence": 0.94, "needs_confirmation": False},
    ],
    "math-ap-02": [
        {"id": 1, "text": "a_n = a + (n - 1) * d", "confidence": 0.97, "needs_confirmation": False},
        {"id": 2, "text": "a_20 = 3 + 19 * 4 = 79", "confidence": 0.95, "needs_confirmation": False},
        {"id": 3, "text": "S_n = (n / 2) * (a + l)", "confidence": 0.96, "needs_confirmation": False},
        {"id": 4, "text": "S_20 = (20 / 2) * (3 + 79) = 10 * 82 = 820", "confidence": 0.95, "needs_confirmation": False},
    ],
    "math-diff-03": [
        {"id": 1, "text": "dy/dx = 9*x**2 - 10*x + 4", "confidence": 0.96, "needs_confirmation": False},
        {"id": 2, "text": "At x = 2: 9*(2)**2 - 10*(2) + 4", "confidence": 0.95, "needs_confirmation": False},
        {"id": 3, "text": "dy/dx = 36 - 20 + 4 = 20", "confidence": 0.96, "needs_confirmation": False},
    ],
    "math-int-04": [
        {"id": 1, "text": "F(x) = x**3 + x**2 - x", "confidence": 0.96, "needs_confirmation": False},
        {"id": 2, "text": "F(3) = 27 + 9 - 3 = 33, F(1) = 1 + 1 - 1 = 1", "confidence": 0.94, "needs_confirmation": False},
        {"id": 3, "text": "I = 33 - 1 = 32", "confidence": 0.97, "needs_confirmation": False},
    ],
    "math-sys-05": [
        {"id": 1, "text": "y = 2*x - 4", "confidence": 0.95, "needs_confirmation": False},
        {"id": 2, "text": "3*x + (2*x - 4) = 11 => 5*x = 15 => x = 3", "confidence": 0.96, "needs_confirmation": False},
        {"id": 3, "text": "y = 2*(3) - 4 = 2", "confidence": 0.96, "needs_confirmation": False},
    ],
    "math-trig-06": [
        {"id": 1, "text": "h = sqrt(4**2 + 3**2) = 5", "confidence": 0.96, "needs_confirmation": False},
        {"id": 2, "text": "sin = 4/5 = 0.8, cos = 3/5 = 0.6", "confidence": 0.95, "needs_confirmation": False},
        {"id": 3, "text": "sin * cos = 0.8 * 0.6 = 0.48", "confidence": 0.96, "needs_confirmation": False},
    ],
    "math-geom-07": [
        {"id": 1, "text": "d = sqrt((x_2 - x_1)**2 + (y_2 - y_1)**2)", "confidence": 0.97, "needs_confirmation": False},
        {"id": 2, "text": "d = sqrt((7 - 1)**2 + (-2 - 6)**2) = sqrt(6**2 + (-8)**2)", "confidence": 0.95, "needs_confirmation": False},
        {"id": 3, "text": "d = sqrt(36 + 64) = sqrt(100) = 10", "confidence": 0.96, "needs_confirmation": False},
    ],
}


def main():
    for pid, steps in PROBLEM_FIXTURES.items():
        out_path = FIXTURES_DIR / f"{pid}.json"
        data = {"problem_id": pid, "steps": steps}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Generated fixture for {pid}: {out_path.name}")


if __name__ == "__main__":
    main()
