import json, math, os, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.special import erfc

W = os.path.dirname(os.path.abspath(__file__))
D = W + '/data/'; F = W + '/fig/'
FS, SPS, RS = 1000000, 100, 10000
FSR, SPSR = 100000, 10
T = ['ref', 'suave', 'media', 'fuerte']
NAMES = {'ref': 'Referencia · Δf = 5 kHz (h = 1), sin ruido',
         'suave': 'Suave · Δf = 5 kHz (h = 1), noise_voltage = 0,05',
         'media': 'Media · Δf = 10 kHz (h = 2), noise_voltage = 0,10',
         'fuerte': 'Fuerte · Δf = 20 kHz (h = 4), noise_voltage = 0,20'}
DEV = {'ref': 5, 'suave': 5, 'media': 10, 'fuerte': 20}
COL = {'ref': '#1f5fa8', 'suave': '#2a9d4b', 'media': '#e08a00', 'fuerte': '#c0392b'}
CD = {5: '#2a9d4b', 10: '#e08a00', 20: '#c0392b'}
plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.35, 'figure.dpi': 150})
out = {}


def psd(x, n=16384):
    f, p = signal.welch(x, FS, nperseg=n, return_onesided=False, scaling='density')
    return np.fft.fftshift(f), np.fft.fftshift(p)


def bw99(x):
    f, p = psd(x)
    c = np.cumsum(p) / np.sum(p)
    return (f[np.searchsorted(c, 0.995)] - f[np.searchsorted(c, 0.005)]) / 1e3


# ---------- PSD de las cuatro pruebas ----------
fig, axs = plt.subplots(2, 2, figsize=(10, 6.4), sharey=True)
for ax, tg in zip(axs.flat, T):
    dv = DEV[tg]
    f, p = psd(np.load(f'{D}rx_{tg}.npy')); ft, pt = psd(np.load(f'{D}tx_{tg}.npy'))
    ref = pt.max()
    ax.plot(f / 1e3, 10 * np.log10(p / ref + 1e-12), color=COL[tg], lw=0.9, label='Salida del canal')
    ax.plot(ft / 1e3, 10 * np.log10(pt / ref + 1e-12), color='k', lw=0.7, alpha=0.6, label='Tx sin ruido')
    cb = 2 * (dv + 5)
    for s in (-1, 1):
        ax.axvline(s * cb / 2, ls='--', color='gray', lw=1)
        ax.axvline(s * dv, ls=':', color=COL[tg], lw=1.2)
    ax.set_title(NAMES[tg], fontsize=9.5)
    ax.set_xlim(-60, 60); ax.set_ylim(-80, 5)
    ax.text(0.02, 0.05, f'Carson = {cb} kHz\nBW99 Tx = {bw99(np.load(f"{D}tx_{tg}.npy")):.1f} kHz',
            transform=ax.transAxes, fontsize=8.5, bbox=dict(fc='white', ec='0.7'))
for ax in axs[1]: ax.set_xlabel('Frecuencia [kHz]')
for ax in axs[:, 0]: ax.set_ylabel('PSD relativa [dB]')
axs[0, 0].legend(fontsize=8, loc='upper right')
fig.suptitle('PSD de las cuatro pruebas (punteadas: ±Δf; discontinuas: ±BW Carson/2)', fontsize=10.5)
fig.tight_layout(); fig.savefig(F + 'psd_4df.png'); plt.close(fig)

# ---------- PSD sin ruido: sólo cambia Δf ----------
out['bw99'] = {}
fig, ax = plt.subplots(figsize=(9, 4.2))
for d in (5, 10, 20):
    x = np.load(f'{D}tx_d{d}.npy'); f, p = psd(x)
    out['bw99'][d] = bw99(x)
    ax.plot(f / 1e3, 10 * np.log10(p / p.max() + 1e-12), color=CD[d], lw=1,
            label=f'Δf = {d} kHz (h = {2*d/10:g}) · Carson {2*(d+5)} kHz · BW99 {out["bw99"][d]:.1f} kHz')
    for s in (-1, 1): ax.axvline(s * d, color=CD[d], ls=':', lw=1)
ax.set_xlim(-60, 60); ax.set_ylim(-70, 5)
ax.set_xlabel('Frecuencia [kHz]'); ax.set_ylabel('PSD relativa [dB]'); ax.legend(fontsize=8, loc='lower center')
ax.set_title('PSD Tx sin ruido: al aumentar Δf los dos tonos se separan y el espectro se ensancha', fontsize=10)
fig.tight_layout(); fig.savefig(F + 'psd_df.png'); plt.close(fig)

# ---------- Frecuencia instantánea (discriminador del GRC base a 1 MS/s) ----------
fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
n = 24 * SPS; t = np.arange(n) / FS * 1e3
for ax, tg in zip(axs, T):
    dv = DEV[tg]
    tx = np.load(f'{D}tx_{tg}.npy')[:n + 1]
    fi_tx = np.angle(tx[1:] * np.conj(tx[:-1])) * FS / (2 * np.pi) / 1e3
    dem = np.load(f'{D}demfull_{tg}.npy')[:n] * dv
    ax.plot(t, dem, color=COL[tg], lw=0.6, label='Discriminador Rx (salida del canal)')
    ax.plot(t, fi_tx, 'k', lw=1.2, label='Frecuencia instantánea Tx')
    lim = max(30, 2.5 * dv); ax.set_ylim(-lim, lim); ax.set_ylabel('f [kHz]')
    ax.set_title(NAMES[tg], fontsize=9.5, loc='left')
axs[0].legend(fontsize=8, loc='upper right', ncol=2)
axs[-1].set_xlabel('Tiempo [ms]  (24 símbolos, Ts = 100 µs)')
fig.suptitle('Frecuencia instantánea: los estados se ubican en ±Δf; el ruido aparece como picos del discriminador', fontsize=10.5)
fig.tight_layout(); fig.savefig(F + 'finst_4df.png'); plt.close(fig)

# ---------- Señal temporal I/Q ----------
fig, axs = plt.subplots(4, 1, figsize=(10, 7.5), sharex=True)
n = 6 * SPS; t = np.arange(n) / FS * 1e3
for ax, tg in zip(axs, T):
    x = np.load(f'{D}rx_{tg}.npy')[:n]; tx = np.load(f'{D}tx_{tg}.npy')[:n]
    ax.plot(t, x.real, color=COL[tg], lw=0.9, label='I (canal)')
    ax.plot(t, x.imag, color=COL[tg], lw=0.9, ls='--', alpha=0.7, label='Q (canal)')
    ax.plot(t, tx.real, 'k', lw=0.6, alpha=0.5, label='I (Tx)')
    ax.set_ylim(-1.7, 1.7); ax.set_ylabel('Amplitud')
    ax.set_title(NAMES[tg], fontsize=9.5, loc='left')
axs[0].legend(fontsize=8, ncol=3, loc='upper right')
axs[-1].set_xlabel('Tiempo [ms]  (6 símbolos)')
fig.suptitle('Envolvente compleja I/Q: con mayor Δf la fase gira más ciclos por símbolo (h/2 ciclos)', fontsize=10.5)
fig.tight_layout(); fig.savefig(F + 'iq_4df.png'); plt.close(fig)

# ---------- Cadena del receptor (extensión) ----------
dem = np.load(f'{D}dem_d5_n3.0.npy'); ma = np.load(f'{D}ma_d5_n3.0.npy')
fig, axs = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True)
s0 = 3000; n = 40 * SPSR; t = np.arange(n) / FSR * 1e3
axs[0].plot(t, dem[s0:s0 + n], color='0.55', lw=0.7, label='Discriminador tras filtro de canal (100 kS/s)')
axs[0].plot(t, ma[s0:s0 + n], color=COL['ref'], lw=1.6, label='Integrador de símbolo (media de 10 muestras)')
axs[0].axhline(0, color='k', lw=0.8); axs[0].set_ylim(-3, 3); axs[0].set_ylabel('f / Δf')
axs[0].legend(fontsize=8, loc='upper right')
axs[0].set_title('Δf = 5 kHz con ruido de estrés (noise_voltage = 3, Eb/N0 ≈ 10,5 dB)', fontsize=9.5, loc='left')
bits = np.load(f'{D}bits_media.npy'); ref = np.load(f'{D}ref_media.npy')
k = 3; m = 40; i0 = 1000
tt = np.arange(m) * 1e3 / RS
axs[1].step(tt, ref[i0:i0 + m] + 0.03, where='post', color='k', lw=1.5, label='Bits Tx (PRBS9)')
axs[1].step(tt, bits[i0 + k:i0 + k + m] - 0.03, where='post', color=COL['media'], lw=1.5, ls='--',
            label='Bits Rx (retardo de 3 bits compensado)')
axs[1].set_ylim(-0.3, 1.3); axs[1].set_ylabel('Bit'); axs[1].set_xlabel('Tiempo [ms]')
axs[1].legend(fontsize=8, loc='upper right', ncol=2)
axs[1].set_title('Prueba media: bits recuperados = bits transmitidos (0 errores en ≈19 500 bits)', fontsize=9.5, loc='left')
fig.tight_layout(); fig.savefig(F + 'rx_cadena.png'); plt.close(fig)

# ---------- Ojo ----------
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for ax, tag, tt in [(axs[0], 'media', 'prueba media (Eb/N0 = 40 dB)'), (axs[1], 'd5_n3.0', 'Δf = 5 kHz, ruido de estrés (Eb/N0 ≈ 10,5 dB)')]:
    ma = np.load(f'{D}ma_{tag}.npy'); L = 2 * SPSR
    for j in range(300):
        seg = ma[1000 + j * SPSR: 1000 + j * SPSR + L + 1]
        ax.plot(np.arange(L + 1) / SPSR, seg, color=COL['media'], alpha=0.15, lw=0.8)
    ax.set_title('Ojo a la salida del integrador · ' + tt, fontsize=9)
    ax.set_xlabel('Tiempo [símbolos]'); ax.set_ylim(-2, 2)
axs[0].set_ylabel('f / Δf')
fig.tight_layout(); fig.savefig(F + 'ojo.png'); plt.close(fig)

# ---------- BER ----------
if os.path.exists(D + 'ber_curves.json'):
    cur = json.load(open(D + 'ber_curves.json'))
    eb = np.arange(15)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for d in (5, 10, 20):
        b = np.array(cur[str(d * 1000)]['ber'])
        ax.semilogy(eb, np.where(b > 0, b, np.nan), 'o-', color=CD[d], ms=4,
                    label=f'Δf = {d} kHz (h = {2*d/10:g})')
    x = np.linspace(0, 14, 200); xl = 10 ** (x / 10)
    ax.semilogy(x, 0.5 * np.exp(-xl / 2), 'k--', lw=1, label='Teoría BFSK no coherente: ½·e^(−Eb/2N0)')
    ax.semilogy(x, 0.5 * erfc(np.sqrt(xl / 2)), 'k:', lw=1, label='Teoría BFSK coherente: Q(√(Eb/N0))')
    ax.axhline(1e-3, color='gray', lw=0.8)
    ax.set_ylim(1e-5, 1); ax.set_xlim(0, 14)
    ax.set_xlabel('Eb/N0 [dB]'); ax.set_ylabel('BER')
    ax.set_title('BER vs Eb/N0 con e_EbN0_Sweep + e_BER_Curve (50 000 bits por punto)', fontsize=10)
    ax.legend(fontsize=8, loc='lower left')
    fig.tight_layout(); fig.savefig(F + 'ber.png'); plt.close(fig)
    req = {}
    for d in (5, 10, 20):
        b = np.array(cur[str(d * 1000)]['ber']); lb = np.log10(np.maximum(b, 1e-9))
        i = np.where(lb < -3)[0]
        if len(i):
            i = i[0]; req[d] = float(eb[i - 1] + (-3 - lb[i - 1]) / (lb[i] - lb[i - 1]))
    out['ebn0_1e3'] = req
    out['teo_noncoh_1e3_dB'] = 10 * math.log10(2 * math.log(2 / 2e-3))

# ---------- BW vs Δf ----------
fig, ax = plt.subplots(figsize=(7, 4))
d = np.array([5, 10, 20])
ax.plot(d, 2 * (d + 5), 's-', color='k', label='Carson: 2(Δf + Rb/2)')
ax.plot(d, [out['bw99'][v] for v in d], 'o-', color=CD[10], label='BW 99 % medido (PSD Tx)')
ax.plot(d, 2 * d, '^--', color=CD[5], label='Separación de tonos 2Δf')
ax.set_xlabel('Desviación Δf [kHz]'); ax.set_ylabel('kHz'); ax.legend(fontsize=8.5)
ax.set_title('Ocupación espectral frente a Δf (Rs = 10 kBd fija)', fontsize=10)
fig.tight_layout(); fig.savefig(F + 'bw_vs_df.png'); plt.close(fig)

json.dump(out, open(D + 'plots_out.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
