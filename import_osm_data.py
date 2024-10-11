# %%
import osmnx as ox
import pandas as pd
import geopandas as gpd
# %% 
city_name = 'Criciúma, Santa Catarina, Brazil'
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
# DB FROM > TO
# osmid > osmid
# oneway > WILL NOT BE IMPORTED
# lanes > nr_faixas
# highway > tipo_via
# reversed > WILL NOT BE IMPORTED
# length > comprimento
# geometry > geom
# ref > observacao
# name > nome
# maxspeed > WILL NOT BE IMPORTED
# junction > WILL NOT BE IMPORTED
# bridge > WILL NOT BE IMPORTED
# tunnel > WILL NOT BE IMPORTED
edges['tunnel'] 

# %%
# Removing duplicate geometries (inverted ones)
edges = edges.reset_index()

edges["node_pair"] = edges.apply(lambda row: tuple(sorted([row.u, row.v])), axis=1)

duplicate_edges = edges[edges.duplicated(subset="node_pair", keep=False)]

unique_edges = edges.drop_duplicates(subset="node_pair", keep="first")
