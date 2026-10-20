Steps to make sure the program runs on vs code


1)Create a blank folder and a separate python .venv folder in that blank folder on your device

2)Use that path to pip install Flask to that specific .venv folder created

3)Then make a "template" folder and save both that folder and the, "test_routing_app.py" in that blank folder 

4)Within that "template" folder should save the "routing_index.html" file to be pulled from for testing
	4a)If you do not have the file, "test_navigation.db" downloaded and saved in the same location as the files mentioned above, save and run the "create_test_database.py" in the same blank folder as the others to make it and save it for you. Additionally, on the terminal should have a print on the terminal screen notifying the database has been created.

5)Run the "test_routing_app.py" after making sure that file, the "template" folder with the "routing_index.htm" inside there, and "test_navigation.db" are all saved in the same location, hence making it easier by a blank folder to fill in.

6)Output on screen should give you some lines of text more for Flask to do it's job, but you will see a line, "Running on http://[whatever pops up for your screen]", the section after the // is a link to the Navi-Gator page with all the city lats and longs saved from the test Database.

