# Capturas de pantalla (terminales financieras y Colab)

Guarda cada captura en esta carpeta **con el nombre exacto** (`.png` o `.jpg`). Al hacer *Knit* del
`WM_Proyecto_Final.Rmd`, el Anexo A las inserta solas. Esta misma tabla sirve como guion de
explicaciones para el documento de Drive.

| Archivo | Terminal / función | Qué debe verse | Para qué se usó en el reporte |
|---|---|---|---|
| `01_LSEG_Overview` | LSEG Workspace → `WM.N` → Overview | Descripción, market cap, EV, estructura de capital | Sección 2 y 4 (estructura de capital) |
| `02_LSEG_PricePerformance` | Overview → Price Performance | Rendimientos 1s-1a, máx/mín 52s, vol. histórica 10/30/90/200d, beta | Sección 2; vol. del warrant (21.04%) |
| `03_LSEG_KeyRatios` | Financials → Key Ratios | EV/EBITDA, Deuda/EBITDA, cobertura de intereses, consenso 2026-2028 | Sección 3 y 13 (métricas de crédito) |
| `04_LSEG_DebtStructure` | `DS` (Debt Structure) | Bonos vigentes, monto por moneda | Sección 4 (perfil de deuda) |
| `05_LSEG_IssuerCurve` | `0#WMUSDABMK=` Issuer Curve | Yield, spread vs. benchmark, Z-spread, prob. de default por plazo | Sección 5; tasa de descuento 5.649% a 6 años |
| `06_LSEG_Ratings` | Bond Ratings / Issuer Ratings | S&P A-, Fitch A-, Moody's WR | Sección 5 |
| `07_LSEG_Bono_7.00_2028` | Página del bono US902917AH67 | Cupón, monto vigente, precio ask | Bonos a recomprar |
| `08_LSEG_Bono_7.75_2032` | Página del bono US94106LAN91 | Cupón, monto vigente, precio ask | Bonos a recomprar |
| `09_LSEG_Bono_6.125_2039` | Página del bono US94106LAV18 | Cupón, monto vigente, precio ask | Bonos a recomprar |
| `10_LSEG_OPW_Opciones` | `OPW` → calls WM ene-2029 | Strikes 170-320, vol. implícita, delta | Sección 6; vol. de conversión 22.75% (strike 290) |
| `11_LSEG_Treasuries` | `US5YT=RR` y `US7YT=RR` | Rendimientos 4.918% y 4.995% | Tasa libre de riesgo 6 años |
| `12c_LSEG_USDCAD_spot` | LSEG `CAD=` | USD/CAD bid/ask y hora | Sección 16, swap de divisas |
| `12d_LSEG_Canada_5Y` | LSEG `CA5YT=RR` → REPS Valuation | Rendimiento del benchmark de Canadá a 5 años | Sección 16, descuento CAD |
| `12e_LSEG_Bono_WM_CAD_2033` | LSEG `CA94107TAB76` → Description | Cupón 3.944%, vencimiento 15-jul-2033, C$ 700 mm | Sección 16, swap de divisas |
| `12f_LSEG_Bono_WM_CAD_REPS` | LSEG `CA94107TAB76` → REPS Valuation | YTM 4.186%, spread sobre Canadá | Sección 16, swap de divisas |
| `12g_LSEG_Bono_Apple_2032_REPS` | LSEG `US037833FA32` → REPS Valuation | YTM 4.905%, spread 27 pb sobre Treasury | Sección 16, ventaja comparativa (referencia AA) |
| `12_LSEG_PriceHistory` | Price History (5 años, diario) | Serie exportada a Excel/CSV | Sección 7 (EWMA/GARCH) → `datos/WM_precios.csv` |
| `13_Bloomberg_OVCV` | Bloomberg `OVCV` (si tienen acceso) | Valuación de un convertible con los mismos términos | Validación cruzada del cupón |
| `14_Bloomberg_HIVG` | Bloomberg `WM US Equity HIVG` | Vol. histórica vs. implícita | Validación de la volatilidad |
| `15_CapitalIQ_Pares` | Capital IQ → Comparables (WM, RSG, WCN) | Múltiplos y apalancamiento | Sección 12 → `datos/pares.csv` |
| `15a_LSEG_KeyRatios_RSG` | LSEG `RSG.N` → Overview → Key Ratios | EV/EBITDA, Deuda/EBITDA, EBITDA/Intereses (ya incluida) | Sección 12 |
| `15b_LSEG_KeyRatios_WCN` | LSEG `WCN.N` → Overview → Key Ratios | Mismos ratios para Waste Connections (ya incluida) | Sección 12 |
| `16_Infosel` | Infosel → cotización WM | Precio y datos de mercado | Respaldo del precio |
| `17_Colab_GARCH` | `WM_GARCH_Derivados.ipynb`, secciones 4-12 | Parámetros GARCH, comparación de modelos, back testing, tabla de la opción de conversión | Sección 7 |
| `17a`–`17f_Colab_*` | `WM_GARCH_Derivados.ipynb` | Parámetros, volatilidades, estructura temporal, back testing, cupón por volatilidad, dilución (ya incluidas) | Sección 7 |
| `18_Colab_Alpaca_Orden` | Colab sección 4 + dashboard de Alpaca (paper) | Orden multi-pierna del call spread y posiciones | Parte operativa |

**Tip:** en Windows `Win + Shift + S`, en Mac `Cmd + Shift + 4`. Recorta solo la parte relevante de la pantalla.
