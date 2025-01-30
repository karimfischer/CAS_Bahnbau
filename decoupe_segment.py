import geopandas as gpd
from shapely.geometry import MultiLineString, LineString
import pandas as pd
import matplotlib.pyplot as plt


# Charger le shapefile des lignes ferroviaires (qui peut être un MultiLineString ou une collection de MultiLineStrings)
shapefile_path = "20250128-etat-voie.geojson"
gdf_railways = gpd.read_file(shapefile_path)

# Charger votre DataFrame non géographique
df = pd.read_csv('out3.csv',
    na_values=["N/A", "NA", "-", " "],    # Gérer les valeurs manquantes
    chunksize=None,                       # Lire tout d'un coup, ou par morceaux si fichier volumineux
    low_memory=False,                     # Accélère les fichiers complexes,
    encoding = 'UTF8'
    )

# Assurez-vous que votre shapefile et votre DataFrame utilisent le même CRS
gdf_railways = gdf_railways.to_crs(epsg=2056)  # Ou un CRS adapté à votre cas

# Le point de départ de la ligne ferroviaire (90.48 km)
km_start_reference = 90.068


# Fonction pour créer un tronçon géographique suivant la géométrie de la ligne (en MultiLineString)
def create_rail_segment(railway_multi_lines, km_start, km_end, km_start_reference):
    segments = []

    # Ajuster les km_debut et km_fin par rapport au km de départ de la ligne (90.48 km)
    km_start_adjusted = km_start - km_start_reference
    km_end_adjusted = km_end - km_start_reference
    current_length = 0  # Longueur cumulée de la ligne
    segment_start = None
    segment_end = None
    start_segment_found = False

    for line in railway_multi_lines.geoms:

        line_length = line.length

        # Vérifier si l'intervalle de km est dans la ligne actuelle
        if (current_length < km_end_adjusted and current_length + line_length > km_start_adjusted):

            if not start_segment_found:
                # Si on n'a pas encore trouvé le point de départ, on découpe à partir du km_debut
                start_position = (km_start_adjusted - current_length) / line_length
                segment_start = line.interpolate(start_position, normalized=True).coords[0]
                start_segment_found = True
            else:
                # Sinon, on peut découper de manière normale
                segment_start = line.interpolate(0, normalized=True).coords[0]

            # Découper à partir du km_debut dans la ligne si nécessaire
            if current_length + line_length >= km_end_adjusted:
                # Si la ligne couvre la fin du tronçon, découper jusqu'au km_fin
                end_position = (km_end_adjusted - current_length) / line_length
                segment_end = line.interpolate(end_position, normalized=True).coords[0]
                segments.append(LineString([segment_start, segment_end]))
                break  # On a terminé le tronçon
            else:
                # Sinon, on prend la ligne entière et on passe à la suivante
                segment_end = line.interpolate(1, normalized=True).coords[0]
                segments.append(LineString([segment_start, segment_end]))

        # Mettre à jour la longueur cumulée
        current_length += line_length



    # Retourner un MultiLineString constitué des sous-segments extraits
    return MultiLineString(segments)


# Liste pour stocker les géométries des nouveaux tronçons
segments = []

# Créer les tronçons pour chaque ligne de votre DataFrame
for index, row in df.iterrows():
    # Prendre la géométrie correspondant à cette ligne ferroviaire (MultiLineString)
    railway_multi_lines = gdf_railways.geometry.iloc[index]

    # Créer le tronçon géographique suivant la géométrie de la ligne entre km_debut et km_fin
    segment = create_rail_segment(railway_multi_lines, row['km_debut'], row['km_fin'], km_start_reference)

    # Ajouter à la liste des segments
    segments.append({
        'km_debut': row['km_debut'],
        'km_fin': row['km_fin'],
        'geometry': segment
    })

# Créer un GeoDataFrame avec les nouveaux tronçons
gdf_segments = gpd.GeoDataFrame(segments, geometry='geometry')

# Assurez-vous que le CRS est le bon
gdf_railways = gdf_railways.to_crs(epsg=4326)
gdf_segments = gdf_segments.set_crs(gdf_railways.crs)

# Sauvegarder dans un shapefile
output_shapefile_path = "path_to_output_shapefile.shp"
gdf_segments.to_csv("path_to_output_shapefile.csv", index=False)
gdf_segments.to_file(output_shapefile_path)

# Afficher un aperçu du résultat
print(gdf_segments)

# Charger le shapefile des tronçons extraits
gdf_segments = gpd.read_file("path_to_output_shapefile.shp")

# Charger le shapefile des lignes ferroviaires (pour contexte)

gdf_railways = gpd.read_file("20250128-etat-voie.geojson")

# Vérifier et harmoniser les CRS
if gdf_segments.crs != gdf_railways.crs:
    gdf_segments = gdf_segments.to_crs(gdf_railways.crs)

# Afficher la carte
fig, ax = plt.subplots(figsize=(10, 6))

# Tracer la ligne ferroviaire complète (en gris)
gdf_railways.plot(ax=ax, color="gray", linewidth=2, linestyle="--", label="Ligne ferroviaire")

# Tracer les tronçons extraits (en rouge)
gdf_segments.plot(ax=ax, color="red", linewidth=3, label="Tronçons extraits")

# Ajouter une légende et un titre
plt.legend()
plt.title("Tronçons extraits le long de la ligne ferroviaire")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Afficher la carte
plt.show()