import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import linemerge
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import folium

# Charger les fichiers shapefile
segments = gpd.read_file("20250128-etat-voie_VM.geojson")  # Contient des MultiLineString
points_km = gpd.read_file("points_km.geojson")  # Contient les points
points_km["km_extrait"] = points_km['name'].str.split('-').str[3]

# Vérifier le système de projection et s'assurer qu'ils sont compatibles
if segments.crs != points_km.crs:
    points_km = points_km.to_crs(segments.crs)

def find_km_for_point(point, line, km_points):
    """
    Trouve le kilométrage correspondant à un point sur un segment en interpolant
    entre les points kilométriques.
    """
    # Trouver les points kilométriques projetés sur la ligne

    projected_distances = line.project(km_points.geometry)

    # Trouver le point le plus proche sur la ligne
    nearest_idx = np.argmin(np.abs(projected_distances - line.project(point)))

    # Retourner le kilométrage correspondant
    return km_points.iloc[nearest_idx]["km_extrait"]


def find_nearest_point(reference_point, points_list):
    """
    Trouve le point le plus proche du point de référence dans une liste de points.

    :param reference_point: Point donné (Shapely Point)
    :param points_list: Liste de points (Shapely Points)
    :return: Le point le plus proche (Shapely Point)
    """
    closest_idx = points_list.geometry.distance(reference_point).idxmin()
    return points_list.loc[closest_idx, "km_extrait"], points_list.geometry.distance(reference_point).min()


def convert_multilinestring_to_linestring(geom):
    return linemerge(geom)

# Fonction pour supprimer la coordonnée Z
def remove_z(point):
    if isinstance(point, Point) and point.has_z:  # Vérifie si c'est un POINT Z
        return Point(point.x, point.y)  # Crée un POINT en 2D (sans Z)
    return point  # Garde tel quel si ce n'est pas un POINT Z

# Appliquer la conversion à toute la colonne "geometry"
points_km["geometry"] = points_km["geometry"].apply(remove_z)
print(segments.iloc[1].geometry.geoms[0].coords[0])
print(segments.iloc[1].geometry.geoms[0])

# Appliquer l'algorithme à chaque segment
km_start = []
km_end = []

segment = segments["geometry"].apply(convert_multilinestring_to_linestring)

for i in range(len(segments)):
    start_point = Point(segments.iloc[i].geometry.geoms[0].coords[0])# Point(line.coords[0])  # Début du segment
    end_point = Point(segments.iloc[i].geometry.geoms[-1].coords[-1])  # Fin du segment

    # Trouver les kilomètres associés
    #km_start.append(find_km_for_point(start_point, segment.iloc[i], points_km))
    #km_end.append(find_km_for_point(end_point, segment.iloc[i], points_km))
    km_start.append(find_nearest_point(start_point, points_km)[0])
    km_end.append(find_nearest_point(end_point, points_km)[0])
# Ajouter les résultats au GeoDataFrame des segments
segments["km_start"] = km_start
segments["km_end"] = km_end

segments.to_file("segments_avec_km.shp")
segments.to_csv("segments_avec_km.csv", index=False)

# Vérifier les projections et convertir en EPSG:3857 (nécessaire pour le fond de carte)
if segments.crs != "EPSG:3857":
    segments = segments.to_crs(epsg=3857)

if points_km.crs != "EPSG:3857":
    points_km = points_km.to_crs(epsg=3857)

# Créer la figure et les axes
fig, ax = plt.subplots(figsize=(12, 8))

# Afficher les segments en bleu
segments.plot(ax=ax, edgecolor="blue", linewidth=1, label="Segments")

# Afficher les points kilométriques en rouge
points_km.plot(ax=ax, color="red", markersize=0.5, label="Points KM")

# Ajouter le fond de carte (Google Maps ou OpenStreetMap)
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)  # Fond clair type Google Maps

# Ajouter une légende et un titre
plt.legend()
plt.title("Segments et Points KM sur un fond Google Maps")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Afficher la carte
#plt.show()

# FOLIUM
# Convertir en WGS84 (EPSG:4326) car Folium utilise latitude/longitude

segments = gpd.read_file('segments_avec_km.shp')

if segments.crs != "EPSG:4326":
    segments = segments.to_crs(epsg=4326)

if points_km.crs != "EPSG:4326":
    points_km = points_km.to_crs(epsg=4326)

# Trouver le centre de la carte
mean_lat = points_km.geometry.y.mean()
mean_lon = points_km.geometry.x.mean()

# Créer une carte centrée sur les données
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=12, tiles="CartoDB Positron")

# Ajouter les segments sur la carte
for _, row in segments.iterrows():
    if row.geometry.geom_type == "MultiLineString":  # Vérifier si c'est un MultiLineString
        for line in row.geometry.geoms:  # Itérer sur chaque sous-`LineString` dans `MultiLineString`
            popup_content = str(row.to_dict())
            folium.PolyLine(
                locations=[(point[1], point[0]) for point in line.coords],  # (lat, lon)
                color="blue",
                weight=3,
                opacity=0.7
            ).add_to(m)
    else:
        popup_content = str(row.to_dict())
        folium.PolyLine(
            locations=[(point[1], point[0]) for point in row.geometry.coords],  # (lat, lon)
            color="blue",
            weight=3,
            opacity=0.7,
            popup=popup_content
        ).add_to(m)

# Ajouter les points kilométriques sur la carte
for _, row in points_km.iterrows():
    folium.Marker(
        location=[row.geometry.y, row.geometry.x],  # (latitude, longitude)
        popup=f"Point KM",
        icon=folium.Icon(color="red", icon="info-sign"),
    )

# Sauvegarder la carte en HTML et l'afficher
m.save("map_interactive.html")
