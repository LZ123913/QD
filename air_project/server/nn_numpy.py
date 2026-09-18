"""
Pure-numpy forward-pass implementations of LSTM, GRU, Conv1d, and additive attention.
Matches PyTorch parameter layout and gate ordering exactly.
"""
import numpy as np


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def _lstm_layer(x, W_ih, W_hh, b_ih, b_hh, h0=None, c0=None):
    """
    x: (seq_len, input_size)
    W_ih: (4*hidden, input_size)
    W_hh: (4*hidden, hidden)
    b_ih, b_hh: (4*hidden,)
    Returns: outputs list of (hidden,), final h, final c
    """
    H = W_hh.shape[1]
    h = np.zeros(H) if h0 is None else h0
    c = np.zeros(H) if c0 is None else c0
    outputs = []
    for t in range(x.shape[0]):
        gates = W_ih @ x[t] + b_ih + W_hh @ h + b_hh
        i, f, g, o = np.split(gates, 4)
        i = _sigmoid(i)
        f = _sigmoid(f)
        g = np.tanh(g)
        o = _sigmoid(o)
        c = f * c + i * g
        h = o * np.tanh(c)
        outputs.append(h.copy())
    return outputs, h, c


def _gru_layer(x, W_ih, W_hh, b_ih, b_hh, h0=None):
    H = W_hh.shape[1]
    h = np.zeros(H) if h0 is None else h0
    outputs = []
    for t in range(x.shape[0]):
        gi = W_ih @ x[t] + b_ih
        gh = W_hh @ h + b_hh
        i_r, i_z, i_n = np.split(gi, 3)
        h_r, h_z, h_n = np.split(gh, 3)
        r = _sigmoid(i_r + h_r)
        z = _sigmoid(i_z + h_z)
        n = np.tanh(i_n + r * h_n)
        h = (1.0 - z) * n + z * h
        outputs.append(h.copy())
    return outputs, h


def _conv1d(x, weight, bias, padding=0):
    """
    x: (in_channels, seq_len)
    weight: (out_channels, in_channels, kernel_size)
    bias: (out_channels,)
    Returns: (out_channels, out_len)
    """
    out_ch, in_ch, k = weight.shape
    seq_len = x.shape[1]
    if padding > 0:
        x = np.pad(x, ((0, 0), (padding, padding)), mode='constant')
        seq_len = x.shape[1]
    out_len = seq_len - k + 1
    out = np.zeros((out_ch, out_len))
    for o in range(out_ch):
        for i in range(out_len):
            out[o, i] = np.sum(weight[o] * x[:, i:i + k]) + bias[o]
    return out


def lstm_forward(x, sd):
    """2-layer LSTM -> fc. x: (seq, feat). Returns (2,)."""
    o1, _, _ = _lstm_layer(
        x, sd['lstm.weight_ih_l0'], sd['lstm.weight_hh_l0'],
        sd['lstm.bias_ih_l0'], sd['lstm.bias_hh_l0'])
    _, h2, _ = _lstm_layer(
        np.array(o1), sd['lstm.weight_ih_l1'], sd['lstm.weight_hh_l1'],
        sd['lstm.bias_ih_l1'], sd['lstm.bias_hh_l1'])
    return sd['fc.weight'] @ h2 + sd['fc.bias']


def gru_forward(x, sd):
    """2-layer GRU -> fc. x: (seq, feat). Returns (2,)."""
    o1, _ = _gru_layer(
        x, sd['gru.weight_ih_l0'], sd['gru.weight_hh_l0'],
        sd['gru.bias_ih_l0'], sd['gru.bias_hh_l0'])
    _, h2 = _gru_layer(
        np.array(o1), sd['gru.weight_ih_l1'], sd['gru.weight_hh_l1'],
        sd['gru.bias_ih_l1'], sd['gru.bias_hh_l1'])
    return sd['fc.weight'] @ h2 + sd['fc.bias']


def cnn_lstm_forward(x, sd):
    """Conv1d -> 2-layer LSTM -> fc. x: (seq, feat). Returns (2,)."""
    # x: (seq_len, 46) -> transpose to (46, seq_len)
    x_t = x.T
    conv_out = _conv1d(x_t, sd['conv1.weight'], sd['conv1.bias'], padding=1)
    conv_out = np.maximum(0, conv_out)  # ReLU
    # conv_out: (64, out_len) -> transpose to (out_len, 64)
    conv_seq = conv_out.T
    o1, _, _ = _lstm_layer(
        conv_seq, sd['lstm.weight_ih_l0'], sd['lstm.weight_hh_l0'],
        sd['lstm.bias_ih_l0'], sd['lstm.bias_hh_l0'])
    _, h2, _ = _lstm_layer(
        np.array(o1), sd['lstm.weight_ih_l1'], sd['lstm.weight_hh_l1'],
        sd['lstm.bias_ih_l1'], sd['lstm.bias_hh_l1'])
    return sd['fc.weight'] @ h2 + sd['fc.bias']


def att_lstm_forward(x, sd):
    """2-layer LSTM -> additive attention -> fc. x: (seq, feat). Returns (2,) and attention weights."""
    o1, _, _ = _lstm_layer(
        x, sd['lstm.weight_ih_l0'], sd['lstm.weight_hh_l0'],
        sd['lstm.bias_ih_l0'], sd['lstm.bias_hh_l0'])
    o2, _, _ = _lstm_layer(
        np.array(o1), sd['lstm.weight_ih_l1'], sd['lstm.weight_hh_l1'],
        sd['lstm.bias_ih_l1'], sd['lstm.bias_hh_l1'])

    H = sd['attn.weight'].shape[0]
    attn_w = sd['attn.weight']
    attn_b = sd['attn.bias']
    v_w = sd['v.weight']

    scores = []
    for h_t in o2:
        s = v_w @ np.tanh(attn_w @ h_t + attn_b)
        scores.append(s[0])
    scores = np.array(scores)
    w = np.exp(scores - np.max(scores))
    w = w / w.sum()

    context = np.zeros(H)
    for t, wt in enumerate(w):
        context += wt * o2[t]

    out = sd['fc.weight'] @ context + sd['fc.bias']
    return out, w


def ablation_forward(x, sd):
    """2-layer LSTM with 128 hidden -> fc. x: (seq, feat). Returns (2,)."""
    o1, _, _ = _lstm_layer(
        x, sd['lstm.weight_ih_l0'], sd['lstm.weight_hh_l0'],
        sd['lstm.bias_ih_l0'], sd['lstm.bias_hh_l0'])
    _, h2, _ = _lstm_layer(
        np.array(o1), sd['lstm.weight_ih_l1'], sd['lstm.weight_hh_l1'],
        sd['lstm.bias_ih_l1'], sd['lstm.bias_hh_l1'])
    return sd['fc.weight'] @ h2 + sd['fc.bias']


MODEL_FORWARD = {
    'baseline_lstm': lstm_forward,
    'baseline_gru': gru_forward,
    'cnn_lstm': cnn_lstm_forward,
    'att_lstm': att_lstm_forward,
    'ablation_noatt_lstm': ablation_forward,
}
