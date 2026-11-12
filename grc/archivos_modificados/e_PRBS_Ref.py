"""
e_PRBS_Ref (Grupo 6)
Referencia de bits Tx alineada con los bits recuperados.

El transmisor envía en bucle una PRBS9 conocida (511 bits). Este bloque:
1) busca, sobre los primeros 'ventana' bits recibidos, la fase de la PRBS9 que
   más coincide (equivale a ajustar delay_bits automáticamente);
2) vigila la tasa de error en bloques de 511 bits; si supera 'umbral_relock'
   (p. ej. por un deslizamiento de bit del sincronizador de símbolo con
   Eb/N0 bajo), vuelve a buscar la fase.

Entrada 0: bits recuperados por el receptor (byte 0/1).
Salida 0 : bits de referencia Tx alineados (byte 0/1)  -> e_BER_Curve entrada 0.
Salida 1 : los mismos bits recuperados                  -> e_BER_Curve entrada 1.
"""
import numpy as np
from gnuradio import gr


def prbs9():
    s = [1] * 9
    out = []
    for _ in range(511):
        b = s[8] ^ s[4]
        out.append(s[8])
        s = [b] + s[:8]
    return np.array(out, dtype=np.int8)


class blk(gr.sync_block):
    def __init__(self, ventana=1022, umbral_relock=0.40):
        gr.sync_block.__init__(self, name='e_PRBS_Ref',
                               in_sig=[np.int8], out_sig=[np.int8, np.int8])
        self.seq = prbs9()
        self.L = len(self.seq)
        self.ventana = max(self.L, int(ventana))
        self.umbral = float(umbral_relock)
        # matriz con las 511 rotaciones de la PRBS9 para buscar la fase rápido
        self.rot = np.array([np.roll(self.seq, -k) for k in range(self.L)], dtype=np.int8)
        self.hist = np.zeros(0, dtype=np.int8)
        self.fase = None      # fase de la PRBS9 que corresponde al bit n = 0
        self.n = 0
        self.err_blk = 0
        self.cnt_blk = 0
        self.relocks = 0

    def _buscar(self, rx, n0):
        """rx: últimos bits recibidos; n0: índice absoluto del primer bit de rx."""
        L = self.L
        m = len(rx) // L * L
        r = rx[:m].reshape(-1, L)
        coinc = np.zeros(L)
        for fila in r:
            coinc += (self.rot == fila).sum(axis=1)
        k = int(np.argmax(coinc))
        self.fase = (k - n0) % L
        return 100.0 * coinc[k] / m

    def work(self, input_items, output_items):
        x = np.asarray(input_items[0], dtype=np.int8) & 1
        n = len(x)
        out_ref = output_items[0]
        if self.fase is None:
            self.hist = np.concatenate([self.hist, x])
            if len(self.hist) >= self.ventana:
                p = self._buscar(self.hist[:self.ventana], self.n - (len(self.hist) - n))
                print('[e_PRBS_Ref] enganche inicial: fase=%d, coincidencia=%.1f %%' % (self.fase, p))
                self.hist = np.zeros(0, dtype=np.int8)
        if self.fase is None:
            out_ref[:n] = x  # todavía sin referencia
        else:
            ref = self.seq[(self.fase + self.n + np.arange(n)) % self.L]
            out_ref[:n] = ref
            self.err_blk += int(np.sum(ref != x))
            self.cnt_blk += n
            self.hist = np.concatenate([self.hist, x])[-2 * self.L:]
            if self.cnt_blk >= self.L:
                if self.err_blk > self.umbral * self.cnt_blk and len(self.hist) >= self.L:
                    h = self.hist[-self.L:]
                    p = self._buscar(h, self.n + n - self.L)
                    self.relocks += 1
                    print('[e_PRBS_Ref] reenganche #%d: fase=%d, coincidencia=%.1f %%'
                          % (self.relocks, self.fase, p))
                self.err_blk = 0
                self.cnt_blk = 0
        output_items[1][:n] = x
        self.n += n
        return n
