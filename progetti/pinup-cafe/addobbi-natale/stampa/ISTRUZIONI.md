# Istruzioni di stampa - Addobbi PIN-UP Cafe

Strato 0,2 mm, ugello 0,4 mm, PLA. Nessun supporto. Tutti i pezzi sono già orientati per la stampa.

**Regola:** in ogni strato c'è un solo colore. Per gli addobbi a strati basta aggiungere nello slicer un *cambio filamento* (M600 / "Change filament") alle quote indicate: si mette sul **primo strato** del nuovo colore (es. 4,0 mm = strato 4,0–4,2).

## Addobbi a strati (un file 3MF, cambi colore a quota)

| File | Colori dal basso | Cambi filamento a |
|---|---|---|
| `polpo.3mf` | rosso (0–4 mm) → bianco (4–5 mm) → nero (5–5.8 mm) | 4 mm, 5 mm |
| `pesciolino.3mf` | azzurro (0–4 mm) → bianco (4–5 mm) → nero (5–5.8 mm) | 4 mm, 5 mm |
| `pizza.3mf` | impasto (0–4 mm) → salsa (4–4.6 mm) → mozzarella (4.6–5.4 mm) → salsa (5.4–6.2 mm) | 4 mm, 4.6 mm, 5.4 mm |
| `patatine.3mf` | rosso (0–31 mm) → bianco (31–38 mm) → patatina (38–75.8 mm) | 31 mm, 38 mm |
| `sandwich.3mf` | pane_chiaro (0–6 mm) → prosciutto (6–8.6 mm) → formaggio (8.6–10.6 mm) → insalata (10.6–13.4 mm) → pane_chiaro (13.4–19.4 mm) → oliva (19.4–43.6 mm) | 6 mm, 8.6 mm, 10.6 mm, 13.4 mm, 19.4 mm |

Nella pizza la salsa e il salame usano lo stesso filamento rosso.

## Hamburger a pezzi (nessun cambio filamento)

Ogni pezzo è un oggetto separato: si stampa solo quello che serve, tutto in un colore.

| File | Pezzo | Colore |
|---|---|---|
| `hamburger_1_pane_sotto.3mf` | pane sotto | pane |
| `hamburger_2_carne.3mf` | carne | carne |
| `hamburger_3_formaggio.3mf` | formaggio | formaggio |
| `hamburger_4_insalata.3mf` | insalata | insalata |
| `hamburger_5_pomodoro.3mf` | pomodoro | pomodoro |
| `hamburger_6_pane_sopra.3mf` | pane sopra | pane |
| `hamburger_tutti_i_pezzi.3mf` | i 6 pezzi insieme (cancella quelli da non stampare) | – |

Consiglio: un piatto pieno di pani (sotto e sopra insieme, stesso colore), poi uno di carne, ecc.

**Montaggio:** sul perno del pane sotto infila carne → formaggio → insalata → pomodoro, poi premi il pane sopra finché la clip fa *clic*. Per renderlo definitivo, una goccia di colla nella sede del pane sopra.

## Pizza a pezzi (nessun cambio filamento)

Quattro pezzi piatti, ognuno di un colore, che si incastrano uno nell'altro: ogni pezzo entra per 0,8 mm nella sede del pezzo sotto e sporge di 0,8 mm.
Gioco tra pezzo e sede: **0,25 mm per lato** (parametro `GIOCO` in `genera_addobbi.py`, consigliato 0,2-0,3 mm sulla P2S).

| File | Pezzo | Colore | Spessore |
|---|---|---|---|
| `pizza_pezzi_1_base.3mf` | base con sede per la salsa e logo sotto | impasto (giallo chiaro) | 5,0 mm |
| `pizza_pezzi_2_salsa.3mf` | salsa con sede per la mozzarella | rosso | 1,6 mm |
| `pizza_pezzi_3_mozzarella.3mf` | mozzarella con sedi per il salame | giallo | 1,6 mm |
| `pizza_pezzi_4_salame.3mf` | 4 fette di salame | rosso (anche lo stesso della salsa) | 1,6 mm |
| `pizza_pezzi_tutti_i_pezzi.3mf` | i 4 pezzi insieme | – | – |

Salsa e salame possono uscire dallo stesso piatto rosso. **Montaggio:** salsa nella base, mozzarella nella salsa, fette nella mozzarella; se gli incastri sono lenti, una goccia di colla.

## Riempimento consigliato

- Addobbi piatti: 20–30%.
- Hamburger, patatine, tramezzino: 10–15%, 2 perimetri (restano leggeri sul ramo).
