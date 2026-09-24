### Basic Navi-Gator Map Access Framework ###
### Created/written by Don Frenzel ###
### Version Alpha 0.0.1 ###

### imports here:

import folium
#Note: Folium helps with basic python map software
import geocoder
#Note: Geocoder necessary for getting personal location for device when the code is run

import networkx as nx
import osmnx as ox

import geopandas as gpd

#general
import os
import webbrowser
from geopy.geocoders import Nominatim


mapboxAccessTok= 'askme'

###Function to get longitude and latitude automatically so that the map has a point to center itself on.  Uses IP address for now for ease.  
def getLongLat():
    loc=geocoder.ip('me')
    if(loc.latlng is not None):
        latitude,longitude=loc.latlng
        return latitude,longitude
    else:
        print("Location not found/recognized from ip; Please try again later when there is a better connection available")
        return None

###FYI, this uses geopy, which 
loc= Nominatim(user_agent='GetLoc')
###enter location name, as is into the python prompt

locName=input("Please input the address of your current location: \n")
destName=input("Please input the address of your destination: \n")
getLocL=loc.geocode(locName)
getLocD=loc.geocode(destName)

print(getLocL.address,'\n')
print(getLocD.address,'\n')

latL=getLocL.latitude
longL=getLocL.longitude

latD=getLocD.latitude
longD=getLocD.longitude

print('Latlong Cur: ',latL,longL)
print('Latlong Dest: ',latD,longD)

###Next should be to get a between A and B shortest path thing going.
locLAddr=getLocL.address
locDAddr=getLocD.address
#latL,longL
#latD,longD
##Get north, south, east, and west amounts to define the map.
north=max(latL,latD)+0.01 #to account for north, we take the max, as that's the positive for latitude
south=min(latL,latD)-0.01
east=max(longL,longD)+0.01
west=min(longL,longD)-0.01

#get the street map for that area as requested
graph=ox.graph_from_bbox(bbox=(west,south,east,north),network_type='drive',simplify=True)

#get the nodes nearest to the locations specified
originNode=ox.distance.nearest_nodes(graph,X=longL,Y=latL)
destNode=ox.distance.nearest_nodes(graph,X=longD,Y=latD)

#get route
route=nx.shortest_path(graph, originNode,destNode,weight='length')

#create the map
roadMap=ox.plot.plot_graph_routes(graph,[route],route_colors='blue',route_linewidth=5)

folium.Marker(location=[latL,longL],popup='Current Location',icon=folium.Icon(color='green',icon='info-sign')).add_to(roadMap)
folium.Marker(location=[latD,longD],popup='Destination',icon=folium.Icon(color='red',icon='info-sign')).add_to(roadMap)

#save the file
fileName='roadmapFile.html'
roadMap.save(fileName)


###Make it so that it's custom.Check the route through this.  
###For getting the map up and running:
#getLocL is the current location name
#destName is current destinatio

#for gps version
'''
satMap=folium.Map(location=[latL,longL],zoom_start=12,tiles=None)

tileSetID='mapbox.satellite'
tileURL=f'https://api.mapbox.com/v4/{tileSetID}/{{z}}/{{x}}/{{y}}.jpg?access_token={mapboxAccessTok}'
attrib='mapbox satellite'


folium.TileLayer(tiles=tileURL,attr=attrib,name='Mapbox Satellite Streets',max_zoom=19).add_to(satMap)

folium.Marker(location=[latL,longL],popup='Current Location',icon=folium.Icon(color='blue',icon='info-sign')).add_to(satMap)
folium.Marker(location=[latD,longD],popup='Destination',icon=folium.Icon(color='red',icon='info-sign')).add_to(satMap)

satMap.save('mapboxFile.html')
'''

###Automatically open the file
filePath=os.path.abspath(fileName)
url=f'file://{filePath}'
webbrowser.open_new_tab(url)

##Test prints
print(latL)
print(longL)
