"""Simulación headless del enlace BFSK del Grupo 6 (decisión corregida, Guía 4 · S5).
Parámetros fijos del escenario: Rs = 10 kBd, SPS = 100, fs = 1 MS/s (GRC base Modulacion_FSK_AWGN.grc).
Variable autorizada: Δf (con el noise_voltage que el selector asocia a cada nivel).
El receptor del grupo (extensión) decima x10 en el filtro de canal: 100 kS/s y 10 muestras/símbolo."""
import sys, json, math, os
import numpy as np
from gnuradio import gr, blocks, analog, digital, channels, filter
from gnuradio.filter import firdes
W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W + '/epy')

FS, SPS = 1000000.0, 100
RS = FS / SPS
RXD = 10                 # decimación del filtro de canal del receptor
FSR, SPSR = FS / RXD, SPS // RXD
PRBS = [int(x) for x in open(W + '/prbs9.txt').read().split(',')]
OUT = W + '/data'

# plan de pruebas del selector guiado (Guía 4, S5)
TESTS = {
    'ref':    dict(dev=5000.0,  noise=0.00, nombre='Referencia', uso='Captura base (sin ruido)'),
    'suave':  dict(dev=5000.0,  noise=0.05, nombre='Suave', uso='Primera degradación'),
    'media':  dict(dev=10000.0, noise=0.10, nombre='Media', uso='Prueba principal'),
    'fuerte': dict(dev=20000.0, noise=0.20, nombre='Fuerte', uso='Prueba de estrés'),
}


class Link(gr.top_block):
    def __init__(self, dev, noise, nbits, sweep=None):
        gr.top_block.__init__(self)
        self.src = blocks.vector_source_b(PRBS, True)
        self.head = blocks.head(gr.sizeof_char, nbits)
        self.nrz = digital.chunks_to_symbols_bf([-1.0, 1.0], 1)
        self.rep = blocks.repeat(gr.sizeof_float, SPS)
        self.mod = analog.frequency_modulator_fc(2 * math.pi * dev / FS)
        self.ch = channels.channel_model(noise_voltage=noise, frequency_offset=0.0,
                                         epsilon=1.0, taps=[1.0 + 0j], noise_seed=0,
                                         block_tags=False)
        self.dem_full = analog.quadrature_demod_cf(FS / (2 * math.pi * dev))  # como el GRC base
        self.taps = firdes.low_pass(1.0, FS, dev + RS / 2, RS / 2)
        self.lpf = filter.fir_filter_ccf(RXD, self.taps)
        self.dem = analog.quadrature_demod_cf(FSR / (2 * math.pi * dev))
        self.ma = blocks.moving_average_ff(SPSR, 1.0 / SPSR, 4000, 1)
        self.k1 = digital.symbol_sync_ff(digital.TED_GARDNER, SPSR, 0.005, 1.0, 1.0, 1.5, 1,
                                         digital.constellation_bpsk().base(),
                                         digital.IR_MMSE_8TAP, 128, [])
        self.sl = digital.binary_slicer_fb()
        self.s_tx = blocks.vector_sink_c(); self.s_rx = blocks.vector_sink_c()
        self.s_demfull = blocks.vector_sink_f()
        self.s_dem = blocks.vector_sink_f(); self.s_ma = blocks.vector_sink_f()
        self.s_soft = blocks.vector_sink_f(); self.s_bits = blocks.vector_sink_b()
        self.s_ref = blocks.vector_sink_b()
        self.connect(self.src, self.head, self.nrz, self.rep, self.mod, self.ch)
        self.connect(self.head, self.s_ref)
        self.connect(self.mod, self.s_tx)
        last = self.ch
        if sweep is not None:
            self.connect(self.ch, sweep)
            self.connect((sweep, 1), blocks.null_sink(gr.sizeof_float))
            last = sweep
        else:
            self.connect(last, self.s_rx)
            self.connect(last, self.dem_full, self.s_demfull)
        self.connect(last, self.lpf, self.dem, self.ma, self.k1, self.sl, self.s_bits)
        if sweep is None:
            self.connect(self.dem, self.s_dem); self.connect(self.ma, self.s_ma)
            self.connect(self.k1, self.s_soft)


def align(ref, rx, maxd=40, skip=500):
    best = None
    for k in range(maxd):
        n = min(len(ref), len(rx) - k)
        e = np.mean(ref[skip:n - 20] != rx[skip + k:k + n - 20])
        if best is None or e < best[1]:
            best = (k, e)
    return best


def _shim():
    gr.sync_decimator = gr.decim_block


def ber_sweep(dev, bits_por_punto=50000, bits_guardia=1000, csv=None):
    _shim()
    import e_EbN0_Sweep, e_BER_Curve, e_PRBS_Ref
    sw = e_EbN0_Sweep.blk(0.0, 14.0, 1.0, FS, RS, bits_por_punto, bits_guardia, 0.0, 2026)
    bc = e_BER_Curve.blk(0.0, 14.0, 1.0, bits_por_punto, bits_guardia, 0, 1000)
    pr = e_PRBS_Ref.blk(1022, 0.40)
    nb = 15 * (bits_por_punto + bits_guardia) + 3000
    tb = Link(dev, 0.0, nb, sweep=sw)
    tb.connect(tb.sl, pr)
    tb.connect((pr, 0), (bc, 0)); tb.connect((pr, 1), (bc, 1))
    vb = blocks.vector_sink_f(15); vl = blocks.vector_sink_f(15)
    tb.connect((bc, 0), vb); tb.connect((bc, 1), vl)
    tb.run()
    ber = np.array(vb.data()).reshape(-1, 15)[-1]
    lb = np.array(vl.data()).reshape(-1, 15)[-1]
    if csv:
        with open(csv, 'w') as f:
            f.write('EbN0_dB,BER,log10_BER\n')
            for i in range(15):
                f.write(f'{float(i):.6f},{ber[i]:.12e},{lb[i]:.12e}\n')
    return ber, lb, bc.count.copy(), bc.errors.copy(), pr.relocks


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'tests'
    if mode == 'tests':
        res = {}
        runs = dict(TESTS)
        # barrido limpio de Δf para medir el BW (aísla la variable del experimento)
        for d in (5, 10, 20):
            runs[f'd{d}'] = dict(dev=d * 1000.0, noise=0.0)
        for tag, t in runs.items():
            tb = Link(t['dev'], t['noise'], 20000); tb.run()
            ref = np.array(tb.s_ref.data()); rx = np.array(tb.s_bits.data())
            k, e = align(ref, rx)
            sig = t['noise']
            res[tag] = dict(dev=t['dev'], noise=sig, delay_bits=int(k), ber=float(e),
                            nbits=int(len(rx) - 520),
                            EbN0_dB=(None if sig == 0 else 10 * math.log10(FS / (RS * sig ** 2))))
            np.save(f'{OUT}/tx_{tag}.npy', np.array(tb.s_tx.data())[:400000])
            np.save(f'{OUT}/rx_{tag}.npy', np.array(tb.s_rx.data())[:400000])
            np.save(f'{OUT}/demfull_{tag}.npy', np.array(tb.s_demfull.data())[:20000])
            np.save(f'{OUT}/dem_{tag}.npy', np.array(tb.s_dem.data())[:20000])
            np.save(f'{OUT}/ma_{tag}.npy', np.array(tb.s_ma.data())[:20000])
            np.save(f'{OUT}/soft_{tag}.npy', np.array(tb.s_soft.data())[:3000])
            np.save(f'{OUT}/bits_{tag}.npy', rx[:3000]); np.save(f'{OUT}/ref_{tag}.npy', ref[:3000])
            print(tag, res[tag], flush=True)
        # estrés adicional (extensión): ruido alto para ver dónde aparecen errores
        for d in (5, 10, 20):
            for sig in (2.0, 3.0, 4.0):
                tb = Link(d * 1000.0, sig, 20000); tb.run()
                k, e = align(np.array(tb.s_ref.data()), np.array(tb.s_bits.data()))
                res[f'd{d}_n{sig}'] = dict(dev=d * 1000.0, noise=sig, ber=float(e), delay_bits=int(k),
                                          EbN0_dB=10 * math.log10(FS / (RS * sig ** 2)))
                print(d, sig, e, flush=True)
                if d == 5 and sig == 3.0:
                    np.save(f'{OUT}/dem_d5_n3.0.npy', np.array(tb.s_dem.data())[:20000])
                    np.save(f'{OUT}/ma_d5_n3.0.npy', np.array(tb.s_ma.data())[:20000])
        json.dump(res, open(f'{OUT}/resultados.json', 'w'), indent=1)
    else:
        cur = {}
        for d in (5, 10, 20):
            b, lb, cnt, err, rl = ber_sweep(d * 1000.0, csv=f'{OUT}/curva_BER_df{d}k.csv')
            cur[str(d * 1000)] = dict(ber=[float(x) for x in b], count=[int(x) for x in cnt],
                                     errors=[int(x) for x in err], relocks=int(rl))
            print(d, b, rl, flush=True)
        json.dump(cur, open(f'{OUT}/ber_curves.json', 'w'), indent=1)
