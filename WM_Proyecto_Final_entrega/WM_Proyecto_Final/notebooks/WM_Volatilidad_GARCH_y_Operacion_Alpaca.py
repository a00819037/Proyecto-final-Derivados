# pip install yfinance alpaca-py  (en Colab: !pip install -q yfinance alpaca-py)
import numpy as np, pandas as pd, matplotlib.pyplot as plt, os
from scipy.stats import norm
from scipy.optimize import minimize, brentq
import yfinance as yf
plt.rcParams["figure.figsize"] = (10, 4)

px = yf.download("WM", period="5y", interval="1d", auto_adjust=True, progress=False)
if isinstance(px.columns, pd.MultiIndex):
    px.columns = px.columns.get_level_values(0)
px = px[["Close"]].dropna()
px.index.name = "Date"
os.makedirs("datos", exist_ok=True)
px.to_csv("datos/WM_precios.csv", date_format="%Y-%m-%d")
print(px.shape[0], "días |", px.index.min().date(), "a", px.index.max().date(), "| último cierre:", round(px.Close.iloc[-1], 2))
px.Close.plot(title="WM — precio de cierre ajustado (5 años)"); plt.show()

# Descarga el CSV para subirlo a la carpeta datos/ del repositorio (lo usa el Rmd)
from google.colab import files
files.download("datos/WM_precios.csv")

S = px.Close.values
u = np.diff(S) / S[:-1]
n = len(u)

# Volatilidad histórica clásica
vol_hist = np.std(np.diff(np.log(S)), ddof=1) * np.sqrt(252)

# EWMA
lam = 0.94
v_ewma = np.zeros(n); v_ewma[1] = u[0]**2
for i in range(2, n):
    v_ewma[i] = lam * v_ewma[i-1] + (1 - lam) * u[i-1]**2

# GARCH(1,1) por máxima verosimilitud (misma reparametrización que el Rmd)
def transforma(th):
    e2, e3 = np.exp(th[1]), np.exp(th[2])
    return np.exp(th[0]), e2 / (1 + e2 + e3), e3 / (1 + e2 + e3)

def garch_var(w, a, b):
    v = np.zeros(n); v[1] = u[0]**2
    for i in range(2, n):
        v[i] = w + a * u[i-1]**2 + b * v[i-1]
    return v

def neg_ll(th):
    w, a, b = transforma(th)
    v = garch_var(w, a, b)[1:]
    return np.sum(np.log(v) + u[1:]**2 / v)

th0 = np.array([np.log(np.var(u) * 0.05), np.log(0.08 / 0.03), np.log(0.87 / 0.03)])
opt = minimize(neg_ll, th0, method="Nelder-Mead", options={"maxiter": 20000, "xatol": 1e-10, "fatol": 1e-10})
w, a, b = transforma(opt.x)
VL = w / (1 - a - b)
v_g = garch_var(w, a, b)
V0 = w + a * u[-1]**2 + b * v_g[-1]
a_r = np.log(1 / (a + b))
def vol_T(anios):
    Td = 252 * anios
    return np.sqrt(252 * (VL + (1 - np.exp(-a_r * Td)) / (a_r * Td) * (V0 - VL)))
vol_garch6 = vol_T(6)

res = pd.Series({
    "Vol. histórica": f"{vol_hist:.2%}",
    "EWMA vol. actual": f"{np.sqrt(252 * (lam * v_ewma[-1] + (1 - lam) * u[-1]**2)):.2%}",
    "omega": f"{w:.3e}", "alpha": round(a, 4), "beta": round(b, 4), "alpha+beta": round(a + b, 4),
    "Vol. largo plazo": f"{np.sqrt(252 * VL):.2%}",
    "GARCH vol. actual": f"{np.sqrt(252 * V0):.2%}",
    "Vida media choque (días)": round(np.log(0.5) / np.log(a + b)),
    "GARCH vol. promedio 6 años": f"{vol_garch6:.2%}",
    "Log-verosimilitud": round(-0.5 * opt.fun, 1)})
res

fig, ax = plt.subplots(1, 2, figsize=(13, 4))
fechas = px.index[1:]
ax[0].plot(fechas[1:], np.sqrt(252 * v_g[1:]) * 100, label="GARCH(1,1)", color="#1F3864")
ax[0].plot(fechas[1:], np.sqrt(252 * v_ewma[1:]) * 100, label="EWMA 0.94", color="#2E75B6", alpha=0.7)
ax[0].axhline(np.sqrt(252 * VL) * 100, ls="--", color="#C00000", label="Largo plazo")
ax[0].set_title("Volatilidad condicional de WM (% anual)"); ax[0].legend()
T = np.linspace(0.1, 6, 60)
ax[1].plot(T, vol_T(T) * 100, color="#1F3864", lw=2, label="GARCH ec. 23.13")
ax[1].axhline(22.7453, ls="--", color="#C00000", label="Implícita LSEG strike 290")
ax[1].set_title("Estructura temporal de la volatilidad"); ax[1].set_xlabel("Años"); ax[1].legend()
plt.show()

# pip install arch  (en Colab: !pip install -q arch)
from arch import arch_model
am = arch_model(u * 100, mean="Zero", vol="GARCH", p=1, q=1).fit(disp="off")
print(am.summary().tables[1])

precio = 229.58; rf = (0.049182 + 0.049954) / 2; y_wm = 0.05649; q = 0.0163
s_c = 0.227453; s_w = 0.2104; Tm = 6; F = 1000; monto = 750
K = precio * 1.25; Kw = precio * 1.60; acc_mm = monto / K

def bs_call(S, K, r, s, T, q=0):
    d1 = (np.log(S / K) + (r - q + s**2 / 2) * T) / (s * np.sqrt(T)); d2 = d1 - s * np.sqrt(T)
    return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

def tf_convertible(cup, s=s_c, prima=0.25, N=360, qd=q):
    nn = F / (precio * (1 + prima)); dt = Tm / N
    up = np.exp(s * np.sqrt(dt)); dn = 1 / up; p = (np.exp((rf - qd) * dt) - dn) / (up - dn)
    rc = 2 * np.log(1 + y_wm / 2); dr = np.exp(-rf * dt); dk = np.exp(-rc * dt)
    paso = N // (2 * Tm); cpn = F * cup / 2
    j = np.arange(N + 1); conv = nn * precio * up**(N - j) * dn**j
    V = np.maximum(conv, F + cpn); B = np.where(conv >= F + cpn, 0, F + cpn)
    for i in range(N - 1, -1, -1):
        Bc = dk * (p * B[:-1] + (1 - p) * B[1:])
        Ec = dr * (p * (V[:-1] - B[:-1]) + (1 - p) * (V[1:] - B[1:]))
        if i > 0 and i % paso == 0: Bc = Bc + cpn
        Vc = Bc + Ec; j = np.arange(i + 1); cv = nn * precio * up**(i - j) * dn**j
        conv_ = cv > Vc; V = np.where(conv_, cv, Vc); B = np.where(conv_, 0, Bc)
    return V[0]

cupon = lambda s: brentq(lambda c: tf_convertible(c, s=s) - F, -0.05, 0.10)
tabla = pd.DataFrame({
    "Volatilidad": ["Implícita LSEG (22.75%)", f"GARCH 6 años ({vol_garch6:.2%})", f"Histórica ({vol_hist:.2%})"],
    "Cupón a la par": [f"{cupon(s):.3%}" for s in (s_c, vol_garch6, vol_hist)]})
hedge = bs_call(precio, K, rf, s_c, Tm, q) * acc_mm
warr = bs_call(precio, Kw, rf, s_w, Tm, q) * acc_mm
print(f"Note hedge: ${hedge:,.1f} mm | Warrants: ${warr:,.1f} mm | Costo neto: ${hedge - warr:,.1f} mm ({(hedge - warr) / monto:.1%})")
tabla

from google.colab import userdata
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest, LimitOrderRequest, OptionLegRequest
from alpaca.trading.enums import AssetStatus, ContractType, OrderSide, OrderClass, TimeInForce
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest, OptionSnapshotRequest, StockLatestTradeRequest

API_KEY = userdata.get("ALPACA_API_KEY"); SECRET = userdata.get("ALPACA_SECRET_KEY")
trading = TradingClient(API_KEY, SECRET, paper=True)
opt_data = OptionHistoricalDataClient(API_KEY, SECRET)
stk_data = StockHistoricalDataClient(API_KEY, SECRET)

cuenta = trading.get_account()
print("Cuenta paper:", cuenta.account_number, "| buying power:", cuenta.buying_power,
      "| nivel de opciones aprobado:", getattr(cuenta, "options_approved_level", "n/d"))
S_hoy = stk_data.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols="WM"))["WM"].price
print("Último precio WM:", S_hoy)

# Todas las calls activas de WM (paginando)
contratos, token = [], None
while True:
    req = GetOptionContractsRequest(underlying_symbols=["WM"], status=AssetStatus.ACTIVE,
                                    type=ContractType.CALL, limit=1000, page_token=token)
    r = trading.get_option_contracts(req)
    contratos += r.option_contracts
    token = r.next_page_token
    if not token: break
cad = pd.DataFrame([{"symbol": c.symbol, "vencimiento": pd.to_datetime(c.expiration_date),
                     "strike": float(c.strike_price), "open_interest": c.open_interest} for c in contratos])
venc = cad.vencimiento.max()
leaps = cad[cad.vencimiento == venc].sort_values("strike")
K_conv, K_warr = 1.25 * S_hoy, 1.60 * S_hoy
largo = leaps.iloc[(leaps.strike - K_conv).abs().argmin()]
corto = leaps.iloc[(leaps.strike - K_warr).abs().argmin()]
print(f"Vencimiento más largo: {venc.date()} | strikes disponibles: {leaps.strike.min():.0f}-{leaps.strike.max():.0f}")
print(f"Pierna larga (note hedge): {largo.symbol}  K={largo.strike}  (objetivo {K_conv:.2f})")
print(f"Pierna corta (warrant):    {corto.symbol}  K={corto.strike}  (objetivo {K_warr:.2f})")
if corto.strike < K_warr * 0.95:
    print("Nota: no hay strike listado tan alto como el warrant; se usa el más alto disponible.")

# Cotizaciones, volatilidad implícita y griegas de ambas piernas
snap = opt_data.get_option_snapshot(OptionSnapshotRequest(symbol_or_symbols=[largo.symbol, corto.symbol]))
filas = []
for sym, s in snap.items():
    g = s.greeks
    filas.append({"symbol": sym, "bid": s.latest_quote.bid_price, "ask": s.latest_quote.ask_price,
                  "IV": s.implied_volatility, "delta": g.delta if g else None, "gamma": g.gamma if g else None,
                  "vega": g.vega if g else None, "theta": g.theta if g else None})
piernas = pd.DataFrame(filas).set_index("symbol")
mid = (piernas.bid + piernas.ask) / 2
debito = mid[largo.symbol] - mid[corto.symbol]
print(f"Débito neto del spread (mid): ${debito:.2f} por acción = ${debito * 100:,.0f} por contrato")
print(f"Escala real: {acc_mm * 1e6 / 100:,.0f} contratos ≈ ${debito * acc_mm:,.1f} mm (vs. ${hedge - warr:,.1f} mm a 6 años en el modelo)")
piernas

# Orden multi-pierna (MLEG): compra la call al precio de conversión y vende la call al strike del warrant
CONTRATOS = 1          # escala de demostración en la cuenta paper
legs = [OptionLegRequest(symbol=largo.symbol, ratio_qty=1, side=OrderSide.BUY),
        OptionLegRequest(symbol=corto.symbol, ratio_qty=1, side=OrderSide.SELL)]
orden = LimitOrderRequest(qty=CONTRATOS, order_class=OrderClass.MLEG, time_in_force=TimeInForce.DAY,
                          limit_price=round(float(debito), 2), legs=legs)
enviada = trading.submit_order(orden)
print("Orden enviada:", enviada.id, "| estado:", enviada.status)

# Estado de la orden y posiciones (tomar captura de esta salida y de la pantalla de Alpaca para el anexo)
print(trading.get_order_by_id(enviada.id).status)
pd.DataFrame([{"symbol": p.symbol, "qty": p.qty, "lado": p.side, "costo": p.cost_basis,
               "valor": p.market_value} for p in trading.get_all_positions()])

ST = np.linspace(0.6 * S_hoy, 2.0 * S_hoy, 300)
payoff = np.maximum(ST - largo.strike, 0) - np.maximum(ST - corto.strike, 0) - debito
plt.plot(ST, payoff * 100 * CONTRATOS, color="#1F3864", lw=2)
plt.axhline(0, color="grey", lw=0.8)
for k, c in ((largo.strike, "#2E75B6"), (corto.strike, "#C00000")): plt.axvline(k, ls="--", color=c)
plt.title("Bull call spread sobre WM (USD por contrato)"); plt.xlabel("Precio de WM al vencimiento"); plt.show()
