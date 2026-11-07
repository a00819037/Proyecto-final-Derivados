const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
  HeadingLevel, LevelFormat, ImageRun, PageBreak, BorderStyle, Footer, PageNumber } = require("docx");

const AZ = "1F3864", GRIS = "595959";
const W = 9360; // ancho útil (Letter, márgenes de 1")
const p = (t, o = {}) => new Paragraph({ spacing: { after: 100 }, ...o.para, children: runs(t, o) });
function runs(t, o = {}) { // **negritas** sencillas
  return String(t).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(s => s.startsWith("**")
    ? new TextRun({ text: s.slice(2, -2), bold: true, size: o.size || 21, color: o.color })
    : new TextRun({ text: s, size: o.size || 21, color: o.color, italics: o.italics }));
}
const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bl = t => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 60 }, children: runs(t) });
const nota = t => p(t, { size: 17, color: GRIS, italics: true });
function tabla(head, rows, widths) {
  const tot = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, hdr) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: hdr ? { type: ShadingType.CLEAR, fill: AZ, color: "auto" } : undefined,
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    children: [new Paragraph({ alignment: i > 0 && !hdr && /^[−\-+$0-9.,%x →·/ ]+$/.test(String(t)) ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: [new TextRun({ text: String(t), size: 18, bold: hdr, color: hdr ? "FFFFFF" : undefined })] })]
  });
  return new Table({ width: { size: tot, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: head.map((t, i) => cell(t, i, true)) }),
      ...rows.map(r => new TableRow({ children: r.map((t, i) => cell(t, i, false)) }))] });
}
const sp = () => new Paragraph({ spacing: { after: 80 }, children: [] });
const img = (f, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: w, height: h } })] });

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 28, bold: true, color: AZ }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 23, bold: true, color: AZ }, paragraph: { spacing: { before: 160, after: 80 }, keepNext: true, outlineLevel: 1 } }]
  },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Waste Management · Bono convertible con call spread · ", size: 16, color: GRIS }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GRIS })] })] }) },
    children: [
      // Portada breve
      new Paragraph({ spacing: { before: 600, after: 120 }, children: [new TextRun({ text: "Reporte ejecutivo", size: 24, color: GRIS })] }),
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: "Waste Management, Inc. (NYSE: WM): emisión de bono convertible con call spread para refinanciar deuda cara", size: 38, bold: true, color: AZ })] }),
      p("Aplicación del caso Molson Coors Brewing Co.: Valuing a Convertible Bond (NE90-06-107)", { color: GRIS }),
      p("Productos derivados y administración de riesgos corporativos (Gpo 40) · Profesor: Dr. Raymundo Díaz Robles"),
      p("Tania Manuela López Suárez (A00819037) · Mauricio Martínez García (A00826170) · Ricardo Terrazas Duque (A01566884)"),
      p("Tecnológico de Monterrey · 9 de noviembre de 2026 · Datos de LSEG Workspace al 21-oct-2026", { color: GRIS }),
      sp(),
      h1("1. Resumen ejecutivo"),
      p("WM tiene tres bonos con cupones altos (7.00% 2028, 7.75% 2032 y 6.125% 2039; USD 647.2 mm nominales y USD 44.2 mm de cupones al año). Refinanciarlos con deuda directa a 6 años costaría 5.65%. Siguiendo a Molson Coors (2007), proponemos emitir **USD 750 mm en un bono convertible senior a 6 años** con prima de conversión de 25%, recomprar esos bonos y comprar un **call spread** (note hedge al 25% y warrants vendidos al 60%) para que la dilución solo empiece si la acción sube 60%."),
      tabla(["Resultado", "Valor"], [
        ["Cupón que deja el convertible a la par (árbol Tsiveriotis-Fernandes)", "2.41%"],
        ["Ahorro frente al bono directo de WM a 6 años (5.649%)", "324 pb"],
        ["Precio de conversión (prima 25%) / strike del warrant (prima 60%)", "$286.98 / $367.33"],
        ["Costo neto del call spread", "USD 54.4 mm (7.3% del principal)"],
        ["Ahorro anual de intereses (antes / después de impuestos 21%)", "USD 26.2 mm / USD 20.7 mm"],
        ["Remanente de caja después de tender, comisión y call spread", "USD 1.3 mm"],
        ["Deuda/EBITDA antes → después · EBITDA/intereses antes → después", "2.98x → 2.99x · 8.65x → 8.91x"]],
        [6560, 2800]),
      sp(),
      p("**Recomendación:** emitir, con dos condiciones: no bajar la prima de conversión de 25% y negociar la volatilidad a la que el banco compra los warrants. El ahorro no es un \"free lunch\": el cupón bajo existe porque WM vende a los inversionistas una opción que vale USD 152.58 por bono, y elevar la prima efectiva a 60% cuesta USD 54.4 mm."),

      h1("2. Selección de la empresa (punto A)"),
      tabla(["Requisito de la rúbrica", "Evidencia"], [
        ["Acciones listadas en EUA", "WM.N, New York Stock Exchange (LSEG Overview, Anexo)"],
        ["Presenta 10-K, 10-Q y 8-K ante la SEC", "Sí (SEC EDGAR, CIK 0000823768): 10-K 2025 presentado el 09-feb-2026; 10-Q del 3T-2026 el 28-oct-2026; 8-K el 27-oct-2026"],
        ["Deuda en circulación", "42 bonos vigentes por USD 17,950 mm y línea de crédito de USD 3,500 mm (LSEG, 03-nov-2026); deuda LP de USD 21,846 mm al 30-sep-2026 (10-Q)"],
        ["Derivados en las notas de los estados financieros", "Sí: 10-K 2025, Nota 2 (política de instrumentos derivados: coberturas de flujo de efectivo) y Nota 6 (Debt: ajustes por derivados de tasa terminados). Item 7A: al 31-dic-2025 los derivados vigentes eran inmateriales"],
        ["Opciones listadas", "Cadena de opciones WM hasta ene-2029 con volatilidad implícita (LSEG OPW)"],
        ["Necesidad real de cobertura", "Vencen USD 9,600 mm entre 2026 y 2030 (10-K 2025); bonos de cupón alto (6.125%–7.75%) frente a una curva de 5.65% a 6 años"],
        ["Relación con el portafolio del equipo", "El portafolio especulativo de Investopedia (AAPL, JPM, NVDA, TSLA, XOM) no tiene empresas defensivas; WM (beta 0.41, A-) es la parte coberturista del curso"],
        ["No usada en clase ni por otro equipo", "[Completar: confirmación del registro con el profesor]"]],
        [3400, 5960]),
      nota("Fuentes: SEC EDGAR (API XBRL, data.sec.gov) y LSEG Workspace. Los campos entre corchetes se llenan con la referencia exacta; no se incluyen datos sin verificar."),

      h1("3. Diagnóstico"),
      h2("Empresa y mercado"),
      p("WM ofrece recolección, reciclaje y disposición de residuos en EE.UU. y Canadá (segmentos East Tier, West Tier, Recycling Processing and Sales, WM Renewable Energy y WM Healthcare Solutions). Al 21-oct-2026: precio USD 229.58, market cap USD 91,767 mm, enterprise value USD 114,567 mm, beta a 5 años 0.41 y volatilidad histórica de 90 días de 21.04%. Es una acción defensiva con volatilidad moderada."),
      h2("Deuda y crédito"),
      p("Deuda total de USD 23,356 mm (20.3% del enterprise value), casi toda en dólares (97.2%) y a tasa fija: el riesgo relevante es de **tasa de interés y refinanciamiento**, no cambiario. Deuda/EBITDA de 2.98x (consenso: 2.51x en 2028) y cobertura de intereses de 8.65x."),
      p("**Item 7A del 10-K 2025:** WM tenía USD 22.9 mil millones de deuda de largo plazo y USD 2.9 mil millones expuestos a cambios de tasa en los siguientes 12 meses (papel comercial y bonos exentos de impuestos). Un alza de 100 pb elevaría su gasto por intereses en USD 35 mm y bajaría el valor justo de su deuda en cerca de USD 0.8 mil millones. Sus derivados vigentes eran inmateriales, así que hoy WM casi no cubre su riesgo de tasa: espacio natural para la estrategia propuesta."),
      tabla(["Bono a recomprar", "ISIN", "Nominal (USD mm)", "Precio ask", "Cupón anual (USD mm)"], [
        ["WM 7.00% 15-jul-2028", "US902917AH67", "257.9", "102.84", "18.1"],
        ["WM 7.75% 15-may-2032", "US94106LAN91", "143.6", "108.84", "11.1"],
        ["WM 6.125% 30-nov-2039", "US94106LAV18", "245.7", "102.30", "15.0"],
        ["Total", "", "647.2", "", "44.2"]], [2700, 1900, 1600, 1360, 1800]),
      nota("Costo del tender (ask + 1 punto, supuesto): USD 679.4 mm. Cupón promedio eliminado: 6.83%."),
      p("**Calificaciones (LSEG Issuer Ratings):** S&P A- (perspectiva estable), Fitch A-. La calificación de emisor de Moody's está retirada (WR), pero Moody's asigna A3 a la deuda senior respaldada y una calificación derivada A3 (30-oct-2025). Egan-Jones califica los bonos senior en BBB. Curva del emisor a 6 años: 5.649%, spread de 65.7 pb sobre Treasuries y probabilidad de incumplimiento acumulada de 6.5%."),
      h2("Pares"),
      tabla(["Empresa", "EV/EBITDA", "Deuda/EBITDA", "EBITDA/Intereses"], [
        ["Waste Management (WM)", "14.61x", "2.98x", "8.65x"],
        ["Republic Services (RSG)", "15.67x", "2.58x", "9.23x"],
        ["Waste Connections (WCN)", "16.62x", "2.90x", "9.00x"]], [3960, 1800, 1800, 1800]),
      p("WM cotiza al múltiplo más bajo, pero es la más apalancada y la de menor cobertura de intereses. Bajar su costo de deuda ataca justo esa debilidad."),

      h1("4. Estrategia propuesta"),
      bl("**Emisión:** USD 750 mm, convertible senior a 6 años, prima de conversión de 25% (3.4846 acciones por bono de USD 1,000)."),
      bl("**Uso de fondos:** recompra vía tender de los bonos 7.00% 2028, 7.75% 2032 y 6.125% 2039 (USD 679.4 mm), comisión de colocación (supuesto 2%, USD 15.0 mm) y call spread (USD 54.4 mm)."),
      bl("**Call spread:** WM compra calls con strike $286.98 (note hedge) y vende warrants con strike $367.33. La prima efectiva sube de 25% a 60%, igual que en Molson Coors (que pagó USD 49.7 mm netos, 8.6% de USD 575 mm)."),
      bl("**Por qué convertible y no deuda directa o capital:** un bono directo costaría 5.65%; emitir acciones diluiría hoy. El convertible baja el cupón a cambio de una dilución futura que el call spread empuja hasta $367 (0.65% de las acciones como máximo)."),

      h2("Comparación de alternativas para financiar el tender (USD 750 mm)"),
      tabla(["Concepto", "Convertible + call spread", "Deuda directa 6 años", "Emisión de acciones"], [
        ["Costo anual en efectivo (USD mm)", "18.1 (cupón 2.41%)", "42.4 (5.65%)", "12.2 (dividendos 1.63%)"],
        ["Ahorro anual vs. cupones eliminados (USD 44.2 mm)", "26.2", "1.9", "32.0"],
        ["Deuda/EBITDA después", "2.99x", "2.99x", "2.90x"],
        ["Acciones nuevas o potenciales", "2.61 mm (0.65%)", "0", "3.27 mm (0.82%)"],
        ["Cuándo diluye", "Solo arriba de $367", "Nunca", "Inmediato"],
        ["Costo inicial adicional", "Call spread USD 54.4 mm", "0", "0"]], [3060, 2100, 2000, 2200]),
      nota("El dividendo subestima el costo de las acciones: el costo real es el rendimiento que exigen los accionistas, mayor que el de la deuda. Emitir acciones también suele leerse como señal de que la acción está cara."),
      h1("5. Valoración"),
      h2("Insumos de mercado (LSEG, 21-oct-2026)"),
      tabla(["Insumo", "Valor", "Fuente"], [
        ["Tasa libre de riesgo a 6 años", "4.957%", "Promedio US5YT=RR (4.918%) y US7YT=RR (4.995%)"],
        ["Tasa de descuento del bono", "5.649%", "Issuer Curve 0#WMUSDABMK=, 6 años"],
        ["Dividend yield", "1.63%", "LSEG Overview"],
        ["Volatilidad de la conversión", "22.75%", "Implícita del call WM ene-2029 strike 290 (OPW)"],
        ["Volatilidad del warrant", "21.04%", "Histórica de 90 días (convención del caso)"]], [3000, 1300, 5060]),
      h2("Convertible = bono recto + opción"),
      p("Con Black-Scholes-Merton y dividendo, la opción de conversión vale USD 43.79 por acción (USD 152.58 por bono), así que el bono recto debe valer USD 847.42 y el cupón a la par es 2.615%. El árbol CRR converge a ese valor (USD 43.79 con 360 pasos). El caso base usa el árbol completo de Tsiveriotis-Fernandes (360 pasos), que agrega conversión anticipada y separa el riesgo de crédito: **cupón de 2.41%**, muy cerca del 2.5% de Molson."),
      img("fig/cupones.png", 520, 228),
      h2("El call spread y sus griegas"),
      tabla(["Pierna", "Strike", "Valor por acción", "USD mm"], [
        ["Compra note hedge (vol 22.75%)", "$286.98", "$43.79", "−114.4"],
        ["Venta warrants (vol 21.04%)", "$367.33", "$22.98", "+60.0"],
        ["Costo neto", "", "", "−54.4"]], [3760, 1700, 1900, 2000]),
      p("Griegas netas para WM: delta de 0.47 mm acciones (gana si sube la acción, lo que compensa la dilución entre $287 y $367), gamma −0.0005 y vega 0.04 USD mm por punto: la posición es casi neutral a la volatilidad una vez pactada; el costo depende de a qué volatilidad se pacta cada pierna (cada punto de volatilidad del warrant mueve su valor en ~USD 5.1 mm)."),
      img("fig/dilucion.png", 520, 244),
      h2("Volatilidad de largo plazo (Hull, cap. 23)"),
      p("Las opciones listadas llegan a ene-2029 y el convertible dura 6 años, así que validamos la volatilidad con EWMA y GARCH(1,1) por máxima verosimilitud sobre 5 años de precios diarios. La persistencia es baja (α+β ≈ 0.68; un choque se disipa en ~2 días) y la volatilidad promedio a 6 años converge a **19.7%**. La razón GARCH/implícita es 0.87 (< 0.90): el mercado paga la volatilidad más cara de lo que GARCH espera, y WM es quien la vende al emitir. Con 19.7% el cupón a la par sería 2.85%, todavía 280 pb abajo del bono directo. El back testing del VaR (Kupiec) pasa al 95%; al 99% falla por poco (p = 0.049), señal de colas más pesadas que la normal."),
      h2("Sensibilidades del cupón a la par (árbol T-F, 180 pasos)"),
      tabla(["Volatilidad \\ prima", "15%", "20%", "25%", "30%", "35%", "40%"], [
        ["18.00%", "2.26%", "2.70%", "3.10%", "3.44%", "3.71%", "3.97%"],
        ["21.04%", "1.76%", "2.25%", "2.67%", "3.00%", "3.32%", "3.57%"],
        ["22.75% (base)", "1.49%", "1.99%", "2.40%", "2.77%", "3.07%", "3.35%"],
        ["25.00%", "1.13%", "1.66%", "2.07%", "2.45%", "2.77%", "3.04%"],
        ["28.00%", "0.65%", "1.17%", "1.64%", "2.01%", "2.37%", "2.65%"]], [2160, 1200, 1200, 1200, 1200, 1200, 1200]),
      p("Más prima significa menos dilución pero más cupón. En ningún escenario el cupón se acerca al 5.65% del bono directo."),

      h1("6. Impacto en WM"),
      tabla(["Fuentes y usos", "USD mm"], [
        ["Emisión del convertible", "750.0"], ["(−) Comisión de colocación (supuesto 2%)", "−15.0"],
        ["(−) Recompra de bonos (tender)", "−679.4"], ["(−) Costo neto del call spread", "−54.4"], ["= Remanente de caja", "1.3"]], [6560, 2800]),
      p("El ahorro de intereses es de USD 26.2 mm al año (USD 20.7 mm después de impuestos) y de USD 24.3 mm frente a emitir un bono directo a 6 años. La operación se autofinancia **con muy poco margen**: con una comisión de 2.2% el remanente ya sería negativo. Parte del ahorro es contable: los bonos viejos se recompran arriba de la par y el cupón bajo se paga con una opción, así que a valor justo la operación es cercana a VPN cero. El beneficio real es de flujo de caja, perfil de vencimientos y costo de deuda reportado."),

      h1("7. Cobertura de tasa del tender"),
      p("Entre el anuncio y el pricing del tender, si las tasas **bajan** los bonos a recomprar suben de precio. El DV01 de la canasta es **USD 339,562 por pb** (precios ask del 21-oct-2026): una baja de 25 pb encarece el tender en USD 8.5 mm, y bastan 4 pb para eliminar el remanente de USD 1.3 mm. Por eso recomendamos cubrirlo. WM debe ganar si las tasas bajan (largo en Treasuries / recibir fijo), lo contrario del T-lock típico de un emisor; en Molson Coors el T-lock generó USD 1.4 mm."),
      tabla(["Bono", "Duración mod.", "DV01 (USD/pb)", "T-lock (nodo, USD mm)", "Futuros (aprox.)", "Swap recibe fijo (USD mm)"], [
        ["7.00% 2028", "1.59", "42,918", "2 años: 227.1", "1,111 TU", "226.7"],
        ["7.75% 2032", "4.40", "70,897", "5 años: 161.0", "1,843 FV", "159.8"],
        ["6.125% 2039", "8.77", "225,748", "10 años: 289.1", "2,738 TN (Ultra 10)", "283.8"],
        ["Total", "", "339,562", "677.3", "", "670.3"]], [1500, 1260, 1400, 1800, 1700, 1700]),
      p("**Instrumento preferido: T-lock por nodos.** Si el tender se fija como spread sobre un Treasury de referencia, el T-lock cubre casi exactamente ese riesgo y se liquida en efectivo al pricing. Los futuros son líquidos y sin riesgo de contraparte, pero piden margen diario y su número es aproximado (factor de conversión estimado, riesgo de cambio de CTD). Los swaps dejan riesgo de base: los swap spreads son negativos y distintos por plazo (−14.5 pb a 2 años, −28.4 pb a 5 y −39.4 pb a 10)."),
      nota("Treasuries benchmark, swap spreads, futuros y CTD: LSEG Rates View, 03-nov-2026 (Anexo). DV01 lineal; con bajas mayores a 50 pb la convexidad eleva algo el costo."),

      h1("8. Swaps de cobertura (Hull, cap. 7)"),
      p("Replicamos el cuaderno de swaps de clase con los datos de WM (notebook WM_Swaps_Hull_cap7 y sección 16 del reporte R Markdown). Los cuatro swaps se plantean desde la tesorería de WM y **todos cubren un riesgo**:"),
      tabla(["Swap", "WM recibe / paga", "Riesgo que cubre", "Resultado"], [
        ["Tasa del tender (3 nodos)", "Fijo / SOFR", "Baja de tasas antes del pricing del tender", "DV01 de USD 347,140/pb vs. 339,562 de la canasta; el swap 5Y gana USD 1.8 mm si la curva baja 25 pb (enfoque de bonos = FRAs)"],
        ["Deuda variable", "SOFR / fijo 4.652%", "Alzas sobre USD 2.9 mil mm de deuda variable (10-K, Item 7A)", "Costo final 5.452% fijo, 20 pb debajo del fijo directo; +100 pb ya no cuestan USD 29 mm al año"],
        ["Divisas CAD/USD", "CAD 3.944% / USD 5.023%", "Tipo de cambio del bono WM 3.944% 2033 (C$ 700 mm)", "Nace en cero; si el CAD se aprecia 5%, el swap gana ≈ USD 27 mm y compensa el mayor costo de la deuda"],
        ["Equity swap", "Rendimiento WM / fijo 4.48%", "Dilución económica de los warrants vendidos (strike 160%)", "Nocional = delta de los warrants (0.36) × 2.61 mm acciones × precio ≈ USD 200 mm"]],
        [1700, 1800, 2700, 3160]),
      sp(),
      p("**Ventaja comparativa.** Como en el ejemplo de Hull, la contraparte del swap sobre la deuda variable es un emisor AA (referencia: bono Apple 4.500% 2032, YTM 4.905%). La diferencia en tasa fija (0.74%) es mayor que en variable (0.35%, supuesto), lo que deja una ganancia de 0.39% a repartir. Parte de esa ganancia refleja que el margen variable se puede revisar y un intermediario cobraría 3-4 pb, así que no es un \"free lunch\"."),
      p("**Réplica operativa.** Alpaca no opera swaps OTC, así que diseñamos la réplica de las coberturas con instrumentos listados (USD 10 mil por pierna): compra de IEF y venta en corto de BIL (recibir fijo / pagar variable), compra de FXC (recibir CAD) y compra de WM (recibir su rendimiento). Las órdenes en la cuenta paper se enviaron como limitadas y no se ejecutaron, así que no hay P&L realizado."),
      nota("Curva swap: Treasuries + swap spreads de LSEG Rates View (03-nov-2026), bootstrapping semestral. Bono en CAD, USD/CAD 1.4124, curva de Canadá (3.40% a 6.7 años) y bono Apple 2032: LSEG Workspace, 05/06-nov-2026. Márgenes sobre SOFR: supuestos."),

      h1("9. Riesgos"),
      tabla(["Riesgo", "Qué pasa", "Mitigante"], [
        ["Dilución", "Arriba de $367 se ejercen los warrants (42.5% de probabilidad a 6 años en el Monte Carlo GARCH con 8% anual supuesto)", "El call spread baja la dilución esperada de USD 307 mm a USD 198 mm"],
        ["Volatilidad", "Pactar a otra volatilidad cambia cupón y costo del spread", "Validar con GARCH; negociar la vol. del warrant"],
        ["Tasas", "El costo del tender y el ahorro cambian con la curva; la curva bajó entre el 21-oct y el 03-nov", "T-lock por nodos de ≈USD 677 mm (sección 7); tender a spread fijo con fecha límite"],
        ["Tasa variable", "Alzas sobre USD 2.9 mil mm de deuda variable", "Swap paga fijo / recibe SOFR (sección 8)"],
        ["Tipo de cambio", "Bono WM 3.944% 2033 en CAD (C$ 700 mm)", "Swap CAD/USD fijo-fijo (sección 8)"],
        ["Contraparte", "El note hedge depende del banco", "Contraparte A o mejor, ISDA con colateral"],
        ["Contable", "Bajo ASU 2020-06 el convertible es un solo pasivo y la dilución se mide con if-converted", "El call spread cubre la dilución económica, no la contable"],
        ["Supuestos", "Comisión 2% y prima de tender de 1 punto", "El remanente es de solo USD 1.3 mm"]], [1500, 4160, 3700]),

      h1("10. Recomendación"),
      p("Emitir el convertible de USD 750 mm a 6 años con cupón cercano a 2.4%, prima de conversión de 25% y call spread al 60%: WM se financia 324 pb abajo de su deuda directa, reduce sus intereses en USD 26.2 mm al año y mantiene el apalancamiento en 2.99x. Condiciones: (i) no bajar la prima de conversión de 25%; (ii) negociar la volatilidad de los warrants; (iii) confirmar que la comisión y la prima del tender no eliminen el remanente; (iv) cubrir la tasa del tender con un T-lock por nodos hasta su pricing; (v) complementar con swaps: pagar fijo sobre la deuda variable, convertir el bono en CAD a USD y, si la dilución preocupa, cubrir los warrants con un equity swap (sección 8)."),
      h2("Parte operativa y reproducibilidad"),
      p("Se envió en Alpaca (paper trading) una orden multi-pierna que replica el call spread con opciones listadas: compra de 1 call WM 19-ene-2029 strike 290 y venta de 1 call strike 340, límite de USD 9.07. La orden limitada de un día no se ejecutó y expiró sin llenarse. Todo el análisis es reproducible: reporte R Markdown, notebooks de Colab, calculadora HTML y dashboard en el repositorio del equipo."),
      nota("Fuentes: LSEG Workspace (21-oct-2026; capturas del 03-nov-2026); SEC EDGAR (XBRL); World Bank; Yahoo Finance (precios diarios); Alpaca; caso Molson Coors (NE90-06-107); Hull, Options, Futures and Other Derivatives, cap. 13 y 23; Tsiveriotis y Fernandes (1998). Uso de IA: Claude (Anthropic) para revisión, recálculo independiente y redacción; los datos y decisiones son del equipo."),
    ]
  }]
});
Packer.toBuffer(doc).then(b => fs.writeFileSync("WM_Reporte_Ejecutivo.docx", b));
