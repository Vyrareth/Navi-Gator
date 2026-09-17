### Basic Navi-Gator Map Access Framework ###
### Created/written by Don Frenzel ###
### Version Alpha 0.0.1 ###

### imports here:

import folium
#Note: Folium helps with basic python map software
import geocoder
#Note: Geocoder necessary for getting personal location for device when the code is run
import os
import webbrowser
from geopy.geocoders import Nominatim


mapboxAccessTok=askme

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
getLoc=loc.geocode(locName)
getLocD=loc.geocode(destName)

print(getLoc.address,'\n')
print(getLocD.address,'\n')

latL=getLoc.latitude
longL=getLoc.longitude

latD=getLocD.latitude
longD=getLocD.longitude

###Next should be to get a between A and B shortest path thing going.



###Make it so that it's custom.Check the route through this.  
###For getting the map up and running:
satMap=folium.Map(location=[latL,longL],zoom_start=12,tiles=None)

tileSetID='mapbox.satellite'
tileURL=f'https://api.mapbox.com/v4/{tileSetID}/{{z}}/{{x}}/{{y}}.jpg?access_token={mapboxAccessTok}'
attrib='mapbox satellite'


folium.TileLayer(tiles=tileURL,attr=attrib,name='Mapbox Satellite Streets',max_zoom=19).add_to(satMap)

folium.Marker(location=[latL,longL],popup='Current Location',icon=folium.Icon(color='blue',icon='info-sign')).add_to(satMap)
folium.Marker(location=[latD,longD],popup='Destination',icon=folium.Icon(color='red',icon='info-sign')).add_to(satMap)

satMap.save('mapboxFile.html')


###Automatically open the file
filePath=os.path.abspath('mapboxFile.html')
url=f'file://{filePath}'
webbrowser.open_new_tab(url)

##Test prints
print(latL)
print(longL)
