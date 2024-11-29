# %%
import osmnx as ox
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
# %% Dados base
city_name = 'Criciúma, Santa Catarina, Brazil'

usuario = 'postgres'
senha = 'postgres'
host = 'localhost'
porta = 5434
database = 'postgres'
conexao = f'postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/'
engine = create_engine(conexao)

# %% IMPORTANDO LOGRADOUROS...
graph = ox.graph_from_place(city_name, network_type='drive')
nodes, edges = ox.graph_to_gdfs(graph) # nós, arestas

# %%
# https://gis.stackexchange.com/questions/455569/exporting-list-type-field-using-geopandas
output_path = 'C:\\Users\\ferna\\Downloads\\'
nodes_json = nodes.to_json()
edges_json = edges.to_json()

with open(output_path+"nodes.geojson", 'w', encoding='utf-8') as file:
    file.write(nodes_json)

with open(output_path+"edges.geojson", 'w', encoding='utf-8') as file:
    file.write(edges_json)

# %%
print(edges.columns)

# %%
# edges has MultiIndex (u, v, key): 
# u (origin) and v (destination) are nodes id; key are used for repeated u, v values. 
isinstance(edges.index, pd.MultiIndex) # True

# %%
# ['osmid', 'oneway', 'lanes', 'highway', 'reversed', 'length', 
# 'geometry', 'ref', 'name', 'maxspeed', 'junction', 'bridge', 'tunnel']
edges['tunnel'] 

# %%
# Removing duplicate geometries (inverted ones)
edges = edges.reset_index()

edges["node_pair"] = edges.apply(lambda row: tuple(sorted([row.u, row.v])), axis=1)

duplicate_edges = edges[edges.duplicated(subset="node_pair", keep=False)]

unique_edges = edges.drop_duplicates(subset="node_pair", keep="first")

# %%
# DB FROM > TO
# osmid > osmid
# oneway > WILL NOT BE IMPORTED
# lanes > nr_faixas
# highway > tipo_via
# reversed > WILL NOT BE IMPORTED
# length > comprimento
# geometry > geometry
# ref > observacao
# name > nome
# maxspeed > WILL NOT BE IMPORTED
# junction > WILL NOT BE IMPORTED
# bridge > WILL NOT BE IMPORTED
# tunnel > WILL NOT BE IMPORTED
ruas = unique_edges[['osmid', 'lanes', 'highway', 'length', 'geometry', 'ref', 'name']]

ruas.rename(columns={'lanes': 'nr_faixas', 'highway': 'tipo_via', 
                     'length': 'comprimento', 'ref': 'observacao', 
                     'name': 'nome'}, inplace=True)

# %%
ruas.to_postgis(name="ruas", con=engine, schema='ygis', if_exists="replace", index=False)

# %% Importando Escolas
school_gdf = ox.features.features_from_place(query=city_name, tags={'amenity': 'school'})

# %%
output_path = 'C:\\Users\\ferna\\Downloads\\'
school_json = school_gdf.to_json()

with open(output_path+"schools.geojson", 'w', encoding='utf-8') as file:
    file.write(school_json)

# %%
school_gdf['geometry'] = school_gdf['geometry'].apply(
    lambda geom: geom.representative_point() if geom.geom_type == 'Polygon' else geom
)

if isinstance(school_gdf.index, pd.MultiIndex):
    school_gdf = school_gdf.reset_index()

# %%
# DB FROM > TO
# 'osmid' > osmid
# 'amenity' > WILL NOT BE IMPORTED
# 'name' > nome
# 'geometry' > geometry
# 'wheelchair' > WILL NOT BE IMPORTED
# 'access' > WILL NOT BE IMPORTED
# 'addr:housenumber' > WILL NOT BE IMPORTED
# 'addr:street' > WILL NOT BE IMPORTED
# 'operator' > WILL NOT BE IMPORTED
# 'short_name' > WILL NOT BE IMPORTED
# 'addr:postcode' > WILL NOT BE IMPORTED
# 'alt_name' > WILL NOT BE IMPORTED
# 'contact:phone' > WILL NOT BE IMPORTED
# 'nodes' > WILL NOT BE IMPORTED
# 'addr:city' > WILL NOT BE IMPORTED
# 'official_name' > WILL NOT BE IMPORTED
# 'phone' > WILL NOT BE IMPORTED
# 'addr:suburb' > WILL NOT BE IMPORTED
# 'website' > WILL NOT BE IMPORTED
# 'ways' > WILL NOT BE IMPORTED
# 'type > WILL NOT BE IMPORTED'
escolas = school_gdf[['osmid', 'name', 'geometry']]

escolas.rename(columns={'name': 'nome'}, inplace=True)
#%%
escolas.to_postgis(name="escolas", con=engine, schema='ygis', if_exists="replace", index=False)