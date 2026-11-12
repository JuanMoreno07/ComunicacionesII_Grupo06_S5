"""Genera los flujogramas .grc del Grupo 6 (BFSK) para GNU Radio 3.10."""
import yaml, sys, os

OUTDIR = sys.argv[1]
DELAY_SIM = int(sys.argv[3]) if len(sys.argv) > 3 else 3
PRBS = open('/tmp/claude-0/w2/prbs9.txt').read().strip()
EPY = '/tmp/claude-0/w2/epy/'
TEMPLATE = sys.argv[2]  # BER_SDR_INSTRUMENTACION_BASE.grc
tpl = yaml.safe_load(open(TEMPLATE))
TPL_EPY = {b['name']: b for b in tpl['blocks'] if b['id'] == 'epy_block'}

PRBS_REF_SRC = open(EPY + 'e_PRBS_Ref.py').read()


def var(name, value, x, y, comment=''):
    return dict(name=name, id='variable', parameters=dict(comment=comment, value=str(value)),
                states=dict(coordinate=[x, y], rotation=0, state='enabled'))


def rng(name, label, value, start, stop, step, x, y):
    return dict(name=name, id='variable_qtgui_range',
                parameters=dict(label=label, value=str(value), start=str(start), stop=str(stop),
                                step=str(step), rangeType='float', widget='counter_slider',
                                orient='QtCore.Qt.Horizontal', min_len='200', gui_hint=''),
                states=dict(coordinate=[x, y], rotation=0, state='enabled'))


def blk(_n, bid, x, y, **p):
    return dict(name=_n, id=bid, parameters={k: str(v) for k, v in p.items()},
                states=dict(coordinate=[x, y], rotation=0, state='enabled'))


def epy(_n, src, x, y, **p):
    d = blk(_n, "epy_block", x, y, **p)
    d['parameters']['_source_code'] = src
    return d


def time_sink(name, title, n, typ, x, y, srate='samp_rate', ymin=-1.5, ymax=1.5, size=1024, labels=()):
    p = dict(name='"%s"' % title, nconnections=n, type=typ, size=size, srate=srate,
             autoscale='False', ymin=ymin, ymax=ymax, grid='True', update_time='0.10',
             ylabel='Amplitude', entags='True', gui_hint='')
    for i, l in enumerate(labels):
        p['label%d' % (i + 1)] = '"%s"' % l
    return blk(name, 'qtgui_time_sink_x', x, y, **p)


def freq_sink(name, title, n, x, y, bw='samp_rate', fc=0, labels=()):
    p = dict(name='"%s"' % title, nconnections=n, type='complex', fftsize=2048, bw=bw, fc=fc,
             wintype='window.WIN_BLACKMAN_hARRIS', average='0.2', grid='True', ymin=-120, ymax=10,
             units='dB', update_time='0.10', gui_hint='', freqhalf='True')
    for i, l in enumerate(labels):
        p['label%d' % (i + 1)] = '"%s"' % l
    return blk(name, 'qtgui_freq_sink_x', x, y, **p)


def options(fid, title, desc, gen='qt_gui'):
    return dict(parameters=dict(author='Grupo 6 - Juan Pablo Moreno Peña; Juan David Ruiz Higuera',
                                catch_exceptions='True', category='[GRC Hier Blocks]',
                                description=desc, generate_options=gen, id=fid, title=title,
                                output_language='python', placement='(0,0)', run='True',
                                run_command='{python} -u {filename}', run_options='prompt',
                                sizing_mode='fixed', window_size='(1500,900)', max_nouts='0',
                                realtime_scheduling='', qt_qss_theme='', thread_safe_setters='',
                                hier_block_src_path='.:', copyright='', gen_linking='dynamic',
                                gen_cmake='On', cmake_opt=''),
                states=dict(coordinate=[8, 8], rotation=0, state='enabled'))


def layout(blocks, conns):
    names = {b['name'] for b in blocks}
    flow = [b for b in blocks if b['id'] not in ('variable', 'variable_qtgui_range', 'import')]
    vars_ = [b for b in blocks if b not in flow]
    preds = {b['name']: set() for b in flow}
    for a, _, c, _ in conns:
        if c in preds and a in preds:
            preds[c].add(a)
    depth = {}
    def d(n, seen=()):
        if n in depth:
            return depth[n]
        if n in seen:
            return 0
        depth[n] = 0
        depth[n] = max([d(p, seen + (n,)) + 1 for p in preds[n]] or [0])
        return depth[n]
    for n in preds:
        d(n)
    # los visualizadores y sumideros se ubican en la columna de su fuente
    sinks = {b['name'] for b in flow if b['id'].startswith('qtgui') or b['id'] in ('blocks_null_sink', 'blocks_char_to_float')}
    for b in flow:
        n = b['name']
        if n in sinks and preds[n]:
            depth[n] = max(depth[p] for p in preds[n] if p not in sinks) if any(p not in sinks for p in preds[n]) else depth[n]
    order = {n: (1 if n in sinks else 0) for n in depth}
    flow.sort(key=lambda b: order[b['name']])
    # variables en una rejilla superior
    x, y = 220, 8
    for b in vars_:
        b['states']['coordinate'] = [x, y]
        x += 230
        if x > 1900:
            x, y = 220, y + 170
    y0 = y + 200
    cols = {}
    for b in flow:
        cols.setdefault(depth[b['name']], []).append(b)
    WRAP = 7
    band_h = {}
    for k, lst in cols.items():
        h = sum(260 if b['id'].startswith('qtgui') or b['id'] in ('osmosdr_sink', 'osmosdr_source', 'epy_block', 'digital_symbol_sync_xx', 'channels_channel_model') else 150 for b in lst)
        band_h[k // WRAP] = max(band_h.get(k // WRAP, 0), h)
    for k, lst in cols.items():
        band = k // WRAP
        yy = y0 + sum(band_h.get(i, 0) + 60 for i in range(band))
        for b in lst:
            b['states']['coordinate'] = [16 + (k % WRAP) * 270, yy]
            yy += 260 if b['id'].startswith('qtgui') or b['id'] in ('osmosdr_sink', 'osmosdr_source', 'epy_block', 'digital_symbol_sync_xx', 'channels_channel_model') else 150


def save(fname, fid, title, desc, blocks, conns):
    layout(blocks, conns)
    d = dict(options=options(fid, title, desc), blocks=blocks,
             connections=[[a, str(b), c, str(e)] for a, b, c, e in conns],
             metadata=dict(file_format=1, grc_version='3.10.9.2'))
    with open(os.path.join(OUTDIR, fname), 'w') as f:
        yaml.dump(d, f, sort_keys=False, allow_unicode=True, width=1000)


# ---------- variables comunes ----------
def common_vars(dev_default=10000, x0=8, y0=120):
    return [
        blk('import_math', 'import', x0, y0, imports='import math\nfrom gnuradio.filter import firdes'),
        var('samp_rate', '1e6', x0 + 180, y0, 'fs = Rs*SPS = 10000*100 (paquete C, GRC base FSK)'),
        var('sps', 100, x0 + 340, y0),
        var('symbol_rate', 'samp_rate/sps', x0 + 460, y0, 'Rs = 10 kBd (fija; selector guiado S5)'),
        var('Rb', 'symbol_rate', x0 + 640, y0, 'BFSK binaria: Rb = Rs'),
        rng('fsk_deviation', 'Desviación FSK Δf [Hz] (variable del experimento)', dev_default,
            1000, 40000, 1000, x0 + 780, y0),
        var('rx_decim', 10, x0 + 180, y0 + 180, 'decimación del filtro de canal del receptor'),
        var('rx_rate', 'samp_rate/rx_decim', x0 + 340, y0 + 180, '100 kS/s en el receptor'),
        var('sps_rx', 'sps//rx_decim', x0 + 520, y0 + 180, '10 muestras/símbolo en el receptor'),
        var('h_fsk', '2*fsk_deviation/symbol_rate', x0 + 1080, y0, 'índice de modulación'),
        var('carson_bw', '2*(fsk_deviation + Rb/2)', x0 + 1240, y0, 'BW de Carson'),
        var('chan_taps', 'firdes.low_pass(1.0, samp_rate, fsk_deviation + symbol_rate/2, symbol_rate/2)',
            x0 + 1400, y0, 'Filtro de canal Rx: corte = BW Carson / 2'),
        var('prbs9', '[' + PRBS + ']', x0 + 180, y0 + 90, 'PRBS9 (511 bits) conocida por Tx y Rx'),
    ]


def tx_chain(y=330):
    return [
        blk('fuente_prbs9', 'blocks_vector_source_x', 8, y, type='byte', vector='prbs9',
            repeat='True', tags='[]', vlen='1'),
        blk('nrz_mapper', 'digital_chunks_to_symbols_xx', 200, y, in_type='byte', out_type='float',
            symbol_table='[-1.0, 1.0]', dimension='1', num_ports='1'),
        blk('symbol_repeat', 'blocks_repeat', 400, y, type='float', interp='sps', vlen='1'),
        blk('fsk_modulator', 'analog_frequency_modulator_fc', 560, y,
            sensitivity='2*math.pi*fsk_deviation/samp_rate'),
    ], [('fuente_prbs9', 0, 'nrz_mapper', 0), ('nrz_mapper', 0, 'symbol_repeat', 0),
        ('symbol_repeat', 0, 'fsk_modulator', 0)]


def rx_chain(src, y=560, x=200, hw=False):
    b = [
        blk('filtro_canal', 'fir_filter_xxx', x, y, type='ccf', decim='rx_decim', taps='chan_taps',
            samp_delay='0'),
        blk('discriminador_frecuencia', 'analog_quadrature_demod_cf', x + 200, y,
            gain='rx_rate/(2*math.pi*fsk_deviation)'),
        blk('integrador_simbolo', 'blocks_moving_average_xx', x + 420, y, type='float',
            length='sps_rx', scale='1.0/sps_rx', max_iter='4000', vlen='1'),
        blk('sincronizador_simbolo', 'digital_symbol_sync_xx', x + 640, y, type='ff',
            ted_type='digital.TED_GARDNER', constellation='digital.constellation_bpsk().base()',
            sps='sps_rx', ted_gain='1.0', loop_bw='0.005', damping='1.0', max_dev='1.5', osps='1',
            resamp_type='digital.IR_MMSE_8TAP', nfilters='128', pfb_mf_taps='[]'),
        blk('decision_umbral_0', 'digital_binary_slicer_fb', x + 840, y),
    ]
    c = [(src, 0, 'filtro_canal', 0), ('filtro_canal', 0, 'discriminador_frecuencia', 0),
         ('integrador_simbolo', 0, 'sincronizador_simbolo', 0),
         ('sincronizador_simbolo', 0, 'decision_umbral_0', 0)]
    if hw:
        b += [blk('quitar_offset_dc', 'dc_blocker_xx', x + 300, y + 110, type='ff',
                  length='1024', long_form='True'),
              blk('hz_por_unidad', 'blocks_multiply_const_vxx', x + 300, y + 200, type='float',
                  const='fsk_deviation', vlen='1'),
              blk('offset_estimado', 'qtgui_number_sink', x + 500, y + 200, type='float',
                  name='"Offset de frecuencia estimado (media del discriminador)"', avg='0.001',
                  autoscale='False', min='-40000', max='40000', unit1='Hz', factor1='1',
                  graph_type='qtgui.NUM_GRAPH_HORIZ', nconnections='1', update_time='0.20',
                  gui_hint='')]
        c += [('discriminador_frecuencia', 0, 'quitar_offset_dc', 0),
              ('quitar_offset_dc', 0, 'integrador_simbolo', 0),
              ('discriminador_frecuencia', 0, 'hz_por_unidad', 0),
              ('hz_por_unidad', 0, 'offset_estimado', 0)]
    else:
        c += [('discriminador_frecuencia', 0, 'integrador_simbolo', 0)]
    return b, c


def rx_views(y=760, x=200):
    b = [
        time_sink('frecuencia_instantanea', 'Rx: salida del discriminador y del integrador [x Δf]',
                  2, 'float', x, y, srate='rx_rate', labels=('Discriminador', 'Integrado (Ts)')),
        blk('ojo_integrado', 'qtgui_eye_sink_x', x + 300, y, type='float', size='512',
            samp_per_symbol='sps_rx', srate='rx_rate', name='"Diagrama de ojo (salida del integrador)"',
            nconnections='1', autoscale='False', ymin='-1.5', ymax='1.5', grid='True',
            update_time='0.10', ylabel='Amplitude', entags='False', gui_hint=''),
        blk('bits_a_float_rx', 'blocks_char_to_float', x + 600, y, scale='1', vlen='1'),
        blk('bits_a_float_tx', 'blocks_char_to_float', x + 600, y + 80, scale='1', vlen='1'),
        time_sink('bits_tx_vs_rx', 'Bits Tx (referencia) vs bits Rx recuperados', 2, 'float',
                  x + 800, y, srate='symbol_rate', ymin=-0.5, ymax=1.5, size=128,
                  labels=('Bits Rx', 'Bits Tx')),
    ]
    c = [('discriminador_frecuencia', 0, 'frecuencia_instantanea', 0),
         ('integrador_simbolo', 0, 'frecuencia_instantanea', 1),
         ('integrador_simbolo', 0, 'ojo_integrado', 0),
         ('decision_umbral_0', 0, 'bits_a_float_rx', 0),
         ('bits_a_float_rx', 0, 'bits_tx_vs_rx', 0), ('bits_a_float_tx', 0, 'bits_tx_vs_rx', 1)]
    return b, c


# ===== 1. Simulación Tx-canal-Rx (Guía 2 + plan de pruebas) =====
b = common_vars()
b += [rng('noise_voltage', 'Ruido AWGN noise_voltage', 0.1, 0.0, 5.0, 0.05, 8, 210),
      var('delay_bits', 3, 300, 210, 'retardo del receptor en bits (medido)')]
t, c = tx_chain()
b += t
b += [blk('throttle', 'blocks_throttle2', 760, 330, type='complex', samples_per_second='samp_rate',
          vlen='1', ignoretag='True', limit='auto', maximum='0.1'),
      blk('canal_awgn', 'channels_channel_model', 940, 330, noise_voltage='noise_voltage',
          freq_offset='0.0', epsilon='1.0', taps='1.0+0.0j', seed='0', block_tags='False'),
      freq_sink('psd_tx_vs_canal', 'PSD BFSK: Tx vs salida del canal', 2, 1160, 250,
                labels=('Tx', 'Salida canal')),
      time_sink('envolvente_compleja', 'Envolvente compleja: Tx vs salida del canal', 2, 'complex',
                1160, 420, size=2048, labels=('Re Tx', 'Im Tx', 'Re canal', 'Im canal')),
      blk('retardo_ref', 'blocks_delay', 400, 880, type='byte', delay='delay_bits', vlen='1',
          num_ports='1', showports='False')]
c += [('fsk_modulator', 0, 'throttle', 0), ('throttle', 0, 'canal_awgn', 0),
      ('throttle', 0, 'psd_tx_vs_canal', 0), ('canal_awgn', 0, 'psd_tx_vs_canal', 1),
      ('throttle', 0, 'envolvente_compleja', 0), ('canal_awgn', 0, 'envolvente_compleja', 1)]
rb, rc = rx_chain('canal_awgn')
vb, vc = rx_views()
b += rb + vb
c += rc + vc + [('fuente_prbs9', 0, 'retardo_ref', 0), ('retardo_ref', 0, 'bits_a_float_tx', 0)]
save('G6_BFSK_TxRx_Simulacion.grc', 'G6_BFSK_TxRx_Simulacion',
     'Grupo 6 - BFSK Tx-canal AWGN-Rx (simulación)',
     'S5 Telemetría binaria BFSK. Rs=10 kBd, SPS=100, fs=1 MS/s. Variable del experimento: Δf (5/10/20 kHz). '
     'Receptor: filtro de canal (Carson, decima x10) + discriminador + integrador de símbolo + Gardner + umbral 0.',
     b, c)

# ===== 2. Transmisor HackRF (Guía 3) =====
def hw_vars(y=210):
    return [var('fc', '960e6', 8, y, 'frecuencia RF central (la usada en la práctica)'),
            var('lo_off', '200e3', 140, y, 'offset para alejar la señal del pico DC del HackRF'),
            var('radio_rate', '2e6', 280, y, 'tasa del HackRF = samp_rate*2/1'),
            var('interp', 2, 420, y), var('decim', 1, 520, y)]

b = common_vars() + hw_vars()
b += [var('hackrf_tx', '"hackrf=0"', 620, 210),
      rng('tx_amp', 'Amplitud digital Tx (pico < 1)', 0.5, 0.05, 1.0, 0.05, 760, 210),
      rng('tx_vga', 'Tx IF gain HackRF (0-47 dB)', 20, 0, 47, 1, 1000, 210)]
t, c = tx_chain()
b += t
b += [blk('tx_escala', 'blocks_multiply_const_vxx', 760, 330, type='complex', const='tx_amp',
          vlen='1'),
      blk('adaptacion_tasa_tx', 'rational_resampler_xxx', 940, 330, type='ccc', interp='interp',
          decim='decim', taps='[]', fbw='0'),
      blk('tx_desplaza', 'freq_xlating_fir_filter_xxx', 1140, 330, type='ccc', decim='1',
          taps='[1]', center_freq='-lo_off', samp_rate='radio_rate'),
      blk('hackrf_sink', 'osmosdr_sink', 1360, 330, type='fc32', args='hackrf_tx', nchan='1',
          sample_rate='radio_rate', freq0='fc - lo_off', corr0='0', gain0='0', if_gain0='tx_vga',
          bb_gain0='0', ant0='', bw0='0', num_mboards='1', sync='none'),
      freq_sink('psd_tx_bb', 'PSD Tx en banda base (bb_rate)', 1, 760, 460),
      freq_sink('psd_tx_radio', 'PSD entregada al HackRF (radio_rate)', 1, 1140, 460,
                bw='radio_rate', fc='fc'),
      time_sink('tx_iq', 'Envolvente compleja Tx (I/Q)', 1, 'complex', 760, 620, size=2048,
                labels=('I', 'Q')),
      blk('observador_tx', 'analog_quadrature_demod_cf', 560, 620,
          gain='samp_rate/(2*math.pi*fsk_deviation)'),
      time_sink('frec_inst_tx', 'Frecuencia instantánea Tx [x Δf]', 1, 'float', 400, 760, size=2048)]
c += [('fsk_modulator', 0, 'tx_escala', 0), ('tx_escala', 0, 'adaptacion_tasa_tx', 0),
      ('adaptacion_tasa_tx', 0, 'tx_desplaza', 0), ('tx_desplaza', 0, 'hackrf_sink', 0),
      ('tx_escala', 0, 'psd_tx_bb', 0), ('tx_desplaza', 0, 'psd_tx_radio', 0),
      ('tx_escala', 0, 'tx_iq', 0), ('fsk_modulator', 0, 'observador_tx', 0),
      ('observador_tx', 0, 'frec_inst_tx', 0)]
save('G6_BFSK_HackRF_Tx.grc', 'G6_BFSK_HackRF_Tx', 'Grupo 6 - Transmisor BFSK con HackRF One',
     'Transmisor BFSK (PRBS9) -> Rational Resampler 2/1 -> desplazamiento lo_off -> Osmocom Sink.',
     b, c)

# ===== 3. Receptor HackRF (Guía 3) y 4. Receptor + BER (Guía 4) =====
def rx_hw(ber):
    b = common_vars() + hw_vars()
    b += [var('hackrf_rx', '"hackrf=0"', 620, 210),
          rng('rx_lna', 'Rx IF gain / LNA HackRF (0-40 dB, pasos de 8)', 16, 0, 40, 8, 760, 210),
          rng('rx_vga', 'Rx BB gain / VGA HackRF (0-62 dB, pasos de 2)', 20, 0, 62, 2, 1000, 210),
          rng('rx_ppm', 'Corrección de frecuencia Rx [ppm]', 0, -40, 40, 0.5, 1240, 210),
          blk('hackrf_source', 'osmosdr_source', 8, 420, type='fc32', args='hackrf_rx', nchan='1',
              sample_rate='radio_rate', freq0='fc + lo_off', corr0='rx_ppm', dc_offset_mode0='0',
              iq_balance_mode0='0', gain_mode0='False', gain0='0', if_gain0='rx_lna',
              bb_gain0='rx_vga', ant0='', bw0='0', num_mboards='1', sync='none'),
          blk('rx_desplaza', 'freq_xlating_fir_filter_xxx', 200, 420, type='ccc', decim='1',
              taps='firdes.low_pass(1.0, radio_rate, 150e3, 50e3)', center_freq='-lo_off',
              samp_rate='radio_rate'),
          blk('adaptacion_tasa_rx', 'rational_resampler_xxx', 420, 420, type='ccc', interp='decim',
              decim='interp', taps='[]', fbw='0'),
          freq_sink('psd_rx_radio', 'Rx: espectro tras el desplazamiento (radio_rate)', 1, 420, 300,
                    bw='radio_rate', fc='fc'),
          freq_sink('psd_rx_bb', 'Rx: PSD en banda base (bb_rate)', 1, 640, 300),
          time_sink('rx_iq', 'Rx: envolvente compleja (bb_rate)', 1, 'complex', 640, 420, size=2048,
                    ymin=-2, ymax=2, labels=('I', 'Q'))]
    c = [('hackrf_source', 0, 'rx_desplaza', 0), ('rx_desplaza', 0, 'adaptacion_tasa_rx', 0),
         ('rx_desplaza', 0, 'psd_rx_radio', 0)]
    src = 'adaptacion_tasa_rx'
    if ber:
        b += [var('EbN0_min', '0.0', 8, 1000), var('EbN0_max', '14.0', 120, 1000),
              var('EbN0_step', '1.0', 240, 1000),
              var('N_EbN0', 'int(round((EbN0_max-EbN0_min)/EbN0_step))+1', 360, 1000),
              var('bb_rate', 'samp_rate', 560, 1000), var('bits_por_punto', 50000, 680, 1000),
              var('bits_guardia', 1000, 820, 1000), var('delay_bits', 0, 940, 1000,
                  'e_PRBS_Ref ya entrega la referencia alineada'),
              var('update_every', 1000, 1060, 1000)]
        sw = dict(TPL_EPY['e_EbN0_Sweep'])
        sw = blk('e_EbN0_Sweep', 'epy_block', 420, 560, EbN0_min='EbN0_min', EbN0_max='EbN0_max',
                 EbN0_step='EbN0_step', samp_rate='bb_rate', bit_rate='Rb',
                 bits_por_punto='bits_por_punto', bits_guardia='bits_guardia', signal_power='0.0',
                 seed='2026')
        sw['parameters']['_source_code'] = TPL_EPY['e_EbN0_Sweep']['parameters']['_source_code']
        bc = blk('e_BER_Curve', 'epy_block', 1100, 860, EbN0_min='EbN0_min', EbN0_max='EbN0_max',
                 EbN0_step='EbN0_step', bits_por_punto='bits_por_punto',
                 bits_guardia='bits_guardia', delay_bits='delay_bits', update_every='update_every')
        bc['parameters']['_source_code'] = TPL_EPY['e_BER_Curve']['parameters']['_source_code']
        csv = blk('e_BER_CSV', 'epy_block', 1360, 960, EbN0_min='EbN0_min', EbN0_max='EbN0_max',
                  EbN0_step='EbN0_step', nombre_archivo='"curva_BER.csv"', guardar_cada='2.0')
        csv['parameters']['_source_code'] = TPL_EPY['e_BER_CSV']['parameters']['_source_code']
        ref = epy('e_PRBS_Ref', PRBS_REF_SRC, 1100, 760, ventana='1022', umbral_relock='0.40')
        vs = blk('curva_ber', 'qtgui_vector_sink_f', 1360, 860, vlen='N_EbN0',
                 name='"Curva BER experimental vs Eb/N0 - Grupo 6 BFSK"', x_axis_label='"Eb/N0 [dB]"',
                 y_axis_label='"log10(BER)"', x_start='EbN0_min', x_step='EbN0_step',
                 x_units='"dB"', y_units='""', ymin='-7', ymax='0', grid='True', autoscale='False',
                 average='1.0', nconnections='1', ref_level='0', showports='False',
                 update_time='0.2', gui_hint='')
        nul = blk('null_ebn0', 'blocks_null_sink', 640, 660, type='float', vlen='1',
                  num_inputs='1', bus_structure_sink='[[0,],]')
        b += [sw, bc, csv, ref, vs, nul]
        c += [('adaptacion_tasa_rx', 0, 'e_EbN0_Sweep', 0), ('e_EbN0_Sweep', 1, 'null_ebn0', 0),
              ('decision_umbral_0', 0, 'e_PRBS_Ref', 0), ('e_PRBS_Ref', 0, 'e_BER_Curve', 0),
              ('e_PRBS_Ref', 1, 'e_BER_Curve', 1), ('e_BER_Curve', 1, 'curva_ber', 0),
              ('e_BER_Curve', 0, 'e_BER_CSV', 0), ('e_BER_Curve', 1, 'e_BER_CSV', 1),
              ('e_PRBS_Ref', 0, 'bits_a_float_tx', 0)]
        src = 'e_EbN0_Sweep'
    else:
        ref = epy('e_PRBS_Ref', PRBS_REF_SRC, 1100, 760, ventana='1022', umbral_relock='0.40')
        nul = blk('null_bits', 'blocks_null_sink', 1300, 760, type='byte', vlen='1',
                  num_inputs='1', bus_structure_sink='[[0,],]')
        b += [ref, nul]
        c += [('decision_umbral_0', 0, 'e_PRBS_Ref', 0), ('e_PRBS_Ref', 0, 'bits_a_float_tx', 0),
              ('e_PRBS_Ref', 1, 'null_bits', 0)]
    c += [(src, 0, 'psd_rx_bb', 0), (src, 0, 'rx_iq', 0)]
    rb, rc = rx_chain(src, y=760 if ber else 560, x=200, hw=True)
    vb, vc = rx_views(y=960 if ber else 760)
    return b + rb + vb, c + rc + vc


b, c = rx_hw(False)
save('G6_BFSK_HackRF_Rx.grc', 'G6_BFSK_HackRF_Rx', 'Grupo 6 - Receptor BFSK con HackRF One',
     'Osmocom Source -> desplazamiento -> Rational Resampler 1/2 -> receptor BFSK del grupo.', b, c)
b, c = rx_hw(True)
save('G6_BFSK_HackRF_Rx_BER.grc', 'G6_BFSK_HackRF_Rx_BER',
     'Grupo 6 - Receptor BFSK HackRF + medición BER vs Eb/N0',
     'Receptor BFSK con e_EbN0_Sweep tras la adaptación de tasa y e_BER_Curve/e_BER_CSV (Guía 4).',
     b, c)

# ===== 5. Curva BER en simulación (canal ideal en lugar del SDR) =====
b = common_vars() + [var('EbN0_min', '0.0', 8, 1000), var('EbN0_max', '14.0', 120, 1000),
                     var('EbN0_step', '1.0', 240, 1000),
                     var('N_EbN0', 'int(round((EbN0_max-EbN0_min)/EbN0_step))+1', 360, 1000),
                     var('bb_rate', 'samp_rate', 560, 1000), var('bits_por_punto', 50000, 680, 1000),
                     var('bits_guardia', 1000, 820, 1000), var('delay_bits', 0, 940, 1000,
                         'e_PRBS_Ref entrega la referencia ya alineada (retardo fijo medido = 3 bits)'),
                     var('update_every', 1000, 1060, 1000)]
t, c = tx_chain()
b += t
sw = blk('e_EbN0_Sweep', 'epy_block', 760, 330, EbN0_min='EbN0_min', EbN0_max='EbN0_max',
         EbN0_step='EbN0_step', samp_rate='bb_rate', bit_rate='Rb',
         bits_por_punto='bits_por_punto', bits_guardia='bits_guardia', signal_power='0.0',
         seed='2026')
sw['parameters']['_source_code'] = TPL_EPY['e_EbN0_Sweep']['parameters']['_source_code']
bc = blk('e_BER_Curve', 'epy_block', 1100, 760, EbN0_min='EbN0_min', EbN0_max='EbN0_max',
         EbN0_step='EbN0_step', bits_por_punto='bits_por_punto', bits_guardia='bits_guardia',
         delay_bits='delay_bits', update_every='update_every')
bc['parameters']['_source_code'] = TPL_EPY['e_BER_Curve']['parameters']['_source_code']
csv = blk('e_BER_CSV', 'epy_block', 1360, 860, EbN0_min='EbN0_min', EbN0_max='EbN0_max',
          EbN0_step='EbN0_step', nombre_archivo='"curva_BER.csv"', guardar_cada='2.0')
csv['parameters']['_source_code'] = TPL_EPY['e_BER_CSV']['parameters']['_source_code']
vs = blk('curva_ber', 'qtgui_vector_sink_f', 1360, 760, vlen='N_EbN0',
         name='"Curva BER vs Eb/N0 - Grupo 6 BFSK (simulación)"', x_axis_label='"Eb/N0 [dB]"',
         y_axis_label='"log10(BER)"', x_start='EbN0_min', x_step='EbN0_step', x_units='"dB"',
         y_units='""', ymin='-7', ymax='0', grid='True', autoscale='False', average='1.0',
         nconnections='1', ref_level='0', showports='False', update_time='0.2', gui_hint='')
nul = blk('null_ebn0', 'blocks_null_sink', 1000, 420, type='float', vlen='1', num_inputs='1',
          bus_structure_sink='[[0,],]')
ret = epy('e_PRBS_Ref', PRBS_REF_SRC, 1100, 900, ventana='1022', umbral_relock='0.40')
b += [sw, bc, csv, vs, nul, ret]
c += [('fsk_modulator', 0, 'e_EbN0_Sweep', 0), ('e_EbN0_Sweep', 1, 'null_ebn0', 0),
      ('decision_umbral_0', 0, 'e_PRBS_Ref', 0), ('e_PRBS_Ref', 0, 'e_BER_Curve', 0),
      ('e_PRBS_Ref', 1, 'e_BER_Curve', 1),
      ('e_BER_Curve', 1, 'curva_ber', 0), ('e_BER_Curve', 0, 'e_BER_CSV', 0),
      ('e_BER_Curve', 1, 'e_BER_CSV', 1), ('e_PRBS_Ref', 0, 'bits_a_float_tx', 0)]
rb, rc = rx_chain('e_EbN0_Sweep')
vb, vc = rx_views()
b += rb + vb
c += rc + vc
save('G6_BFSK_BER_Simulacion.grc', 'G6_BFSK_BER_Simulacion',
     'Grupo 6 - Curva BER vs Eb/N0 BFSK (simulación)',
     'Mismo Tx/Rx del grupo; el SDR se reemplaza por una conexión directa y e_EbN0_Sweep agrega el AWGN.',
     b, c)
print('ok')

# ===== 0. Copia del GRC base del selector (Modulacion_FSK_AWGN.grc) con los valores del plan =====
base = yaml.safe_load(open(os.path.join(os.path.dirname(TEMPLATE), '..', '..', 'GUIA_2', 'Modulacion_FSK_AWGN.grc'))
                      if os.path.exists(os.path.join(os.path.dirname(TEMPLATE), '..', '..', 'GUIA_2', 'Modulacion_FSK_AWGN.grc'))
                      else open(sys.argv[4]))
for bl in base['blocks']:
    if bl['name'] == 'fsk_deviation':
        bl['parameters'].update(value='10000', start='1000', stop='40000', step='1000',
                                label='Desviación FSK Δf (Hz) · ref/suave 5k · media 10k · fuerte 20k')
    if bl['name'] == 'noise_voltage':
        bl['parameters'].update(value='0.1', label='noise_voltage · ref 0 · suave 0.05 · media 0.10 · fuerte 0.20')
ys = max(bl['states']['coordinate'][1] for bl in base['blocks'] if bl['id'] == 'variable') if any(
    bl['id'] == 'variable' for bl in base['blocks']) else 8
base['blocks'] += [
    var('Rb', 'symbol_rate', 1000, 8, 'Rb = Rs'),
    var('h_fsk', '2*fsk_deviation/symbol_rate', 1180, 8, 'h = 2Δf/Rs'),
    var('carson_bw', '2*(fsk_deviation + Rb/2)', 1360, 8, 'BW Carson'),
    var('EbN0_dB', '10*math.log10(samp_rate/(Rb*noise_voltage**2)) if noise_voltage > 0 else 99',
        1560, 8, 'Eb/N0 del canal'),
]
if not any(bl['id'] == 'import' and 'math' in bl['parameters'].get('imports', '') for bl in base['blocks']):
    base['blocks'].append(blk('import_math', 'import', 1760, 8, imports='import math'))
base['options']['parameters'].update(
    id='G6_Modulacion_FSK_AWGN_S5', title='Grupo 6 - S5 BFSK: plan de pruebas sobre Modulacion_FSK_AWGN.grc',
    author='Grupo 6 - Juan Pablo Moreno Peña; Juan David Ruiz Higuera',
    description='Copia del GRC base del selector. Sólo se modifican fsk_deviation y noise_voltage '
                '(Rs = 10 kBd, SPS = 100, fs = 1 MS/s fijos).')
with open(os.path.join(OUTDIR, 'G6_Modulacion_FSK_AWGN_S5.grc'), 'w') as f:
    yaml.dump(base, f, sort_keys=False, allow_unicode=True, width=1000)
print('ok base')
# distribución de la ventana para ver las tres gráficas a la vez
for bl in base['blocks']:
    hints = {'spectrum_compare': '0,0,1,2', 'freq_inst_compare': '1,0,1,1', 'rx_time': '1,1,1,1'}
    if bl['name'] in hints:
        bl['parameters']['gui_hint'] = hints[bl['name']]
base['options']['parameters']['window_size'] = '(1500,950)'
with open(os.path.join(OUTDIR, 'G6_Modulacion_FSK_AWGN_S5.grc'), 'w') as f:
    yaml.dump(base, f, sort_keys=False, allow_unicode=True, width=1000)
