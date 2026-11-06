// =====================================================
//  Emozioni in 3D - Segnaposto con nome in piedi
//  Modifica i parametri qui sotto e premi F6 + "Export STL"
// =====================================================

/* [Testo] */
nome = "Giulia";
font_nome = "Liberation Serif:style=Bold Italic";

/* [Dimensioni (mm)] */
altezza_lettere = 18;   // altezza del nome
spessore_lettere = 4;   // profondità delle lettere
altezza_base = 3;       // spessore della base
margine_base = 4;       // quanto la base sporge attorno al nome
fessura_cartoncino = true; // taglio dietro per infilare un bigliettino
spessore_fessura = 1.0;

/* [Esportazione] */
parte = "tutto"; // [tutto, base, nome]

$fn = 64;

// misura approssimata della scritta per dimensionare la base
lunghezza = len(nome) * altezza_lettere * 0.62 + 2*margine_base;
profondita = spessore_lettere + 2*margine_base + 6;

module base() {
    difference() {
        translate([-lunghezza/2, -profondita/2, 0])
            linear_extrude(altezza_base)
                offset(r = 3) offset(delta = -3)
                    square([lunghezza, profondita]);
        if (fessura_cartoncino)
            translate([-lunghezza*0.35, profondita/2 - 4, 1])
                cube([lunghezza*0.7, spessore_fessura, altezza_base]);
    }
}

module lettere() {
    // lettere in piedi, leggermente affondate nella base per unirle
    translate([0, spessore_lettere/2 - 2, altezza_base - 0.4])
        rotate([90, 0, 0])
            linear_extrude(spessore_lettere)
                text(nome, font = font_nome, size = altezza_lettere,
                     halign = "center", valign = "baseline");
}

if (parte == "tutto")     { color("white") base(); color("gold") lettere(); }
else if (parte == "base") base();
else if (parte == "nome") lettere();
