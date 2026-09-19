import pytest
import sympy as sp
from app.services.problems_repo import get_all_problems, get_problem_by_id


def test_problem_bank_counts():
    problems = get_all_problems()
    assert len(problems) == 15
    physics_probs = [p for p in problems if p.subject.value == "physics"]
    math_probs = [p for p in problems if p.subject.value == "math"]
    assert len(physics_probs) == 8
    assert len(math_probs) == 7


def test_phy_ohm_01():
    prob = get_problem_by_id("phy-ohm-01")
    assert prob is not None
    # Independent SymPy solution
    I, R = sp.symbols("I R")
    V = I * R
    val = float(V.subs({I: 0.5, R: 20.0}))
    assert val == 10.0
    assert prob.expected.value == 10.0
    assert prob.expected.unit == "V"
    calc_item = next(r for r in prob.rubric if r.id == "calculation")
    assert float(calc_item.target) == 10.0


def test_phy_res_02():
    prob = get_problem_by_id("phy-res-02")
    assert prob is not None
    R1, R2, V_src = sp.symbols("R1 R2 V_src")
    R_p = (R1 * R2) / (R1 + R2)
    r_val = float(R_p.subs({R1: 6.0, R2: 3.0}))
    assert r_val == 2.0
    I_tot = V_src / R_p
    i_val = float(I_tot.subs({R1: 6.0, R2: 3.0, V_src: 12.0}))
    assert i_val == 6.0
    assert prob.expected.value == 6.0
    assert prob.expected.unit == "A"
    req_item = next(r for r in prob.rubric if r.id == "req_calc")
    assert float(req_item.target) == 2.0


def test_phy_lens_03():
    prob = get_problem_by_id("phy-lens-03")
    assert prob is not None
    f_sym, u_sym, v_sym = sp.symbols("f u v")
    # 1/f = 1/v + 1/u => v = (f * u) / (u - f)
    sol = sp.solve(sp.Eq(1 / f_sym, 1 / v_sym + 1 / u_sym), v_sym)[0]
    v_val = float(sol.subs({f_sym: -20.0, u_sym: -30.0}))
    assert v_val == -60.0
    assert prob.expected.value == -60.0
    assert prob.expected.unit == "cm"


def test_phy_kin_04():
    prob = get_problem_by_id("phy-kin-04")
    assert prob is not None
    u, a, t = sp.symbols("u a t")
    v = u + a * t
    val = float(v.subs({u: 0.0, a: 2.5, t: 8.0}))
    assert val == 20.0
    assert prob.expected.value == 20.0
    assert prob.expected.unit == "m/s"


def test_phy_kin_05():
    prob = get_problem_by_id("phy-kin-05")
    assert prob is not None
    u, a, t = sp.symbols("u a t")
    s = u * t + sp.Rational(1, 2) * a * t**2
    val = float(s.subs({u: 0.0, a: 1.2, t: 10.0}))
    assert val == 60.0
    assert prob.expected.value == 60.0
    assert prob.expected.unit == "m"


def test_phy_work_06():
    prob = get_problem_by_id("phy-work-06")
    assert prob is not None
    m, u, v = sp.symbols("m u v")
    W = sp.Rational(1, 2) * m * (v**2 - u**2)
    val = float(W.subs({m: 4.0, u: 5.0, v: 0.0}))
    assert val == -50.0
    assert prob.expected.value == -50.0
    assert prob.expected.unit == "J"


def test_phy_trap_07():
    prob = get_problem_by_id("phy-trap-07")
    assert prob is not None
    F, A_cm2 = sp.symbols("F A_cm2")
    A_m2 = A_cm2 * 10**-4
    P = F / A_m2
    conv_val = float(A_m2.subs({A_cm2: 25.0}))
    assert conv_val == 0.0025
    p_val = float(P.subs({F: 50.0, A_cm2: 25.0}))
    assert p_val == 20000.0
    assert prob.expected.value == 20000.0
    assert prob.expected.unit == "Pa"


def test_phy_power_08():
    prob = get_problem_by_id("phy-power-08")
    assert prob is not None
    V_rated, P_rated, V_op = sp.symbols("V_rated P_rated V_op")
    R = V_rated**2 / P_rated
    r_val = float(R.subs({V_rated: 220.0, P_rated: 100.0}))
    assert r_val == 484.0
    P_op = V_op**2 / R
    p_val = float(P_op.subs({V_rated: 220.0, P_rated: 100.0, V_op: 110.0}))
    assert pytest.approx(p_val, 0.001) == 25.0
    assert prob.expected.value == 25.0
    assert prob.expected.unit == "W"


def test_math_quad_01():
    prob = get_problem_by_id("math-quad-01")
    assert prob is not None
    x = sp.Symbol("x")
    eq = 2 * x**2 - 7 * x + 3
    roots = [float(r) for r in sp.solve(eq, x)]
    assert sorted(roots) == [0.5, 3.0]
    D = (-7) ** 2 - 4 * 2 * 3
    assert D == 25.0
    assert sorted(prob.expected.value) == [0.5, 3.0]


def test_math_ap_02():
    prob = get_problem_by_id("math-ap-02")
    assert prob is not None
    a, d, n = 3, 4, 20
    an = a + (n - 1) * d
    assert an == 79
    sn = (n / 2) * (2 * a + (n - 1) * d)
    assert sn == 820.0
    assert prob.expected.value == 820.0


def test_math_diff_03():
    prob = get_problem_by_id("math-diff-03")
    assert prob is not None
    x = sp.Symbol("x")
    f = 3 * x**3 - 5 * x**2 + 4 * x - 7
    df = sp.diff(f, x)
    assert sp.simplify(df - (9 * x**2 - 10 * x + 4)) == 0
    val = float(df.subs({x: 2}))
    assert val == 20.0
    assert prob.expected.value == 20.0


def test_math_int_04():
    prob = get_problem_by_id("math-int-04")
    assert prob is not None
    x = sp.Symbol("x")
    f = 3 * x**2 + 2 * x - 1
    F = sp.integrate(f, x)
    assert sp.simplify(F - (x**3 + x**2 - x)) == 0
    val = float(sp.integrate(f, (x, 1, 3)))
    assert val == 32.0
    assert prob.expected.value == 32.0


def test_math_sys_05():
    prob = get_problem_by_id("math-sys-05")
    assert prob is not None
    x, y = sp.symbols("x y")
    eq1 = sp.Eq(3 * x + 2 * y, 13)
    eq2 = sp.Eq(2 * x - y, 4)
    sol = sp.solve((eq1, eq2), (x, y))
    assert float(sol[x]) == 3.0
    assert float(sol[y]) == 2.0
    assert prob.expected.value == [3.0, 2.0]


def test_math_trig_06():
    prob = get_problem_by_id("math-trig-06")
    assert prob is not None
    opp, adj = 4.0, 3.0
    hyp = sp.sqrt(opp**2 + adj**2)
    assert float(hyp) == 5.0
    sin_val = opp / float(hyp)
    cos_val = adj / float(hyp)
    prod = sin_val * cos_val
    assert pytest.approx(prod, 0.001) == 0.48
    assert prob.expected.value == 0.48


def test_math_geom_07():
    prob = get_problem_by_id("math-geom-07")
    assert prob is not None
    x1, y1 = -2.0, 3.0
    x2, y2 = 4.0, -5.0
    d = sp.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    assert float(d) == 10.0
    assert prob.expected.value == 10.0
