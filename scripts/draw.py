import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Polygon, FancyArrowPatch, Arc
F = '/tmp/claude-0/w2/fig/'
plt.rcParams.update({'font.size': 9, 'figure.dpi': 170})

# ================= Escenario contextual =================
fig, ax = plt.subplots(figsize=(11, 6.2))
ax.set_xlim(0, 110); ax.set_ylim(0, 62); ax.set_aspect('equal'); ax.axis('off')
# edificio: sala de bombas/tanques (izq) y sala de control (der)
ax.add_patch(Rectangle((2, 4), 66, 50, fc='#f3f1ea', ec='#5d5d5d', lw=2))
ax.add_patch(Rectangle((70, 4), 36, 50, fc='#eef3f7', ec='#5d5d5d', lw=2))
ax.add_patch(Rectangle((68, 4), 2, 50, fc='#9c9c9c', ec='#5d5d5d'))  # muro
ax.add_patch(Rectangle((68, 24), 2, 9, fc='#c8a46b', ec='#5d5d5d'))  # puerta
ax.text(35, 56, 'Sala de tanques y bombas (planta de tratamiento de agua)', ha='center', fontsize=10, weight='bold')
ax.text(88, 56, 'Sala de control / supervisión', ha='center', fontsize=10, weight='bold')
ax.add_patch(Rectangle((0, 0), 110, 4, fc='#d9d9d9', ec='none')); ax.text(55, 1.6, 'Piso', ha='center', fontsize=7, color='0.4')
# tanques
for x, h, lab in [(6, 30, 'Tanque 1'), (20, 26, 'Tanque 2')]:
    ax.add_patch(FancyBboxPatch((x, 4), 11, h, boxstyle='round,pad=0,rounding_size=2', fc='#b7cde3', ec='#33526e', lw=1.5))
    ax.add_patch(Rectangle((x, 4), 11, h * 0.6, fc='#7ea6cc', ec='none', alpha=0.8))
    ax.text(x + 5.5, 4 + h * 0.6 + 2.5, lab, ha='center', fontsize=8)
# bombas / motores (fuente de ruido)
for x in (36, 46):
    ax.add_patch(Rectangle((x, 4), 7, 6, fc='#8a8f99', ec='k')); ax.add_patch(Circle((x + 3.5, 12), 3, fc='#a7adb8', ec='k'))
ax.text(44.5, 17, 'Bombas y variadores\n(ruido de banda ancha)', ha='center', fontsize=7.5, color='#8a2d2d')
for r in (5, 7, 9):
    ax.add_patch(Arc((44.5, 11), r * 2, r * 1.4, theta1=20, theta2=160, ec='#c0392b', ls=':', lw=1))
# tuberías
ax.plot([17, 20], [10, 10], color='#33526e', lw=3); ax.plot([31, 36], [8, 8], color='#33526e', lw=3); ax.plot([43, 46], [8, 8], color='#33526e', lw=3)
# estantería / gabinete
ax.add_patch(Rectangle((55, 4), 10, 22, fc='#d8c7a3', ec='k'))
for y in (9, 14, 19): ax.plot([55, 65], [y, y], 'k', lw=0.8)
ax.text(60, 27.5, 'Estantería', ha='center', fontsize=7.5)
# Tx: nodo de telemetría sobre tanque 1
ax.add_patch(Rectangle((8.5, 34.5), 6, 4, fc='#2a9d4b', ec='k')); ax.plot([11.5, 11.5], [38.5, 44], 'k', lw=1.6)
ax.add_patch(Polygon([[10.3, 44], [12.7, 44], [11.5, 46.5]], fc='k'))
ax.text(11.5, 31.2, 'Tx\nHackRF One\n(nodo nivel/estado)', ha='center', fontsize=7.5, color='#1d6e35', weight='bold', va='top')
# Rx: estación en sala de control
ax.add_patch(Rectangle((80, 4), 22, 12, fc='#c9b18a', ec='k'))  # mesa
ax.add_patch(Rectangle((84, 16), 9, 7, fc='#30343b', ec='k')); ax.add_patch(Rectangle((85, 17), 7, 5, fc='#79c3ff', ec='none'))
ax.add_patch(Rectangle((94.5, 16), 5, 3, fc='#1f5fa8', ec='k')); ax.plot([97, 97], [19, 25], 'k', lw=1.6)
ax.add_patch(Polygon([[95.8, 25], [98.2, 25], [97, 27.5]], fc='k'))
ax.text(97, 29, 'Rx\nHackRF One + PC\n(GNU Radio)', ha='center', fontsize=7.5, color='#1f5fa8', weight='bold')
ax.add_patch(Rectangle((73, 4), 5, 20, fc='#555', ec='k')); ax.text(75.5, 25.5, 'Rack', ha='center', fontsize=7.5)
# ondas: camino directo + reflejado
ax.add_patch(FancyArrowPatch((13, 45), (95.5, 26.5), arrowstyle='-|>', mutation_scale=14, color='#1f5fa8', lw=1.8))
ax.text(52, 38.8, 'camino directo', color='#1f5fa8', fontsize=8, rotation=-12)
ax.add_patch(FancyArrowPatch((13, 45), (60, 26), arrowstyle='-', color='#7f7f7f', lw=1.2, ls='--'))
ax.add_patch(FancyArrowPatch((60, 26), (95.5, 26.5), arrowstyle='-|>', mutation_scale=12, color='#7f7f7f', lw=1.2, ls='--'))
ax.text(40, 27.5, 'reflexión (estantería)', color='#555', fontsize=7)
for r in (3, 5, 7):
    ax.add_patch(Arc((11.5, 46), r * 2, r * 2, theta1=-40, theta2=40, ec='#1f5fa8', lw=1))
# recuadro técnico
ax.add_patch(FancyBboxPatch((20, 46.5), 46, 7.8, boxstyle='round,pad=0.4', fc='white', ec='#1f5fa8'))
ax.text(21, 52.8, 'BFSK: bit 1 → fc + Δf     bit 0 → fc − Δf', fontsize=8.2, weight='bold')
ax.text(21, 50.3, 'fc = 960 MHz · Rs = Rb = 10 kb/s · Δf = 5 / 10 / 20 kHz (h = 1 / 2 / 4)', fontsize=8)
ax.text(21, 47.8, 'Canal: AWGN (noise_voltage 0 / 0,05 / 0,10 / 0,20)', fontsize=8)
# leyenda
ax.add_patch(Rectangle((71, 34), 34, 17, fc='white', ec='0.6'))
ax.text(72, 49, 'Leyenda', weight='bold', fontsize=8)
items = [('#2a9d4b', 'Tx: transmisor de telemetría'), ('#1f5fa8', 'Rx: receptor / supervisión'),
         ('#1f5fa8', '→ trayectoria directa'), ('#7f7f7f', '- - trayectoria reflejada'), ('#c0392b', '··· fuente de ruido (AWGN)')]
for i, (c, t) in enumerate(items):
    ax.text(72.5, 46 - i * 2.6, t, color=c, fontsize=7.5)
ax.text(108, 0.5, 'Figura elaborada por el Grupo 6 con Python/matplotlib', ha='right', fontsize=6, color='0.5')
fig.tight_layout(); fig.savefig(F + 'escenario.png'); plt.close(fig)

# ================= Diagrama técnico =================
fig = plt.figure(figsize=(11, 6.4))
ax = fig.add_axes([0, 0.36, 1, 0.64]); ax.set_xlim(0, 110); ax.set_ylim(0, 40); ax.axis('off')
def box(x, y, w, h, t, c='#e8f0fb', ec='#1f5fa8'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3', fc=c, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=7.6)
def arr(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=11, color='k', lw=1))
ax.text(1, 37.5, 'TRANSMISOR (G6_BFSK_HackRF_Tx.grc)', weight='bold', color='#1d6e35', fontsize=9)
tx = [('Fuente PRBS9\n(511 bits)', 1), ('Chunks to\nSymbols\n0→−1, 1→+1', 15), ('Repeat\n× SPS = 100', 29),
      ('Frequency\nMod\nk = 2πΔf/fs', 43), ('× tx_amp\n(0,5)', 57), ('Rational\nResampler\n2/1', 71), ('Xlating\n+lo_off', 85), ('Osmocom\nSink\nfc − lo_off', 97)]
for t, x in tx:
    box(x, 27, 11 if x < 97 else 11.5, 8, t, c='#e6f4ea', ec='#2a9d4b')
for (a, xa), (b, xb) in zip(tx[:-1], tx[1:]):
    arr(xa + 11.3, 31, xb - 0.3, 31)
ax.text(29, 24.8, 'fs = Rs·SPS = 10k·100 = 1 MS/s', fontsize=7.5, color='#1d6e35')
ax.text(73, 24.8, 'radio_rate = 1 MS/s·2 = 2 MS/s', fontsize=7.5, color='#1d6e35')
ax.text(55, 21.2, 'CANAL: aire (antenas) + ruido · en simulación: Channel Model AWGN / e_EbN0_Sweep', ha='center', fontsize=8, color='#8a2d2d', weight='bold')
ax.add_patch(FancyArrowPatch((102.5, 26.5), (102.5, 16.5), arrowstyle='-|>', mutation_scale=11, color='#8a2d2d', lw=1.4, ls='--'))
ax.text(1, 18, 'RECEPTOR (G6_BFSK_HackRF_Rx.grc)', weight='bold', color='#1f5fa8', fontsize=9)
rx = [('Osmocom\nSource\nfc + lo_off', 97), ('Xlating −lo_off\n+ LPF 150 kHz', 85), ('Rational\nResampler\n1/2', 71),
      ('FIR canal\nLPF Δf+Rs/2\ndecima ×10', 57), ('Quadrature\nDemod\n(discriminador)', 43), ('DC Blocker\n+ Moving Avg\n10 muestras (Ts)', 29),
      ('Symbol Sync\nGardner\n1 muestra/símb.', 15), ('Binary Slicer\numbral 0\n→ bits', 1)]
for t, x in rx:
    box(x, 5, 11 if x < 97 else 11.5, 9, t)
for (a, xa), (b, xb) in zip(rx[:-1], rx[1:]):
    arr(xa - 0.3, 9.5, xb + 11.3, 9.5)
ax.text(6.5, 1.5, '→ e_PRBS_Ref + e_BER_Curve (Guía 4)', fontsize=7.5, color='#1f5fa8')
# parámetros
ax2 = fig.add_axes([0.03, 0.03, 0.40, 0.30]); ax2.axis('off')
rows = [['Modulación', 'BFSK (CPFSK, 2 estados)'], ['Rs', '10 kBd (fija)'], ['Rb = Rs·log2(2)', '10 kb/s'], ['SPS', '100'],
        ['fs (samp_rate)', 'Rs·SPS = 1 MS/s'], ['Δf (variable)', '5 / 10 / 20 kHz'], ['h = 2Δf/Rs', '1 / 2 / 4'],
        ['BW Carson 2(Δf+Rb/2)', '20 / 30 / 50 kHz'], ['GRC base', 'Modulacion_FSK_AWGN.grc']]
tb = ax2.table(cellText=rows, colLabels=['Parámetro', 'Valor'], loc='center', cellLoc='left', colWidths=[0.45, 0.55])
tb.auto_set_font_size(False); tb.set_fontsize(7.5); tb.scale(1, 1.25)
# dos estados de frecuencia
ax3 = fig.add_axes([0.52, 0.06, 0.45, 0.25])
f = np.linspace(-40, 40, 600)
for c, s, lab in [('#c0392b', -10, 'bit 0: −Δf'), ('#2a9d4b', 10, 'bit 1: +Δf')]:
    ax3.plot(f, np.sinc((f - s) / 10) ** 2, color=c, label=lab)
    ax3.axvline(s, color=c, ls=':')
ax3.annotate('', xy=(10, 1.08), xytext=(-10, 1.08), arrowprops=dict(arrowstyle='<->'))
ax3.text(0, 1.12, '2Δf', ha='center', fontsize=8)
ax3.set_xlabel('Frecuencia respecto a fc [kHz]', fontsize=8); ax3.set_yticks([]); ax3.set_ylim(0, 1.25)
ax3.set_title('Representación de los dos estados (prueba media, Δf = 10 kHz)', fontsize=8.5); ax3.legend(fontsize=7, loc='upper right')
ax3.tick_params(labelsize=7)
fig.savefig(F + 'diagrama_tecnico.png'); plt.close(fig)
print('ok')
