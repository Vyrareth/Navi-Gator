### Database Documentation ###

This database is basically meant to encapsulate the entire satellite image need for Camden County and potentially other counties depending on how well our stuff runs.

In the screenshot file, you can clearly see the schema for the database, including which primary/foreign keys are included in each table; additionally, multiple items 
may be marked as required for entry (designated as 'NOT NULL') and are therefore important to include during data entry.  There should be a spreadsheet that reflects 
the real-world data that the satellite images require, especially within a sector (with coordinates important for general location of the roads).   

A general guide: 

State is the State.  

County is a subsection of state within that state.

Sector is a square section of the county from the satellite imagery.  A sector is a singular .tif (image) file, on which all roads in the sector are displayed. 

Road is basically the collection of roads within a sector, not tied directly to an image.  

Segment is the segment of a Sector which is a screenshot focused solely on the road.  This is to be used for the CNN's classification and is what we will primarily be working with.  

