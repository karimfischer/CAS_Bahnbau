import pandas as pd
from fractions import Fraction

# Charger les fichiers CSV
segments_file = "segments_superieurs.csv"
report_file = "report2025-01-08_13-28.csv"

segments_df = pd.read_csv(segments_file)
report_df = pd.read_csv(report_file, encoding='latin-1')

# Convertir les kilomètres von/bis en km (diviser par 1000)
report_df["von_km"] = report_df["von"] / 1000
report_df["bis_km"] = report_df["bis"] / 1000


# Fonction pour vérifier si un nombre est rationnel
def is_rational(value):
    try:
        frac = Fraction(value).limit_denominator()
        return frac.denominator != 1  # Vérifie si le dénominateur est > 1
    except:
        return False


# Créer une liste pour stocker les nouvelles lignes
new_rows = []

for _, segment in segments_df.iterrows():
    km_start, km_end = segment["km_start"], segment["km_end"]

    # Filtrer les rayons de courbe qui chevauchent le tronçon
    overlapping_curves = report_df[(report_df["von_km"] < km_end) & (report_df["bis_km"] > km_start)]

    if overlapping_curves.empty:
        segment["rayon_de_courbe"] = None
        new_rows.append(segment)
    else:
        sorted_curves = overlapping_curves.sort_values(by="von_km")
        previous_rayon = None
        new_km_start = km_start

        for _, curve in sorted_curves.iterrows():
            curve_start, curve_end = curve["von_km"], curve["bis_km"]

            # Extraire et ajuster le rayon de courbe
            try:
                rayon = curve["Nom_Infrastructure_Horizontal geometry"]
                if is_rational(rayon) and rayon != 0:
                    rayon = 1 / rayon  # Prendre l'inverse si c'est rationnel
                rayon = round(rayon)  # Arrondir à l'unité près
            except ValueError:
                rayon = None

            if previous_rayon is None:
                previous_rayon = rayon
                new_km_start = max(km_start, curve_start)
            elif rayon != previous_rayon:
                new_segment = segment.copy()
                new_segment["km_start"] = new_km_start
                new_segment["km_end"] = min(km_end, curve_start)
                new_segment["rayon_de_courbe"] = previous_rayon
                new_rows.append(new_segment)
                new_km_start = curve_start
                previous_rayon = rayon

        # Ajouter le dernier tronçon si besoin
        if new_km_start < km_end:
            new_segment = segment.copy()
            new_segment["km_start"] = new_km_start
            new_segment["km_end"] = km_end
            new_segment["rayon_de_courbe"] = previous_rayon
            new_rows.append(new_segment)

# Convertir en DataFrame
final_df = pd.DataFrame(new_rows)

# Sauvegarder le fichier mis à jour
output_file = "segments_superieurs_avec_rayon.csv"
final_df.to_csv(output_file, index=False)
print(f"Fichier enregistré : {output_file}")
