# Waste Management (WM): bono convertible con call spread

**Proyecto final de Derivados.** Aplicamos el caso *Molson Coors Brewing Co.: Valuing a Convertible Bond* a
Waste Management, Inc. (NYSE: WM) con datos de LSEG Workspace al 21-oct-2026.

| Resultado | Valor |
|---|---|
| Emisión propuesta | USD 750 mm, 6 años, prima de conversión 25% (precio de conversión $286.98) |
| Cupón que deja el convertible a la par (árbol Tsiveriotis-Fernandes) | **2.41%** vs. 5.65% del bono directo de WM |
| Costo neto del call spread (note hedge 25% / warrants 60%) | USD 54.4 mm (7.3% del principal) |
| Uso de los recursos | Recompra de los bonos 7.00% 2028, 7.75% 2032 y 6.125% 2039 (USD 647 mm) |
| Ahorro anual de intereses | USD 26.2 mm antes de impuestos |
| Recomendación | Emitir. La operación se paga sola, conserva la calificación A- y la dilución empieza hasta $367 |

## Equipo

Productos derivados y administración de riesgos corporativos (Gpo 40) · Profesor: Dr. Raymundo Díaz Robles
Tania Manuela López Suárez (A00819037) · Mauricio Martínez García (A00826170) · Ricardo Terrazas Duque (A01566884)

## Entregables (rúbrica, sección 3)

| # | Entregable | Archivo / carpeta |
|---|---|---|
| 1 | Reporte ejecutivo (Word y PDF) | [`reporte_ejecutivo/`](reporte_ejecutivo/) |
| 2 | Dashboard HTML con Plotly | [`index.html`](index.html) (página principal de GitHub Pages, 10 capítulos con laboratorio de escenarios) |
| 3 | Reporte reproducible R Markdown + HTML con código visible | [`WM_Proyecto_Final.Rmd`](WM_Proyecto_Final.Rmd) · [`WM_Proyecto_Final.html`](WM_Proyecto_Final.html) |
| 4 | Calculadora HTML interactiva (bono recto + opción, call spread) | [`calculadora/WM_Calculadora_Convertible.html`](calculadora/WM_Calculadora_Convertible.html) |
| 5 | Código en Python y notebooks de Colab con outputs | [`notebooks/`](notebooks/) (`.ipynb`, `_ejecutado.ipynb` y `.py`); swaps: `WM_Swaps_Hull_cap7.ipynb` |
| 6 | PDF del prompt de IA y nota de lo validado | [`ia/`](ia/) |
| 7 | Anexo de capturas de terminal (LSEG Workspace) | [`anexo/WM_Anexo_Capturas_LSEG.pdf`](anexo/WM_Anexo_Capturas_LSEG.pdf) · imágenes en [`capturas/`](capturas/) |
| 8 | Repositorio | este README; datos en [`datos/`](datos/) con su fuente |

Presentación: [`presentacion/`](presentacion/) (HTML de 16 láminas y PDF).

## Selección de la empresa

El portafolio especulativo del equipo en Investopedia (Portafolio Final: AAPL, JPM, NVDA, TSLA y XOM) se complementa con una empresa
nueva para la parte de cobertura. WM es defensiva (beta de 0.41, calificación A-), de un sector que no está en el portafolio, y
cumple las reglas del proyecto: NYSE con 10-K/10-Q/8-K, bonos en circulación y derivados en sus notas, opciones listadas
(LEAPS a 2029) y necesidades reales de cobertura (bonos de cupón alto a refinanciar, deuda a tasa variable y un bono en CAD).
**Todas las operaciones del proyecto son coberturistas**: call spread (dilución), T-lock, futuros y swaps (tasa, tipo de cambio).

**Terminal:** el equipo usó **LSEG Workspace (Refinitiv)** en lugar de Bloomberg por acceso; el anexo incluye las pantallas
equivalentes (DES → Overview, FA → Financial Summary, DS, Issuer Curve, Ratings, OPW y Rates View para swaps, captura 12a).

## Datos y fuentes

| Archivo | Contenido | Fuente |
|---|---|---|
| `datos/WM_precios.csv` | Cierre diario ajustado de WM, 03-nov-2021 a 03-nov-2026 | Yahoo Finance (yfinance) |
| `datos/pares.csv` | Ratios de WM, RSG y WCN | LSEG Workspace, Key Ratios (21 y 28-oct-2026) |
| `datos/fuentes/macro_worldbank_yahoo.json` | PIB, inflación, desempleo y cuenta corriente de EE.UU.; rendimientos del Tesoro (3 años) | World Bank API; Yahoo Finance (^IRX, ^FVX, ^TNX, ^TYX), 03-nov-2026 |
| Cifras de balance, resultados, vencimientos y derivados (en `datos/build_dashboard.py`) | 10-K 2021–2025 y 10-Q 3T-2026 | SEC EDGAR, API XBRL (data.sec.gov), CIK 0000823768 |
| Insumos del motor (en el Rmd) | Precio, Treasuries, curva del emisor, volatilidad implícita, bonos | LSEG Workspace, 21-oct-2026 |
| Cobertura de tasa (en el Rmd, sección 15) | Treasuries benchmark, swap spreads, OIS, futuros TU/FV/TN y CTD | LSEG Rates View, 03-nov-2026 (capturas 12a y 12b) |
| Estados financieros (captura 03) | Ingresos, activos, deuda y capital FY2021-2025 | LSEG Financial Summary (FA), 03-nov-2026; coincide con SEC XBRL |

## Metodología

1. **Overview, ratios, estructura de capital y deuda** de WM (LSEG: Overview, Key Ratios, DS, Issuer Curve, Ratings).
2. **Insumos:** tasa libre de riesgo interpolada de Treasuries a 5 y 7 años, YTM de WM a 6 años, dividend yield,
   volatilidad implícita de los LEAPS ene-2029 (OPW).
3. **Volatilidad de largo plazo:** EWMA (λ = 0.94) y GARCH(1,1) por máxima verosimilitud; estructura temporal (Hull, ec. 23.13).
4. **Opción de conversión:** Black-Scholes-Merton con dividendo y árbol binomial CRR (convergencia, versión americana).
5. **Convertible completo:** árbol de 360 pasos con conversión anticipada y riesgo de crédito (Tsiveriotis-Fernandes, 1998).
6. **Call spread:** costo, payoff a vencimiento y griegas de la posición.
7. **Sensibilidades** del cupón a la prima de conversión y a la volatilidad; impacto en las métricas de crédito.
8. **Alternativas:** convertible + call spread vs. deuda directa vs. emisión de acciones (costo, apalancamiento y dilución).
9. **Cobertura de tasa del tender:** DV01 de los bonos a recomprar y tamaño de la cobertura con T-lock por nodos, futuros del Tesoro y swaps; riesgos y recomendación.
10. **Parte operativa:** orden multi-pierna limitada en Alpaca (paper trading) que replica el call spread con opciones listadas de WM; expiró sin ejecutarse.
11. **Swaps de cobertura (Hull, cap. 7):** el cuaderno de clase aplicado a WM en `notebooks/WM_Swaps_Hull_cap7.ipynb` y en la sección 16 del reporte: swaps *receive fixed* de la cobertura del tender (enfoque de bonos y de FRAs, DV01), swap paga fijo sobre la deuda variable (ventaja comparativa con una contraparte AA), swap de divisas CAD/USD sobre el bono en CAD y equity swap que cubre la dilución de los warrants. Réplica propuesta con ETFs y acciones listadas (IEF + corto BIL, FXC y WM); las órdenes paper en Alpaca fueron limitadas y no se ejecutaron.

## Cómo reproducir

* **Reporte:** abrir `WM_Proyecto_Final.Rmd` en RStudio o Posit Cloud y hacer **Knit**. Si existen
  `datos/WM_precios.csv` y las imágenes de `capturas/`, se incluyen solas.
* **Colab:** abrir el notebook, guardar `ALPACA_API_KEY` y `ALPACA_SECRET_KEY` en *Secrets* (cuenta paper gratuita en alpaca.markets)
  y ejecutar todo. Descarga `WM_precios.csv` para la carpeta `datos/`.

## Fuentes

LSEG Workspace (Refinitiv); Yahoo Finance (precios diarios para GARCH); Alpaca (paper trading); caso "Molson Coors Brewing Co.: Valuing a Convertible Bond"
(NE90-06-107); J. Hull, *Options, Futures and Other Derivatives*, cap. 23; K. Tsiveriotis y C. Fernandes (1998),
"Valuing Convertible Bonds with Credit Risk", *Journal of Fixed Income*.

## Uso de inteligencia artificial

Se usó Claude (Anthropic) para revisar la coherencia entre notebook, reporte y dashboard, recalcular el motor de valuación,
ejecutar el notebook de Colab (`notebooks/WM_GARCH_Derivados_ejecutado.ipynb`, datos de Yahoo hasta el 02-nov-2026),
tomar las capturas de LSEG del 03-nov-2026 y corregir la redacción. Los datos, modelos y decisiones son del equipo.
