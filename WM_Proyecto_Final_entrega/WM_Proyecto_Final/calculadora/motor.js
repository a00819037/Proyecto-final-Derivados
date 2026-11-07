// Motor de valuación (mismo método que WM_Proyecto_Final.Rmd)
const N01 = x => { // CDF normal estándar (Abramowitz-Stegun 7.1.26 vía erf)
  const t = 1 / (1 + 0.3275911 * Math.abs(x) / Math.SQRT2);
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x / 2);
  return x >= 0 ? 0.5 * (1 + y) : 0.5 * (1 - y);
};
const n01 = x => Math.exp(-x * x / 2) / Math.sqrt(2 * Math.PI);

function bsCall(S, K, r, s, T, q) {
  const d1 = (Math.log(S / K) + (r - q + s * s / 2) * T) / (s * Math.sqrt(T)), d2 = d1 - s * Math.sqrt(T);
  return {
    precio: S * Math.exp(-q * T) * N01(d1) - K * Math.exp(-r * T) * N01(d2),
    delta: Math.exp(-q * T) * N01(d1),
    gamma: Math.exp(-q * T) * n01(d1) / (S * s * Math.sqrt(T)),
    vega: S * Math.exp(-q * T) * n01(d1) * Math.sqrt(T) / 100
  };
}
function valorBono(cup, y, T, F = 1000, m = 2) {
  let v = 0; const n = Math.round(T * m);
  for (let t = 1; t <= n; t++) v += (F * cup / m + (t === n ? F : 0)) / Math.pow(1 + y / m, t);
  return v;
}
function biseccion(f, a, b, tol = 1e-10) {
  let fa = f(a), fb = f(b);
  if (fa * fb > 0) return NaN;
  for (let i = 0; i < 200; i++) {
    const c = (a + b) / 2, fc = f(c);
    if (Math.abs(fc) < tol || (b - a) / 2 < tol) return c;
    if (fa * fc < 0) { b = c; fb = fc; } else { a = c; fa = fc; }
  }
  return (a + b) / 2;
}
// Convertible completo: Tsiveriotis-Fernandes en árbol CRR
function tfConvertible(cup, p) {
  const { S, primaConv, s, q, N, T, r, y, F = 1000 } = p;
  const nn = F / (S * (1 + primaConv)), dt = T / N;
  const u = Math.exp(s * Math.sqrt(dt)), d = 1 / u, pr = (Math.exp((r - q) * dt) - d) / (u - d);
  const rc = 2 * Math.log(1 + y / 2), dr = Math.exp(-r * dt), dk = Math.exp(-rc * dt);
  const paso = N / (2 * T), cpn = F * cup / 2;
  let V = new Float64Array(N + 1), B = new Float64Array(N + 1);
  for (let j = 0; j <= N; j++) {
    const conv = nn * S * Math.pow(u, N - j) * Math.pow(d, j);
    V[j] = Math.max(conv, F + cpn); B[j] = conv >= F + cpn ? 0 : F + cpn;
  }
  for (let i = N - 1; i >= 0; i--) {
    for (let j = 0; j <= i; j++) {
      let Bc = dk * (pr * B[j] + (1 - pr) * B[j + 1]);
      const Ec = dr * (pr * (V[j] - B[j]) + (1 - pr) * (V[j + 1] - B[j + 1]));
      if (i > 0 && Math.abs(i % paso) < 1e-9) Bc += cpn;
      const Vc = Bc + Ec, cv = nn * S * Math.pow(u, i - j) * Math.pow(d, j);
      if (cv > Vc) { V[j] = cv; B[j] = 0; } else { V[j] = Vc; B[j] = Bc; }
    }
  }
  return V[0];
}
function calcular(p) {
  const K = p.S * (1 + p.primaConv), Kw = p.S * (1 + p.primaWarr), n = 1000 / K, accMM = p.monto / K;
  const c = bsCall(p.S, K, p.r, p.s, p.T, p.q), w = bsCall(p.S, Kw, p.r, p.sw, p.T, p.q);
  const opcionBono = c.precio * n;
  const cuponBS = biseccion(cc => valorBono(cc, p.y, p.T) - (1000 - opcionBono), -0.05, 0.15);
  const cuponTF = biseccion(cc => tfConvertible(cc, p) - 1000, -0.03, 0.15, 1e-8);
  const hedge = c.precio * accMM, warr = w.precio * accMM, neto = hedge - warr;
  return {
    K, Kw, n, accMM, call: c.precio, warrant: w.precio, opcionBono, bonoRecto: 1000 - opcionBono, cuponBS, cuponTF,
    hedge, warr, neto, netoPct: neto / p.monto,
    delta: (c.delta - w.delta) * accMM, gamma: (c.gamma - w.gamma) * accMM, vega: (c.vega - w.vega) * accMM,
    ahorroPb: (p.y - cuponTF) * 1e4
  };
}
if (typeof module !== "undefined") module.exports = { calcular, bsCall, tfConvertible, valorBono };
