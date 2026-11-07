# %% [markdown]
# # Waste Management (WM) — Swaps de cobertura: tasas, divisas y acciones (Hull, cap. 7)
# 
# **Proyecto final de Derivados · Bono convertible con call spread (caso Molson Coors aplicado a WM)**
# 
# Este notebook replica el cuaderno de clase *Swaps: tasas de interés, divisas y acciones* (Hull, 11.ª ed., cap. 7)
# **con los datos de WM** en lugar de los ejemplos hipotéticos. Todos los swaps se plantean desde el punto de vista de la tesorería
# de WM y con **fines de cobertura** (no especulativos):
# 
# | Cuaderno de clase | Aquí (WM) | Riesgo que cubre |
# |---|---|---|
# | 1–2. Swap fijo/variable, curva hipotética | Swaps *receive fixed* del tender (sección 15 del reporte), curva swap de **LSEG Rates View (03-nov-2026)** | Que bajen las tasas y se encarezca la recompra de bonos |
# | 3. Ventaja comparativa, empresas A y B | WM paga fijo / recibe SOFR con una contraparte AA | Deuda de WM a tasa variable (USD 2.9 mil mm, 10-K Item 7A) |
# | 4. Swap de divisas USD/MXN | Swap **CAD/USD** sobre el bono WM 3.944% 2033 en dólares canadienses (C$ 700 mm) | Tipo de cambio CAD/USD |
# | 5. Equity swap AAPL / TSLA | Equity swap: WM **recibe el rendimiento de su acción** y paga fijo | Dilución económica de los warrants del call spread si WM sube |
# | — | **6. Parte operativa:** diseño de la réplica en Alpaca (*paper*) con ETFs y acciones; las órdenes enviadas fueron limitadas y **no se ejecutaron** | |
# | — | **7. Seguimiento:** código para medir el P&L de cada réplica si hay posiciones (sin ejecución, no aplica) | |
# 
# > Llaves de Alpaca en los **Secrets** de Colab: `ALPACA_API_KEY` y `ALPACA_SECRET_KEY` (las mismas del notebook del call spread).
# > Sin llaves, el notebook corre completo y solo se salta las secciones 6 y 7.

# %%
# !pip install -q yfinance alpaca-py
import numpy as np, pandas as pd, matplotlib.pyplot as plt, os, datetime as dt
pd.options.display.float_format = '{:,.4f}'.format
plt.rcParams['figure.figsize'] = (9, 4); plt.rcParams['axes.grid'] = True
AZUL, AZUL2, ROJO, VERDE = '#1F3864', '#2E75B6', '#C00000', '#548235'

# %% [markdown]
# ## 0. Insumos de mercado
# 
# Mismos datos del reporte (`WM_Proyecto_Final.Rmd`, secciones 4, 5 y 15). Lo marcado como **SUPUESTO** no viene de una terminal;
# si lo confirman en LSEG basta con cambiar el número aquí y volver a correr todo.

# %%
# ---- Curva swap USD: Treasuries benchmark + swap spreads (LSEG Rates View, 03-nov-2026) ----
plazos   = np.array([2, 5, 7, 10])
ust      = np.array([0.04629, 0.04757, 0.04848, 0.04964])
swap_spr = np.array([-14.50, -28.38, -34.88, -39.38]) / 1e4
par_swap = ust + swap_spr                       # tasas swap par (semestrales)

# ---- Cobertura del tender (sección 15 del Rmd) ----
DV01_TENDER = 339_562                            # USD por pb, canasta 7.00% 2028 / 7.75% 2032 / 6.125% 2039
NOC_SWAPS   = {'2Y': 226.7e6, '5Y': 159.8e6, '10Y': 283.8e6}   # nocionales receive fixed por nodo

# ---- WM y pares ----
Y_WM_6A  = 0.05649                               # YTM curva WM a 6 años (Issuer Curve, 21-oct-2026)
DEUDA_VAR_WM = 2.9e9                             # deuda expuesta a tasa variable en 12 meses (10-K 2025, Item 7A)
BONO_CAD_USD = 498.4e6                           # bono de WM en CAD, monto vigente en USD (LSEG DS)
# Bono en CAD: WM 3.944% 15-jul-2033 (CA94107TAB76), C$ 700 mm, cupón semestral (LSEG Workspace, 06-nov-2026)
BONO_CAD, CUPON_CAD, VENC_CAD = 700e6, 0.03944, '2033-07-15'
YTM_CAD_WM = 0.04186      # YTM del bono (REPS/EJV 05-nov-2026): 78 pb sobre la curva de Canadá
R_CAD      = 0.0340       # curva del Gobierno de Canadá interpolada a 6.69 años (LSEG REPS); 5 años: 3.374%
S0_CAD     = 1.4124       # USD/CAD spot (CAD por USD), LSEG CAD= 06-nov-2026 15:22 (bid 1.4122 / ask 1.4126)

FECHA_COMPRA, FECHA_ENTREGA = '2026-11-05', '2026-11-09'
print('Tasas swap par USD:', dict(zip([f'{p}Y' for p in plazos], np.round(par_swap * 100, 3))))

# %% [markdown]
# ## 1. Swap de tasa: WM recibe fijo y paga variable
# 
# En la sección 15 del reporte WM necesita **ganar si las tasas bajan** mientras fija el precio del tender
# (si bajan, los bonos que va a recomprar suben de precio). El swap que lo logra es **recibir fijo / pagar variable**.
# Tomamos el swap del nodo de 5 años (cubre el bono 7.75% 2032): nocional USD 159.8 mm, pagos semestrales, tasa fija = tasa swap par a 5 años.
# 
# La curva cero se obtiene por *bootstrapping* de las tasas swap par (debajo de 2 años se usa la tasa de 2 años, simplificación;
# en la práctica se usarían SOFR y OIS, sección 7.6 del libro). Los flujos variables futuros se **proyectan con las tasas forward** de la curva.

# %%
dt_ = 0.5
t = np.arange(dt_, 10 + 1e-9, dt_)                       # semestres hasta 10 años
par_t = np.interp(t, plazos, par_swap)                  # tasa par por semestre (plana debajo de 2 años)

def bootstrap(par):
    D = np.zeros(len(par))
    for i, c in enumerate(par):
        D[i] = (1 - c * dt_ * D[:i].sum()) / (1 + c * dt_)
    return D

D_all = bootstrap(par_t)
z_all = -np.log(D_all) / t                               # tasas cero continuas (como el cuaderno de clase)

# Swap del nodo 5Y
N = NOC_SWAPS['5Y']; n5 = int(5 / dt_)
t5, Z = t[:n5], D_all[:n5]
tasa_fija = (1 - Z[-1]) / (dt_ * Z.sum())               # tasa par del swap (vale 0 al inicio)
Z_ant = np.concatenate([[1.0], Z[:-1]])
fwd = (Z_ant / Z - 1) / dt_                             # forwards semestrales proyectados

flujos = pd.DataFrame({'Semestre': np.arange(1, n5 + 1), 't (años)': t5, 'Forward proyectada': fwd,
                       'Cobro fijo WM': N * tasa_fija * dt_, 'Pago variable WM': N * fwd * dt_})
flujos['Neto WM (recibe fijo)'] = flujos['Cobro fijo WM'] - flujos['Pago variable WM']
print(f'Tasa fija del swap 5Y (par): {tasa_fija:.4%}  |  nocional USD {N/1e6:,.1f} mm')
flujos

# %%
colores = [VERDE if x >= 0 else ROJO for x in flujos['Neto WM (recibe fijo)']]
fig, ax = plt.subplots()
ax.bar(flujos['Semestre'], flujos['Neto WM (recibe fijo)'] / 1e6, color=colores)
ax.axhline(0, color='k', lw=0.8)
ax.set_xlabel('Semestre'); ax.set_ylabel('Millones de USD')
ax.set_title('Swap 5Y: flujo neto proyectado para WM (recibe fijo)')
plt.show()
print(f"VP de los netos proyectados: USD {(flujos['Neto WM (recibe fijo)'] * Z).sum():,.0f} (≈ 0: el swap nace a la par)")
print('Interpretación: con curva de pendiente positiva WM cobra neto en los primeros semestres y paga en los últimos, '
      'pero en valor presente se compensa.')

# %% [markdown]
# ## 2. Valuación del swap y sensibilidad
# 
# Igual que en el cuaderno de clase, con los dos enfoques de Hull (sección 7.7), pero desde el lado de WM (**recibe fijo**):
# $V = B_{fijo} - B_{var}$. Para que el valor no sea cero, lo valuamos **después de una baja paralela de 25 pb** (el escenario que la cobertura busca proteger).

# %%
def valuar(shift_pb, noc=N, K=tasa_fija, n=n5):
    zs = z_all[:n] + shift_pb / 1e4
    Zs = np.exp(-zs * t[:n])
    B_fijo = (noc * K * dt_ * Zs).sum() + noc * Zs[-1]
    B_var = noc                                          # justo después del reajuste vale el nocional
    Zs_ant = np.concatenate([[1.0], Zs[:-1]]); f = (Zs_ant / Zs - 1) / dt_
    V_fra = (noc * dt_ * (K - f) * Zs).sum()
    return B_fijo - B_var, V_fra

V_b, V_f = valuar(-25)
print(f'Valor para WM tras -25 pb (enfoque bonos): USD {V_b:,.0f}')
print(f'Valor para WM tras -25 pb (enfoque FRAs):  USD {V_f:,.0f}')
print('Ambos coinciden:', np.isclose(V_b, V_f))
pd.DataFrame({'t (años)': t5, 'Tasa cero': z_all[:n5], 'Factor desc.': Z, 'Forward semestral': fwd})

# %%
desplaz = np.arange(-100, 101, 25)
vals = [valuar(s)[0] / 1e6 for s in desplaz]
fig, ax = plt.subplots()
ax.plot(desplaz, vals, marker='o', color=AZUL)
ax.axhline(0, color='k', lw=0.8)
ax.set_xlabel('Desplazamiento paralelo de la curva (pb)'); ax.set_ylabel('Millones USD')
ax.set_title('Swap 5Y: valor para WM (recibe fijo)')
plt.show()

# DV01 de los tres swaps de cobertura vs. DV01 del tender
fila = []
for nodo, noc in NOC_SWAPS.items():
    n = int(int(nodo[:-1]) / dt_); K = (1 - D_all[n-1]) / (dt_ * D_all[:n].sum())
    dv01 = (valuar(-1, noc, K, n)[0] - valuar(1, noc, K, n)[0]) / 2
    fila.append({'Nodo': nodo, 'Nocional USD mm': noc / 1e6, 'Tasa fija': K, 'DV01 USD/pb': dv01})
cob = pd.DataFrame(fila)
print(cob.to_string(index=False, formatters={'Tasa fija': '{:.3%}'.format, 'DV01 USD/pb': '{:,.0f}'.format}))
print(f"\nDV01 de los 3 swaps: USD {cob['DV01 USD/pb'].sum():,.0f} por pb vs. DV01 del tender USD {DV01_TENDER:,.0f}")
print('Interpretación: WM gana en el swap cuando bajan las tasas, justo cuando el tender se encarece. '
      'Los tres swaps compensan casi todo el DV01 de la canasta (la diferencia viene de usar convención continua aquí '
      'y semestral en el Rmd, y del riesgo de base swap-Treasury que explica la sección 15).')

# %% [markdown]
# ## 3. Ventaja comparativa: WM fija su deuda variable con un swap
# 
# Según el Item 7A de su 10-K, WM tiene **USD 2.9 mil millones de deuda expuesta a tasa variable** en los próximos 12 meses
# (papel comercial y vencimientos a refinanciar). Para **cubrirse de alzas de tasa** quiere pagar fijo. Como en el ejemplo de Hull,
# la contraparte es un emisor de mejor calificación (AA) que prefiere tasa variable. WM es la "empresa B": pide prestado variable,
# donde su desventaja relativa es menor, y con el swap queda pagando **fijo**.
# 
# Tasas fijas de LSEG: WM, su YTM a 6 años (5.649%); contraparte AA, el bono **Apple 4.500% 12-may-2032** (YTM 4.905%, 27 pb sobre el Treasury). Los **márgenes sobre SOFR** (WM +0.80%, Apple +0.45%) son **SUPUESTOS**.

# %%
fija_A, spread_A = 0.04905, 0.0045      # AA: Apple 4.500% 12-may-2032, YTM 4.905% (LSEG REPS 05-nov-2026); SOFR+0.45% SUPUESTO
fija_B, spread_B = Y_WM_6A, 0.0080      # WM: fija LSEG; SOFR + 0.80% SUPUESTO

dif_fija = fija_B - fija_A
dif_var = spread_B - spread_A
ganancia_total = dif_fija - dif_var
g = ganancia_total / 2                  # se reparte en partes iguales
# AA pide fijo en el mercado y WM variable. Swap: AA paga SOFR a WM y WM paga X (fija) a AA
X = fija_A - spread_A + g
costo_A = spread_A - g                  # AA queda en variable
costo_B = spread_B + X                  # WM queda en FIJA

tabla_va = pd.DataFrame({'Fija': [fija_A, fija_B], 'Variable (margen s/SOFR)': [spread_A, spread_B]},
                        index=['Apple (AA+, contraparte)', 'WM (A-)'])
print(tabla_va.to_string(formatters={'Fija': '{:.3%}'.format, 'Variable (margen s/SOFR)': '{:.2%}'.format}))
print(f"\nDiferencia en fija: {dif_fija:.2%} | en variable: {dif_var:.2%} | ganancia total: {ganancia_total:.2%} (cada una {g:.3%})")
print(f"Tasa fija que WM paga a la contraparte en el swap: {X:.3%}")
print(f"Costo final WM: {costo_B:.3%} FIJO (emitiendo fijo directo: {fija_B:.3%})")
print(f"Costo final contraparte AA: SOFR {costo_A:+.3%} (sin swap SOFR {spread_A:+.2%})")

alzas = np.array([0, 50, 100, 200]) / 1e4
cob = pd.DataFrame({'Alza de SOFR (pb)': (alzas * 1e4).astype(int),
                    'Gasto extra sin cobertura (USD mm)': DEUDA_VAR_WM * alzas / 1e6,
                    'Gasto extra con swap (USD mm)': 0.0})
print('\n' + cob.to_string(index=False, formatters={'Gasto extra sin cobertura (USD mm)': '{:,.1f}'.format,
                                                     'Gasto extra con swap (USD mm)': '{:,.1f}'.format}))
print('Interpretación: con el swap, el costo de la deuda variable de WM queda fijo; un alza de 100 pb ya no le cuesta '
      f'USD {DEUDA_VAR_WM * 0.01 / 1e6:,.0f} mm al año (el 10-K estima USD 35 mm). Cautela (Hull): parte de la "ganancia" refleja que '
      'el margen variable se puede revisar y que un intermediario cobra 3-4 pb.')

# %% [markdown]
# ## 4. Swap de divisas CAD/USD sobre el bono en dólares canadienses
# 
# WM tiene **un bono en CAD**: **WM 3.944% 15-jul-2033, C$ 700 mm** (≈ USD 496 mm; LSEG Workspace). Para dejar toda su deuda en USD,
# WM entra a un swap fijo-fijo: **recibe CAD** (3.944% semestral, con lo que paga cupones y principal del bono) y **paga USD**.
# Al inicio se intercambian principales al tipo de cambio spot.
# 
# $$V_{WM} = \frac{B_{CAD}}{S_0} - B_{USD}, \qquad S_0 = \text{CAD por USD}$$
# 
# Datos de LSEG (06-nov-2026): USD/CAD 1.4124; curva de Canadá a 6.69 años 3.40% (descuento CAD); curva swap USD interpolada
# (descuento USD). La tasa USD del swap se fija para que valga **cero al inicio**. Como simplificación, el primer cupón se toma completo.

# %%
S0 = S0_CAD
HOY = pd.Timestamp('2026-11-06')
fechas_cad = pd.date_range('2027-01-15', VENC_CAD, freq=pd.DateOffset(months=6))
tt = ((fechas_cad - HOY).days / 365).values             # años a cada pago semestral
T_CAD = tt[-1]
N_cad = BONO_CAD; N_usd = N_cad / S0
r_usd = np.interp(T_CAD, plazos, par_swap)              # descuento USD (curva swap)
cf_cad = np.full(len(tt), N_cad * CUPON_CAD / 2); cf_cad[-1] += N_cad
B_cad0 = (cf_cad * np.exp(-R_CAD * tt)).sum()
K_usd = (B_cad0 / S0 / N_usd - np.exp(-r_usd * T_CAD)) / (0.5 * np.exp(-r_usd * tt)).sum()
cf_usd = np.full(len(tt), N_usd * K_usd / 2); cf_usd[-1] += N_usd
print(f'Bono: C$ {N_cad/1e6:,.0f} mm = USD {N_usd/1e6:,.1f} mm a {S0:.4f} | {len(tt)} cupones, plazo {T_CAD:.2f} años')
print(f'Tasa USD justa del swap: {K_usd:.3%} (WM paga) contra {CUPON_CAD:.3%} en CAD (WM recibe) | descuento USD {r_usd:.3%}, CAD {R_CAD:.2%}')
flujos_div = pd.DataFrame({'Fecha': ['06-nov-2026'] + [d.strftime('%d-%b-%Y') for d in fechas_cad],
    'CAD (WM recibe)': np.r_[-N_cad, cf_cad], 'USD (WM paga)': np.r_[N_usd, -cf_usd]})
flujos_div.style.format({'CAD (WM recibe)': '{:,.0f}', 'USD (WM paga)': '{:,.0f}'})

# %%
def valor_swap_cad(S, r_usd=r_usd, r_cad=R_CAD):
    B_cad = (cf_cad * np.exp(-r_cad * tt)).sum()
    B_usd = (cf_usd * np.exp(-r_usd * tt)).sum()
    return B_cad / S - B_usd, B_cad / S, B_usd

for S in [S0, S0 * 0.95, S0 * 1.05]:
    V, Bc, Bu = valor_swap_cad(S)
    print(f'S = {S:.4f} -> Bono CAD en USD: {Bc:,.0f} | Bono USD: {Bu:,.0f} | Valor swap WM: USD {V:,.0f}')

# Verificación con forwards: F_T = S * exp((r_cad - r_usd) T)
def v_fwd(S):
    Fw = S * np.exp((R_CAD - r_usd) * tt)
    return ((cf_cad / Fw - cf_usd) * np.exp(-r_usd * tt)).sum()
print('Enfoque forwards = enfoque bonos (S0 y S0 -5%):', np.isclose(v_fwd(S0), valor_swap_cad(S0)[0], atol=1),
      np.isclose(v_fwd(S0 * 0.95), valor_swap_cad(S0 * 0.95)[0], atol=1))

spots = np.linspace(S0 * 0.85, S0 * 1.15, 31)
fig, ax = plt.subplots()
ax.plot(spots, [valor_swap_cad(s)[0] / 1e6 for s in spots], color=AZUL, label='Swap (WM recibe CAD)')
ax.plot(spots, [-(N_cad / s - N_usd) / 1e6 for s in spots], color=ROJO, ls='--', label='Principal del bono en CAD (en USD, signo de WM)')
ax.axhline(0, color='k', lw=0.8); ax.axvline(S0, color='gray', ls='--')
ax.set_xlabel('Tipo de cambio (CAD por USD)'); ax.set_ylabel('Millones USD'); ax.legend()
ax.set_title('Swap CAD/USD: la ganancia del swap compensa el costo de la deuda en CAD')
plt.show()
print('Interpretación: el swap nace en cero. Si el CAD se aprecia (baja CAD/USD) la deuda en CAD cuesta más en dólares, '
      'pero el swap gana casi lo mismo; si se deprecia, ocurre lo contrario. La deuda queda sintéticamente en USD.')

# %% [markdown]
# ## 5. Equity swap de cobertura: WM recibe el rendimiento de su propia acción
# 
# En el call spread del proyecto WM **vende warrants** con strike de 60% de prima (sección 10 del reporte): si la acción sube
# mucho, esos warrants se ejercen y diluyen. Un **equity swap** en el que WM **recibe el rendimiento de su acción y paga fijo**
# compensa ese costo: cuando WM sube, el swap paga y cubre el aumento de valor de los warrants; cuando baja, WM paga en el swap,
# pero los warrants valen menos. Es el mismo instrumento que usan las empresas para cubrir planes de compensación en acciones.
# 
# - **Nocional:** delta de los warrants × acciones subyacentes × precio (cobertura delta al inicio).
# - **Pierna fija:** tasa swap a 2 años (4.48%), pagos trimestrales.
# - **Ilustración retrospectiva con datos reales:** como si los warrants se hubieran vendido hace un año (strike = 160% del precio de ese día).

# %%
from scipy.stats import norm
TICKERS = ['WM', 'IEF', 'BIL', 'FXC']
try:
    import yfinance as yf
    px = yf.download(TICKERS, period='1y', interval='1d', auto_adjust=True, progress=False)['Close'][TICKERS].dropna()
    if px.empty: raise ValueError('Sin datos')
    fuente = 'Yahoo Finance (datos reales)'
except Exception:
    rng = np.random.default_rng(7)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=252)
    mu, sd, p0 = [0.0003, 0.0001, 0.00016, 0.0], [0.012, 0.004, 0.0002, 0.004], [235, 96, 91.5, 71]
    px = pd.DataFrame(np.array(p0) * np.exp(np.cumsum(rng.normal(mu, sd, size=(len(idx), 4)), axis=0)), index=idx, columns=TICKERS)
    if os.path.exists('datos/WM_precios.csv'):
        wm = pd.read_csv('datos/WM_precios.csv', index_col=0, parse_dates=True)['Close']
        px['WM'] = wm.reindex(px.index).ffill().bfill()
    fuente = 'datos SIMULADOS (sin conexión a Yahoo Finance)'
print('Fuente:', fuente, '|', px.index.min().date(), 'a', px.index.max().date())

def bs_call(S, K, r, s, T, q):
    d1 = (np.log(S / K) + (r - q + s * s / 2) * T) / (s * np.sqrt(T)); d2 = d1 - s * np.sqrt(T)
    return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2), np.exp(-q * T) * norm.cdf(d1)

ACC_WARR = 750e6 / (229.58 * 1.25)            # acciones subyacentes del convertible (≈ 2.61 mm)
S_W, R_W, Q_W, T_W = 0.2104, 0.0496, 0.0163, 6.0   # mismos insumos del warrant en el reporte
fijo = par_swap[0]                            # 2Y, 4.48%
pos = np.linspace(0, len(px) - 1, 5).round().astype(int)
S_ini = px['WM'].iloc[pos[0]]; K_W = 1.60 * S_ini
_, delta_w = bs_call(S_ini, K_W, R_W, S_W, T_W, Q_W)
N_eq = delta_w * ACC_WARR * S_ini
print(f'Delta de los warrants al inicio: {delta_w:.3f} -> nocional del swap: USD {N_eq / 1e6:,.1f} mm '
      f'(equivale a {delta_w * ACC_WARR / 1e6:,.2f} mm de acciones)')

filas = []
for i in range(1, 5):
    Sa, Sb = px['WM'].iloc[pos[i - 1]], px['WM'].iloc[pos[i]]
    Ta, Tb = T_W - 0.25 * (i - 1), T_W - 0.25 * i
    dW = ACC_WARR * (bs_call(Sb, K_W, R_W, S_W, Tb, Q_W)[0] - bs_call(Sa, K_W, R_W, S_W, Ta, Q_W)[0])
    swap = N_eq * (Sb / Sa - 1) - N_eq * fijo / 4
    filas.append({'Trimestre': f'T{i} (al {px.index[pos[i]].date()})', 'Rend. WM': Sb / Sa - 1,
                  'Δ valor warrants (costo WM)': dW, 'Flujo neto swap (WM recibe)': swap, 'Resultado cubierto': swap - dW})
tabla_eq = pd.DataFrame(filas).set_index('Trimestre')
print(tabla_eq.to_string(formatters={'Rend. WM': '{:.2%}'.format, 'Δ valor warrants (costo WM)': '{:,.0f}'.format,
                                     'Flujo neto swap (WM recibe)': '{:,.0f}'.format, 'Resultado cubierto': '{:,.0f}'.format}))
tot = tabla_eq.sum(numeric_only=True)
print(f"\nAño: Δ warrants USD {tot['Δ valor warrants (costo WM)']:,.0f} | swap USD {tot['Flujo neto swap (WM recibe)']:,.0f} | "
      f"neto USD {tot['Resultado cubierto']:,.0f}")
c = np.corrcoef(tabla_eq['Δ valor warrants (costo WM)'], tabla_eq['Flujo neto swap (WM recibe)'])[0, 1]
print(f'Correlación trimestral entre el costo de los warrants y el swap: {c:.2f}')

tabla_eq[['Δ valor warrants (costo WM)', 'Flujo neto swap (WM recibe)']].div(1e6).plot(kind='bar', color=[ROJO, AZUL],
    title='Equity swap vs. costo de los warrants (millones USD)')
plt.axhline(0, color='k', lw=0.8); plt.xticks(rotation=0); plt.show()
print('Interpretación: el swap se mueve en la misma dirección que el costo de los warrants, así que el resultado cubierto '
      'varía mucho menos. La diferencia viene de la gamma de los warrants (el delta cambia) y del costo de la pierna fija.')

# %%
# 5.3 Valuación a mitad de vida (Hull, sección 7.13): pasaron 2 trimestres, quedan 2
S_ratio = px['WM'].iloc[pos[2]] / px['WM'].iloc[pos[0]]
cupon = N_eq * fijo / 4
tt = np.array([0.25, 0.50])
B_fijo_eq = cupon * np.exp(-fijo * tt[0]) + (cupon + N_eq) * np.exp(-fijo * tt[1])
V_eq = N_eq * S_ratio - B_fijo_eq
print(f'WM acumuló {S_ratio - 1:+.2%} en la primera mitad. Valor del equity swap para WM: USD {V_eq:,.0f}')
print('Interpretación: si WM sube más que los pagos fijos pendientes, el swap tiene valor positivo para WM (compensa la '
      'dilución); solo esa parte está expuesta al riesgo de crédito del banco contraparte.')

# %% [markdown]
# ## 6. Parte operativa: réplica de los swaps en Alpaca (paper)
# 
# > **Estado:** las órdenes de la cuenta paper se enviaron como **limitadas y no se ejecutaron**; no hay posiciones ni P&L realizado. El código queda como diseño reproducible (con `ENVIAR = True` manda órdenes a mercado).
# 
# Alpaca no opera swaps OTC, así que replicamos cada uno con **ETFs y acciones listadas**. Cada pierna del swap es una posición:
# 
# | Swap de cobertura | Pierna que WM **recibe** | Pierna que WM **paga** | Réplica en Alpaca |
# |---|---|---|---|
# | 1. Tasa del tender (receive fixed) | Fija de mediano plazo | Variable | **Compra IEF** (Treasuries 7-10 años) + **venta en corto BIL** (T-bills 1-3 meses ≈ tasa variable) |
# | 4. Divisas CAD/USD | CAD | USD | **Compra FXC** (CurrencyShares dólar canadiense = largo CAD / corto USD) |
# | 5. Equity swap (warrants) | Rendimiento de WM | Fijo (se financia con la caja de la cuenta) | **Compra WM** |
# 
# El swap de la sección 3 (WM paga fijo sobre su deuda variable) no tiene réplica sencilla con ETFs sin duplicar la posición de tasa,
# así que se deja solo en la parte de valuación.
# 
# Nocional de **USD 10,000 por pierna** (cuenta simulada). Se usan acciones enteras porque Alpaca no permite cortos fraccionales.
# Cada orden lleva un `client_order_id` que empieza con `swapWM-`, para reconstruir la entrada el 13-nov aunque Colab se haya reiniciado.
# Si el mercado está cerrado, las órdenes quedan en cola y se ejecutan en la apertura.

# %%
NOCIONAL_PIERNA = 10_000
PORTAFOLIO = [  # (swap, pierna, símbolo, lado)
    ('1_Tasa',      'recibe_fijo',  'IEF', 'buy'),
    ('1_Tasa',      'paga_var',     'BIL', 'sell'),
    ('4_CAD_USD',   'recibe_CAD',   'FXC', 'buy'),
    ('5_WM_warrants', 'recibe_WM',  'WM',  'buy'),
]
try:
    from google.colab import userdata
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
    from alpaca.data.historical.stock import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestTradeRequest
    API_KEY, SECRET = userdata.get('ALPACA_API_KEY'), userdata.get('ALPACA_SECRET_KEY')
    trading = TradingClient(API_KEY, SECRET, paper=True)
    stk_data = StockHistoricalDataClient(API_KEY, SECRET)
    cuenta = trading.get_account()
    reloj = trading.get_clock()
    ALPACA = True
    print('Cuenta paper:', cuenta.account_number, '| equity:', cuenta.equity, '| buying power:', cuenta.buying_power,
          '| shorting:', getattr(cuenta, 'shorting_enabled', 'n/d'))
    print('Mercado abierto:', reloj.is_open, '| próxima apertura:', reloj.next_open)
except Exception as e:
    ALPACA = False
    print('Sin conexión a Alpaca (se omiten las secciones 6 y 7):', e)

# %%
# Plan de órdenes con el último precio de Alpaca
if ALPACA:
    simbolos = sorted({p[2] for p in PORTAFOLIO})
    ult = stk_data.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=simbolos))
    plan = pd.DataFrame(PORTAFOLIO, columns=['Swap', 'Pierna', 'Símbolo', 'Lado'])
    plan['Precio'] = plan['Símbolo'].map(lambda s: float(ult[s].price))
    plan['Acciones'] = (NOCIONAL_PIERNA // plan['Precio']).astype(int)
    plan['Monto USD'] = plan['Acciones'] * plan['Precio']
    display(plan)

# %%
# ENVÍO DE ÓRDENES: correr UNA sola vez (vuelve a comprar si se corre de nuevo)
ENVIAR = False   # cambiar a True para enviar las órdenes
if ALPACA and ENVIAR:
    sello = dt.datetime.now().strftime('%m%d%H%M%S')
    enviadas = []
    for _, f in plan.iterrows():
        cid = f"swapWM-{f['Swap']}-{f['Pierna']}-{sello}"
        try:
            o = trading.submit_order(MarketOrderRequest(symbol=f['Símbolo'], qty=int(f['Acciones']),
                    side=OrderSide.BUY if f['Lado'] == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY, client_order_id=cid))
            enviadas.append({'client_order_id': cid, 'símbolo': o.symbol, 'lado': str(o.side), 'qty': o.qty, 'estado': str(o.status)})
        except Exception as e:
            enviadas.append({'client_order_id': cid, 'símbolo': f['Símbolo'], 'lado': f['Lado'], 'qty': f['Acciones'], 'estado': f'ERROR: {e}'})
    display(pd.DataFrame(enviadas))   # CAPTURA 19a_Colab_Swaps_Ordenes

# %% [markdown]
# ## 7. Seguimiento: P&L de cada réplica (solo si hay órdenes ejecutadas)
# 
# Esta sección se puede correr cualquier día después de la compra. Lee las órdenes `swapWM-` ejecutadas en Alpaca (precio promedio de llenado),
# las valúa al último precio y suma las piernas de cada swap. Después compara con lo que **pagaría el swap teórico** con el mismo nocional:
# 
# * Swap 5 (warrants): $N \cdot r_{WM} - N \cdot k \cdot \tfrac{días}{360}$ (la pierna fija se devenga, no se cobra en Alpaca).
# * Swap 1: el ETF largo/corto aproxima el *receive fixed*; su P&L se compara con el cambio de valor de un swap de 7 años con el mismo DV01.

# %%
if ALPACA:
    ords = trading.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, limit=500,
                                               after=dt.datetime(2026, 11, 1)))
    ent = pd.DataFrame([{'cid': o.client_order_id, 'Símbolo': o.symbol, 'Lado': str(o.side.value),
                         'Qty': float(o.filled_qty or 0), 'Precio entrada': float(o.filled_avg_price or 'nan'),
                         'Fecha': pd.Timestamp(o.filled_at).tz_convert('America/Mexico_City') if o.filled_at else pd.NaT}
                        for o in ords if (o.client_order_id or '').startswith('swapWM-')],
                       columns=['cid', 'Símbolo', 'Lado', 'Qty', 'Precio entrada', 'Fecha'])
    ent = ent[ent['Qty'] > 0].copy()
    if ent.empty:
        raise SystemExit('Todavía no hay órdenes swapWM- ejecutadas (si el mercado estaba cerrado, se llenan en la apertura).')
    ent['Swap'] = ent['cid'].str.split('-').str[1]
    ent['Pierna'] = ent['cid'].str.split('-').str[2]
    # Órdenes de la primera versión del notebook (si se enviaron): 5A pasa a ser la cobertura de warrants;
    # 5B (WM vs RSG) era especulativo y se reporta aparte para cerrarlo
    ent['Swap'] = ent['Swap'].replace({'5A_WM_fijo': '5_WM_warrants'})
    ent['Signo'] = np.where(ent['Lado'] == 'buy', 1, -1)
    ult = stk_data.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=sorted(ent['Símbolo'].unique())))
    ent['Precio hoy'] = ent['Símbolo'].map(lambda s: float(ult[s].price))
    ent['Rend.'] = ent['Precio hoy'] / ent['Precio entrada'] - 1
    ent['P&L USD'] = ent['Signo'] * ent['Qty'] * (ent['Precio hoy'] - ent['Precio entrada'])
    print('Valuación al', pd.Timestamp.now(tz='America/Mexico_City').strftime('%d-%b-%Y %H:%M'))
    display(ent[['Swap', 'Pierna', 'Símbolo', 'Lado', 'Qty', 'Precio entrada', 'Precio hoy', 'Rend.', 'P&L USD']]
            .style.format({'Precio entrada': '{:.2f}', 'Precio hoy': '{:.2f}', 'Rend.': '{:.2%}', 'P&L USD': '{:,.2f}'}))

# %%
if ALPACA and len(ent):
    dias = max((pd.Timestamp.now(tz='America/Mexico_City') - ent['Fecha'].min()).days, 1)
    r = ent.groupby('Pierna')['Rend.'].first()
    teorico = {
        '1_Tasa':     np.nan,
        '4_CAD_USD':  NOCIONAL_PIERNA * r.get('recibe_CAD', np.nan),
        '5_WM_warrants': NOCIONAL_PIERNA * (r.get('recibe_WM', np.nan) - par_swap[0] * dias / 360),
    }
    res = ent.groupby('Swap')['P&L USD'].sum().to_frame('P&L réplica Alpaca')
    res['Swap teórico (mismo nocional)'] = pd.Series(teorico)
    res.loc['TOTAL'] = res.sum(numeric_only=True, min_count=1)
    print(f'Días desde la compra: {dias}')
    display(res.style.format('{:,.2f}', na_rep='—'))   # CAPTURA 19c_Colab_Swaps_Seguimiento
    os.makedirs('datos', exist_ok=True)
    res.rename(columns={'P&L réplica Alpaca': 'PyL_replica_Alpaca_USD', 'Swap teórico (mismo nocional)': 'Swap_teorico_USD'}) \
       .round(2).rename_axis('Swap').to_csv('datos/WM_swaps_seguimiento.csv')
    try:
        from google.colab import files; files.download('datos/WM_swaps_seguimiento.csv')   # subirlo a datos/ del repo (lo lee el Rmd)
    except Exception:
        pass
    print('Lectura: la réplica y el swap teórico difieren por acciones enteras (el nocional no es exactamente 10,000), '
          'la pierna fija devengada y el costo de préstamo de los cortos; en un swap OTC no hay que fondear ninguna pierna.')

# %%
# Evolución diaria del P&L por swap desde la compra (cierres de Yahoo Finance)
if ALPACA and len(ent):
    import yfinance as yf
    ini = ent['Fecha'].min().tz_localize(None).normalize()
    cl = yf.download(sorted(ent['Símbolo'].unique()), start=ini, auto_adjust=False, progress=False)['Close']
    if isinstance(cl, pd.Series): cl = cl.to_frame(ent['Símbolo'].iloc[0])
    pnl = pd.DataFrame(index=cl.index)
    for sw, g in ent.groupby('Swap'):
        pnl[sw] = sum(f['Signo'] * f['Qty'] * (cl[f['Símbolo']] - f['Precio entrada']) for _, f in g.iterrows())
    ax = pnl.plot(marker='o', title='P&L acumulado de cada swap replicado (USD)')
    ax.axhline(0, color='k', lw=0.8); ax.set_ylabel('USD'); plt.show()   # CAPTURA 19d_Colab_Swaps_PnL
    display(pnl.round(2))

# %%
# Posiciones abiertas en la cuenta (CAPTURA 19b: esta tabla + la pantalla Positions de app.alpaca.markets)
if ALPACA:
    display(pd.DataFrame([{'símbolo': p.symbol, 'qty': p.qty, 'lado': p.side.value, 'precio prom.': p.avg_entry_price,
                           'precio actual': p.current_price, 'valor': p.market_value, 'P&L no realizado': p.unrealized_pl}
                          for p in trading.get_all_positions()]))

# %%

# Solo si se enviaron las órdenes de la versión anterior: cerrar el corto de RSG (pierna especulativa 5B)
CERRAR_5B = False
if ALPACA and CERRAR_5B:
    for p in trading.get_all_positions():
        if p.symbol == 'RSG' and p.side.value == 'short':
            o = trading.submit_order(MarketOrderRequest(symbol='RSG', qty=abs(int(float(p.qty))), side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY, client_order_id=f"swapWM-cierre5B-RSG-{dt.datetime.now():%m%d%H%M%S}"))
            print('Cierre del corto RSG enviado:', o.id, o.status)


# %% [markdown]
# ## 8. Resumen
# 
# * **Swap de tasa del tender:** WM recibe fijo (5Y ≈ 4.47%) y paga variable; gana si bajan las tasas y compensa el encarecimiento del tender.
#   Los tres swaps por nodo igualan el DV01 de la canasta (≈ USD 340 mil por pb). Enfoque de bonos = enfoque de FRAs.
# * **Swap sobre la deuda variable:** WM paga fijo y recibe SOFR; elimina el riesgo de alzas sobre USD 2.9 mil mm y, por ventaja comparativa, queda debajo de su tasa fija directa.
# * **Swap de divisas:** recibir CAD / pagar USD convierte el único bono en CAD a deuda sintética en USD.
# * **Equity swap:** recibir el rendimiento de WM cubre la dilución económica de los warrants vendidos en el call spread.
# * **Operativa:** la réplica con ETFs y acciones queda diseñada; las órdenes paper fueron limitadas y no se ejecutaron, así que no hay P&L realizado.
# 
# *Referencia:* J. C. Hull, *Options, Futures, and Other Derivatives*, 11.ª ed., cap. 7. Cuaderno base: *swaps_hull_cap7.ipynb* (clase).
