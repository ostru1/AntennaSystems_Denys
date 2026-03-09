import math
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy

F1E = [1]
FC = [1]
FE = [1]
steps = [0]
SGP1 = 0
SGP2 = 0
fS1 = 0
fS2 = 0
Zeros = []

max_x_FC = []
max_y_FC = []
max_x_FE = []
max_y_FE = []

min_x_FC = []
min_y_FC = []
min_x_FE = []
min_y_FE = []

N = 8
F = 580 * 10 ** 6
lambd = 299792458 / F
print("λ = " + str(lambd) + "(m)")
d = 0.25 * lambd
print("dcp = " + str(d) + "(m)")
k = (2 * numpy.pi) / lambd
print("k = " + str(k) + "(rad/m)")

output_dir = Path("output_lab2")
output_dir.mkdir(parents=True, exist_ok=True)
show_plots = os.getenv("SHOW_PLOTS", "0") == "1"


for teta in numpy.arange(0.01, numpy.pi / 2, 0.00001):
    mn1 = abs((numpy.cos(numpy.pi/2 * numpy.sin(teta))/numpy.cos(teta)))
    mn2 = abs(numpy.sin((N * k * d * (1 - numpy.cos(teta)) / 2)) / (N * numpy.sin((k * d * (1 - numpy.cos(teta))) / 2)))
    mn3 = mn1 * mn2

    F1E += [mn1]
    FC += [mn2]
    FE += [mn3]

    if 0.707 < mn2 < 0.708:
        SGP1 = 2 * math.degrees(teta)
        fS1 = mn2

    if 0.707 < mn3 < 0.708:
        SGP2 = 2 * math.degrees(teta)
        fS2 = mn3

    steps += [math.degrees(teta)]


for i in range(1, len(FC) - 1):
    if FC[i] > FC[i - 1] and FC[i] > FC[i + 1]:
        max_x_FC.append(steps[i])
        max_y_FC.append(FC[i])
    if FE[i] > FE[i - 1] and FE[i] > FE[i + 1]:
        max_x_FE.append(steps[i])
        max_y_FE.append(FE[i])


for i in range(1, len(FC) - 1):
    if FC[i] < FC[i - 1] and FC[i] < FC[i + 1]:
        min_x_FC.append(steps[i])
        min_y_FC.append(FC[i])
    if FE[i] < FE[i - 1] and FE[i] < FE[i + 1]:
        min_x_FE.append(steps[i])
        min_y_FE.append(FE[i])


print("Ширина головної пелюстки в площині H = " + str(round(SGP1, 2)) + '\u00b0')
print("Ширина головної пелюстки в площині E = " + str(round(SGP2, 2)) + '\u00b0')




len_value = [len(max_x_FC), len(max_x_FE), len(min_x_FC), len(min_x_FE)]
print("Табл. 1 - Аналіз ДС Директорної антени в площині Н та Е")
print("-----------------------------------------")
print("| № |θminH|θminE|θmaxH|FH(θ)|θmaxE|FE(θ)|")
for i in range(0, max(len_value)):
    v1 = f" {i + 1:.0f}"
    if len(v1) < len(str(max(len_value))) + 2:
        v1 += " "
    v2 = f"{min_x_FC[i]:.2f}" if i < len_value[3] else '  -  '
    if len(v2) < 5:
        v2 += "0"
    v3 = f"{min_x_FE[i]:.2f}" if i < len_value[2] else '  -  '
    if len(v3) < 5:
        v3 += "0"
    v4 = f"{max_x_FC[i]:.2f}" if i < len_value[0] else '  -  '
    if len(v4) < 5:
        v4 += "0"
    h4 = f"{max_y_FC[i]:.3f}" if i < len_value[0] else '  -  '
    if len(h4) < 5:
        h4 += "0"
    v5 = f"{max_x_FE[i]:.2f}" if i < len_value[1] else '  -  '
    if len(v5) < 5:
        v5 += "0"
    h5 = f"{max_y_FE[i]:.3f}" if i < len_value[1] else '  -  '
    if len(h5) < 5:
        h5 += "0"
    print(f"|{v1}|{v2}|{v3}|{v4}|{h4}|{v5}|{h5}|")
print("-----------------------------------------")




fig, ax = plt.subplots(figsize=(20/2.54, 12/2.54))
ax.plot(steps, F1E, linewidth=0.7, label="$ F_{1e}(θ) $")
ax.plot(steps, FC, linewidth=0.7, label="$ F_{H}(θ) $")
ax.plot(steps, FE, linewidth=0.7, label="$ F_{E}(θ) $")
ax.plot(SGP1/2, fS1, 'ro', markersize=4, label="ШГП в площині H")
ax.plot(SGP2/2, fS2, 'go', markersize=4, label="ШГП в площині E")

plt.annotate(f'({fS1:.3f}, {SGP1/2:.2f}\u00b0)',
                 xy=(SGP1 / 2, fS1),
                 xytext=((SGP1/2)+3, fS1+0.05),
                 arrowprops=dict(arrowstyle='->', color='black'), fontsize=6)

plt.annotate(f'({fS2:.3f}, {SGP2/2:.2f}\u00b0)',
                 xy=(SGP2 / 2, fS2),
                 xytext=((SGP2/2)-13, fS2+0.05),
                 arrowprops=dict(arrowstyle='->', color='black'), fontsize=6)

ax.plot([0, SGP1/2], [fS2, fS2], 'r--', linewidth=0.5)
ax.plot([SGP2/2, SGP2/2], [0, fS2], 'r--', linewidth=0.5)
ax.plot([SGP1/2, SGP1/2], [0, fS1], 'r--', linewidth=0.5)

ax.plot(max_x_FC, max_y_FC, "o", markersize=4, color="black", label="$ \\theta_{max} $ FH")
ax.plot(max_x_FE, max_y_FE, "o", markersize=4, color="grey", label="$ \\theta_{max} $ FE")

ax.plot(min_x_FC, min_y_FC, "o", markersize=4, color="blue", label="$ \\theta_{min} $ FH та FE")
# ax.plot(min_x_FE, min_y_FE, "o", markersize=4, color="blue", label="$ \\theta_{min} $ FE")

ax.set_xlabel('θ' + '\u00b0', fontsize=10)
ax.set_ylabel('|Fh(θ' + '\u00b0' + ')|, |Fe(θ' + '\u00b0' + ')|, |F1e(θ' + '\u00b0' + ')|', fontsize=10)
plt.xticks(numpy.arange(0, 100, 2), fontsize=7)
plt.yticks(numpy.arange(0, 1.2, 0.1), fontsize=7)
plt.ylim(-0.01, 1.01)
plt.xlim(0, 90.5)



plt.legend(loc="upper right", fontsize=7)
plt.grid(which='both', linestyle='--', linewidth=0.2, color='gray')

fig.savefig(output_dir / "ds_combined.png", dpi=600)


fig_h, ax_h = plt.subplots(figsize=(20/2.54, 12/2.54))
ax_h.plot(steps, FC, linewidth=0.7, label="$ F_{H}(\\theta) $")
ax_h.plot(SGP1/2, fS1, 'ro', markersize=4, label="ШГП в площині H")
ax_h.set_xlabel('θ' + '\u00b0', fontsize=10)
ax_h.set_ylabel('|Fh(θ)|', fontsize=10)
ax_h.set_xticks(numpy.arange(0, 100, 2))
ax_h.set_yticks(numpy.arange(0, 1.2, 0.1))
ax_h.set_ylim(-0.01, 1.01)
ax_h.set_xlim(0, 90.5)
ax_h.legend(loc="upper right", fontsize=7)
ax_h.grid(which='both', linestyle='--', linewidth=0.2, color='gray')
fig_h.savefig(output_dir / "ds_H.png", dpi=600)
plt.close(fig_h)

fig_e, ax_e = plt.subplots(figsize=(20/2.54, 12/2.54))
ax_e.plot(steps, FE, linewidth=0.7, label="$ F_{E}(\\theta) $")
ax_e.plot(SGP2/2, fS2, 'go', markersize=4, label="ШГП в площині E")
ax_e.set_xlabel('θ' + '\u00b0', fontsize=10)
ax_e.set_ylabel('|Fe(θ)|', fontsize=10)
ax_e.set_xticks(numpy.arange(0, 100, 2))
ax_e.set_yticks(numpy.arange(0, 1.2, 0.1))
ax_e.set_ylim(-0.01, 1.01)
ax_e.set_xlim(0, 90.5)
ax_e.legend(loc="upper right", fontsize=7)
ax_e.grid(which='both', linestyle='--', linewidth=0.2, color='gray')
fig_e.savefig(output_dir / "ds_E.png", dpi=600)
plt.close(fig_e)


data_path = output_dir / "ds_normalized.csv"
with data_path.open("w", encoding="utf-8") as f:
    f.write("theta_deg,F1E,FH,FE\n")
    for i in range(len(steps)):
        f.write(f"{steps[i]:.5f},{F1E[i]:.6f},{FC[i]:.6f},{FE[i]:.6f}\n")


def side_lobe_level(max_list):
    if len(max_list) < 2:
        return None
    sorted_vals = sorted(max_list, reverse=True)
    return sorted_vals[1]

side_h = side_lobe_level(max_y_FC)
side_e = side_lobe_level(max_y_FE)
side_h_db = 20 * math.log10(side_h) if side_h and side_h > 0 else None
side_e_db = 20 * math.log10(side_e) if side_e and side_e > 0 else None

report_path = output_dir / "lab2_report.md"
with report_path.open("w", encoding="utf-8") as f:
    f.write("# Лабораторна робота 2\n")
    f.write("## Вхідні дані\n")
    f.write("- Варіант: 9\n")
    f.write(f"- Частота f: {F / 10**6:.0f} МГц\n")
    f.write(f"- Число елементів N: {N}\n\n")
    f.write("## Розрахункові параметри\n")
    f.write(f"- Довжина хвилі λ: {lambd:.6f} м\n")
    f.write(f"- Крок елементів d: {d:.6f} м\n")
    f.write(f"- Хвильове число k: {k:.6f} рад/м\n\n")
    f.write("## Показники ДС\n")
    f.write(f"- Ширина головної пелюстки (площина H, рівень 0.707): {SGP1:.2f}°\n")
    f.write(f"- Ширина головної пелюстки (площина E, рівень 0.707): {SGP2:.2f}°\n")
    if side_h is None:
        f.write("- Рівень бокових пелюсток (H): н/д\n")
    else:
        f.write(f"- Рівень бокових пелюсток (H): {side_h:.3f} ({side_h_db:.2f} дБ)\n")
    if side_e is None:
        f.write("- Рівень бокових пелюсток (E): н/д\n")
    else:
        f.write(f"- Рівень бокових пелюсток (E): {side_e:.3f} ({side_e_db:.2f} дБ)\n")

if show_plots:
    plt.show()
