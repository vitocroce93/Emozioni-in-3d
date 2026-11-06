// =====================================================
//  Emozioni in 3D - Portachiavi / bomboniera a cuore
//  Modifica i parametri qui sotto e premi F6 + "Export STL"
// =====================================================

/* [Testo] */
nome   = "Sofia";        // nome del festeggiato
data   = "12.04.2026";   // data dell'evento
font_nome = "Liberation Serif:style=Bold Italic";
font_data = "Liberation Sans:style=Bold";

/* [Dimensioni (mm)] */
larghezza       = 55;   // larghezza del cuore
spessore_base   = 3;    // spessore del cuore
altezza_testo   = 1.2;  // rilievo delle scritte
diametro_foro   = 5;    // foro per l'anellino
bordo           = 1.6;  // cornice in rilievo

/* [Esportazione] */
// "tutto" = pezzo unico; "base" o "testo" = parti separate per stampa a 2 colori
parte = "tutto"; // [tutto, base, testo]

$fn = 96;

// ---------- forme ----------
module cuore(w) {
    r = w / 4;
    translate([0, -w*0.18])
    hull() {
        translate([-r, r]) circle(r);
        translate([0, -w*0.55]) circle(0.6);
        translate([-w*0.42, r*0.4]) circle(r*0.55);
    }
    translate([0, -w*0.18])
    hull() {
        translate([ r, r]) circle(r);
        translate([0, -w*0.55]) circle(0.6);
        translate([ w*0.42, r*0.4]) circle(r*0.55);
    }
}

pos_foro = [0, larghezza*0.33];

module base_2d() {
    difference() {
        union() {
            cuore(larghezza);
            // occhiello per l'anellino
            translate(pos_foro) circle(d = diametro_foro + 5);
        }
        translate(pos_foro) circle(d = diametro_foro);
    }
}

module testo_2d() {
    // cornice
    difference() {
        offset(-1.2) cuore(larghezza);
        offset(-1.2 - bordo) cuore(larghezza);
    }
    // nome (si adatta alla larghezza)
    translate([0, -larghezza*0.08])
        resize([larghezza*0.62, 0], auto = true)
            text(nome, font = font_nome, size = 10, halign = "center", valign = "center");
    // data
    translate([0, -larghezza*0.33])
        text(data, font = font_data, size = larghezza*0.075, halign = "center", valign = "center");
}

module base()  { linear_extrude(spessore_base) base_2d(); }
module testo() { translate([0,0,spessore_base]) linear_extrude(altezza_testo) testo_2d(); }

if (parte == "tutto")      { color("white") base(); color("gold") testo(); }
else if (parte == "base")  base();
else if (parte == "testo") testo();
