# %%
import osmnx as ox
import geopandas as gpd
# %% 
city_name = 'Criciúma, Santa Catarina, Brazil'
graph = ox.graph_from_place(city_name, network_type='drive')
nodes, edges = ox.graph_to_gdfs(graph)

# %%
print(edges.head())

# %%
print(nodes.head())