import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from scipy import ndimage
from shapely.geometry import Point



def heatmap(d, 
            bins=(100,100), 
            smoothing=1.3, 
            cmap='jet'):
    
    x = d.geometry.x
    y = d.geometry.y
    heatmap, xedges, yedges = np.histogram2d(y, x, bins=bins)
    extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]

    #logheatmap = np.log(heatmap)
    #logheatmap[np.isneginf(logheatmap)] = 0
    
    heatmap = ndimage.filters.gaussian_filter(heatmap, 
                                                 smoothing, 
                                                 mode='nearest')
    
    #return logheatmap
    d.plot(color='none', 
                     edgecolor='white', 
                     linewidth=.5, alpha=.5)

    plt.imshow(heatmap, cmap=cmap, extent=extent)
    plt.colorbar()
    plt.gca().invert_yaxis()
    plt.show()



if '__main__' == __name__:
    
    # this shapefile is from natural earth data
    # http://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/
        
    X = np.random.normal(-40, 10, size=100)
    Y = np.random.normal(0, 10, size=100)
    Z = np.random.normal(2, 10, size=100)
    
    gdf = gpd.GeoDataFrame({'Z':Z
                            }, geometry=[Point(x, y) for x,y in zip(X,Y)])
    
    heatmap(gdf, 
            bins=(100,100),
            smoothing=2.5, cmap='jet')