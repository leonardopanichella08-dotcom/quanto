"""QUANTO — Riassunto: il documento breve (7 pagine) che dice cosa fa QUANTO, come lavora, con quali strumenti e perché conviene a uno studio.

A differenza del dossier (che spiega ogni processo e dichiara lo stato di ogni funzione) il riassunto non entra nei processi: descrive, in parole semplici,
il prodotto e il suo valore per studi di commercialisti e boutique di finanza agevolata. Non contiene la visione strategica interna.

Uso:  python docs/riassunto/build_riassunto.py   (dalla radice del repository)
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Flowable, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
WIN = Path("C:/Windows/Fonts")
try:
    pdfmetrics.registerFont(TTFont("Body", str(WIN / "segoeui.ttf")))
    pdfmetrics.registerFont(TTFont("Body-B", str(WIN / "segoeuib.ttf")))
    pdfmetrics.registerFont(TTFont("Body-I", str(WIN / "segoeuii.ttf")))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-B", italic="Body-I", boldItalic="Body-B")
    F, FB, FI = "Body", "Body-B", "Body-I"
except Exception:                                      # fuori da Windows: caratteri standard
    F, FB, FI = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"

INK = colors.HexColor("#1a1a17")
MUTE = colors.HexColor("#5b5b52")
LINE = colors.HexColor("#d8d8cc")
YEL = colors.HexColor("#f1e21b")
YEL_SOFT = colors.HexColor("#fff7b8")
YEL_PALE = colors.HexColor("#fffbe0")
PAPER = colors.HexColor("#faf9f4")

S = {
    "title": ParagraphStyle("title", fontName=FB, fontSize=30, leading=34, textColor=INK, spaceAfter=4),
    "sub": ParagraphStyle("sub", fontName=F, fontSize=13.5, leading=19, textColor=MUTE, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName=FB, fontSize=17, leading=21, textColor=INK, spaceBefore=4, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=FB, fontSize=11.5, leading=15, textColor=INK, spaceBefore=8, spaceAfter=3, keepWithNext=1),
    "p": ParagraphStyle("p", fontName=F, fontSize=10.4, leading=15, textColor=INK, spaceAfter=7, alignment=TA_LEFT),
    "lead": ParagraphStyle("lead", fontName=F, fontSize=12.4, leading=18.5, textColor=INK, spaceAfter=10),
    "small": ParagraphStyle("small", fontName=F, fontSize=8.8, leading=12.2, textColor=MUTE, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName=F, fontSize=9.6, leading=13.4, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName=FB, fontSize=9.6, leading=13.4, textColor=INK),
    "card_t": ParagraphStyle("card_t", fontName=FB, fontSize=11, leading=14, textColor=INK, spaceAfter=3),
    "card_p": ParagraphStyle("card_p", fontName=F, fontSize=9.4, leading=13, textColor=INK, spaceAfter=3),
    "card_g": ParagraphStyle("card_g", fontName=FI, fontSize=9.2, leading=12.6, textColor=MUTE),
    "num": ParagraphStyle("num", fontName=FB, fontSize=20, leading=22, textColor=INK),
    "numl": ParagraphStyle("numl", fontName=F, fontSize=8.8, leading=11.5, textColor=MUTE),
    "bullet": ParagraphStyle("bullet", fontName=F, fontSize=10.4, leading=14.6, textColor=INK, leftIndent=13, bulletIndent=2, spaceAfter=4),
}
story: list = []
W = A4[0] - 40 * mm


class Flow(Flowable):
    """Il percorso di un cliente in sette tappe, disegnato come una striscia di riquadri collegati."""

    def __init__(self, steps, width, height=64 * mm):
        super().__init__()
        self.steps, self.width, self.height = steps, width, height

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        n = len(self.steps)
        gap = 5 * mm
        bw = (self.width - gap * (n - 1)) / n
        for i, (title, text) in enumerate(self.steps):
            x = i * (bw + gap)
            top = self.height
            h = 56 * mm
            c.setFillColor(YEL_PALE if i % 2 == 0 else YEL_SOFT)
            c.setStrokeColor(colors.HexColor("#e8d94a"))
            c.setLineWidth(0.6)
            c.roundRect(x, top - h, bw, h, 3 * mm, stroke=1, fill=1)
            c.setFillColor(INK)
            c.circle(x + 5 * mm, top - 6 * mm, 3.2 * mm, stroke=0, fill=1)
            c.setFillColor(YEL)
            c.setFont(FB, 8.5)
            c.drawCentredString(x + 5 * mm, top - 7.3 * mm, str(i + 1))
            c.setFillColor(INK)
            c.setFont(FB, 8.2)
            y = top - 14 * mm
            for ln in _wrap(title, FB, 8.2, bw - 4 * mm):
                c.drawString(x + 2 * mm, y, ln)
                y -= 3.6 * mm
            c.setFont(F, 7.2)
            c.setFillColor(MUTE)
            y -= 1 * mm
            for ln in _wrap(text, F, 7.2, bw - 4 * mm)[:9]:
                c.drawString(x + 2 * mm, y, ln)
                y -= 3.1 * mm
            if i < n - 1:
                c.setStrokeColor(INK)
                c.setLineWidth(0.9)
                ay = top - h / 2
                c.line(x + bw + 0.6 * mm, ay, x + bw + gap - 0.8 * mm, ay)
                c.line(x + bw + gap - 1.8 * mm, ay + 0.9 * mm, x + bw + gap - 0.8 * mm, ay)
                c.line(x + bw + gap - 1.8 * mm, ay - 0.9 * mm, x + bw + gap - 0.8 * mm, ay)


def _wrap(text: str, font: str, size: float, width: float):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if pdfmetrics.stringWidth(t, font, size) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def P(t, style="p"): story.append(Paragraph(t, S[style]))
def H1(t): story.append(Paragraph(t, S["h1"]))
def H2(t): story.append(Paragraph(t, S["h2"]))
def SP(h=6): story.append(Spacer(1, h))
def B(items): [story.append(Paragraph(i, S["bullet"], bulletText="•")) for i in items]


def bar():
    t = Table([[""]], colWidths=[W], rowHeights=[3.2 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), YEL)]))
    story.append(t)
    SP(10)


def card(title: str, what: str, gain: str):
    return [Paragraph(title, S["card_t"]), Paragraph(what, S["card_p"]), Paragraph(f"<b>Cosa ottieni:</b> {gain}", S["card_g"])]


def cards(items):
    rows = []
    for k in range(0, len(items), 2):
        row = [card(*items[k])]
        row.append(card(*items[k + 1]) if k + 1 < len(items) else "")
        rows.append(row)
    t = Table(rows, colWidths=[W / 2 - 2 * mm, W / 2 - 2 * mm], hAlign="LEFT", spaceBefore=2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), PAPER), ("BOX", (0, 0), (-1, -1), 0.4, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story.append(t)


def table(rows, widths, head=True, zebra=True):
    data = [[Paragraph(str(c), S["cellb"] if (head and i == 0) else S["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
          ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    if head:
        st += [("BACKGROUND", (0, 0), (-1, 0), YEL_SOFT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#e8d94a"))]
    if zebra:
        st += [("BACKGROUND", (0, i), (-1, i), PAPER) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    story.append(t)
    SP(8)


def kpis(items):
    cells = [[Paragraph(v, S["num"]), Paragraph(l, S["numl"])] for v, l in items]
    t = Table([[c[0] for c in cells], [c[1] for c in cells]], colWidths=[W / len(items)] * len(items))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), YEL_PALE), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e8d94a")), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, 1), (-1, 1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t)
    SP(10)


def decor(c, doc):
    c.saveState()
    c.setFillColor(YEL)
    c.rect(0, A4[1] - 3 * mm, A4[0], 3 * mm, stroke=0, fill=1)
    c.setFont(FB, 8)
    c.setFillColor(INK)
    c.drawString(20 * mm, 11 * mm, "QUANTO")
    c.setFont(F, 8)
    c.setFillColor(MUTE)
    c.drawString(34 * mm, 11 * mm, "Riassunto · 12 ottobre 2026")
    c.drawRightString(A4[0] - 20 * mm, 11 * mm, f"{doc.page}")
    c.restoreState()


def build() -> Path:
    # ------------------------------------------------------------------ 1. copertina e in breve
    SP(26)
    story.append(Paragraph("QUANTO", ParagraphStyle("brand", fontName=FB, fontSize=13, leading=16, textColor=MUTE, spaceAfter=10)))
    story.append(Paragraph("Il riassunto", S["title"]))
    story.append(Paragraph("Cosa fa QUANTO, come lavora e perché conviene a uno studio", S["sub"]))
    bar()
    story.append(Paragraph("QUANTO è un motore di calcolo <b>gratuito</b> per studi di commercialisti e boutique di finanza agevolata. Dato un cliente, dice <b>a quali bandi può partecipare</b>, "
                           "<b>quanto valgono in euro</b>, <b>come combinarli</b> senza far pagare due volte la stessa spesa, costruisce il <b>budget del progetto</b> e lo controlla con <b>60 regole</b>. "
                           "Ogni numero porta la sua fonte e, a parità di dati, il risultato è sempre lo stesso.", S["lead"]))
    P("QUANTO non scrive progetti né testi di candidatura: fa la parte che si calcola. Il resto, la parte che si racconta e si negozia con il cliente, resta allo studio.")
    SP(8)
    H1("Le tre garanzie")
    table([["Non inventa mai un dato", "Ogni numero ha una fonte", "Stesso dato, stesso risultato"],
           ["Se un numero non c'è, QUANTO scrive «manca» e dice cosa serve per averlo. Nessuna stima a occhio, nessun testo generato da un modello.",
            "Una percentuale, un tetto, una data: accanto c'è la frase del testo ufficiale da cui viene, con il documento e il suo link.",
            "Il calcolo non usa il caso. Ogni controllo lascia un'impronta firmata che chiunque può verificare, anche un anno dopo."]],
          [W / 3, W / 3, W / 3], zebra=False)
    SP(4)
    H1("Per chi è")
    B(["<b>Studi di commercialisti</b> che seguono decine di aziende e vogliono proporre ai clienti i bandi giusti, con numeri che reggono davanti a un'istruttoria.",
       "<b>Boutique di finanza agevolata</b> che costruiscono budget e piani di allocazione e hanno bisogno di ripetibilità e di una fonte per ogni cifra.",
       "<b>Direttori finanziari e consulenti d'impresa</b> che pianificano più fondi insieme per l'azienda che seguono e vogliono sapere chi paga cosa lungo l'anno."])
    SP(4)
    kpis([("60", "regole applicate a ogni voce di budget"), ("8", "bandi con un modello di calcolo curato a mano"), ("780+", "bandi aperti nel catalogo nazionale, aggiornati ogni notte"), ("509", "test automatici sul motore")])
    story.append(PageBreak())

    # ------------------------------------------------------------------ 2. come lavora
    H1("Come lavora")
    P("Il percorso è lo stesso per ogni cliente e si può percorrere da soli o farlo fare all'assistente. Ogni tappa usa i dati della precedente.")
    story.append(Flow([("Un lavoro per cliente", "Ogni azienda cliente ha il suo spazio: dati, documenti e risultati separati dagli altri."),
                       ("Documenti e profilo", "Visura e bilanci diventano dati con la loro provenienza. Quello che manca lo si dice."),
                       ("Stima dell'anno", "Dall'ultimo bilancio si stimano spese e ricavi dell'anno da pianificare."),
                       ("Bandi adatti", "Per ogni bando: può partecipare? quanto vale in euro? cosa va adeguato?"),
                       ("Piano e potenziale", "Tutti i bandi insieme, senza doppioni: il massimo teorico e il piano voce per voce."),
                       ("Budget e controllo", "La bozza di budget dal bilancio, controllata voce per voce con 60 regole."),
                       ("Impronta firmata", "Il risultato lascia un'impronta verificabile da chi controlla.")], W))
    SP(8)
    H2("In concreto")
    B(["<b>Parte dal cliente, non dal bando.</b> Si carica visura e bilancio e QUANTO propone i bandi più adatti all'azienda, in ordine di affinità e con i motivi.",
       "<b>Dà una cifra, con l'intervallo.</b> Per ogni bando c'è il valore prudente e quello con tutte le maggiorazioni, con le ipotesi scritte accanto.",
       "<b>Mette insieme più bandi senza sbagliare.</b> Rispetta cumulo, tetti e il limite degli aiuti «de minimis»; dice quali bandi non servono e perché.",
       "<b>Costruisce il budget dal bilancio.</b> Poi lo controlla voce per voce: ammessa, ridotta, respinta o in attesa di un documento, sempre con il motivo.",
       "<b>Si ricorda di tutto.</b> Cambiando pagina, chiudendo l'app o passando a un altro cliente, ogni scelta resta al suo posto."])
    H2("Due modi di lavorare")
    table([["Da soli", "Con l'assistente"], ["Si naviga tra le pagine (Allocazione, Budget, Confronto…) e si inseriscono i dati dove servono.",
           "Si scrive nella chat cosa si vuole fare, o si sceglie un suggerimento: l'assistente esegue i passaggi, chiede solo i dati che mancano e spiega cos'è ogni dato, perché serve e dove si trova."]], [W / 2, W / 2], zebra=False)
    H2("Dove interviene il calcolo e dove no")
    P("Tutti i numeri sono calcolati con regole fisse e aritmetica esatta, non stimati da un modello linguistico. L'intelligenza artificiale non scrive e non interpreta cifre: la ricerca dei documenti usa un motore di ricerca per trovare gli indirizzi, "
      "e le regole si leggono dai testi ufficiali con schemi precisi, ognuna legata alla frase da cui nasce.")
    story.append(PageBreak())

    # ------------------------------------------------------------------ 3-4. gli strumenti
    H1("Gli strumenti")
    P("QUANTO è un insieme di strumenti che lavorano sugli stessi dati del cliente. Sono tutti gratuiti per gli studi.")
    cards([("Lavori e profilo", "Un lavoro per ogni azienda cliente, con profilo, bilanci per anno, documenti e modello di previsione. Ogni dato ricorda da dove viene.", "dati ordinati per cliente, mai mescolati, con la provenienza di ogni valore"),
           ("Catalogo e studio dei bandi", "L'elenco nazionale dei bandi aperti, con la scheda ufficiale di ciascuno. Con un clic QUANTO studia un bando: cerca i documenti ufficiali, li legge e ne ricava regole, requisiti e percentuale.", "un bando letto per intero, con la fonte di ogni regola"),
           ("Allocazione e potenziale massimo", "Stima l'anno successivo, trova i bandi adatti, li combina e mostra quanto potrebbe coprire l'azienda se li ottenesse tutti, con il bilancio ricostruito e un grafico per ogni bando.", "il massimo teorico e il piano voce per voce, con ogni numero spiegato"),
           ("Budget e 60 criteri", "Crea la bozza di budget dal bilancio e controlla ogni voce con 60 regole su personale, beni strumentali, consulenze, spese generali e coerenza.", "un budget controllato, con il motivo di ogni riduzione"),
           ("Pacchetti di lavoro", "Divide il budget ammesso tra i pacchetti di lavoro del bando, rispettando le quote minime e massime e i tetti per categoria.", "la ripartizione per WP già calcolata, o il motivo per cui non esiste"),
           ("Confronto", "Ogni budget salvato diventa un template, con nicchia, bando ed esito. Il consiglio per un nuovo cliente nasce dai budget simili, pesando di più quelli che hanno vinto, e migliora a ogni dato nuovo.", "una ripartizione di partenza basata sui casi reali dello studio"),
           ("Verifica e registro firmato", "Ogni budget controllato può lasciare un'impronta in un registro che non si può riscrivere. Un revisore la verifica con una chiave pubblica, senza accedere a nulla.", "una prova che il budget non è stato modificato"),
           ("Assistente guidato", "Una chat che esegue al posto dell'utente i passaggi in cui servono dati: cambia pagina, salva, calcola e, quando serve un valore, lo chiede spiegando cos'è e dove si trova.", "meno clic e nessuna dimenticanza, senza inventare nulla"),
           ("Manuale e guida", "Un manuale dei processi in parole semplici (con PDF), una guida in ogni pagina e la spiegazione dei 60 criteri con esempi.", "ogni funzione spiegata, con esempi veri"),
           ("Dietro le quinte", "Il team di QUANTO tiene aggiornati catalogo, regole dei bandi e tabelle ufficiali (contratti collettivi, aliquote) da un'area riservata, con la fonte di ogni valore.", "dati sempre aggiornati e verificabili alla fonte")])
    story.append(PageBreak())

    # ------------------------------------------------------------------ 5. valore aggiunto
    H1("Il valore per uno studio")
    P("Uno studio che segue molte aziende perde tempo e credibilità in tre punti: trovare i bandi, quantificarli e dimostrare al cliente da dove viene ogni cifra. QUANTO lavora esattamente lì.")
    table([["Il lavoro oggi", "Con QUANTO"],
           ["Cercare i bandi giusti su più siti, uno per uno", "Una lista ordinata per affinità con l'azienda, con descrizione ufficiale, motivi e ciò che resta da verificare"],
           ["Stimare quanto vale un bando «a occhio»", "Un importo con intervallo prudente-massimo e le ipotesi scritte accanto"],
           ["Mettere insieme più bandi con il rischio di contare due volte la stessa spesa", "Un piano che rispetta cumulo, tetti e de minimis e dice quali bandi non servono"],
           ["Partire da un foglio vuoto per il budget", "Una bozza costruita dal bilancio del cliente, controllata voce per voce"],
           ["Rispondere al cliente «me l'ha detto il bando»", "Ogni numero con la frase del testo ufficiale e il link al documento"],
           ["File sparsi per ogni cliente", "Un lavoro per cliente, dati separati, scelte salvate"],
           ["La memoria dei budget passati resta nella testa di qualcuno", "Template con esito e un consiglio che migliora a ogni budget salvato"],
           ["Ripetere ogni volta le stesse operazioni", "L'assistente le esegue e chiede solo i dati che mancano"]], [W * 0.42, W * 0.58])
    H2("Cosa ottiene concretamente lo studio")
    B(["<b>Tempo:</b> la ricerca dei bandi e la prima stima non partono da zero ma da un risultato già calcolato da rivedere.",
       "<b>Credibilità:</b> davanti al cliente ogni cifra si può difendere, perché porta la sua fonte e il suo calcolo.",
       "<b>Proposte:</b> lo studio può presentare al cliente il «potenziale massimo» dei bandi accessibili e il piano per ottenerlo.",
       "<b>Controllo:</b> il budget arriva alla domanda già controllato, con le voci a rischio segnalate prima dell'istruttoria.",
       "<b>Costo:</b> gli strumenti sono gratuiti; non c'è abbonamento da giustificare ai clienti."])
    SP(4)
    P("<b>Privacy.</b> I documenti del cliente sono cifrati; nomi, codici fiscali e IBAN diventano codici che non si possono invertire; i dati di ogni cliente sono separati dagli altri. I template di budget condivisi non contengono ragione sociale né partita IVA e si usano solo in gruppi di almeno tre.", "small")
    story.append(PageBreak())

    # ------------------------------------------------------------------ 6. fiducia e limiti
    H1("Fiducia e limiti")
    H2("Cosa rende affidabile il risultato")
    B(["Il motore usa aritmetica decimale: nessun arrotondamento nascosto, importi sempre in centesimi.", "Un controllo senza dato o senza regola risulta «non valutato», mai «superato»: il silenzio non diventa un sì.",
       "Il piano combinato è sempre lo stesso a parità di dati e sempre il massimo possibile; cambia solo se cambiano i dati dell'azienda o il catalogo dei bandi.",
       "Se le regole di un bando cambiano, cambia l'impronta di ogni budget calcolato con quelle regole: il passato non si riscrive in silenzio."])
    H2("Cosa QUANTO non fa, e dice")
    table([["Limite", "Come lo gestisce"], ["Non prevede l'esito di un bando", "Il potenziale è un massimo teorico; il Confronto è una statistica sulla struttura della spesa, non una previsione"],
           ["Non scrive il progetto", "Produce solo la componente numerica: budget, ammissibilità, allocazione"], ["Non somma garanzie e contributi", "Le garanzie pubbliche si calcolano a parte, come importo garantibile"],
           ["Una percentuale di un bando non si trova", "Il bando resta senza importo e lo dice; si può rilanciare lo studio per cercarla"],
           ["Gli aiuti già ricevuti dall'azienda non si leggono da un registro", "Il tetto de minimis si stima dagli aiuti dichiarati e dice su cosa si regge; si corregge a mano"],
           ["Le scansioni dei documenti", "Dove non è disponibile il riconoscimento ottico, il documento si rifiuta con un messaggio chiaro, senza inventare un testo"]], [W * 0.38, W * 0.62])
    H2("A che punto è")
    P("Il motore, i 60 controlli, l'allocazione, il budget, il Confronto, il registro firmato e l'assistente sono realizzati e provati con migliaia di casi automatici. Non sono ancora state presentate pratiche reali tramite QUANTO: per questo non esiste una percentuale di successo e il documento non ne dichiara nessuna. "
      "L'aggiornamento di catalogo, regole e tabelle ufficiali è un lavoro continuo del team di QUANTO.")
    story.append(PageBreak())

    # ------------------------------------------------------------------ domande frequenti
    H1("Le domande che fa uno studio")
    for q, ans in [("Devo caricare i dati dei miei clienti su un sistema di terzi?", "I documenti sono cifrati e separati per cliente; nomi, codici fiscali e IBAN diventano codici. Si possono esportare ed eliminare in qualsiasi momento: l'esportazione e l'eliminazione dei dati dello studio sono funzioni del profilo."),
                   ("Posso fidarmi di una cifra senza rifare il calcolo?", "Ogni cifra porta la regola e la frase del testo ufficiale da cui viene, e il calcolo è ripetibile. Per le ipotesi (per esempio «si finanzia tutto l'investimento con un prestito») l'ipotesi è scritta accanto al numero."),
                   ("Cosa succede se un bando cambia?", "Il team di QUANTO aggiorna le regole e il bando si può studiare di nuovo. Cambia l'impronta dei budget calcolati con le regole nuove, quindi si vede sempre con quale versione è stato fatto un calcolo."),
                   ("Che cosa insegna il Confronto, e a chi?", "Impara dai template dello studio e, in forma anonima e solo in gruppi di almeno tre, da quelli di tutti. Si può scegliere di confrontarsi con il solo studio. Con pochi dati lo dice invece di inventare un consiglio."),
                   ("Quanto costa?", "Gli strumenti sono gratuiti per gli studi."),
                   ("Cosa non devo aspettarmi?", "Un testo di candidatura, una previsione sull'esito del bando o un importo per un bando di cui nessuna fonte ufficiale dichiara la percentuale.")]:
        H2(q)
        P(ans)
    story.append(PageBreak())

    # ------------------------------------------------------------------ 7. un caso
    H1("Un caso di prova")
    P("Azienda fittizia di prova: <b>Meridiana Digital Solutions S.r.l.</b> (software, Torino, 15 dipendenti, ricavi 2025 di 1.583.200 euro). Si caricano 35 documenti: visura, tre bilanci completi di 58-63 pagine, due cedolini, nove F24, la bozza di candidatura, il DURC, la dichiarazione de minimis, il business plan di 46 pagine, le dichiarazioni fiscali, i registri delle fatture, il contratto di locazione, l'estratto conto e otto fogli Excel con centinaia di righe. QUANTO li legge e compila il profilo (100% dopo una sola risposta: se è una start-up innovativa).")
    table([["Passo", "Cosa produce QUANTO"], ["Bilanci 2023-2025", "Ricavi, costi per categoria (personale 890.700 €, consulenze 172.500 €, spese generali 194.650 €, beni strumentali 119.100 € nel 2025), utile, dipendenti medi"],
           ["Stima 2027", "Spesa prevista di 1.991.026 euro, con la variazione di ogni voce spiegata dai due ultimi bilanci"],
           ["Bandi adatti", "6 bandi adatti all'azienda, 5 con un importo calcolabile e un'etichetta «de minimis» dove la fonte lo dichiara"],
           ["Potenziale massimo", "Dal valore prudente di 1.252.699 € a 1.718.015 € con tutte le maggiorazioni: il 62,9% della spesa prevista; restano a carico 738.327 €"],
           ["Budget", "Bozza dal bilancio per il bando scelto, persone del progetto aggiunte dall'assistente e controllo dei 60 criteri"]], [W * 0.26, W * 0.74])
    P("I numeri del potenziale sono quelli calcolati sul catalogo di prova con i dati fittizi: servono a mostrare il percorso. Sul catalogo reale e su un'azienda vera il risultato è diverso.", "small")
    H2("Come si comincia")
    B(["Si apre un lavoro per il cliente e si carica visura e ultimo bilancio (anche con l'assistente: «Completa i dati dell'azienda»).", "Si sceglie l'anno da pianificare e si legge la stima.",
       "Si guarda l'elenco dei bandi adatti e si preme «Combina tutti i bandi adatti».", "Si crea la bozza di budget per il bando scelto e si controlla.", "Si salva il budget come template, con il suo esito, quando il bando risponde."])
    SP(6)
    bar()
    story.append(Paragraph("<b>QUANTO</b> · strumenti gratuiti per studi di commercialisti e boutique di finanza agevolata · quanto-self.vercel.app", S["small"]))

    out = ROOT / "docs" / "riassunto" / "QUANTO_riassunto.pdf"
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm, title="QUANTO — Riassunto", author="QUANTO",
                          subject="Cosa fa QUANTO, come lavora, strumenti e valore per gli studi")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=decor)])
    doc.build(story)
    return out


if __name__ == "__main__":
    print(build())
