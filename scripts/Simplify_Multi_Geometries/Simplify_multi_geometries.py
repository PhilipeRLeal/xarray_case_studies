
# coding: utf-8

# In[ ]:


def explode(gdf):
    """
    This function takes as entry an GeoDataFrame and returns another GeoDataFrame with its geometries simplified (exploded) 
    in case the given GDF had multi geometries (i.e.: multi polygons)
    
    """
    import geopandas as gpd
    
    indf = gdf
    outdf = gpd.GeoDataFrame(columns=indf.columns)
    for idx, row in indf.iterrows():
        if type(row.geometry) == 'Polygon':
            outdf = outdf.append(row,ignore_index=True)
        if type(row.geometry) == 'MultiPolygon':
            multdf = gpd.GeoDataFrame(columns=indf.columns)
            recs = len(row.geometry)
            multdf = multdf.append([row]*recs,ignore_index=True)
            for geom in range(recs):
                multdf.loc[geom,'geometry'] = row.geometry[geom]
            outdf = outdf.append(multdf,ignore_index=True)
    return outdf

