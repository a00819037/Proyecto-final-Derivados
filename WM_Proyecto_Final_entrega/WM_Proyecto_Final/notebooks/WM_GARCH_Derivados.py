# ---- Instalación de paquetes (solo si faltan) ----
import subprocess, sys

def _pip(*pkgs):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *pkgs])

for _mod, _pkg in [("yfinance", "yfinance"), ("arch", "arch"), ("statsmodels", "statsmodels")]:
    try:
        __import__(_mod)
    except ImportError:
        try:
            _pip(_pkg)
        except Exception as e:
            print(f"No se pudo instalar {_pkg}:", e)

# ---- Librerías y configuración ----
import os, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize, brentq
from scipy.signal import lfilter
from scipy.stats import norm, chi2

# Acciones: WM (emisor) y Republic Services (par del sector, para la correlación)
TICKERS = ["WM", "RSG"]
PRINCIPAL = "WM"
YEARS = 5                       # años de historia
R_FREE = (0.049182 + 0.049954) / 2   # Treasury 6 años interpolado (LSEG US5YT=RR y US7YT=RR)
Y_WM = 0.05649                  # YTM de WM a 6 años (LSEG Issuer Curve)
DIV_YIELD = {"WM": 0.0163, "RSG": 0.0114}   # LSEG Overview
HORIZON_DAYS = 126              # pronóstico corto del precio: ~6 meses
N_SIM = 5000                    # trayectorias de Monte Carlo
LAMBDA_EWMA = 0.94              # valor clásico de RiskMetrics
MU_ANUAL = 0.08                 # rendimiento esperado anual SUPUESTO para el pronóstico del precio
SEED = 123
UMBRAL_SEÑAL = 0.10             # 10 % de diferencia entre GARCH y volatilidad implícita

# Términos del convertible (reporte WM_Proyecto_Final)
S_EMISION = 229.58              # cierre oficial de WM el 21-oct-2026 (LSEG)
T_CONV = 6.0                    # años
PRIMA_CONV, PRIMA_WARR = 0.25, 0.60
MONTO = 750.0                   # USD mm
F = 1000.0                      # valor nominal por bono
K_CONV = S_EMISION * (1 + PRIMA_CONV)
K_WARR = S_EMISION * (1 + PRIMA_WARR)
N_ACC = F / K_CONV              # acciones por bono
ACC_MM = MONTO / K_CONV         # mm de acciones subyacentes
IV_LSEG = 0.227453              # vol. implícita LSEG, calls ene-2029 strike 290
VOL_WARR_LSEG = 0.2104          # vol. histórica 90 días LSEG (la que usa el caso para el warrant)

# Valores de respaldo si no hay datos de mercado
FALLBACK_PRICE = {"WM": 229.58, "RSG": 233.40}
FALLBACK_IV = {"WM": IV_LSEG, "RSG": 0.22}
COLORES = {"WM": "#1F3864", "RSG": "darkorange"}

SAVE_FIGS = os.environ.get("SAVE_FIGS")      # carpeta opcional para guardar las figuras
if SAVE_FIGS:
    os.makedirs(SAVE_FIGS, exist_ok=True)

def mostrar(nombre):
    plt.tight_layout()
    if SAVE_FIGS:
        plt.savefig(f"{SAVE_FIGS}/{nombre}.png", dpi=110)
    plt.show()

print(f"Precio de conversión: {K_CONV:.2f} | strike del warrant: {K_WARR:.2f} | acciones por bono: {N_ACC:.4f}")

def descargar_precios():
    try:
        import yfinance as yf
        fin = pd.Timestamp.today().normalize()
        ini = fin - pd.DateOffset(years=YEARS)
        df = yf.download(TICKERS, start=ini, end=fin, auto_adjust=True, progress=False, timeout=20)["Close"]
        df = df.dropna()
        if df.shape[0] > 300 and all(t in df.columns for t in TICKERS):
            return df[TICKERS], "Yahoo Finance (yfinance)"
    except Exception as e:
        print("No se pudo descargar de Yahoo Finance:", e)
    return None, None


def datos_sinteticos(n=1255):
    """Serie simulada con GARCH(1,1) para WM y RSG (solo como respaldo didáctico)."""
    rng = np.random.default_rng(SEED)
    rho = 0.7
    z = rng.standard_normal((n, 2))
    z[:, 1] = rho * z[:, 0] + np.sqrt(1 - rho ** 2) * z[:, 1]
    par = {"WM": (0.06, 0.06, 0.90), "RSG": (0.06, 0.06, 0.90)}   # (omega, alpha, beta) en %²
    cols = {}
    for j, t in enumerate(TICKERS):
        omega, alpha, beta = par[t]
        v = omega / (1 - alpha - beta)
        u = np.empty(n)
        for i in range(n):
            u[i] = np.sqrt(v) * z[i, j]
            v = omega + alpha * u[i] ** 2 + beta * v
        s = np.exp(np.cumsum(u / 100 + 0.0003))
        cols[t] = s / s[-1] * FALLBACK_PRICE[t]
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    return pd.DataFrame(cols, index=idx)


precios, fuente = descargar_precios()
SINTETICO = precios is None
if SINTETICO:
    precios = datos_sinteticos()
    fuente = "DATOS SIMULADOS (no son precios reales de mercado)"
print("Fuente de datos:", fuente)
print(f"Observaciones: {len(precios)}   desde {precios.index[0].date()} hasta {precios.index[-1].date()}")

rend = 100 * np.log(precios / precios.shift(1)).dropna()      # rendimientos en %
print(precios.tail(3).round(2))

# Exportar los precios de WM para el reporte en R (sección 7)
if not SINTETICO:
    os.makedirs("datos", exist_ok=True)
    precios[[PRINCIPAL]].rename(columns={PRINCIPAL: "Close"}).rename_axis("Date").to_csv(
        "datos/WM_precios.csv", date_format="%Y-%m-%d")
    print("Guardado datos/WM_precios.csv (súbelo a la carpeta datos/ del repositorio)")

def vol_anual_desde_var(v):
    """Varianza diaria en %² -> volatilidad anual en decimal."""
    return np.sqrt(252 * np.asarray(v)) / 100

vol_30 = rend.rolling(30).std() * np.sqrt(252) / 100
vol_hist_1a = rend.iloc[-252:].std() * np.sqrt(252) / 100
vol_hist_5a = rend.std() * np.sqrt(252) / 100

print(pd.DataFrame({"Último año": vol_hist_1a, "Toda la muestra": vol_hist_5a}).round(4))
print(f"\nReferencia LSEG para WM: vol. histórica 90 días 21.04 %, implícita (strike 290, ene-2029) {IV_LSEG:.2%}")

def var_garch(params, u, v0=None):
    """Serie de varianzas condicionales de GARCH(1,1). v[t] usa u[t-1] y v[t-1]."""
    omega, alpha, beta = params
    if v0 is None:
        v0 = np.var(u)
    x = omega + alpha * u[:-1] ** 2
    y, _ = lfilter([1.0], [1.0, -beta], x, zi=[beta * v0])
    return np.r_[v0, y]


def var_ewma(u, lam=LAMBDA_EWMA):
    return var_garch((0.0, 1 - lam, lam), u, v0=np.var(u[:30]))


def loglik(v, u):
    """Log-verosimilitud gaussiana (Hull 23.5: maximizar sum[-ln v - u^2/v], aquí con constantes)."""
    return -0.5 * np.sum(np.log(2 * np.pi) + np.log(v) + u ** 2 / v)

def ajustar_garch(u):
    v = np.var(u)
    x0 = [v * 0.03, 0.08, 0.90]
    cons = ({"type": "ineq", "fun": lambda p: 0.9999 - p[1] - p[2]},)
    bnds = [(1e-6, None), (1e-4, 0.5), (0.30, 0.9998)]
    res = minimize(lambda p: -loglik(var_garch(p, u), u), x0, method="SLSQP",
                   bounds=bnds, constraints=cons, options={"maxiter": 500, "ftol": 1e-10})
    return res.x


M = {}   # resultados por acción
for t in TICKERS:
    u = rend[t].values
    p = ajustar_garch(u)
    v = var_garch(p, u)
    omega, alpha, beta = p
    VL = omega / (1 - alpha - beta)
    M[t] = dict(u=u, p=p, v=v, VL=VL, v_next=omega + alpha * u[-1] ** 2 + beta * v[-1])

tabla = pd.DataFrame({
    t: {
        "omega": M[t]["p"][0], "alpha": M[t]["p"][1], "beta": M[t]["p"][2],
        "alpha+beta": M[t]["p"][1] + M[t]["p"][2],
        "Vol largo plazo (anual)": vol_anual_desde_var(M[t]["VL"]),
        "Vol hoy (anual, GARCH)": vol_anual_desde_var(M[t]["v_next"]),
        "Vida media del shock (días)": np.log(0.5) / np.log(M[t]["p"][1] + M[t]["p"][2]),
    } for t in TICKERS
}).round(4)
print(tabla)

# Validación contra el paquete `arch` (debe dar valores muy parecidos)
try:
    from arch import arch_model
    for t in TICKERS:
        am = arch_model(M[t]["u"], mean="Zero", vol="GARCH", p=1, q=1, dist="normal").fit(disp="off")
        print(f"{t}  paquete arch: omega={am.params['omega']:.4f} alpha={am.params['alpha[1]']:.4f} "
              f"beta={am.params['beta[1]']:.4f}  |  nuestro MLE: "
              f"{M[t]['p'][0]:.4f} {M[t]['p'][1]:.4f} {M[t]['p'][2]:.4f}")
except Exception as e:
    print("Validación con `arch` omitida:", e)

print("\nInterpretación:")
for t in TICKERS:
    a, b = M[t]["p"][1], M[t]["p"][2]
    print(f"- {t}: persistencia {a + b:.3f}. Un shock pierde la mitad de su efecto en "
          f"~{np.log(0.5) / np.log(a + b):.0f} días. La volatilidad de largo plazo es "
          f"{vol_anual_desde_var(M[t]['VL']):.1%} y hoy el modelo ve {vol_anual_desde_var(M[t]['v_next']):.1%}.")

# Gráfica: volatilidad histórica 30 días vs EWMA vs GARCH
fig, axs = plt.subplots(1, 2, figsize=(13, 4.2))
for ax, t in zip(axs, TICKERS):
    idx = rend.index
    ax.plot(idx, vol_30[t], color="gray", alpha=0.6, lw=1, label="Histórica 30 días")
    ax.plot(idx, vol_anual_desde_var(var_ewma(M[t]["u"])), color="black", lw=1, ls="--", label="EWMA λ=0,94")
    ax.plot(idx, vol_anual_desde_var(M[t]["v"]), color=COLORES[t], lw=1.6, label="GARCH(1,1)")
    ax.axhline(vol_anual_desde_var(M[t]["VL"]), color=COLORES[t], ls=":", lw=1.2, label="Largo plazo (V_L)")
    if t == PRINCIPAL:
        ax.axhline(IV_LSEG, color="firebrick", ls="-.", lw=1.2, label="Implícita LSEG (conversión)")
    ax.set_title(f"{t}: volatilidad anualizada")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.legend(fontsize=8)
mostrar("01_volatilidades")
print("Lectura: GARCH sube rápido tras un shock y luego regresa hacia su nivel de largo plazo (línea punteada).")

try:
    from statsmodels.stats.diagnostic import acorr_ljungbox
    def lb_pvalue(serie, lags=10):
        return float(acorr_ljungbox(serie, lags=[lags], return_df=True)["lb_pvalue"].iloc[0])
except Exception:
    def lb_pvalue(serie, lags=10):            # misma prueba, programada a mano
        x = np.asarray(serie) - np.mean(serie); n = len(x); d = np.sum(x ** 2)
        Q = n * (n + 2) * sum((np.sum(x[k:] * x[:-k]) / d) ** 2 / (n - k) for k in range(1, lags + 1))
        return float(1 - chi2.cdf(Q, lags))

filas = []
for t in TICKERS:
    u, n = M[t]["u"], len(M[t]["u"])
    # mejor λ por máxima verosimilitud
    grid = np.arange(0.80, 0.995, 0.005)
    lls = [loglik(var_ewma(u, l), u) for l in grid]
    lam_opt = grid[int(np.argmax(lls))]
    M[t]["lam_opt"] = lam_opt
    modelos = {
        "Volatilidad constante": (np.full(n, np.var(u)), 1),
        "EWMA λ=0,94": (var_ewma(u, 0.94), 0),
        f"EWMA λ óptimo ({lam_opt:.3f})": (var_ewma(u, lam_opt), 1),
        "GARCH(1,1)": (M[t]["v"], 3),
    }
    for nombre, (v, k) in modelos.items():
        ll = loglik(v, u)
        filas.append({
            "Acción": t, "Modelo": nombre, "Log-verosim.": ll,
            "AIC": 2 * k - 2 * ll, "BIC": k * np.log(n) - 2 * ll,
            "p Ljung-Box (u²/σ²)": lb_pvalue(u ** 2 / v),
        })
comparacion = pd.DataFrame(filas).round(3)
print(comparacion.to_string(index=False))
print("\nu² sin modelar (hay clustering si p es pequeño):",
      {t: round(lb_pvalue(M[t]["u"] ** 2), 4) for t in TICKERS})
print("Interpretación: el mejor modelo tiene menor AIC/BIC y p de Ljung-Box mayor a 0,05.")

def pron_var(params, u, v, H):
    omega, alpha, beta = params
    VL = omega / (1 - alpha - beta)
    v_next = omega + alpha * u[-1] ** 2 + beta * v[-1]
    k = np.arange(H)
    return VL + (alpha + beta) ** k * (v_next - VL)


def vol_promedio(t, dias):
    """Volatilidad anual promedio esperada en los próximos `dias` días hábiles."""
    fv = pron_var(M[t]["p"], M[t]["u"], M[t]["v"], max(int(dias), 1))
    return float(np.sqrt(252 * fv.mean()) / 100)


def vol_promedio_hull(t, dias):
    """Fórmula continua de Hull: V_L + (1-e^{-aT})/(aT) (V(0)-V_L), a = ln(1/(alpha+beta))."""
    omega, alpha, beta = M[t]["p"]
    a = np.log(1 / (alpha + beta))
    V0 = M[t]["v_next"]
    return float(np.sqrt(252 * (M[t]["VL"] + (1 - np.exp(-a * dias)) / (a * dias) * (V0 - M[t]["VL"]))) / 100)


DIAS_CONV = int(T_CONV * 252)
plazos = [10, 30, 63, 126, 252, 554, DIAS_CONV]
est = pd.DataFrame({t: [vol_promedio(t, d) for d in plazos] for t in TICKERS},
                   index=[f"{d} días" for d in plazos[:-2]] + ["554 días (LEAPS ene-2029)", f"{DIAS_CONV} días (convertible)"]).round(4)
print("Volatilidad anual promedio esperada (estructura temporal GARCH):")
print(est)
VOL_GARCH_6A = vol_promedio(PRINCIPAL, DIAS_CONV)
print(f"\nControl con la fórmula continua de Hull (WM, {DIAS_CONV} días): {vol_promedio_hull(PRINCIPAL, DIAS_CONV):.4f}")
print(f"WM — GARCH 6 años: {VOL_GARCH_6A:.2%} vs. implícita LSEG {IV_LSEG:.2%}")

fig, ax = plt.subplots(figsize=(8, 4))
dd = np.arange(1, DIAS_CONV + 1)
for t in TICKERS:
    fv = pron_var(M[t]["p"], M[t]["u"], M[t]["v"], DIAS_CONV)
    ax.plot(dd / 252, vol_anual_desde_var(fv), color=COLORES[t], lw=2, label=f"{t}: volatilidad pronosticada")
    ax.axhline(vol_anual_desde_var(M[t]["VL"]), color=COLORES[t], ls=":", lw=1)
ax.plot(dd / 252, [vol_promedio(PRINCIPAL, d) for d in dd], color=COLORES[PRINCIPAL], ls="--", lw=1.2,
        label="WM: promedio hasta T (el que usa el árbol)")
ax.axhline(IV_LSEG, color="firebrick", ls="-.", lw=1, label="Implícita LSEG 22.75 %")
ax.set_xlabel("Años hacia adelante"); ax.set_title("Reversión de la volatilidad a su nivel de largo plazo")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}")); ax.legend(fontsize=8)
mostrar("02_estructura_temporal_vol")
print("Lectura: a 6 años casi todo el efecto de la volatilidad de hoy ya se disipó; manda la volatilidad de largo plazo.")

x, y = rend[TICKERS[0]].values, rend[TICKERS[1]].values
cov = np.empty(len(x)); cov[0] = np.mean(x[:30] * y[:30])
for i in range(1, len(x)):
    cov[i] = LAMBDA_EWMA * cov[i - 1] + (1 - LAMBDA_EWMA) * x[i - 1] * y[i - 1]
corr_ewma = cov / np.sqrt(var_ewma(x) * var_ewma(y))
corr_60 = rend[TICKERS[0]].rolling(60).corr(rend[TICKERS[1]])

fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(rend.index, corr_60, color="gray", alpha=0.6, label="Móvil 60 días")
ax.plot(rend.index, corr_ewma, color="black", lw=1.6, label="EWMA λ=0,94")
ax.set_title(f"Correlación {TICKERS[0]}-{TICKERS[1]}"); ax.legend()
mostrar("03_correlacion")
print(f"Correlación actual (EWMA): {corr_ewma[-1]:.2f}  |  promedio de la muestra: {np.nanmean(corr_ewma):.2f}")

def simular_trayectorias(t, S0, H, n_sim, deriva_anual, rng, solo_final=False):
    omega, alpha, beta = M[t]["p"]
    v = np.full(n_sim, omega + alpha * M[t]["u"][-1] ** 2 + beta * M[t]["v"][-1])  # varianza del día n+1, en %²
    S = np.full(n_sim, float(S0)) if solo_final else np.empty((H + 1, n_sim))
    if not solo_final:
        S[0] = S0
    for k in range(1, H + 1):
        sig = np.sqrt(v)
        z = rng.standard_normal(n_sim)
        ret = deriva_anual / 252 - 0.5 * (sig / 100) ** 2 + (sig / 100) * z
        if solo_final:
            S = S * np.exp(ret)
        else:
            S[k] = S[k - 1] * np.exp(ret)
        v = omega + alpha * (sig * z) ** 2 + beta * v
    return S


rng = np.random.default_rng(SEED)
S0 = {t: float(precios[t].iloc[-1]) for t in TICKERS}
SIM = {t: simular_trayectorias(t, S0[t], HORIZON_DAYS, N_SIM, MU_ANUAL, rng) for t in TICKERS}

resumen_mc = {}
for t in TICKERS:
    ST = SIM[t][-1]
    q5, q25, q50, q75, q95 = np.percentile(ST, [5, 25, 50, 75, 95])
    r10 = SIM[t][10] / S0[t] - 1
    resumen_mc[t] = {"Precio hoy": S0[t], "P5": q5, "P25": q25, "Mediana": q50, "P75": q75, "P95": q95,
                     "Prob. sube": (ST > S0[t]).mean(), "VaR 99% 10 días": -np.percentile(r10, 1)}
print(pd.DataFrame(resumen_mc).round(3))

fig, axs = plt.subplots(1, 2, figsize=(13, 4.2))
for ax, t in zip(axs, TICKERS):
    dias = np.arange(HORIZON_DAYS + 1)
    p = np.percentile(SIM[t], [5, 25, 50, 75, 95], axis=1)
    ax.fill_between(dias, p[0], p[4], color=COLORES[t], alpha=0.15, label="Percentil 5-95")
    ax.fill_between(dias, p[1], p[3], color=COLORES[t], alpha=0.30, label="Percentil 25-75")
    ax.plot(dias, p[2], color=COLORES[t], lw=2, label="Mediana")
    ax.axhline(S0[t], color="gray", ls=":")
    ax.set_title(f"{t}: abanico de precios a {HORIZON_DAYS} días (GARCH)"); ax.set_xlabel("Días hábiles"); ax.legend(fontsize=8)
mostrar("04_abanico_precios")

# WM a 6 años desde el precio de emisión: ¿cuándo se activan la conversión y los warrants?
rng = np.random.default_rng(SEED + 10)
SIM6 = simular_trayectorias(PRINCIPAL, S_EMISION, DIAS_CONV, 2000, MU_ANUAL, rng)   # 1,513 x 2,000
ST6 = SIM6[-1]
prob = {"P(S_T > precio de conversión $%.0f)" % K_CONV: (ST6 > K_CONV).mean(),
        "P(S_T > strike del warrant $%.0f)" % K_WARR: (ST6 > K_WARR).mean(),
        "Mediana de S_T": np.median(ST6), "P5 de S_T": np.percentile(ST6, 5), "P95 de S_T": np.percentile(ST6, 95)}
print(pd.Series(prob).round(3))

fig, ax = plt.subplots(figsize=(9, 4))
anios = np.arange(DIAS_CONV + 1) / 252
p = np.percentile(SIM6, [5, 25, 50, 75, 95], axis=1)
ax.fill_between(anios, p[0], p[4], color=COLORES[PRINCIPAL], alpha=0.12, label="Percentil 5-95")
ax.fill_between(anios, p[1], p[3], color=COLORES[PRINCIPAL], alpha=0.28, label="Percentil 25-75")
ax.plot(anios, p[2], color=COLORES[PRINCIPAL], lw=2, label="Mediana")
ax.axhline(K_CONV, color="firebrick", ls="--", label=f"Precio de conversión ${K_CONV:.0f}")
ax.axhline(K_WARR, color="darkgreen", ls="--", label=f"Strike del warrant ${K_WARR:.0f}")
ax.set_title("WM: abanico GARCH a 6 años (vida del convertible)"); ax.set_xlabel("Años"); ax.legend(fontsize=8)
mostrar("04b_abanico_6_anios")
print("Lectura: la probabilidad de superar el strike del warrant mide qué tan probable es que WM llegue a diluir.")

def kupiec(x, N, p):
    if x == 0:
        lr = -2 * N * np.log(1 - p)
    else:
        ph = x / N
        lr = -2 * ((N - x) * np.log((1 - p) / (1 - ph)) + x * np.log(p / ph))
    return float(1 - chi2.cdf(lr, 1))


def backtest(t, nivel, inicio, refit=63):
    u = M[t]["u"]; n = len(u)
    z = norm.ppf(nivel)
    v_ew = var_ewma(u)
    var_pred = {"GARCH(1,1)": np.full(n, np.nan), "EWMA": v_ew, "Histórica 250d": np.full(n, np.nan)}
    for s in range(inicio, n, refit):
        fin = min(n, s + refit)
        p = ajustar_garch(u[:s])
        var_pred["GARCH(1,1)"][s:fin] = var_garch(p, u[:fin], v0=np.var(u[:s]))[s:fin]
    for s in range(inicio, n):
        var_pred["Histórica 250d"][s] = np.var(u[s - 250:s])
    filas = []
    for nombre, vp in var_pred.items():
        var_ = z * np.sqrt(vp[inicio:])
        exc = u[inicio:] < -var_
        N, x = len(exc), int(exc.sum())
        filas.append({"Acción": t, "Confianza": f"{nivel:.0%}", "Modelo": nombre, "Días": N, "Excepciones": x,
                      "Tasa observada": x / N, "Tasa esperada": 1 - nivel, "p Kupiec": kupiec(x, N, 1 - nivel)})
    return filas, var_pred["GARCH(1,1)"], z


filas_bt, serie_var = [], {}
inicio_bt = int(len(rend) * 0.6)
for t in TICKERS:
    for nivel in (0.95, 0.99):
        f, vg, z = backtest(t, nivel, inicio_bt)
        filas_bt += f
        if nivel == 0.99:
            serie_var[t] = (vg, z)
bt = pd.DataFrame(filas_bt)
print(bt.round(4).to_string(index=False))
print("\nInterpretación: p Kupiec > 0,05 y tasa observada cercana a la esperada = el modelo mide bien el riesgo.")

fig, axs = plt.subplots(1, 2, figsize=(13, 4))
for ax, t in zip(axs, TICKERS):
    u = M[t]["u"]; vg, z = serie_var[t]
    ax.plot(rend.index[inicio_bt:], u[inicio_bt:], color="gray", lw=0.8, label="Rendimiento diario (%)")
    ax.plot(rend.index[inicio_bt:], -z * np.sqrt(vg[inicio_bt:]), color=COLORES[t], lw=1.5, label="−VaR 99% (GARCH)")
    exc = u[inicio_bt:] < -z * np.sqrt(vg[inicio_bt:])
    ax.scatter(rend.index[inicio_bt:][exc], u[inicio_bt:][exc], color="black", zorder=3, s=18, label="Excepciones")
    ax.set_title(f"{t}: back testing del VaR 99% a 1 día"); ax.legend(fontsize=8)
mostrar("05_backtesting_var")

def crr(S0_, K, r, sigma, T, N=500, tipo="put", americana=True, q=0.0):
    dt = T / N
    u_ = np.exp(sigma * np.sqrt(dt)); d_ = 1 / u_
    p = (np.exp((r - q) * dt) - d_) / (u_ - d_); disc = np.exp(-r * dt)
    sg = 1 if tipo == "call" else -1
    niveles = [None] * 3
    j = np.arange(N + 1)
    V = np.maximum(sg * (S0_ * u_ ** (N - j) * d_ ** j - K), 0.0)
    if N <= 2: niveles[N] = V
    for i in range(N - 1, -1, -1):
        k = np.arange(i + 1)
        cont = disc * (p * V[:i + 1] + (1 - p) * V[1:i + 2])
        V = np.maximum(cont, np.maximum(sg * (S0_ * u_ ** (i - k) * d_ ** k - K), 0.0)) if americana else cont
        if i <= 2: niveles[i] = V
    return V[0], niveles, u_, d_, dt


def griegas(S0_, K, r, sigma, T, N=500, tipo="put", americana=True, q=0.0):
    precio, niv, u_, d_, dt = crr(S0_, K, r, sigma, T, N, tipo, americana, q)
    f0, f1, f2 = niv[0][0], niv[1], niv[2]
    delta = (f1[0] - f1[1]) / (S0_ * u_ - S0_ * d_)
    gamma = ((f2[0] - f2[1]) / (S0_ * u_ ** 2 - S0_) - (f2[1] - f2[2]) / (S0_ - S0_ * d_ ** 2)) / (0.5 * (S0_ * u_ ** 2 - S0_ * d_ ** 2))
    theta = (f2[1] - f0) / (2 * dt) / 365
    vega = crr(S0_, K, r, sigma + 0.01, T, N, tipo, americana, q)[0] - precio
    rho = crr(S0_, K, r + 0.01, sigma, T, N, tipo, americana, q)[0] - precio
    return dict(precio=precio, delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)


def valor_bono(cup, y=Y_WM, T=6, m=2):
    t_ = np.arange(1, int(T * m) + 1); cf = np.full(len(t_), F * cup / m); cf[-1] += F
    return float(np.sum(cf / (1 + y / m) ** t_))


def contrato_mercado(t, S0_):
    """LEAPS más largo de Yahoo con strike cercano al precio de conversión; si falla, usa la implícita de LSEG."""
    base = dict(iv=FALLBACK_IV[t], fuente="LSEG OPW: calls ene-2029, strike 290 (22.75 %)")
    if SINTETICO:
        return base
    try:
        import yfinance as yf
        tk = yf.Ticker(t)
        exp = max(tk.options, key=lambda e: pd.Timestamp(e))
        ch = tk.option_chain(exp)
        c = ch.calls.iloc[(ch.calls.strike - 1.25 * S0_).abs().argsort().iloc[0]]
        if float(c.impliedVolatility) > 0.05:
            return dict(iv=float(c.impliedVolatility), fuente=f"Yahoo Finance, call {exp} strike {c.strike:.0f}")
    except Exception:
        pass
    return base


mercado = contrato_mercado(PRINCIPAL, S0[PRINCIPAL])
VOLS = {"Histórica 1 año": float(vol_hist_1a[PRINCIPAL]), "GARCH promedio 6 años": VOL_GARCH_6A,
        "Implícita LSEG": IV_LSEG}
if mercado["iv"] != IV_LSEG:
    VOLS["Implícita Yahoo (LEAPS)"] = mercado["iv"]
q_wm = DIV_YIELD[PRINCIPAL]

filas, RES = [], {}
for etiqueta, sg in VOLS.items():
    g = griegas(S_EMISION, K_CONV, R_FREE, sg, T_CONV, 500, "call", True, q_wm)
    opcion_bono = g["precio"] * N_ACC
    cupon = brentq(lambda c: valor_bono(c) - (F - opcion_bono), -0.05, 0.10)
    hedge = g["precio"] * ACC_MM
    warr = crr(S_EMISION, K_WARR, R_FREE, sg, T_CONV, 500, "call", True, q_wm)[0] * ACC_MM
    RES[etiqueta] = dict(sigma=sg, call=g["precio"], cupon=cupon, hedge=hedge, warr=warr)
    filas.append({"Volatilidad usada": etiqueta, "σ": sg, "Call por acción": g["precio"], "Δ": g["delta"],
                  "Gamma": g["gamma"], "Vega (1 pto)": g["vega"], "Opción por bono": opcion_bono,
                  "Cupón a la par": cupon, "Note hedge (USD mm)": hedge, "Warrants (USD mm)": warr,
                  "Call spread neto (USD mm)": hedge - warr})
tabla_op = pd.DataFrame(filas).round(4)
print(tabla_op.to_string(index=False))
# Convención del caso y del reporte: note hedge con la implícita, warrant con la histórica de 90 días (LSEG)
hedge_rep = RES["Implícita LSEG"]["hedge"]
warr_rep = crr(S_EMISION, K_WARR, R_FREE, VOL_WARR_LSEG, T_CONV, 500, "call", True, q_wm)[0] * ACC_MM
NETO_REPORTE = hedge_rep - warr_rep
print(f"\nConvención del reporte (hedge a {IV_LSEG:.2%}, warrant a {VOL_WARR_LSEG:.2%}): "
      f"note hedge USD {hedge_rep:.1f} mm − warrants USD {warr_rep:.1f} mm = USD {NETO_REPORTE:.1f} mm "
      f"({NETO_REPORTE / MONTO:.1%} del principal)")
print(f"\nStrike conversión {K_CONV:.2f}, warrant {K_WARR:.2f}, plazo {T_CONV:.0f} años, S = {S_EMISION} (emisión). "
      f"Implícita de mercado: {mercado['fuente']}")
print("Interpretación: el árbol es el mismo de clase; GARCH solo cambia la volatilidad que le damos.")

sg = VOL_GARCH_6A
ca = crr(S_EMISION, K_CONV, R_FREE, sg, T_CONV, 500, "call", True, q_wm)[0]
ce = crr(S_EMISION, K_CONV, R_FREE, sg, T_CONV, 500, "call", False, q_wm)[0]
grid_s = np.linspace(K_CONV, 4 * K_CONV, 80)
ejercer = [crr(s, K_CONV, R_FREE, sg, T_CONV, 300, "call", True, q_wm)[0] - (s - K_CONV) < 1e-6 for s in grid_s]
critico = float(grid_s[np.where(ejercer)[0].min()]) if any(ejercer) else None
print(pd.DataFrame([{"σ GARCH": sg, "Call americana": ca, "Call europea": ce, "Prima ejercicio anticipado": ca - ce,
                     "% del precio": 100 * (ca - ce) / ce}]).round(4).to_string(index=False))
if critico:
    print(f"\nSi WM sube por arriba de ~USD {critico:.0f} (hoy {S_EMISION}), convertir hoy es óptimo: "
          f"los dividendos que se pierden por esperar valen más que el valor tiempo de la opción.")
else:
    print("\nEn este rango de precios nunca conviene convertir hoy: esperar vale más.")
print("Por eso el reporte valúa el convertible completo en el árbol (Tsiveriotis-Fernandes) y no con la fórmula europea.")

def tf_convertible(cup, s, S=S_EMISION, prima=PRIMA_CONV, N=360, qd=DIV_YIELD["WM"]):
    nn = F / (S * (1 + prima)); dt = T_CONV / N
    up = np.exp(s * np.sqrt(dt)); dn = 1 / up; p = (np.exp((R_FREE - qd) * dt) - dn) / (up - dn)
    rc = 2 * np.log(1 + Y_WM / 2); dr = np.exp(-R_FREE * dt); dk = np.exp(-rc * dt)
    paso = int(N / (2 * T_CONV)); cpn = F * cup / 2
    j = np.arange(N + 1); conv = nn * S * up ** (N - j) * dn ** j
    V = np.maximum(conv, F + cpn); B = np.where(conv >= F + cpn, 0, F + cpn)
    for i in range(N - 1, -1, -1):
        Bc = dk * (p * B[:-1] + (1 - p) * B[1:])
        Ec = dr * (p * (V[:-1] - B[:-1]) + (1 - p) * (V[1:] - B[1:]))
        if i > 0 and i % paso == 0:
            Bc = Bc + cpn
        Vc = Bc + Ec; j = np.arange(i + 1); cv = nn * S * up ** (i - j) * dn ** j
        convierte = cv > Vc
        V = np.where(convierte, cv, Vc); B = np.where(convierte, 0, Bc)
    return V[0]


cupon_tf = {k: brentq(lambda c: tf_convertible(c, v["sigma"]) - F, -0.05, 0.10) for k, v in RES.items()}
res_tf = pd.DataFrame({"σ": {k: v["sigma"] for k, v in RES.items()},
                       "Cupón (bono + call, caso)": {k: v["cupon"] for k, v in RES.items()},
                       "Cupón (árbol T-F)": cupon_tf,
                       "Ahorro vs. bono directo (pb)": {k: (Y_WM - c) * 1e4 for k, c in cupon_tf.items()}}).round(4)
print(res_tf)
print(f"\nCaso base del reporte (implícita LSEG): cupón T-F = {cupon_tf['Implícita LSEG']:.3%}")

rng = np.random.default_rng(SEED + 1)
S_rn = simular_trayectorias(PRINCIPAL, S_EMISION, DIAS_CONV, N_SIM * 2, R_FREE - q_wm, rng, solo_final=True)
disc = np.exp(-R_FREE * T_CONV)
comp = []
for nombre, K in (("Opción de conversión / note hedge", K_CONV), ("Warrant", K_WARR)):
    pagos = np.maximum(S_rn - K, 0)
    mc = disc * pagos.mean(); ee = disc * pagos.std() / np.sqrt(len(pagos))
    ar = crr(S_EMISION, K, R_FREE, VOL_GARCH_6A, T_CONV, 500, "call", False, q_wm)[0]
    comp.append({"Opción": nombre, "Strike": K, "MC-GARCH": mc, "Error estándar MC": ee,
                 "Árbol (σ GARCH)": ar, "Dif. %": 100 * (ar / mc - 1)})
print(pd.DataFrame(comp).round(3).to_string(index=False))
print("Interpretación: si la diferencia es de pocos puntos porcentuales, usar la volatilidad promedio de GARCH en el árbol "
      "es una buena aproximación.")

ratio = VOL_GARCH_6A / IV_LSEG
if ratio < 1 - UMBRAL_SEÑAL:
    senal = "EMITIR: el mercado cobra la volatilidad más cara de lo que GARCH espera (WM vende volatilidad cara)"
elif ratio > 1 + UMBRAL_SEÑAL:
    senal = "CAUTELA: GARCH ve más volatilidad que el mercado; subir la prima de conversión o esperar"
else:
    senal = "SIN VENTAJA clara: GARCH y el mercado coinciden; decide el ahorro de cupón, no la volatilidad"

ST = ST6                                    # trayectorias del mundo real (sección 8), 6 años
dil_sin = ACC_MM * np.maximum(ST - K_CONV, 0)          # USD mm entregados en acciones arriba del principal
dil_con = ACC_MM * np.maximum(ST - K_WARR, 0)
neto_cs = NETO_REPORTE
SENAL = dict(ratio=ratio, senal=senal, dil_sin=dil_sin.mean(), dil_con=dil_con.mean(), neto_cs=neto_cs,
             valor_fut_cs=neto_cs * np.exp(R_FREE * T_CONV))

fig, ax = plt.subplots(figsize=(9, 4))
bins = np.linspace(0, np.percentile(dil_sin, 99), 60)
ax.hist(dil_sin[dil_sin > 0], bins=bins, color="firebrick", alpha=0.45, label="Sin call spread")
ax.hist(dil_con[dil_con > 0], bins=bins, color="darkgreen", alpha=0.45, label="Con call spread")
ax.set_title("WM: dilución al vencimiento en escenarios con conversión (GARCH, 6 años)")
ax.set_xlabel("USD mm entregados en acciones por encima del principal"); ax.legend()
mostrar("06_dilucion_call_spread")

print(f"σ GARCH 6 años {VOL_GARCH_6A:.1%}  |  σ implícita {IV_LSEG:.1%}  |  razón {ratio:.2f}")
print("Señal:", senal)
print(f"Dilución esperada al vencimiento: sin call spread USD {SENAL['dil_sin']:.1f} mm, con call spread USD {SENAL['dil_con']:.1f} mm")
print(f"Costo del call spread hoy USD {neto_cs:.1f} mm (≈ USD {SENAL['valor_fut_cs']:.1f} mm capitalizado a 6 años)")
print(f"P(se diluye sin call spread) = {(ST > K_CONV).mean():.1%} | P(se diluye con call spread) = {(ST > K_WARR).mean():.1%}")

print("RESUMEN")
print("Fuente de datos:", fuente)
for t in TICKERS:
    a, b = M[t]["p"][1], M[t]["p"][2]
    print(f"\n{t}: α={a:.3f}, β={b:.3f}, persistencia={a + b:.3f}; vol hoy {vol_anual_desde_var(M[t]['v_next']):.1%} "
          f"→ largo plazo {vol_anual_desde_var(M[t]['VL']):.1%}.")
    print(f"   Precio {S0[t]:.2f}; mediana a {HORIZON_DAYS} días {resumen_mc[t]['Mediana']:.2f} "
          f"(P5 {resumen_mc[t]['P5']:.2f} – P95 {resumen_mc[t]['P95']:.2f}).")
print(f"\nConvertible WM: σ GARCH 6 años {VOL_GARCH_6A:.1%} → cupón a la par (árbol T-F) "
      f"{cupon_tf['GARCH promedio 6 años']:.2%} vs. {cupon_tf['Implícita LSEG']:.2%} con la implícita de LSEG.")
print(f"   Call spread neto (convención del reporte): USD {SENAL['neto_cs']:.1f} mm. Señal: {SENAL['senal']}")
print(f"   P(WM > ${K_WARR:.0f} en 6 años) = {(ST6 > K_WARR).mean():.1%}")

# (Opcional) Descargar los precios de WM para el repositorio y tomar captura de las tablas para capturas/17_Colab_GARCH.png
try:
    from google.colab import files
    if os.path.exists("datos/WM_precios.csv"):
        files.download("datos/WM_precios.csv")
except Exception:
    pass
