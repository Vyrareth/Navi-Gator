### DON FRENZEL - SQL Database Setup Code for Navi-Gator 1.0

import sqlite3

###'Connect' to database, specifically database made for the sat images.  
conn=sqlite3.connect('naviGator_camcounty_db.db')
cursor=conn.cursor() #basically allows for SQL commands to be made at all

### Run table creation ###
### State table only exists for the sake of possible expansion; disregard and route only to NJ
cursor.execute('''
    CREATE TABLE IF NOT EXISTS state (
        stateID INT NOT NULL,
        state_name VARCHAR(50),
        PRIMARY KEY (stateID)
    );
''')

### county table exists only for the sake of expansion; disregard and route only to Camden County for now
cursor.execute('''
    CREATE TABLE IF NOT EXISTS county (
		countyID INT NOT NULL,
        stateID INT NOT NULL,
        county_name VARCHAR(50),
        PRIMARY KEY (countyID),
        FOREIGN KEY (stateID) REFERENCES state(stateID)
    );
''')

###Note, each sector is supposed to act basically like a square from the NJ satellite; data is to be recorded and stored per each
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sector (
        sectorID INT NOT NULL,
        countyID INT NOT NULL,
        sector_name VARCHAR(50),
        sector_uleft_lat DECIMAL, -- may make these of NOT NULL type in the future but may not depending on need cases.  
        sector_uleft_lon DECIMAL,
        sector_lright_lat DECIMAL, 
        sector_lright_lon DECIMAL, 
		sector_file_loc VARCHAR(100) NOT NULL,
        PRIMARY KEY (sectorID),
        FOREIGN KEY (countyID) REFERENCES county(countyID)
    );
''')

###Stores data for any particular road, note that road type specifically denotes the road's use classification, that being 
###residential, Collector, Artery, & Freeway, which may help with future routing needs.  
cursor.execute('''
    CREATE TABLE IF NOT EXISTS road (
        roadID INT NOT NULL,
        sectorID INT NOT NULL,
        road_name VARCHAR(50),
        road_type VARCHAR(50),
        PRIMARY KEY (roadID),
        FOREIGN KEY (sectorID) REFERENCES sector(sectorID)
    );
''')

###Segment is specifically for locating photo files for CNN analysis
cursor.execute('''
    CREATE TABLE IF NOT EXISTS segment (
		segmentID INT NOT NULL, 
        roadID INT NOT NULL, 
        length_miles DECIMAL,
        photo_file_loc VARCHAR(100) NOT NULL,
        PRIMARY KEY (segmentID),
        FOREIGN KEY (roadID) REFERENCES road(roadID)
    );
''')


### Data entry here

###RUN THESE IF AND ONLY IF YOU NEED TO POPULATE YOUR DATABASE
### New Jersey StateID is 3 (Since we were the third to ratify the constitution)
#cursor.execute("INSERT INTO state (stateID,state_name) VALUES (?,?)", (3,"New Jersey"))
#cursor.execute("INSERT INTO state (stateID,state_name) VALUES (?,?)", (2,"Pennsylvania"))

###NOTE: For County entry, please refer to the FIPS Codes (First two digits indicate state, last three indicate county: NJ is 34 for State and Camden County is 007, in this case just 7)
#cursor.execute("INSERT INTO county (countyID,stateID,county_name) VALUES (?,?,?)", (7,3,"Camden County"))

#conn.commit()

###
cursor.execute("SELECT * FROM county")
rows=cursor.fetchall()

print("countyID","\t","stateID","\t","County Name\n")
for row in rows:
    #print(row[0],"\t\t",row[1])
    print(row[0],"\t\t",row[1],"\t\t",row[2])

conn.close()


