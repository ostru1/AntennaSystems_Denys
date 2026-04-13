import math
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


VARIANT = 9
LAMBDA = 3.3e-2
A = 12e-2
B = 12e-2

OUTPUT_DIR = Path("output_lab3")
SHOW_PLOTS = os.getenv("SHOW_PLOTS", "0") == "1"
HALF_POWER_LEVEL = 0.707
THETA_STEP = 1e-4


def huygens_factor(theta: np.ndarray) -> np.ndarray:
    return (1.0 + np.cos(theta)) / 2.0


def aperture_factor_e(theta: np.ndarray) -> np.ndarray:
    x = np.pi * B * np.sin(theta) / LAMBDA
    factor = np.ones_like(theta)
    mask = np.abs(x) > 1e-12
    factor[mask] = np.sin(x[mask]) / x[mask]
    return factor


def aperture_factor_h(theta: np.ndarray) -> np.ndarray:
    s = np.sin(theta)
    x = np.pi * A * s / LAMBDA
    denominator = 1.0 - (2.0 * A * s / LAMBDA) ** 2
    factor = np.cos(x) / denominator

    removable = np.abs(denominator) < 1e-8
    factor[removable] = np.pi / 4.0
    factor[np.isclose(theta, 0.0)] = 1.0
    return factor


def find_half_power_width(theta_deg: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    for idx in range(1, len(values)):
        if values[idx] <= HALF_POWER_LEVEL:
            x1 = theta_deg[idx - 1]
            x2 = theta_deg[idx]
            y1 = values[idx - 1]
            y2 = values[idx]
            theta_hp = x1 + (HALF_POWER_LEVEL - y1) * (x2 - x1) / (y2 - y1)
            return theta_hp, 2.0 * theta_hp
    raise ValueError("Half-power point was not found.")


def find_local_extrema(theta_deg: np.ndarray, values: np.ndarray) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    minima = []
    maxima = []
    for idx in range(1, len(values) - 1):
        if values[idx] < values[idx - 1] and values[idx] < values[idx + 1]:
            minima.append((theta_deg[idx], values[idx]))
        if values[idx] > values[idx - 1] and values[idx] > values[idx + 1]:
            maxima.append((theta_deg[idx], values[idx]))
    return minima, maxima


def side_lobe_level(maxima: list[tuple[float, float]]) -> tuple[float, float] | None:
    return maxima[0] if maxima else None


def save_csv(path: Path, theta_deg: np.ndarray, f1: np.ndarray, fc_e: np.ndarray, fc_h: np.ndarray, f_e: np.ndarray, f_h: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as file:
        file.write("theta_deg,F1,FC_E,FC_H,F_E,F_H\n")
        for idx in range(len(theta_deg)):
            file.write(
                f"{theta_deg[idx]:.5f},{f1[idx]:.6f},{fc_e[idx]:.6f},{fc_h[idx]:.6f},{f_e[idx]:.6f},{f_h[idx]:.6f}\n"
            )


def save_report(
    path: Path,
    width_h: float,
    width_e: float,
    half_theta_h: float,
    half_theta_e: float,
    minima_h: list[tuple[float, float]],
    minima_e: list[tuple[float, float]],
    maxima_h: list[tuple[float, float]],
    maxima_e: list[tuple[float, float]],
) -> None:
    first_side_h = side_lobe_level(maxima_h)
    first_side_e = side_lobe_level(maxima_e)

    with path.open("w", encoding="utf-8") as file:
        file.write("# Лабораторна робота 3\n\n")
        file.write("## Вхідні дані\n")
        file.write(f"- Варіант: {VARIANT}\n")
        file.write(f"- Довжина хвилі λ: {LAMBDA:.3f} м\n")
        file.write(f"- Розмір розкриву рупора a x b: {A:.3f} x {B:.3f} м\n\n")

        file.write("## Основні результати\n")
        file.write(f"- Ширина головної пелюстки у площині E: {width_e:.2f}°\n")
        file.write(f"- Ширина головної пелюстки у площині H: {width_h:.2f}°\n")
        file.write(f"- Кут половинної потужності у площині E: {half_theta_e:.2f}°\n")
        file.write(f"- Кут половинної потужності у площині H: {half_theta_h:.2f}°\n")
        if first_side_e is not None:
            file.write(
                f"- Перший боковий пелюсток у площині E: θ = {first_side_e[0]:.2f}°, |F_E| = {first_side_e[1]:.3f}, {20 * math.log10(first_side_e[1]):.2f} дБ\n"
            )
        if first_side_h is not None:
            file.write(
                f"- Перший боковий пелюсток у площині H: θ = {first_side_h[0]:.2f}°, |F_H| = {first_side_h[1]:.3f}, {20 * math.log10(first_side_h[1]):.2f} дБ\n"
            )

        file.write("\n## Нулі ДС\n")
        for idx, (theta, _) in enumerate(minima_e[:5], start=1):
            file.write(f"- Площина E, мінімум {idx}: {theta:.2f}°\n")
        for idx, (theta, _) in enumerate(minima_h[:5], start=1):
            file.write(f"- Площина H, мінімум {idx}: {theta:.2f}°\n")

        file.write("\n## Максимуми бокових пелюсток\n")
        for idx, (theta, value) in enumerate(maxima_e[:5], start=1):
            file.write(f"- Площина E, максимум {idx}: θ = {theta:.2f}°, |F_E| = {value:.3f}\n")
        for idx, (theta, value) in enumerate(maxima_h[:5], start=1):
            file.write(f"- Площина H, максимум {idx}: θ = {theta:.2f}°, |F_H| = {value:.3f}\n")


def build_plot(
    path: Path,
    theta_deg: np.ndarray,
    f1: np.ndarray,
    fc: np.ndarray,
    total: np.ndarray,
    half_theta: float,
    half_value: float,
    minima: list[tuple[float, float]],
    maxima: list[tuple[float, float]],
    plane_name: str,
) -> None:
    fig, ax = plt.subplots(figsize=(20 / 2.54, 12 / 2.54))
    ax.plot(theta_deg, f1, linewidth=0.8, label=r"$F_1(\theta)$")
    ax.plot(theta_deg, fc, linewidth=0.8, label=rf"$F_{{C{plane_name}}}(\theta)$")
    ax.plot(theta_deg, total, linewidth=1.0, label=rf"$F_{{{plane_name}}}(\theta)$")
    ax.plot(half_theta, half_value, "o", markersize=5, label=f"ШГП у площині {plane_name}")

    if minima:
        ax.plot(
            [theta for theta, _ in minima],
            [value for _, value in minima],
            "o",
            markersize=4,
            color="blue",
            label=f"Мінімуми {plane_name}",
        )
    if maxima:
        ax.plot(
            [theta for theta, _ in maxima],
            [value for _, value in maxima],
            "o",
            markersize=4,
            color="black",
            label=f"Максимуми {plane_name}",
        )

    ax.axhline(HALF_POWER_LEVEL, linestyle="--", linewidth=0.7, color="red")
    ax.axvline(half_theta, linestyle="--", linewidth=0.7, color="red")
    ax.annotate(
        f"({half_value:.3f}, {half_theta:.2f}°)",
        xy=(half_theta, half_value),
        xytext=(half_theta + 2, min(0.95, half_value + 0.08)),
        arrowprops={"arrowstyle": "->", "color": "black"},
        fontsize=7,
    )

    ax.set_xlabel("θ°", fontsize=10)
    ax.set_ylabel(f"|F{plane_name}(θ)|", fontsize=10)
    ax.set_xlim(0, 90)
    ax.set_ylim(-0.01, 1.01)
    ax.set_xticks(np.arange(0, 91, 5))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.grid(which="both", linestyle="--", linewidth=0.3, color="gray")
    ax.legend(loc="upper right", fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=600)
    plt.close(fig)


def build_combined_plot(
    path: Path,
    theta_deg: np.ndarray,
    f_e: np.ndarray,
    f_h: np.ndarray,
    half_theta_e: float,
    half_theta_h: float,
) -> None:
    fig, ax = plt.subplots(figsize=(20 / 2.54, 12 / 2.54))
    ax.plot(theta_deg, f_e, linewidth=1.0, label=r"$F_E(\theta)$")
    ax.plot(theta_deg, f_h, linewidth=1.0, label=r"$F_H(\theta)$")
    ax.axhline(HALF_POWER_LEVEL, linestyle="--", linewidth=0.7, color="red", label="Рівень 0.707")
    ax.axvline(half_theta_e, linestyle="--", linewidth=0.7, color="green")
    ax.axvline(half_theta_h, linestyle="--", linewidth=0.7, color="orange")
    ax.set_xlabel("θ°", fontsize=10)
    ax.set_ylabel(r"$|F_E(\theta)|, |F_H(\theta)|$", fontsize=10)
    ax.set_xlim(0, 90)
    ax.set_ylim(-0.01, 1.01)
    ax.set_xticks(np.arange(0, 91, 5))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.grid(which="both", linestyle="--", linewidth=0.3, color="gray")
    ax.legend(loc="upper right", fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=600)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    theta = np.arange(0.0, np.pi / 2 + THETA_STEP, THETA_STEP)
    theta_deg = np.degrees(theta)

    f1 = np.abs(huygens_factor(theta))
    fc_e = np.abs(aperture_factor_e(theta))
    fc_h = np.abs(aperture_factor_h(theta))
    f_e = np.abs(f1 * fc_e)
    f_h = np.abs(f1 * fc_h)

    half_theta_e, width_e = find_half_power_width(theta_deg, f_e)
    half_theta_h, width_h = find_half_power_width(theta_deg, f_h)

    minima_e, maxima_e = find_local_extrema(theta_deg, f_e)
    minima_h, maxima_h = find_local_extrema(theta_deg, f_h)

    print(f"Варіант = {VARIANT}")
    print(f"Довжина хвилі λ = {LAMBDA:.3f} м")
    print(f"Розмір розкриву рупора a x b = {A:.3f} x {B:.3f} м")
    print(f"Ширина головної пелюстки в площині E = {width_e:.2f}°")
    print(f"Ширина головної пелюстки в площині H = {width_h:.2f}°")

    build_plot(
        OUTPUT_DIR / "ds_E.png",
        theta_deg,
        f1,
        fc_e,
        f_e,
        half_theta_e,
        HALF_POWER_LEVEL,
        minima_e,
        maxima_e,
        "E",
    )
    build_plot(
        OUTPUT_DIR / "ds_H.png",
        theta_deg,
        f1,
        fc_h,
        f_h,
        half_theta_h,
        HALF_POWER_LEVEL,
        minima_h,
        maxima_h,
        "H",
    )
    build_combined_plot(OUTPUT_DIR / "ds_combined.png", theta_deg, f_e, f_h, half_theta_e, half_theta_h)
    save_csv(OUTPUT_DIR / "ds_normalized.csv", theta_deg, f1, fc_e, fc_h, f_e, f_h)
    save_report(
        OUTPUT_DIR / "lab3_report.md",
        width_h,
        width_e,
        half_theta_h,
        half_theta_e,
        minima_h,
        minima_e,
        maxima_h,
        maxima_e,
    )

    if SHOW_PLOTS:
        plt.show()


if __name__ == "__main__":
    main()
