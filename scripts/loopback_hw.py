"""Prueba en lazo (sin radio) de la cadena Tx/Rx de hardware del Grupo 6:
resampler 2/1, desplazamientos lo_off, offset de frecuencia y ruido."""
import sys, math, numpy as np
sys.path.insert(0, '/tmp/claude-0/w2/epy')
from gnuradio import gr, blocks, analog, digital, filter
from gnuradio.filter import firdes
import e_PRBS_Ref
FS, SPS, RS = 1000000, 100, 10000
RXD = 10; FSR = FS / RXD; SPSR = SPS // RXD
RR, LO = 2e6, 200e3
PRBS = [int(x) for x in open('/tmp/claude-0/w2/prbs9.txt').read().split(',')]

def test(dev, foff, noise, nbits=20000, dc=True):
    tb = gr.top_block()
    src = blocks.vector_source_b(PRBS, True); hd = blocks.head(1, nbits)
    nrz = digital.chunks_to_symbols_bf([-1.0, 1.0], 1); rep = blocks.repeat(4, SPS)
    mod = analog.frequency_modulator_fc(2*math.pi*dev/FS); amp = blocks.multiply_const_cc(0.5)
    rs_tx = filter.rational_resampler_ccc(2, 1)
    xl_tx = filter.freq_xlating_fir_filter_ccc(1, [1], -LO, RR)
    # canal "radio": Tx sintonizado en fc-LO, Rx en fc+LO -> desplazamiento -2LO, + offset
    lo = analog.sig_source_c(RR, analog.GR_COS_WAVE, -2*LO + foff, 1.0)
    mix = blocks.multiply_cc(); nz = analog.noise_source_c(analog.GR_GAUSSIAN, noise, 1); add = blocks.add_cc()
    xl_rx = filter.freq_xlating_fir_filter_ccc(1, firdes.low_pass(1.0, RR, 150e3, 50e3), -LO, RR)
    rs_rx = filter.rational_resampler_ccc(1, 2)
    lpf = filter.fir_filter_ccf(RXD, firdes.low_pass(1.0, FS, dev + RS/2, RS/2))
    dem = analog.quadrature_demod_cf(FSR/(2*math.pi*dev))
    dcb = filter.dc_blocker_ff(1024, True)
    ma = blocks.moving_average_ff(SPSR, 1.0/SPSR, 4000, 1)
    sy = digital.symbol_sync_ff(digital.TED_GARDNER, SPSR, 0.005, 1.0, 1.0, 1.5, 1,
                                digital.constellation_bpsk().base(), digital.IR_MMSE_8TAP, 128, [])
    sl = digital.binary_slicer_fb(); pr = e_PRBS_Ref.blk(1022, 0.40)
    s_ref = blocks.vector_sink_b(); s_rx = blocks.vector_sink_b(); s_dem = blocks.vector_sink_f()
    tb.connect(src, hd, nrz, rep, mod, amp, rs_tx, xl_tx, (mix, 0)); tb.connect(lo, (mix, 1))
    tb.connect(mix, (add, 0)); tb.connect(nz, (add, 1)); tb.connect(add, xl_rx, rs_rx, lpf, dem)
    if dc: tb.connect(dem, dcb, ma)
    else: tb.connect(dem, ma)
    tb.connect(ma, sy, sl, pr); tb.connect((pr, 0), s_ref); tb.connect((pr, 1), s_rx); tb.connect(dem, s_dem)
    tb.run()
    ref = np.array(s_ref.data()); rx = np.array(s_rx.data()); d = np.array(s_dem.data())
    sk = 4000
    return float(np.mean(ref[sk:] != rx[sk:])), float(np.mean(d[sk*SPSR:])*dev), pr.relocks

if __name__ == '__main__':
    import io, contextlib
    for dev in [5000, 10000, 20000]:
        for foff in [0, 2000, 5000, 10000]:
            for dc in [False, True]:
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    r = test(dev, foff, 0.02, dc=dc)
                print(dev, foff, 'dc_blocker' if dc else 'sin_dc', 'BER=%.4g offset_est=%.0f Hz relocks=%d' % r)
