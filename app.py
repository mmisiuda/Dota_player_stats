import pandas as pd
import numpy as np

import requests
import json
import time
from datetime import datetime

import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.graph_objs import *
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# default stylesheet
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])  # BOOTSTRAP stylesheet


# functions needed to clean the data
def unix_time_converter(ts):

    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M')


def duration_converter(duration):
    sec = duration
    ty_res = time.gmtime(sec)
    res = time.strftime("%H:%M:%S", ty_res)

    return res


def game_mode_cleaner(mode):
    mode = mode[10:]
    mode = mode.replace("_", " ")

    return mode


heroes_link = f'https://api.opendota.com/api/heroStats'
r = requests.get(heroes_link)
heroes_df = pd.DataFrame(json.loads(r.text))

# APP LAYOUT
# ***************************************************************************************
app.layout = dbc.Container([

    dbc.Row([

        dbc.Col([

            html.Div([
                dcc.Input(id="insert_id",
                          placeholder='Insert ID', inputMode='numeric', type="text"),
                html.Button(
                    id="info_button", children=['Get info!'])
            ]
            )], xs=8, sm=4, md=2, lg=2, xl=1),

        dbc.Col(
            dcc.Graph(id='wins_pie',
                      figure={}),
            xs=8, sm=8, md=5, lg=3, xl=3
        ),

        dbc.Col(
            dcc.Graph(id='side',
                      figure={}),
            xs=8, sm=6, md=5, lg=3, xl=3
        ),

        dbc.Col(
            dcc.Graph(id='kda_bar',
                      figure={}),
            xs=8, sm=6, md=8, lg=4, xl=4
        )
    ], align='start', no_gutters=True, justify='start'),

    dbc.Row([

        dbc.Col([

            dcc.Graph(id='stacked_bar',
                      figure={})
        ], xs=8, sm=8, md=6, lg=5, xl=5
        ),

        dbc.Col([

            dcc.Graph(id='top_all_time_wins',
                      figure={})
        ], xs=8, sm=8, md=6, lg=5, xl=5
        )
    ], align='start', no_gutters=True, justify='start'),


    dbc.Row([

        dbc.Col(

            html.H4('Top 3 friends', className='text-left text-dark'),
            width={'size': 5, 'offset': 1},
            style={'fontSize': 9}
        ),

        dbc.Col(

            html.H4('Top 3 winning friends', className='text-left text-dark'),
            width={'size': 5},
            style={'fontSize': 9}
        )
    ], no_gutters=False, justify='start'),

    dbc.Row([

        dbc.Col([

            dcc.Graph(id='top_friends',
                      figure={})
        ], xs=8, sm=8, md=6, lg=5, xl=5
        ),

        dbc.Col([

            dcc.Graph(id='top_win_friends',
                      figure={})
        ], xs=8, sm=8, md=6, lg=5, xl=5
        )
    ])
], fluid=True)


# CALLBACKS
# ---------------------------------------------------------------------------------

@app.callback([Output("wins_pie", "figure"),
               Output("side", "figure"),
               Output("kda_bar", "figure"),
               Output("stacked_bar", "figure"),
               Output("top_all_time_wins", "figure"),
               Output("top_friends", "figure"),
               Output("top_win_friends", "figure")],
              [Input("info_button", "n_clicks")],
              [State("insert_id", "value")]
              )

def update_fig(*args):

    if not any(args):
        raise PreventUpdate
    else:
        num_clicks, player_id = args

    # get player info and make dataframes
    if num_clicks > 0:
        r = requests.get(f'https://api.opendota.com/api/players/{player_id}')

    if r.ok:
        player_df = pd.DataFrame(json.loads(r.text))

    matches_link = f'https://api.opendota.com/api/players/{player_id}/matches?significant=0'
    r = requests.get(matches_link)
    player_matches_df = pd.DataFrame(json.loads(r.text))

    player_heroes_link = f'https://api.opendota.com/api/players/{player_id}/heroes'
    r = requests.get(player_heroes_link)
    player_heroes_df = pd.DataFrame(json.loads(r.text))

    player_peers = f'https://api.opendota.com/api/players/{player_id}/peers'
    r = requests.get(player_peers)
    player_peers_df = pd.DataFrame(json.loads(r.text))

    # --------------------------------- data cleaning

    # remove some columns
    player_matches_df.drop(['lobby_type',
                            'version',
                            'party_size',
                            'leaver_status'], axis=1, inplace=True)

    # convert 'player_slot' into Radiant/Dire
    player_matches_df['player_slot'] = player_matches_df['player_slot'].apply(
        lambda x: 'Radiant' if x < 128 else 'Dire')

    # winner side istead of True/False Radiant win
    player_matches_df['radiant_win'] = player_matches_df['radiant_win'].apply(
        lambda x: 'Radiant' if x == True else 'Dire')

    # convert duration into proper format
    player_matches_df['duration'] = player_matches_df['duration'].fillna(0)
    player_matches_df['duration'] = player_matches_df['duration'].apply(duration_converter)

    # mapping skill levels
    skill_lvl = {1.0: 'Normal',
                 2.0: 'High',
                 3.0: 'Very high'}

    player_matches_df['skill'] = player_matches_df['skill'].map(skill_lvl)
    player_matches_df['skill'].fillna('N/A', inplace=True)

    # renaming columns
    renamed_col = ['Match ID', 'Side', 'Winner', 'Hero', 'Match date', 'Duration', 'Game mode',
                   'Kills', 'Deaths', 'Assists', 'Skill level']

    player_matches_df.columns = renamed_col

    # creating 'Result' column
    player_matches_df['Result'] = player_matches_df['Side'] == player_matches_df['Winner']
    player_matches_df['Result'] = player_matches_df['Result'].apply(lambda x: 'Win' if x == True else 'Loss')

    # reading in game modes json
    game_modes = pd.read_json('game_mode.json')
    game_modes = game_modes.transpose()
    game_modes.set_index('id', inplace=True)
    game_modes.drop('balanced', axis=1, inplace=True)
    game_modes['name'] = game_modes['name'].apply(game_mode_cleaner)
    # decoding game modes names
    player_matches_df['Game mode'] = player_matches_df['Game mode'].replace(game_modes['name'])

    player_heroes_df['hero_id'] = player_heroes_df['hero_id'].astype(int)
    player_heroes_df['hero_id'] = player_heroes_df['hero_id'].map(heroes_df.set_index('id')['localized_name'])
    player_heroes_df.drop('last_played', axis=1, inplace=True)
    player_heroes_df.columns = ['Hero', 'Games', 'Win', 'Games with', 'Wins with', 'Games against', 'Wins against']
    player_heroes_df['Win %'] = np.round((player_heroes_df['Win'] / player_heroes_df['Games']) * 100, 1)
    player_heroes_df['Win against %'] = \
        np.round((player_heroes_df['Wins against'] / player_heroes_df['Games against']) * 100, 1)
    player_heroes_df.columns = ['Hero', 'Games', 'Win', 'Games with', 'Wins with', 'Games against',
                                'Wins against', 'Win %', 'Win against %']
    player_heroes_cols = list(player_heroes_df.columns.values)
    player_heroes_cols.insert(3, player_heroes_cols.pop(-2))
    player_heroes_df = player_heroes_df[player_heroes_cols]
    player_heroes_df.fillna(0, inplace=True)

    top10_heroes = player_heroes_df[:10]
    top10_win_heroes = player_heroes_df.sort_values(by='Win %', ascending=False)[:10]

    kda_df = player_matches_df[['Kills', 'Deaths', 'Assists']]
    top10_heroes_dict = {name: player_matches_df.loc[player_matches_df['Hero'] == name] \
        [['Hero', 'Match date', 'Kills', 'Deaths', 'Assists']] for name in top10_heroes['Hero']}

    # top 3 friends
    top_friends = player_peers_df.sort_values(by='with_games', ascending=False).iloc[:3, [10, 5]]

    # top 3 winning friends
    top_winning_friends = player_peers_df.sort_values(by='with_win', ascending=False).iloc[:3, [10, 4]]

    # variables with various infos
    match_count = player_matches_df.shape[0]
    pl_wins = player_matches_df.loc[player_matches_df['Result'] == 'Win'].shape[0]
    pl_losses = player_matches_df.loc[player_matches_df['Result'] == 'Loss'].shape[0]

    total_kills = player_matches_df['Kills'].sum()
    total_deaths = player_matches_df['Deaths'].sum()
    total_assists = player_matches_df['Assists'].sum()

    player_df = player_df.to_dict()
    player_matches_df = player_matches_df.to_dict()
    player_peers_df = player_peers_df.to_dict()
    player_heroes_df = player_heroes_df.to_dict()

    # ---------------------------------------- plots
    # win/loss
    wins_pie = px.pie(player_matches_df,
                      names='Result',
                      width=320, height=320,
                      hole=.4,
                      color='Result',
                      color_discrete_map={'Win': '#7FC57D',
                                          'Loss': '#F1572E'}
                      )

    wins_pie.update_traces(textposition='outside',
                           textinfo='label+percent',
                           hoverinfo='label+percent',
                           hoverlabel=dict(bgcolor='white'),
                           marker=dict(line=dict(color='#000000',
                                                 width=1.5))
                           )

    wins_pie.update_layout(showlegend=False,
                           paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
                           title=dict(
                               text=f'Games: {match_count}, W/L: {pl_wins}/{pl_losses}',
                               y=0.9,
                               x=0.5,
                               font=dict(size=14))
                           )

    # side distribution
    side = px.pie(player_matches_df,
                  names='Side',
                  width=320, height=320,
                  hole=.4,
                  color='Side',
                  color_discrete_map={'Radiant': '#7FC57D',
                                      'Dire': '#F1572E'}
                  )

    side.update_traces(textposition='outside',
                       textinfo='percent+label',
                       hoverinfo='label+percent',
                       hoverlabel=dict(bgcolor='white'),
                       marker=dict(line=dict(color='#000000', width=1.5))
                       )

    side.update_layout(showlegend=False,
                       paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                       title=dict(
                           text=f'Match side distribution',
                           y=0.9, x=0.5,
                           font=dict(size=14))
                       )

    # kill deaths assists
    kda = px.bar(kda_df.sum(),
                 width=650, height=320,
                 color=['Kills', 'Deaths', 'Assists'],
                 color_discrete_map={'Kills': '#449ED0',
                                     'Deaths': '#B08787',
                                     'Assists': '#FFDF49'},
                 title='Career total KDA',
                 text=[total_kills, total_deaths, total_assists],
                 )

    kda.update_traces(hoverinfo='skip',
                      hovertemplate=None,
                      marker_line_color='rgb(0,0,0)',
                      marker_line_width=1
                      )

    kda.update_yaxes(visible=False,
                     showticklabels=False
                     )

    kda.update_xaxes(title_text='',
                     showticklabels=True
                     )

    kda.update_layout(showlegend=False,
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)',
                      title=dict(
                          text=f'Total KDA',
                          y=0.9, x=0.5,
                          font=dict(size=14)))

    # stacked games/wins
    stacked = go.Figure(data=[

        go.Bar(
            x=top10_heroes['Hero'],
            y=top10_heroes['Games'],
            name='Games',
            marker=dict(color='#e08e45')
        ),

        go.Bar(
            x=top10_heroes['Hero'],
            y=top10_heroes['Win'],
            name='Wins',
            marker=dict(color='#08415c'))
    ])

    stacked.update_layout(showlegend=False,
                          barmode='overlay',
                          hovermode='x unified',
                          hoverlabel=dict(bgcolor='white'),
                          paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)',
                          width=700,
                          height=450,
                          title_text='10 most picked heroes games and wins',
                          title_x=0.5,
                          font_size=10
                          )

    stacked.update_traces(marker_line_color='rgb(0,0,0)',
                          marker_line_width=0.85)

    stacked.update_xaxes(showgrid=False)
    stacked.update_yaxes(showgrid=False, title_text='Games')

    # all time winning heroes
    top_all_wins = go.Figure(px.bar(top10_win_heroes,
                                    x=top10_win_heroes['Hero'],
                                    y=top10_win_heroes.sort_values(by='Win %', ascending=False)['Win %'],
                                    height=465,
                                    width=700,
                                    text=[hero for hero in top10_win_heroes['Win %']])
                             )

    top_all_wins.update_layout(showlegend=False,
                               paper_bgcolor='rgba(0,0,0,0)',
                               plot_bgcolor='rgba(0,0,0,0)',
                               title_text='Top 10 all heroes win %',
                               font_size=10,
                               title_x=0.5,
                               hoverlabel=dict(bgcolor='white')
                               )

    top_all_wins.update_traces(marker_line_color='rgb(0,0,0)',
                               marker_line_width=1,
                               hovertemplate='%{x} Win %: %{y}',
                               marker_color='#3A5778',
                               )

    top_all_wins.update_yaxes(showgrid=False, title_text='Win %')
    top_all_wins.update_xaxes(showgrid=False, title_text='')

    # top 3 most played friends
    top_friends_bar = px.bar(top_friends,
                             width=600, height=350,
                             x='personaname',
                             y='with_games',
                             color='personaname',
                             color_discrete_sequence=['#052f5f', '#006691', '#71A3AD']
                             )

    top_friends_bar.update_traces(marker_line_color='rgb(0,0,0)',
                                  marker_line_width=1,
                                  hovertemplate='Nickname: %{x}<br>Games: %{y}'
                                  )

    top_friends_bar.update_traces(textposition='inside',
                                  marker=dict(line=dict(color='#000000', width=1.5))
                                  )

    top_friends_bar.update_layout(showlegend=False,
                                  paper_bgcolor='rgba(0,0,0,0)',
                                  plot_bgcolor='rgba(0,0,0,0)'
                                  )

    top_friends_bar.update_yaxes(title_text='Games', showgrid=False)
    top_friends_bar.update_xaxes(title_text='', showgrid=False)

    # top 3 most winning friends
    top_win_friends_bar = px.bar(top_winning_friends,
                                 width=600, height=350,
                                 x='personaname',
                                 y='with_win',
                                 color='personaname',
                                 color_discrete_sequence=['#052f5f', '#006691', '#71A3AD']
                                 )
    top_win_friends_bar.update_traces(marker_line_color='rgb(0,0,0)',
                                      marker_line_width=1,
                                      hovertemplate='Nickname: %{x}<br>Wins: %{y}'
                                      )

    top_win_friends_bar.update_traces(textposition='inside',
                                      marker=dict(line=dict(color='#000000', width=1.5))
                                      )

    top_win_friends_bar.update_layout(showlegend=False,
                                      paper_bgcolor='rgba(0,0,0,0)',
                                      plot_bgcolor='rgba(0,0,0,0)'
                                      )

    top_win_friends_bar.update_yaxes(title_text='Wins', showgrid=False)
    top_win_friends_bar.update_xaxes(title_text='', showgrid=False)

    return wins_pie, side, kda, \
           stacked, top_all_wins, \
           top_friends_bar, top_win_friends_bar


if __name__ == '__main__':
    app.run_server(debug=True)