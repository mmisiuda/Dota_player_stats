# Dota player basic statistics

This is a simple script to extract DotA2 player basic statistics using OpenDota API.

The script access the OpenDota API and retrieve information about given ID using the Requests library.

Data cleaning/organizing was made using Pandas.

App.py is a Python 3 script with Dash application made with Dash Bootstrap Components, the plots are made with Plotly.

Game_mode.json is needed to decode the names of game modes that OpenDota API uses.

Simply run the script (either in your IDE or in the terminal), dash will run localy on http://127.0.0.1:8050/, there input your Player ID (You can find it on pages like Dotabuff or OpenDota by inputing your Nickname) to display few charts with basic infos.

Using the Jupyter Notebook file (Dota_stats.ipynb) You can see some more charts and graphs and also freely explore your data.

Libraries needed are listed in Requirements file.

Enjoy!
