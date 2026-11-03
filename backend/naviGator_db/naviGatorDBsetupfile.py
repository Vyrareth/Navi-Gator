### DON FRENZEL - SQL Database Setup Code for Navi-Gator

### Vers. 2.0

import sqlite3

### Run table creation ###
conn = sqlite3.connect('naviGator_camcountyUpdated_db.db')
cursor = conn.cursor()

### MANDATORY: Enable foreign key enforcement for this connection session
cursor.execute('PRAGMA foreign_keys = ON;')

### Create State Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS state (
        stateID INTEGER,
        state_name VARCHAR(50),
        PRIMARY KEY (stateID));
    ''')

### Establish County Table (Integer primary key)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS county (
        countyID INTEGER PRIMARY KEY,
        stateID INTEGER,
        County_Name TEXT,
        FOREIGN KEY (stateID) REFERENCES state (stateID)
    ) STRICT;
    ''')

### Establish Sector Table (Optimized String Key via WITHOUT ROWID)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sector (
        sectorID TEXT PRIMARY KEY,
        countyID INTEGER NOT NULL,
        sector_Name TEXT,
        sector_Uright_Lat REAL,
        sector_Uright_Long REAL,
        sector_Lleft_Lat REAL,
        sector_Lleft_Long REAL,
        FOREIGN KEY (countyID) REFERENCES county (countyID)
    ) WITHOUT ROWID, STRICT;
    ''')

### Establish Road Table (Optimized String Key via WITHOUT ROWID)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS road (
        roadID TEXT PRIMARY KEY,
        sectorID TEXT NOT NULL,
        road_Name TEXT,
        FOREIGN KEY (sectorID) REFERENCES sector (sectorID)
    ) WITHOUT ROWID, STRICT;
    ''')

### Establish Segments Table (Integer primary key, RoadID typed as TEXT to fix mismatch)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS segments (
        segmentID INTEGER PRIMARY KEY,
        roadID TEXT NOT NULL,
        photo_file TEXT,
        FOREIGN KEY (roadID) REFERENCES road (roadID)
    ) STRICT;
    ''')


### Data entry here

###RUN THESE IF AND ONLY IF YOU NEED TO POPULATE YOUR DATABASE INITIALLY

### New Jersey StateID is 3 (Since we were the third to ratify the constitution)
#cursor.execute('INSERT INTO state (stateID,state_name) VALUES (?,?)', (3,'New Jersey'))
#cursor.execute('INSERT INTO state (stateID,state_name) VALUES (?,?)', (2,'Pennsylvania'))

###NOTE: For County entry, please refer to the FIPS Codes (First two digits indicate state, last three indicate county: NJ is 34 for State and Camden County is 007, in this case just 7)
#cursor.execute('INSERT INTO county (countyID,stateID,county_name) VALUES (?,?,?)', (7,3,'Camden County'))

###Also blank this out
#conn.commit()

###
cursor.execute('SELECT * FROM county')
rows=cursor.fetchall()

print('countyID','\t','stateID','\t','County Name\n')
for row in rows:
    #print(row[0],'\t\t',row[1])
    print(row[0],'\t\t',row[1],'\t\t',row[2])


conn.close()


