# WebScrapingJS

<h3>Files</h3>

- `templates/index.html`: includes the web design (the html blocks) + hover on instructions script + a script that connects the buttons to other files 
- `app.py`: a flask app that connects the .html with the .py file. Flask documentation can be found here: https://flask.palletsprojects.com/en/stable/.
- `requirements.txt`: the names of the libraries used in the code
- `user_agents.py`: a data variable that includes a bunch of possible user agents (chosen randomly in the script)
-  `webs_craping.py`: logic to get the product information from Amazon

<h3> Running the program: </h3>

- The program can be opened by double clicking the .app file and going to this URL: http://127.0.0.1:10000/.
- Produces a .csv file that is downloaded to the user's computer when it finishes running.


<h3>Ways to improve the program:</h3>

- I tried to use Render to get a website to host the code: https://webscraping-k68h.onrender.com. However, after a few links, Amazon blocked requests from the program. So, it can only run locally.