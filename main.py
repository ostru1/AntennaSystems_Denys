
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager


f_mhz = 580
N = 8



c = 3e8
f = f_mhz * 1e6
lam = c / f
k = 2*np.pi / lam

d = lam / 2
beta = -k * d


font_path = r'C:\\Windows\\Fonts\\arial.ttf'
if os.path.exists(font_path):
    font_manager.fontManager.addfont(font_path)
    font_prop = font_manager.FontProperties(fname=font_path)
    font_name = font_prop.get_name()
else:
    font_prop = None
    font_name = 'DejaVu Sans'

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = [font_name]
matplotlib.rcParams['axes.unicode_minus'] = False


th = np.linspace(-90, 90, 20001)
rad = np.deg2rad(th)
psi = k * d * np.cos(rad) + beta
n = np.arange(N)
AF = np.abs(np.sum(np.exp(1j * np.outer(n, psi)), axis=0))
AFn = AF / AF.max()


hp = 0.707
max_idx = np.argmax(AFn)

left_idx = np.where(AFn[:max_idx] <= hp)[0]
if len(left_idx) == 0:
    left_theta = th[0]
else:
    i = left_idx[-1]
    x0, x1 = th[i], th[i+1]
    y0, y1 = AFn[i], AFn[i+1]
    left_theta = x0 + (hp - y0) * (x1 - x0) / (y1 - y0)

right_idx = np.where(AFn[max_idx:] <= hp)[0]
if len(right_idx) == 0:
    right_theta = th[-1]
else:
    i = right_idx[0] + max_idx
    x0, x1 = th[i-1], th[i]
    y0, y1 = AFn[i-1], AFn[i]
    right_theta = x0 + (hp - y0) * (x1 - x0) / (y1 - y0)

hpbw = right_theta - left_theta


mid = AFn[1:-1]
peaks = np.where((mid > AFn[:-2]) & (mid > AFn[2:]))[0] + 1
main_angle = th[max_idx]
mask = np.abs(th[peaks] - main_angle) > (hpbw / 2)
sl_peaks = peaks[mask]
if len(sl_peaks) > 0:
    sll = AFn[sl_peaks].max()
    sll_db = 20 * np.log10(sll)
else:
    sll = None
    sll_db = None

out_dir = os.path.join(os.getcwd(), 'output_lab2')
os.makedirs(out_dir, exist_ok=True)


csv_path = os.path.join(out_dir, 'ds_normalized.csv')
with open(csv_path, 'w', encoding='utf-8-sig') as f:
    f.write('theta_deg,AF_norm\n')
    for t, a in zip(th, AFn):
        f.write(f"{t:.6f},{a:.8f}\n")



def plot_ds(title, filename):
    plt.figure(figsize=(7.5, 4.6), dpi=150)
    plt.plot(th, AFn, color='#1f77b4', lw=1.8, label='|AF|, нормована')
    plt.axhline(hp, color='#d62728', ls='--', lw=1.2, label='Рівень 0.707')
    plt.axvline(left_theta, color='#2ca02c', ls=':', lw=1.2)
    plt.axvline(right_theta, color='#2ca02c', ls=':', lw=1.2)

    if font_prop is not None:
        plt.title(title, fontproperties=font_prop)
        plt.xlabel('Кут, град', fontproperties=font_prop)
        plt.ylabel('Нормована ДС', fontproperties=font_prop)
    else:
        plt.title(title)
        plt.xlabel('Кут, град')
        plt.ylabel('Нормована ДС')

    plt.xlim(-90, 90)
    plt.ylim(0, 1.05)
    plt.grid(True, alpha=0.25)
    plt.legend(loc='upper right', frameon=False, prop=font_prop)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

plot_ds('Нормована ДС у площині E (прийнята модель)', 'ds_E.png')
plot_ds('Нормована ДС у площині H (прийнята модель)', 'ds_H.png')
print('Готово. Файли у папці output_lab2')
