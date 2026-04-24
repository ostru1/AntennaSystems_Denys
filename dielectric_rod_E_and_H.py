import math
import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize, special


@dataclass(frozen=True)
class VariantParams:
    variant: int
    wavelength_m: float
    spacing_m: float
    rod_length_m: float
    rod_diameter_avg_m: float
    eps_r: float


VARIANT_9 = VariantParams(
    variant=9,
    wavelength_m=4.1e-2,
    spacing_m=14e-2,
    rod_length_m=23.7e-2,
    rod_diameter_avg_m=2.3e-2,
    eps_r=2.2,
)

OUTPUT_DIR = Path("output_lab4")
SHOW_PLOTS = os.getenv("SHOW_PLOTS", "0") == "1"
HALF_POWER_LEVEL = 0.707
THETA_STEP_RAD = 1e-4
XI_METHOD = os.getenv("XI_METHOD", "length").strip().lower()
XI_VALUE = os.getenv("XI_VALUE")


def xi_opt_by_length(wavelength_m: float, rod_length_m: float) -> float:
    return 1.0 + wavelength_m / (2.0 * rod_length_m)


def estimate_slowing_coefficient(eps_r: float, radius_m: float, wavelength_m: float) -> float:
    k0 = 2.0 * math.pi / wavelength_m
    k1 = k0 * math.sqrt(eps_r)
    k2 = k0

    v = radius_m * math.sqrt(k1**2 - k2**2)
    if v <= 0:
        raise ValueError("Invalid waveguide parameters: V must be positive.")

    def equation(u: float) -> float:
        if u <= 0 or u >= v:
            return float("nan")
        w = math.sqrt(v * v - u * u)

        j0 = special.jv(0, u)
        j1 = special.jv(1, u)
        k0w = special.kv(0, w)
        k1w = special.kv(1, w)

        if abs(j0) < 1e-14 or abs(k0w) < 1e-300:
            return float("nan")

        left = u * (j1 / j0)
        right = w * (k1w / k0w)
        return left - right

    grid = np.linspace(1e-6, v - 1e-6, 2000)
    values = []
    for u in grid:
        val = equation(float(u))
        values.append(val)

    for idx in range(1, len(grid)):
        f1 = values[idx - 1]
        f2 = values[idx]
        if not np.isfinite(f1) or not np.isfinite(f2):
            continue
        if f1 == 0:
            root_u = float(grid[idx - 1])
            break
        if f1 * f2 < 0:
            root_u = optimize.brentq(equation, float(grid[idx - 1]), float(grid[idx]), maxiter=200)
            break
    else:
        raise ValueError("Failed to find propagation constant root for the dielectric rod.")

    beta = math.sqrt(k1**2 - (root_u / radius_m) ** 2)
    if not (k2 < beta < k1):
        raise ValueError("Computed propagation constant is outside expected bounds.")
    return beta / k0


def normalize(values: np.ndarray) -> np.ndarray:
    max_value = float(np.max(values))
    if max_value <= 0:
        return values
    return values / max_value


def fb(theta: np.ndarray, *, slowing: float, rod_length_m: float, wavelength_m: float) -> np.ndarray:
    x = math.pi * rod_length_m / wavelength_m
    numerator = (slowing - 1.0) * np.sin(x * (slowing - np.cos(theta)))
    denominator = np.sin(x * (slowing - 1.0)) * (slowing - np.cos(theta))
    values = np.abs(numerator / denominator)
    values[np.isclose(theta, 0.0)] = 1.0
    return values


def fc(theta: np.ndarray, *, spacing_m: float, wavelength_m: float) -> np.ndarray:
    return np.abs(np.cos(math.pi * spacing_m * np.sin(theta) / wavelength_m))


def first_crossing(theta_deg: np.ndarray, values: np.ndarray, level: float) -> float:
    for idx in range(1, len(values)):
        if values[idx] <= level:
            x1 = theta_deg[idx - 1]
            x2 = theta_deg[idx]
            y1 = values[idx - 1]
            y2 = values[idx]
            return float(x1 + (level - y1) * (x2 - x1) / (y2 - y1))
    raise ValueError("Crossing was not found.")


def local_maxima(theta_deg: np.ndarray, values: np.ndarray) -> list[tuple[float, float]]:
    maxima = []
    for idx in range(1, len(values) - 1):
        if values[idx] > values[idx - 1] and values[idx] > values[idx + 1]:
            maxima.append((float(theta_deg[idx]), float(values[idx])))
    return maxima


def first_sidelobe_level(theta_deg: np.ndarray, values: np.ndarray, first_null_deg: float) -> tuple[float, float] | None:
    maxima = [(t, v) for (t, v) in local_maxima(theta_deg, values) if t >= first_null_deg]
    if not maxima:
        return None
    maxima.sort(key=lambda tv: tv[0])
    peak = max(maxima, key=lambda tv: tv[1])
    return peak


def arccos_if_valid(x: float) -> float | None:
    if x < -1.0 or x > 1.0:
        return None
    return math.degrees(math.acos(x))


def arcsin_if_valid(x: float) -> float | None:
    if x < -1.0 or x > 1.0:
        return None
    return math.degrees(math.asin(x))


def theoretical_angles_single_rod(params: VariantParams, slowing: float, m_max: int = 8) -> dict[str, list[float]]:
    lam = params.wavelength_m
    l = params.rod_length_m
    zeros = []
    maxima = []
    for m in range(1, m_max + 1):
        theta0 = arccos_if_valid(slowing - m * lam / l)
        thetam = arccos_if_valid(slowing - (2 * m + 1) * lam / (2 * l))
        if theta0 is not None:
            zeros.append(theta0)
        if thetam is not None:
            maxima.append(thetam)
    return {"zeros_deg": zeros, "maxima_deg": maxima}


def theoretical_angles_array_factor(params: VariantParams, m_max: int = 8) -> dict[str, list[float]]:
    lam = params.wavelength_m
    h = params.spacing_m
    zeros = []
    maxima = []
    for m in range(0, m_max + 1):
        theta0 = arcsin_if_valid((2 * m + 1) * lam / (2 * h))
        thetam = arcsin_if_valid(m * lam / h)
        if theta0 is not None:
            zeros.append(theta0)
        if thetam is not None:
            maxima.append(thetam)
    return {"zeros_deg": zeros, "maxima_deg": maxima}


def build_plot(path: Path, theta_deg: np.ndarray, values_h: np.ndarray, values_e: np.ndarray, title: str) -> None:
    fig, ax = plt.subplots(figsize=(20 / 2.54, 12 / 2.54))
    ax.plot(theta_deg, values_h, linewidth=1.0, label="|F_H(θ)|")
    ax.plot(theta_deg, values_e, linewidth=1.0, label="|F_E(θ)|")
    ax.axhline(HALF_POWER_LEVEL, linestyle="--", linewidth=0.7, color="red", label="Рівень 0.707")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("θ°", fontsize=10)
    ax.set_ylabel("|F(θ)|", fontsize=10)
    ax.set_xlim(0, 90)
    ax.set_ylim(-0.01, 1.01)
    ax.set_xticks(np.arange(0, 91, 5))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.grid(which="both", linestyle="--", linewidth=0.3, color="gray")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=600)
    plt.close(fig)


def save_csv(path: Path, theta_deg: np.ndarray, fh1: np.ndarray, fe1: np.ndarray, fh2: np.ndarray, fe2: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as file:
        file.write("theta_deg,FH_single,FE_single,FH_double,FE_double\n")
        for idx in range(len(theta_deg)):
            file.write(f"{theta_deg[idx]:.5f},{fh1[idx]:.6f},{fe1[idx]:.6f},{fh2[idx]:.6f},{fe2[idx]:.6f}\n")


def db(value: float) -> float:
    return 20.0 * math.log10(value)


def main(params: VariantParams = VARIANT_9) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    radius = params.rod_diameter_avg_m / 2.0
    xi_opt = xi_opt_by_length(params.wavelength_m, params.rod_length_m)
    xi_waveguide = None
    if XI_METHOD == "waveguide":
        try:
            xi_waveguide = estimate_slowing_coefficient(params.eps_r, radius, params.wavelength_m)
        except Exception:
            xi_waveguide = None

    if XI_METHOD == "value":
        if not XI_VALUE:
            raise ValueError("XI_METHOD=value requires XI_VALUE to be set.")
        slowing = float(XI_VALUE)
    elif XI_METHOD == "waveguide":
        if xi_waveguide is None:
            raise ValueError("XI_METHOD=waveguide failed to estimate xi for this variant.")
        slowing = xi_waveguide
    else:
        slowing = xi_opt

    theta = np.arange(0.0, math.pi / 2 + THETA_STEP_RAD, THETA_STEP_RAD)
    theta_deg = np.degrees(theta)

    fb_vals = fb(theta, slowing=slowing, rod_length_m=params.rod_length_m, wavelength_m=params.wavelength_m)
    fc_vals = fc(theta, spacing_m=params.spacing_m, wavelength_m=params.wavelength_m)

    fh_single = fb_vals
    fe_single = fb_vals * np.cos(theta)
    fh_double = fb_vals * fc_vals
    fe_double = fh_double * np.cos(theta)

    fh_single = normalize(fh_single)
    fe_single = normalize(fe_single)
    fh_double = normalize(fh_double)
    fe_double = normalize(fe_double)

    hp_single_h = first_crossing(theta_deg, fh_single, HALF_POWER_LEVEL)
    hp_single_e = first_crossing(theta_deg, fe_single, HALF_POWER_LEVEL)
    hp_double_h = first_crossing(theta_deg, fh_double, HALF_POWER_LEVEL)
    hp_double_e = first_crossing(theta_deg, fe_double, HALF_POWER_LEVEL)

    width_single_h = 2.0 * hp_single_h
    width_single_e = 2.0 * hp_single_e
    width_double_h = 2.0 * hp_double_h
    width_double_e = 2.0 * hp_double_e

    theoretical_single = theoretical_angles_single_rod(params, slowing)
    first_null_single = theoretical_single["zeros_deg"][0] if theoretical_single["zeros_deg"] else 0.0
    first_null_fc = arcsin_if_valid(params.wavelength_m / (2.0 * params.spacing_m))
    candidates = [v for v in [first_null_single, first_null_fc] if v is not None]
    first_null_double = min(candidates) if candidates else 0.0

    sll_single_h = first_sidelobe_level(theta_deg, fh_single, first_null_single)
    sll_single_e = first_sidelobe_level(theta_deg, fe_single, first_null_single)
    sll_double_h = first_sidelobe_level(theta_deg, fh_double, first_null_double)
    sll_double_e = first_sidelobe_level(theta_deg, fe_double, first_null_double)

    print(f"ЛР4, варіант = {params.variant}")
    print(f"lambda = {params.wavelength_m:.4f} m, h = {params.spacing_m:.4f} m")
    print(f"l = {params.rod_length_m:.4f} m, d_avg = {params.rod_diameter_avg_m:.4f} m, eps_r = {params.eps_r:.2f}")
    print(f"Estimated slowing coefficient xi = {slowing:.4f}")
    print(f"Reference xi_opt(=1+lambda/(2l)) = {xi_opt:.4f}")
    if xi_waveguide is not None:
        print(f"Reference xi_waveguide = {xi_waveguide:.4f}")
    print(f"xi method = {XI_METHOD}")
    print(f"Однострижнева: ШГП H={width_single_h:.2f}°, E={width_single_e:.2f}°")
    print(f"Двострижнева: ШГП H={width_double_h:.2f}°, E={width_double_e:.2f}°")
    if sll_single_h:
        print(f"SLL (single, H): theta={sll_single_h[0]:.2f} deg, |F|={sll_single_h[1]:.3f}, {db(sll_single_h[1]):.2f} dB")
    if sll_single_e:
        print(f"SLL (single, E): theta={sll_single_e[0]:.2f} deg, |F|={sll_single_e[1]:.3f}, {db(sll_single_e[1]):.2f} dB")
    if sll_double_h:
        print(f"SLL (double, H): theta={sll_double_h[0]:.2f} deg, |F|={sll_double_h[1]:.3f}, {db(sll_double_h[1]):.2f} dB")
    if sll_double_e:
        print(f"SLL (double, E): theta={sll_double_e[0]:.2f} deg, |F|={sll_double_e[1]:.3f}, {db(sll_double_e[1]):.2f} dB")

    build_plot(OUTPUT_DIR / "single_ds.png", theta_deg, fh_single, fe_single, "ДС однострижневої ДСА (H та E)")
    build_plot(OUTPUT_DIR / "double_ds.png", theta_deg, fh_double, fe_double, "ДС двострижневої ДСА (H та E)")
    save_csv(OUTPUT_DIR / "ds_normalized.csv", theta_deg, fh_single, fe_single, fh_double, fe_double)

    report_path = OUTPUT_DIR / "lab4_report.md"
    with report_path.open("w", encoding="utf-8") as file:
        file.write("# Лабораторна робота 4\n\n")
        file.write(f"- Варіант: {params.variant}\n")
        file.write(f"- λ: {params.wavelength_m:.4f} м\n")
        file.write(f"- h: {params.spacing_m:.4f} м\n")
        file.write(f"- l: {params.rod_length_m:.4f} м\n")
        file.write(f"- dср: {params.rod_diameter_avg_m:.4f} м\n")
        file.write(f"- εr: {params.eps_r:.2f}\n")
        file.write(f"- Оцінений ξ: {slowing:.4f}\n")
        file.write(f"- Довідково ξопт = 1 + λ/(2l): {xi_opt:.4f}\n\n")
        file.write(f"- Метод вибору ξ: {XI_METHOD}\n")
        if xi_waveguide is not None:
            file.write(f"- Довідково ξ (waveguide): {xi_waveguide:.4f}\n")
        file.write("\n")

        file.write("## Ширина головної пелюстки (0.707)\n")
        file.write(f"- Однострижнева, H: {width_single_h:.2f}°\n")
        file.write(f"- Однострижнева, E: {width_single_e:.2f}°\n")
        file.write(f"- Двострижнева, H: {width_double_h:.2f}°\n")
        file.write(f"- Двострижнева, E: {width_double_e:.2f}°\n\n")

        file.write("## Рівень бокових пелюсток (чисельно)\n")
        if sll_single_h:
            file.write(f"- Однострижнева, H: θ={sll_single_h[0]:.2f}°, |F|={sll_single_h[1]:.3f}, {db(sll_single_h[1]):.2f} дБ\n")
        if sll_single_e:
            file.write(f"- Однострижнева, E: θ={sll_single_e[0]:.2f}°, |F|={sll_single_e[1]:.3f}, {db(sll_single_e[1]):.2f} дБ\n")
        if sll_double_h:
            file.write(f"- Двострижнева, H: θ={sll_double_h[0]:.2f}°, |F|={sll_double_h[1]:.3f}, {db(sll_double_h[1]):.2f} дБ\n")
        if sll_double_e:
            file.write(f"- Двострижнева, E: θ={sll_double_e[0]:.2f}°, |F|={sll_double_e[1]:.3f}, {db(sll_double_e[1]):.2f} дБ\n")

        file.write("\n## Теоретичні кути (за формулами методички)\n")
        file.write("### Однострижнева (множник Fб)\n")
        file.write("- Нулі θ0: " + ", ".join(f"{v:.2f}°" for v in theoretical_single["zeros_deg"][:6]) + "\n")
        file.write("- Максимуми θm: " + ", ".join(f"{v:.2f}°" for v in theoretical_single["maxima_deg"][:6]) + "\n")

        theoretical_fc = theoretical_angles_array_factor(params)
        file.write("\n### Двострижнева (множник Fс)\n")
        file.write("- Нулі θ0c: " + ", ".join(f"{v:.2f}°" for v in theoretical_fc["zeros_deg"][:6]) + "\n")
        file.write("- Максимуми θmc: " + ", ".join(f"{v:.2f}°" for v in theoretical_fc["maxima_deg"][:6]) + "\n")

    if SHOW_PLOTS:
        plt.show()


if __name__ == "__main__":
    main()
