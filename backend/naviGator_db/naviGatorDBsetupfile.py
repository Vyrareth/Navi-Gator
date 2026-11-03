### DON FRENZEL - SQL Database Setup Code for Navi-Gator

### Vers. 2.1

import sqlite3

### Run table creation ###
conn = sqlite3.connect('naviGator_camcountyUpdated_db.db')
cursor = conn.cursor()

### MANDATORY: Enable foreign key enforcement for this connection session
cursor.execute('PRAGMA foreign_keys = ON;')

### Create State Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS State (
        StateID INTEGER,
        State_name VARCHAR(50),
        PRIMARY KEY (stateID));
    ''')

### Establish County Table (Integer primary key)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS County (
        CountyID INTEGER PRIMARY KEY,
        StateID INTEGER,
        County_Name TEXT,
        FOREIGN KEY (StateID) REFERENCES State (StateID)
    ) STRICT;
    ''')

### Establish Sector Table (Optimized String Key via WITHOUT ROWID)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sector (
        SectorID TEXT PRIMARY KEY,
        CountyID INTEGER NOT NULL,
        Sector_Name TEXT,
        Sector_Uright_Lat REAL,
        Sector_Uright_Long REAL,
        Sector_Lleft_Lat REAL,
        Sector_Lleft_Long REAL,
        FOREIGN KEY (CountyID) REFERENCES County (CountyID)
    ) WITHOUT ROWID, STRICT;
    ''')

### Establish Road Table (Optimized String Key via WITHOUT ROWID)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Road (
        RoadID TEXT PRIMARY KEY,
        SectorID TEXT NOT NULL,
        Road_Name TEXT,
        FOREIGN KEY (SectorID) REFERENCES Sector (SectorID)
    ) WITHOUT ROWID, STRICT;
    ''')

### Establish Segments Table (Integer primary key, RoadID typed as TEXT to fix mismatch)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Segments (
        SegmentID INTEGER PRIMARY KEY,
        RoadID TEXT NOT NULL,
        Photo_file TEXT,
        FOREIGN KEY (RoadID) REFERENCES Road (RoadID)
    ) STRICT;
    ''')


### Data entry here

###RUN THESE IF AND ONLY IF YOU NEED TO POPULATE YOUR DATABASE INITIALLY

### New Jersey StateID is 3 (Since we were the third to ratify the constitution)
cursor.execute('INSERT OR IGNORE INTO state (stateID,state_name) VALUES (?,?)', (3,'New Jersey'))
cursor.execute('INSERT OR IGNORE INTO state (stateID,state_name) VALUES (?,?)', (2,'Pennsylvania'))

###NOTE: For County entry, please refer to the FIPS Codes (First two digits indicate state, last three indicate county: NJ is 34 for State and Camden County is 007, in this case just 7)
cursor.execute('INSERT OR IGNORE INTO county (countyID,stateID,county_name) VALUES (?,?,?)', (7,3,'Camden County'))

###Also blank this out
conn.commit()
'''
### SAMPLE CODE HERE
cursor.execute('SELECT * FROM county')
rows=cursor.fetchall()

print('CountyID','\t','StateID','\t','County Name\n')
for row in rows:
    #print(row[0],'\t\t',row[1])
    print(row[0],'\t\t',row[1],'\t\t',row[2])
### END SAMPLE CODE
'''
conn.close()


