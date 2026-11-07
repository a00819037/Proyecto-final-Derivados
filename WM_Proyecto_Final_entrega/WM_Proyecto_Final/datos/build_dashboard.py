import json, datetime
mkt = json.load(open('/home/claude/dash/mkt.json'))
mac = json.load(open('/home/claude/dash/macro.json'))
motor = open('/home/claude/wm_final/calculadora/motor.js', encoding='utf-8').read().split('if (typeof module')[0]
ust = mac['ust']; L = lambda k: ust[k][-1][1]
irx, tnx = L('^IRX'), L('^TNX')
mats = [2028.54, 2029.04, 2029.12, 2029.42, 2030.12, 2030.2, 2031.2, 2031.5, 2032.2, 2032.29, 2032.37, 2033.12, 2034.12, 2035.16, 2035.2, 2039.91, 2041.42, 2045.16, 2049.54, 2050.87, 2054.79]
D = dict(
  mkt=mkt, mac=mac,
  bonds=dict(cup=[7.00, 3.88, 4.88, 2.00, 4.63, 4.65, 1.50, 4.95, 4.80, 4.15, 7.75, 4.63, 4.88, 3.90, 4.95, 6.13, 2.95, 4.10, 4.15, 2.50, 5.35],
             t=[round(m - 2026.8, 1) for m in mats],
             ytm=[5.256, 5.149, 5.135, 5.187, 5.276, 5.238, 5.332, 5.331, 5.409, 5.383, 5.866, 5.454, 5.509, 5.751, 5.633, 5.870, 5.953, 6.007, 6.108, 5.991, 6.040]),
  curve=dict(t=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30], y=[5.363, 5.292, 5.350, 5.454, 5.559, 5.649, 5.722, 5.783, 5.838, 5.886, 5.967, 6.060, 6.145, 6.170, 6.164]),
  iv=dict(k=[170, 175, 180, 185, 190, 195, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320],
          v=[28.1390, 27.8401, 27.3338, 26.8558, 26.5135, 26.5080, 26.4654, 25.0615, 25.3394, 24.4515, 24.1535, 23.7319, 23.3327, 23.3120, 22.5082, 22.7453, 22.4926, 22.3048, 22.4595]),
  mat={'2026': 1800, '2027': 2000, '2028': 2000, '2029': 2100, '2030': 1700, 'Después': 13500},
  sec=dict(y=['2021', '2022', '2023', '2024', '2025'], rev=[17931, 19698, 20426, 22063, 25204], ebitda=[4964, 5403, 5646, 6330, 7171], ni=[1816, 2238, 2304, 2746, 2708], intpaid=[387, 348, 447, 530, 927]),
)
html = r'''<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WM · Convertible con call spread</title>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.1/plotly.min.js"></script>
<style>
:root{--ink:#14262B;--deep:#0F3B3A;--teal:#127A72;--mint:#E3F1EE;--amber:#D48A1E;--sand:#F7F4EE;--paper:#FFFFFF;--line:#E4E1D8;--muted:#62706F;--red:#B5452F;--blue:#2F5C8A}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}
body{font-family:Inter,system-ui,sans-serif;background:var(--sand);color:var(--ink);font-size:14.5px;line-height:1.6}
.num{font-family:"JetBrains Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}
h1,h2,h3{font-family:Newsreader,Georgia,serif;font-weight:600;letter-spacing:-.01em}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
/* hero */
.hero{background:var(--deep);color:#EAF4F1;padding:34px 0 30px;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;right:-120px;top:-120px;width:420px;height:420px;border-radius:50%;border:60px solid rgba(255,255,255,.04)}
.eyebrow{font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:#9CC9C0;font-weight:600}
.hero h1{font-size:34px;line-height:1.15;margin:8px 0 10px;max-width:820px}
.hero .q{font-size:16px;color:#CFE3DE;max-width:760px}
.verdict{display:inline-flex;align-items:center;gap:10px;margin-top:18px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);padding:8px 14px;border-radius:999px;font-weight:600}
.verdict i{width:10px;height:10px;border-radius:50%;background:#5DD3A6;display:inline-block}
.team{font-size:12.5px;color:#9CC9C0;margin-top:16px}
.big{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(255,255,255,.12);margin-top:26px;border-radius:12px;overflow:hidden}
.big div{background:var(--deep);padding:16px 18px}.big span{display:block;font-size:11.5px;color:#9CC9C0;letter-spacing:.06em;text-transform:uppercase}
.big b{font-family:"JetBrains Mono",monospace;font-size:26px;color:#fff;font-weight:500}.big em{font-style:normal;font-size:12.5px;color:#CFE3DE;display:block}
/* nav */
nav{position:sticky;top:0;z-index:20;background:rgba(247,244,238,.94);backdrop-filter:blur(6px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;gap:4px;overflow-x:auto;padding:8px 24px}
nav a{white-space:nowrap;font-size:12.5px;color:var(--muted);text-decoration:none;padding:6px 10px;border-radius:6px}
nav a b{font-family:"JetBrains Mono",monospace;color:var(--amber);margin-right:5px;font-weight:500}
nav a:hover,nav a.on{background:var(--mint);color:var(--deep)}
/* chapters */
section.ch{padding:40px 0 10px}
.chh{display:grid;grid-template-columns:76px 1fr;gap:6px 18px;align-items:start;margin-bottom:18px}
.chh .n{font-family:"JetBrains Mono",monospace;font-size:34px;color:var(--amber);line-height:1}
.chh h2{font-size:27px;color:var(--deep);line-height:1.2}.chh p{grid-column:2;color:var(--muted);max-width:820px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:18px 20px;min-width:0}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.g2>*,.g3>*,.g4>*{min-width:0}
.kp span{display:block;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}.kp b{font-family:"JetBrains Mono",monospace;font-size:23px;color:var(--deep);font-weight:500}.kp em{display:block;font-style:normal;font-size:12px;color:var(--muted)}
.callout{border-left:4px solid var(--amber);background:#FFF8EC;padding:14px 18px;border-radius:0 10px 10px 0}
.callout.t{border-color:var(--teal);background:var(--mint)}
.src{font-size:11.5px;color:var(--muted);margin-top:8px}
.plot{height:310px}.plot.s{height:270px}
table{width:100%;border-collapse:collapse;font-size:13.5px}th{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;text-align:left;border-bottom:1px solid var(--line);padding:6px 8px}
td{padding:8px;border-bottom:1px solid var(--line)}td.r,th.r{text-align:right}tr.hl td{background:#FFF4E2}
/* flow */
.flow{display:grid;grid-template-columns:1fr 70px 1.1fr 70px 1.3fr;align-items:center;gap:0}
.node{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:14px 16px}.node h4{font-size:13px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.node b{font-family:"JetBrains Mono",monospace;font-size:21px;color:var(--deep);font-weight:500}.node.c{background:var(--deep);color:#fff;border-color:var(--deep)}.node.c h4{color:#9CC9C0}.node.c b{color:#fff}
.arr{height:2px;background:var(--amber);position:relative;margin:0 6px}.arr:after{content:"";position:absolute;right:-1px;top:-5px;border-left:9px solid var(--amber);border-top:6px solid transparent;border-bottom:6px solid transparent}
.uses div{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px dashed var(--line)}.uses div:last-child{border:0}
/* lab */
.lab{display:grid;grid-template-columns:320px 1fr;gap:16px}
.ctl label{display:block;margin:10px 0 2px;font-size:12.5px;color:var(--muted)}.ctl label b{float:right;font-family:"JetBrains Mono",monospace;color:var(--deep);font-weight:500}
input[type=range]{width:100%;accent-color:var(--teal)}
.out{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.pill{display:inline-block;font-size:11.5px;font-weight:600;padding:3px 10px;border-radius:999px;background:var(--mint);color:var(--deep)}.pill.a{background:#FFF0D6;color:#8A5300}.pill.r{background:#F8E1DB;color:var(--red)}
.risk{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.risk .card h3{font-size:17px;color:var(--deep);margin:6px 0}
.ev a{color:var(--teal);font-weight:500}
footer{margin-top:40px;background:var(--ink);color:#B8C7C4;font-size:12.5px;padding:26px 0}
footer a{color:#E3F1EE}
@media(max-width:900px){.big,.g4{grid-template-columns:repeat(2,1fr)}.g2,.g3,.risk,.lab,.out{grid-template-columns:1fr}.flow{grid-template-columns:1fr}.arr{height:24px;width:2px;margin:6px auto}.arr:after{right:-5px;top:auto;bottom:-2px;border-left:6px solid transparent;border-right:6px solid transparent;border-top:9px solid var(--amber);border-bottom:0}.hero h1{font-size:26px}.chh{grid-template-columns:1fr}.chh p{grid-column:1}}
</style></head><body>
<header class="hero"><div class="wrap">
<div class="eyebrow">Proyecto final · Waste Management, Inc. (NYSE: WM) · caso Molson Coors aplicado</div>
<h1>¿Debe WM emitir un bono convertible con call spread para refinanciar su deuda cara?</h1>
<p class="q">WM paga 6.83% promedio en tres bonos (USD 647.2 mm). Proponemos emitir USD 750 mm en un convertible a 6 años, recomprar esos bonos y comprar un call spread que empuja la dilución hasta una prima de 60%.</p>
<div class="verdict"><i></i>Recomendación: emitir, con condiciones</div>
<div class="big">
<div><span>Cupón a la par</span><b>2.41%</b><em>vs. 5.65% del bono directo</em></div>
<div><span>Ahorro de intereses</span><b>$26.2M</b><em>al año, antes de impuestos</em></div>
<div><span>Costo del call spread</span><b>$54.4M</b><em>7.3% del principal</em></div>
<div><span>Dilución empieza en</span><b>$367</b><em>+60% sobre $229.58</em></div>
</div>
<div class="team">Tania Manuela López Suárez · Mauricio Martínez García · Ricardo Terrazas Duque — Productos derivados y administración de riesgos corporativos (Gpo 40) · Dr. Raymundo Díaz Robles · 3-nov-2026</div>
</div></header>
<nav><div class="wrap">
<a href="#c1"><b>01</b>El problema</a><a href="#c2"><b>02</b>La propuesta</a><a href="#c3"><b>03</b>Cuánto vale</a><a href="#c4"><b>04</b>Volatilidad</a><a href="#c5"><b>05</b>Call spread</a><a href="#c6"><b>06</b>Impacto en WM</a><a href="#c7"><b>07</b>Cobertura de tasa</a><a href="#c8"><b>08</b>Riesgos</a><a href="#c9"><b>09</b>Contexto</a><a href="#c10"><b>10</b>Evidencia</a>
</div></nav>
<main class="wrap">

<section class="ch" id="c1"><div class="chh"><div class="n">01</div><h2>El problema: deuda cara y sin cobertura de tasa</h2>
<p>WM tiene una calificación A- y una cobertura de intereses holgada, pero carga bonos emitidos cuando las tasas eran otras. Su 10-K 2025 confirma que hoy casi no usa derivados para cubrir tasa.</p></div>
<div class="g4">
<div class="card kp"><span>Bonos de cupón alto</span><b>$647.2M</b><em>7.00% 2028 · 7.75% 2032 · 6.125% 2039</em></div>
<div class="card kp"><span>Vencen 2026–2030</span><b>$9.6B</b><em>10-K 2025, calendario de principal</em></div>
<div class="card kp"><span>+100 pb en tasas</span><b>+$35M</b><em>de intereses al año (Item 7A)</em></div>
<div class="card kp"><span>Derivados vigentes</span><b>Inmateriales</b><em>al 31-dic-2025 (Item 7A)</em></div>
</div>
<div class="g2" style="margin-top:16px">
<div class="card"><div id="p-bonds" class="plot"></div><p class="src">LSEG Issuer Curve 0#WMUSDABMK=, cotizaciones del 21-oct-2026. En ámbar, los tres bonos a recomprar; el tamaño del punto es el cupón.</p></div>
<div class="card"><div id="p-mat" class="plot"></div><p class="src">SEC EDGAR, 10-K 2025 (vencimientos de principal) · intereses pagados: estado de flujos (XBRL).</p></div>
</div>
<div class="callout" style="margin-top:16px"><b>Lectura:</b> la curva de WM a 6 años rinde 5.649%. Refinanciar con deuda directa ahorraría poco frente al 6.83% promedio de los bonos viejos, y los intereses pagados subieron de USD 530 mm (2024) a USD 927 mm (2025). Un instrumento que baje el cupón sin subir el apalancamiento resuelve justo esa tensión.</div>
</section>

<section class="ch" id="c2"><div class="chh"><div class="n">02</div><h2>La propuesta: convertible + recompra + call spread</h2>
<p>Igual que Molson Coors en 2007 (USD 575 mm, cupón 2.5%, prima 25%, warrants al 60%), adaptado a WM con datos de LSEG al 21-oct-2026.</p></div>
<div class="flow">
<div class="node"><h4>Inversionistas</h4><b>$750M</b><div style="font-size:12.5px;color:var(--muted)">Convertible senior, 6 años, prima 25% · 3.4846 acciones por bono</div></div>
<div class="arr"></div>
<div class="node c"><h4>Waste Management</h4><b>Cupón ≈ 2.41%</b><div style="font-size:12.5px;color:#CFE3DE">Conversión a $286.98 · dilución económica desde $367.33</div></div>
<div class="arr"></div>
<div class="node uses"><h4>Uso de los fondos (USD mm)</h4>
<div><span>Tender de 3 bonos (ask + 1 pt)</span><b class="num">679.4</b></div><div><span>Call spread neto</span><b class="num">54.4</b></div><div><span>Comisión (supuesto 2%)</span><b class="num">15.0</b></div><div><span>Remanente de caja</span><b class="num">1.3</b></div></div>
</div>
<div class="g2" style="margin-top:16px">
<div class="card"><div id="p-wf" class="plot s"></div></div>
<div class="card"><h3 style="font-size:18px;color:var(--deep);margin-bottom:8px">Cómo funciona el call spread</h3>
<table><tr><th>Pierna</th><th class="r">Strike</th><th class="r">USD mm</th></tr>
<tr><td>WM compra calls (note hedge, vol 22.75%)</td><td class="r num">$286.98</td><td class="r num">−114.4</td></tr>
<tr><td>WM vende warrants (vol 21.04%)</td><td class="r num">$367.33</td><td class="r num">+60.0</td></tr>
<tr class="hl"><td><b>Costo neto</b></td><td></td><td class="r num"><b>−54.4</b></td></tr></table>
<p style="margin-top:10px">Entre $287 y $367 lo que WM entrega en acciones lo paga el banco; arriba de $367 los warrants diluyen. La prima efectiva sube de 25% a 60% por 7.3% del principal (Molson pagó 8.6%).</p></div>
</div>
</section>

<section class="ch" id="c3"><div class="chh"><div class="n">03</div><h2>Cuánto vale: convertible = bono recto + opción</h2>
<p>No hay free lunch: el cupón bajo existe porque WM vende a los inversionistas una opción. Mueve los supuestos y observa el precio de cada mejora.</p></div>
<div class="g2">
<div class="card"><div id="p-dec" class="plot s"></div><p class="src">Black-Scholes-Merton con dividendo de 1.63%; bono recto descontado a la YTM de WM (5.649%).</p></div>
<div class="card"><div id="p-cup" class="plot s"></div><p class="src">El caso base es el árbol Tsiveriotis-Fernandes (360 pasos): conversión anticipada y riesgo de crédito separado.</p></div>
</div>
<div class="lab" style="margin-top:16px">
<div class="card ctl"><h3 style="font-size:18px;color:var(--deep)">Laboratorio de escenarios</h3>
<label>Prima de conversión <b id="lv1">25%</b></label><input id="s1" type="range" min="15" max="40" step="1" value="25">
<label>Volatilidad de la conversión <b id="lv2">22.75%</b></label><input id="s2" type="range" min="16" max="30" step="0.25" value="22.75">
<label>Prima del warrant <b id="lv3">60%</b></label><input id="s3" type="range" min="40" max="100" step="5" value="60">
<label>Volatilidad del warrant <b id="lv4">21.04%</b></label><input id="s4" type="range" min="16" max="30" step="0.01" value="21.04">
<button id="rst" style="margin-top:14px;padding:7px 12px;border:1px solid var(--teal);background:#fff;color:var(--teal);border-radius:8px;cursor:pointer;font:inherit">Volver al caso base</button>
<p class="src">Mismo motor que la calculadora (árbol T-F de 120 pasos para responder rápido; el caso base del reporte usa 360).</p></div>
<div><div class="out">
<div class="card kp"><span>Cupón a la par (T-F)</span><b id="o1">–</b><em id="o1b"></em></div>
<div class="card kp"><span>Call spread neto</span><b id="o2">–</b><em id="o2b"></em></div>
<div class="card kp"><span>Opción por bono</span><b id="o3">–</b><em>valor que WM vende</em></div></div>
<div class="card" style="margin-top:12px"><div id="p-heat" class="plot s"></div></div></div>
</div>
</section>

<section class="ch" id="c4"><div class="chh"><div class="n">04</div><h2>¿Es cara la volatilidad que WM vende?</h2>
<p>Las opciones listadas llegan a ene-2029 y el convertible dura 6 años. Con GARCH(1,1) estimamos la volatilidad de largo plazo y la comparamos con la implícita.</p></div>
<div class="g2">
<div class="card"><div id="p-vol" class="plot"></div><p class="src">GARCH(1,1) por máxima verosimilitud (α = 0.135, β = 0.539) y EWMA (λ = 0.94), precios diarios de Yahoo Finance.</p></div>
<div class="card"><div id="p-smile" class="plot"></div><p class="src">LSEG Option Watch (OPW), calls WM 19-ene-2029, 21-oct-2026.</p></div>
</div>
<div class="g3" style="margin-top:16px">
<div class="card kp"><span>GARCH promedio 6 años</span><b>19.7%</b><em>persistencia α+β = 0.68; choques duran ~2 días</em></div>
<div class="card kp"><span>Implícita usada</span><b>22.75%</b><em>strike 290 ≈ precio de conversión</em></div>
<div class="card kp"><span>Razón GARCH / implícita</span><b>0.87</b><em><span class="pill">Señal: emitir</span> umbral 0.90</em></div>
</div>
<div class="callout t" style="margin-top:16px">El mercado paga la volatilidad más cara de lo que GARCH espera, y WM es quien la vende al emitir. Aun con la volatilidad GARCH (19.7%) el cupón sería 2.85%, 280 pb abajo del bono directo. Back testing del VaR: pasa al 95%; al 99% falla por poco (p = 0.049), señal de colas pesadas.</div>
</section>

<section class="ch" id="c5"><div class="chh"><div class="n">05</div><h2>El call spread: dilución, griegas y escenarios</h2>
<p>El call spread no elimina la dilución: la pospone. Su valor depende sobre todo de la volatilidad pactada en cada pierna.</p></div>
<div class="g3">
<div class="card"><div id="p-dil" class="plot s"></div></div>
<div class="card"><div id="p-gr" class="plot s"></div></div>
<div class="card"><div id="p-esc" class="plot s"></div></div>
</div>
<div class="g4" style="margin-top:16px">
<div class="card kp"><span>P(S &gt; $287 en 6 años)</span><b>62.3%</b><em>Monte Carlo GARCH, μ = 8% supuesto</em></div>
<div class="card kp"><span>P(S &gt; $367 en 6 años)</span><b>42.5%</b><em>los warrants diluyen</em></div>
<div class="card kp"><span>Dilución esperada</span><b>$307M → $198M</b><em>sin → con call spread</em></div>
<div class="card kp"><span>Griegas netas (WM)</span><b>Δ 0.47</b><em>mm acciones · Γ −0.0005 · vega 0.04</em></div>
</div>
</section>

<section class="ch" id="c6"><div class="chh"><div class="n">06</div><h2>Impacto en WM</h2>
<p>La operación baja el gasto por intereses sin mover el apalancamiento. Parte del ahorro es contable: a valor justo es cercana a VPN cero.</p></div>
<div class="g2">
<div class="card"><table><tr><th>Métrica</th><th class="r">Antes</th><th class="r">Después</th></tr>
<tr><td>Deuda total (USD mm)</td><td class="r num">23,356</td><td class="r num">23,459</td></tr>
<tr><td>Deuda / EBITDA</td><td class="r num">2.98x</td><td class="r num">2.99x</td></tr>
<tr><td>EBITDA / intereses</td><td class="r num">8.65x</td><td class="r num">8.91x</td></tr>
<tr><td>Cupones anuales de estos bonos (USD mm)</td><td class="r num">44.2</td><td class="r num">18.1</td></tr>
<tr class="hl"><td>Ahorro anual antes / después de impuestos</td><td class="r num" colspan="2">$26.2M / $20.7M</td></tr>
<tr><td>Acciones potenciales por conversión</td><td class="r num">–</td><td class="r num">2.61 mm (0.65%)</td></tr></table>
<p class="src">Métricas con EBITDA e intereses LTM implícitos en los ratios de LSEG (21-oct-2026); tasa de impuestos de 21% supuesta.</p></div>
<div class="card"><div id="p-peer" class="plot s"></div><p class="src">LSEG Key Ratios LTM: WM al 21-oct-2026; RSG y WCN al 28-oct-2026.</p></div>
</div>
<div class="card" style="margin-top:16px"><h3 style="font-size:18px;color:var(--deep);margin-bottom:8px">¿Por qué convertible y no deuda directa o acciones?</h3>
<div style="overflow-x:auto"><table style="min-width:620px"><tr><th>Mismos USD 750 mm vía…</th><th class="r">Convertible + call spread</th><th class="r">Deuda directa 6 años</th><th class="r">Emisión de acciones</th></tr>
<tr><td>Costo anual en efectivo (USD mm)</td><td class="r num">18.1 (2.41%)</td><td class="r num">42.4 (5.65%)</td><td class="r num">12.2 (div. 1.63%)</td></tr>
<tr class="hl"><td>Ahorro anual vs. cupones eliminados de 44.2</td><td class="r num"><b>26.2</b></td><td class="r num">1.9</td><td class="r num">32.0</td></tr>
<tr><td>Deuda / EBITDA después</td><td class="r num">2.99x</td><td class="r num">2.99x</td><td class="r num">2.90x</td></tr>
<tr><td>Acciones nuevas o potenciales</td><td class="r num">2.61 mm (0.65%)</td><td class="r num">0</td><td class="r num">3.27 mm (0.82%)</td></tr>
<tr><td>Cuándo diluye</td><td class="r">Solo arriba de $367</td><td class="r">Nunca</td><td class="r">Inmediato</td></tr>
<tr><td>Costo inicial adicional (USD mm)</td><td class="r num">54.4</td><td class="r num">0</td><td class="r num">0</td></tr></table></div>
<p class="src">La deuda directa casi no ahorra. En acciones, el dividendo subestima el costo real: los accionistas exigen un rendimiento mayor que la deuda, y la emisión suele leerse como señal de acción cara. Cálculo en el reporte R Markdown, sección 14.</p></div>
</section>

<section class="ch" id="c7"><div class="chh"><div class="n">07</div><h2>Cobertura de tasa del tender</h2>
<p>Si las tasas bajan antes de fijar el precio del tender, los bonos a recomprar suben y la operación deja de autofinanciarse. Medimos la exposición (DV01) y dimensionamos la cobertura.</p></div>
<div class="g4">
<div class="card kp"><span>DV01 de la canasta</span><b>$339,562</b><em>por punto base (precios ask 21-oct-2026)</em></div>
<div class="card kp"><span>−25 pb en tasas</span><b>+$8.5M</b><em>de costo del tender</em></div>
<div class="card kp"><span>Baja que borra el remanente</span><b>4 pb</b><em>remanente de solo $1.3M</em></div>
<div class="card kp"><span>T-lock por nodos</span><b>$677M</b><em>2, 5 y 10 años · WM gana si bajan las tasas</em></div>
</div>
<div class="g2" style="margin-top:16px">
<div class="card"><div id="p-dv01" class="plot s"></div><p class="src">Duración modificada con YTM implícita en el precio ask (LSEG, 21-oct-2026), liquidación 23-oct-2026, 30/360.</p></div>
<div class="card"><h3 style="font-size:18px;color:var(--deep);margin-bottom:8px">Tamaño de la cobertura por instrumento</h3>
<div style="overflow-x:auto"><table style="min-width:440px"><tr><th>Bono</th><th class="r">T-lock (USD mm)</th><th class="r">Futuros*</th><th class="r">Swap recibe fijo</th></tr>
<tr><td>7.00% 2028</td><td class="r num">2a: 227.1</td><td class="r num">1,111 TU</td><td class="r num">226.7</td></tr>
<tr><td>7.75% 2032</td><td class="r num">5a: 161.0</td><td class="r num">1,843 FV</td><td class="r num">159.8</td></tr>
<tr><td>6.125% 2039</td><td class="r num">10a: 289.1</td><td class="r num">2,738 TN</td><td class="r num">283.8</td></tr>
<tr class="hl"><td><b>Total</b></td><td class="r num"><b>677.3</b></td><td></td><td class="r num">670.3</td></tr></table></div>
<p class="src">Treasuries benchmark, swap spreads (2a −14.5, 5a −28.4, 10a −39.4 pb), futuros dic-2026 y CTD: LSEG Rates View, 03-nov-2026. *Contratos aproximados: DV01 del CTD / factor de conversión estimado.</p></div>
</div>
<div class="callout t" style="margin-top:16px"><b>Recomendación:</b> T-lock por nodos desde el anuncio hasta el <i>pricing</i> del tender. Si el tender se fija como spread sobre un Treasury de referencia, el T-lock cubre casi exactamente ese riesgo. Los futuros son líquidos pero piden margen diario y su número es aproximado; los swaps dejan riesgo de base porque los swap spreads son negativos y cambian por plazo. Es la posición contraria al T-lock típico de un emisor (en Molson Coors el T-lock dejó una ganancia de USD 1.4 mm).</div>
</section>

<section class="ch" id="c8"><div class="chh"><div class="n">08</div><h2>Riesgos y condiciones</h2><p>La recomendación se sostiene si se cumplen tres condiciones y se cubre la tasa del tender.</p></div>
<div class="risk">
<div class="card"><span class="pill a">Condición 1</span><h3>No bajar la prima de 25%</h3><p>Con 20% el cupón baja 41 pb, pero la conversión empieza antes. Con 30% cuesta 37 pb más de cupón.</p></div>
<div class="card"><span class="pill a">Condición 2</span><h3>Negociar la vol. del warrant</h3><p>Cada punto de volatilidad del warrant mueve su valor en cerca de USD 5.1 mm: el costo neto depende de la volatilidad pactada.</p></div>
<div class="card"><span class="pill a">Condición 3</span><h3>Cuidar el remanente</h3><p>Sobran solo USD 1.3 mm; con una comisión de 2.2% en lugar de 2% ya sería negativo.</p></div>
<div class="card"><span class="pill r">Tasa</span><h3>La curva se mueve</h3><p>Entre el 21-oct y el 3-nov la curva de WM bajó. Cada pb de baja encarece el tender en USD 340 mil: cubrir con T-lock por nodos (capítulo 07).</p></div>
<div class="card"><span class="pill r">Contraparte</span><h3>El banco del note hedge</h3><p>Elegir contraparte A o mejor, con ISDA y colateral.</p></div>
<div class="card"><span class="pill r">Contable</span><h3>ASU 2020-06</h3><p>El convertible es un solo pasivo y la dilución contable se mide con if-converted: el call spread solo cubre la dilución económica.</p></div>
</div>
</section>

<section class="ch" id="c9"><div class="chh"><div class="n">09</div><h2>Contexto: la empresa y el entorno de tasas</h2>
<p>Emisor defensivo (beta 0.39), con ingresos recurrentes y deuda casi toda en dólares: su exposición macro es a la curva del Tesoro, no al tipo de cambio.</p></div>
<div class="g4">
<div class="card kp"><span>Último cierre</span><b>$__LAST__</b><em>__LASTD__ · YTD __YTD__%</em></div>
<div class="card kp"><span>Ingresos LTM</span><b>$26.07B</b><em>margen neto 12.21% (LSEG)</em></div>
<div class="card kp"><span>Calificación</span><b>A- / A-</b><em>S&amp;P / Fitch · Moody's A3 (respaldada)</em></div>
<div class="card kp"><span>Treasury 10 años</span><b>__TNX__%</b><em>T-Bill 13s __IRX__% · Yahoo</em></div>
</div>
<div class="g3" style="margin-top:16px">
<div class="card"><div id="p-px" class="plot s"></div></div>
<div class="card"><div id="p-fin" class="plot s"></div></div>
<div class="card"><div id="p-ust" class="plot s"></div></div>
</div>
<p class="src">Yahoo Finance (precio, medias móviles y Treasuries) · SEC EDGAR 10-K (ingresos, EBITDA = EBIT + D&amp;A, utilidad neta) · PIB EE.UU. 2025: __GDP__%, desempleo __UNEMP__% (World Bank).</p>
</section>

<section class="ch" id="c10"><div class="chh"><div class="n">10</div><h2>Evidencia y entregables</h2><p>Todo el análisis es reproducible y cada cifra tiene fuente.</p></div>
<div class="g3 ev">
<div class="card"><h3 style="font-size:17px;color:var(--deep)">Análisis</h3><p><a href="WM_Proyecto_Final.html">Reporte R Markdown</a> (código visible)<br><a href="reporte_ejecutivo/WM_Reporte_Ejecutivo.pdf">Reporte ejecutivo</a> · <a href="reporte_ejecutivo/WM_Reporte_Ejecutivo.docx">Word</a><br><a href="calculadora/WM_Calculadora_Convertible.html">Calculadora interactiva</a><br><a href="presentacion/WM_Presentacion.html">Presentación</a></p></div>
<div class="card"><h3 style="font-size:17px;color:var(--deep)">Código y datos</h3><p><a href="notebooks/WM_GARCH_Derivados_ejecutado.ipynb">Notebook de Colab ejecutado</a> · <a href="notebooks/WM_GARCH_Derivados.py">.py</a><br><a href="notebooks/WM_Volatilidad_GARCH_y_Operacion_Alpaca.ipynb">Operación en Alpaca</a><br><a href="datos/">Datos</a> · <a href="README.md">README</a> · <a href="ia/Nota_uso_IA.pdf">Uso de IA</a></p></div>
<div class="card"><h3 style="font-size:17px;color:var(--deep)">Terminales y ejecución</h3><p><a href="anexo/WM_Anexo_Capturas_LSEG.pdf">Anexo de capturas LSEG</a> (03-nov-2026)<br>Alpaca paper: compra call WM ene-2029 K=290 y venta K=340, límite $9.07 — <span class="pill a">enviada, no ejecutada</span></p></div>
</div>
</section>
</main>
<footer><div class="wrap">Fuentes: LSEG Workspace (21-oct-2026; capturas 03-nov-2026) · SEC EDGAR (10-K 2025, 10-Q 3T-2026, API XBRL) · Yahoo Finance · World Bank · Alpaca · Caso Molson Coors Brewing Co.: Valuing a Convertible Bond (NE90-06-107) · Hull, cap. 13 y 23 · Tsiveriotis y Fernandes (1998). Material académico; no es recomendación de inversión. Versiones anteriores: <a href="dashboard_formato_curso.html">formato del curso</a> · <a href="dashboard_v1.html">primera versión</a></div></footer>
<script>
__MOTOR__
const D=__DATA__;
const C={ink:"#14262B",deep:"#0F3B3A",teal:"#127A72",amber:"#D48A1E",red:"#B5452F",blue:"#2F5C8A",grey:"#A7B2B0"};
const cfg={displayModeBar:false,responsive:true};
function L(t,x){return Object.assign({title:{text:t,font:{family:"Newsreader,Georgia,serif",size:16,color:C.deep},x:0.02},margin:{l:50,r:46,t:46,b:84},font:{family:"Inter,sans-serif",size:11.5,color:C.ink},paper_bgcolor:"#fff",plot_bgcolor:"#fff",legend:{orientation:"h",y:-0.36,x:0},xaxis:{gridcolor:"#EFECE4",zeroline:false},yaxis:{gridcolor:"#EFECE4",zeroline:false}},x||{});}
// 01
const B=D.bonds, hi=B.cup.map(c=>c>=6);
Plotly.newPlot("p-bonds",[{x:D.curve.t,y:D.curve.y,name:"Curva WM (Issuer Curve)",line:{color:C.deep,width:2}},
{x:B.t,y:B.ytm,mode:"markers",name:"Bonos WM",marker:{size:B.cup.map(c=>6+c*2.2),color:hi.map(h=>h?C.amber:"rgba(18,122,114,.45)"),line:{color:"#fff",width:1}},text:B.cup.map(c=>"cupón "+c.toFixed(2)+"%"),hovertemplate:"%{x} años · YTM %{y:.2f}% · %{text}<extra></extra>"}],
L("Bonos de WM: rendimiento vs. plazo",{xaxis:{title:"Años al vencimiento",gridcolor:"#EFECE4",range:[0,30]},yaxis:{title:"YTM (%)",gridcolor:"#EFECE4"}}),cfg);
const mk=Object.keys(D.mat);
Plotly.newPlot("p-mat",[{x:mk,y:mk.map(k=>D.mat[k]/1000),type:"bar",name:"Vencimientos de principal (USD bn)",marker:{color:mk.map(k=>k=="Después"?C.grey:C.teal)},text:mk.map(k=>(D.mat[k]/1000).toFixed(1)),textposition:"outside"}],L("Vencimientos de principal (USD bn)",{xaxis:{type:"category"},yaxis:{range:[0,16],gridcolor:"#EFECE4"},showlegend:false,annotations:[{x:0.5,xref:"paper",y:12,text:"Intereses pagados: $530M (2024) → $927M (2025)",showarrow:false,font:{size:12,color:C.red}}]}),cfg);
// 02 waterfall
Plotly.newPlot("p-wf",[{type:"waterfall",x:["Emisión","Tender","Call spread","Comisión","Remanente"],measure:["absolute","relative","relative","relative","total"],y:[750,-679.4,-54.4,-15,0],text:["750.0","−679.4","−54.4","−15.0","1.3"],textposition:"outside",connector:{line:{color:C.grey}},increasing:{marker:{color:C.teal}},decreasing:{marker:{color:C.amber}},totals:{marker:{color:C.deep}}}],L("Fuentes y usos (USD mm)",{showlegend:false,yaxis:{range:[0,850],gridcolor:"#EFECE4"}}),cfg);
// 03
Plotly.newPlot("p-dec",[{y:["Convertible"],x:[847.42],type:"bar",orientation:"h",name:"Bono recto $847.42",marker:{color:C.deep},text:["Bono recto $847.42"],textposition:"inside"},{y:["Convertible"],x:[152.58],type:"bar",orientation:"h",name:"Opción de conversión $152.58",marker:{color:C.amber},text:["Opción<br>$152.58"],textposition:"inside",insidetextanchor:"middle"}],
L("Un bono de $1,000 = bono recto + opción",{barmode:"stack",showlegend:false,xaxis:{range:[0,1000],title:"USD por bono",gridcolor:"#EFECE4"},yaxis:{showticklabels:false},margin:{l:20,r:20,t:46,b:62}}),cfg);
Plotly.newPlot("p-cup",[{x:["Bono directo<br>WM","Avance<br>B-S sin div.","B-S con<br>dividendo","Árbol T-F<br>(base)","Molson<br>2007"],y:[5.649,1.685,2.615,2.408,2.5],type:"bar",marker:{color:[C.grey,"#7FA9A3","#7FA9A3",C.deep,C.amber]},text:["5.65%","1.69%","2.62%","2.41%","2.50%"],textposition:"outside"}],L("Cupón a la par según el método (%)",{showlegend:false,yaxis:{range:[0,6.6],gridcolor:"#EFECE4"}}),cfg);
const base={S:229.58,T:6,r:(0.049182+0.049954)/2,y:0.05649,q:0.0163,monto:750,N:120};
const ids=["s1","s2","s3","s4"],def=["25","22.75","60","21.04"];
function lab(){const p=Object.assign({},base,{primaConv:+s1.value/100,s:(s2.value=="22.75"?0.227453:+s2.value/100),primaWarr:+s3.value/100,sw:+s4.value/100});const R=calcular(p);
lv1.textContent=s1.value+"%";lv2.textContent=(+s2.value).toFixed(2)+"%";lv3.textContent=s3.value+"%";lv4.textContent=(+s4.value).toFixed(2)+"%";
o1.textContent=(100*R.cuponTF).toFixed(2)+"%";o1b.textContent=((base.y-R.cuponTF)*1e4).toFixed(0)+" pb abajo del bono directo";
o2.textContent="$"+R.neto.toFixed(1)+"M";o2b.textContent=(100*R.netoPct).toFixed(1)+"% del principal · dilución desde $"+R.Kw.toFixed(0);
o3.textContent="$"+R.opcionBono.toFixed(2);
const pr=[15,20,25,30,35,40],vs=[18,20,22,24,26,28],z=vs.map(v=>pr.map(k=>100*calcular(Object.assign({},p,{primaConv:k/100,s:v/100,N:60})).cuponTF));
Plotly.react("p-heat",[{z:z,x:pr.map(k=>k+"%"),y:vs.map(v=>v+"%"),type:"heatmap",colorscale:[[0,"#E3F1EE"],[1,C.deep]],text:z.map(r=>r.map(v=>v.toFixed(2)+"%")),texttemplate:"%{text}",showscale:false,hovertemplate:"prima %{x} · vol %{y}: %{text}<extra></extra>"}],
L("Cupón a la par: prima × volatilidad (T-F 60 pasos)",{xaxis:{type:"category",title:"Prima de conversión"},yaxis:{type:"category",title:"Volatilidad"},margin:{l:70,r:20,t:46,b:56}}),cfg);}
ids.forEach(i=>document.getElementById(i).addEventListener("input",lab));rst.onclick=()=>{ids.forEach((i,j)=>document.getElementById(i).value=def[j]);lab();};lab();
// 04
const V=D.mkt.vol;
Plotly.newPlot("p-vol",[{x:V.d,y:V.g,name:"GARCH(1,1)",line:{color:C.deep,width:1.2}},{x:V.d,y:V.e,name:"EWMA 0.94",line:{color:C.amber,width:1}},{x:[V.d[0],V.d[V.d.length-1]],y:[19.66,19.66],name:"Largo plazo 19.7%",line:{color:C.teal,dash:"dash",width:2}},{x:[V.d[0],V.d[V.d.length-1]],y:[22.75,22.75],name:"Implícita 22.75%",line:{color:C.red,dash:"dot",width:2}}],L("Volatilidad condicional de WM (% anual)"),cfg);
Plotly.newPlot("p-smile",[{x:D.iv.k,y:D.iv.v,mode:"lines+markers",name:"Volatilidad implícita",line:{color:C.deep,width:2}}],L("Sonrisa de volatilidad, calls ene-2029",{showlegend:false,xaxis:{title:"Strike (USD)",gridcolor:"#EFECE4"},yaxis:{title:"Vol. implícita (%)",gridcolor:"#EFECE4"},shapes:[{type:"line",x0:229.58,x1:229.58,yref:"paper",y0:0,y1:1,line:{color:C.grey,dash:"dash"}},{type:"line",x0:286.98,x1:286.98,yref:"paper",y0:0,y1:1,line:{color:C.amber,dash:"dash"}}],annotations:[{x:229.58,y:1,yref:"paper",text:"precio",showarrow:false,yanchor:"bottom",font:{size:11,color:C.muted}},{x:286.98,y:1,yref:"paper",text:"conversión",showarrow:false,yanchor:"bottom",font:{size:11,color:C.amber}}]}),cfg);
// 05
const K=229.58*1.25,Kw=229.58*1.6,A=750/K,r=base.r,q=base.q;let xs=[],a=[],b=[],dl=[],vg=[],mtm=[],pay=[];
for(let s=120;s<=520;s+=4){const c=bsCall(s,K,r,0.227453,6,q),w=bsCall(s,Kw,r,0.2104,6,q);xs.push(s);a.push(A*Math.max(s-K,0));b.push(A*Math.max(s-Kw,0));dl.push(A*(c.delta-w.delta));vg.push(A*(c.vega-w.vega));mtm.push(A*(c.precio-w.precio));pay.push(A*(Math.max(s-K,0)-Math.max(s-Kw,0))-54.389);}
const vl={type:"line",x0:229.58,x1:229.58,yref:"paper",y0:0,y1:1,line:{color:C.grey,dash:"dash",width:1}};
Plotly.newPlot("p-dil",[{x:xs,y:a,name:"Sin call spread",line:{color:C.red,width:2}},{x:xs,y:b,name:"Con call spread",line:{color:C.teal,width:2}}],L("Dilución al vencimiento (USD mm)",{xaxis:{title:"Precio de WM (USD)",gridcolor:"#EFECE4"},shapes:[vl]}),cfg);
Plotly.newPlot("p-gr",[{x:xs,y:dl,name:"Delta neta",line:{color:C.deep,width:2}},{x:xs,y:vg,name:"Vega neta",yaxis:"y2",line:{color:C.amber,width:2,dash:"dot"}}],L("Griegas netas del call spread",{xaxis:{title:"Precio de WM (USD)",gridcolor:"#EFECE4"},yaxis:{title:"Δ (mm acc.)",gridcolor:"#EFECE4"},yaxis2:{title:"Vega",overlaying:"y",side:"right",showgrid:false},shapes:[vl]}),cfg);
Plotly.newPlot("p-esc",[{x:xs,y:mtm,name:"Valor hoy",line:{color:C.blue,width:2}},{x:xs,y:pay,name:"Pago al vencimiento − costo",line:{color:C.teal,width:2}}],L("Valor del call spread (USD mm)",{xaxis:{title:"Precio de WM (USD)",gridcolor:"#EFECE4"},yaxis:{gridcolor:"#EFECE4",zeroline:true,zerolinecolor:C.grey},shapes:[vl]}),cfg);
// 06
Plotly.newPlot("p-peer",[{x:["WM","RSG","WCN"],y:[2.98,2.58,2.90],type:"bar",name:"Deuda/EBITDA",offsetgroup:1,marker:{color:[C.deep,C.grey,C.grey]}},{x:["WM","RSG","WCN"],y:[8.65,9.23,9.00],type:"bar",name:"EBITDA/intereses",offsetgroup:2,marker:{color:[C.amber,"#E7CFA4","#E7CFA4"]},yaxis:"y2"}],
L("WM: más apalancada y con menor cobertura que sus pares",{barmode:"group",yaxis:{title:"Deuda/EBITDA (x)",gridcolor:"#EFECE4",range:[0,3.6]},yaxis2:{title:"EBITDA/intereses (x)",overlaying:"y",side:"right",showgrid:false,range:[0,11]}}),cfg);
// 07
const dvb=[42918,70897,225748],bps=[0,10,25,50,100];
Plotly.newPlot("p-dv01",[{x:["7% 2028","7¾% 2032","6⅛% 2039"],y:dvb.map(v=>v/1000),type:"bar",name:"DV01 (miles USD/pb)",marker:{color:[C.teal,C.teal,C.deep]},text:dvb.map(v=>"$"+(v/1000).toFixed(1)+"k"),textposition:"outside"},
{x:bps.map(b=>"−"+b+" pb"),y:bps.map(b=>339562*b/1e6),xaxis:"x2",yaxis:"y2",type:"scatter",mode:"lines+markers",name:"Costo extra del tender (USD mm)",line:{color:C.red,width:2}}],
L("DV01 por bono y costo extra si bajan las tasas",{grid:{rows:1,columns:2,pattern:"independent"},showlegend:false,xaxis:{domain:[0,0.46],type:"category"},yaxis:{title:"miles USD por pb",gridcolor:"#EFECE4",range:[0,270]},xaxis2:{domain:[0.58,1],type:"category"},yaxis2:{anchor:"x2",title:"USD mm",gridcolor:"#EFECE4"},margin:{l:50,r:20,t:46,b:60}}),cfg);
// 09
const P=D.mkt.px;
Plotly.newPlot("p-px",[{x:P.d,y:P.p,name:"Precio",line:{color:C.deep,width:1.4}},{x:P.d,y:P.m50,name:"MA 50",line:{color:C.amber,width:1.2,dash:"dot"}},{x:P.d,y:P.m200,name:"MA 200",line:{color:C.teal,width:1.2,dash:"dash"}}],L("Precio de WM, 3 años (USD)"),cfg);
const S=D.sec;
Plotly.newPlot("p-fin",[{x:S.y,y:S.rev.map(v=>v/1000),type:"bar",name:"Ingresos",marker:{color:C.deep}},{x:S.y,y:S.ebitda.map(v=>v/1000),type:"bar",name:"EBITDA",marker:{color:C.teal}},{x:S.y,y:S.ni.map(v=>v/1000),type:"bar",name:"Utilidad neta",marker:{color:C.amber}}],L("Finanzas anuales (USD bn) · 10-K",{barmode:"group",xaxis:{type:"category"}}),cfg);
const U=D.mac.ust,nm={"^IRX":"13 semanas","^FVX":"5 años","^TNX":"10 años","^TYX":"30 años"},cl={"^IRX":C.grey,"^FVX":C.teal,"^TNX":C.deep,"^TYX":C.amber};
Plotly.newPlot("p-ust",Object.keys(nm).map(k=>({x:U[k].map(p=>p[0]),y:U[k].map(p=>p[1]),name:nm[k],line:{color:cl[k],width:1.3}})),L("Rendimientos del Tesoro (%)"),cfg);
// nav activo
const secs=[...document.querySelectorAll("section.ch")],links=[...document.querySelectorAll("nav a")];
addEventListener("scroll",()=>{let i=secs.findIndex(s=>s.getBoundingClientRect().top>120);i=(i<0?secs.length:i)-1;links.forEach((l,j)=>l.classList.toggle("on",j===Math.max(0,i)));},{passive:true});
</script></body></html>'''
rep = {'__MOTOR__': motor, '__DATA__': json.dumps(D), '__LAST__': f"{mkt['last']:.2f}", '__LASTD__': '02-nov-2026', '__YTD__': f"{mkt['ytd']:.1f}",
       '__TNX__': f"{tnx:.2f}", '__IRX__': f"{irx:.2f}", '__GDP__': f"{mac['gdp']['2025']:.1f}", '__UNEMP__': f"{mac['unemp']['2025']:.1f}"}
for k, v in rep.items(): html = html.replace(k, v)
open('/home/claude/dash/index_v3.html', 'w', encoding='utf-8').write(html)
print('ok', len(html))
