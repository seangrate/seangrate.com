import datetime
from pathlib import Path
import sys
from typing import Tuple

import numpy as np
import pandas as pd

from bokeh.plotting import figure, save
from bokeh.models import ColumnDataSource, DataTable, HoverTool, LinearColorMapper, ColorBar, \
                         TableColumn, TabPanel, Tabs, Div, Column, Row, \
                         DateFormatter, HTMLTemplateFormatter, CustomJS
from bokeh.transform import transform, linear_cmap
from bokeh.palettes import Magma256, Inferno256, Plasma256, Category20, viridis, RdYlBu, BuRd
from bokeh.io import output_file


class Player:
    def __init__(self, name: str):
        self.name = name


class Game:
    def __init__(self, score: Tuple[int], date: datetime.datetime):
        self.score = score
        self.date = date

    @property
    def point_differential(self) -> int:
        return abs(self.score[0] - self.score[1])
    

class SinglesGame(Game):
    def __init__(self, first_player, second_player, score: Tuple[int], date: datetime.datetime):
        super().__init__(score, date)
        self.first_player = first_player
        self.second_player = second_player

    @property
    def winner(self) -> Player:
        return self.first_player if self.score[0] > self.score[1] else self.second_player
    
    @property
    def loser(self) -> Player:
        return self.first_player if self.score[0] < self.score[1] else self.second_player


class DoublesGame(Game):
    def __init__(self, first_team: Tuple[Player], second_team: Tuple[Player], score: Tuple[int], date: datetime.datetime):
        super().__init__(score, date)
        self.first_team = first_team
        self.second_team = second_team

    @property
    def winner(self) -> Tuple[Player]:
        return self.first_team if self.score[0] > self.score[1] else self.second_team
    
    @property
    def loser(self) -> Tuple[Player]:
        return self.first_team if self.score[0] < self.score[1] else self.second_team
   

def read_games(file_path: str) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        games_df = pd.read_csv(f)
    return games_df


def avg_games_chart(games_df):
    """
    Plots the average games played per day for each player in a bar chart.

    Note: Only days where at least one game was played are considered.
    """
    # Melt the DataFrame to have a single column for players
    melted_df = games_df.melt(id_vars=['date'], value_vars=['player1', 'player2'], var_name='player_role', value_name='player')
    unique_player_days = melted_df.drop_duplicates(subset=['player', 'date'])

    # Calculate the number of unique days each player played
    player_days = unique_player_days.groupby('player')['date'].nunique().reset_index()
    player_days.columns = ['player', 'unique_days']

    # Group by player and date to get the total games played by each player on each day
    daily_games = melted_df.groupby(['player', 'date']).size().reset_index(name='games_played')

    # Calculate the average games played per day for each player
    avg_games_per_day = daily_games.groupby('player')['games_played'].mean().reset_index()
    avg_games_per_day.columns = ['player', 'avg_games']
    avg_games_per_day['avg_games'] = avg_games_per_day['avg_games'].round(2)
    avg_games_per_day = avg_games_per_day.sort_values('avg_games', ascending=False)

    # Create a bar chart
    source = ColumnDataSource(avg_games_per_day)
    p = figure(x_range=avg_games_per_day['player'], title='Average Games Played per Day for Each Player',
               x_axis_label='Player', y_axis_label='Average Games Played', 
               height=700, width=700, margin=(50, 50, 50, 50),
               toolbar_location=None)

    p.vbar(x='player', top='avg_games', width=0.9, source=source,
           line_color='white', fill_color='navy')

    # Customize the plot
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.major_label_orientation = 1.0

    return p


def total_games_chart(players_df, source):
    # Melt the DataFrame to have a single column for players
    players_df['sorted_players'] = players_df.apply(lambda row: tuple(sorted([row['player1'], row['player2']])), axis=1)
    unique_games_df = players_df.drop_duplicates(subset=['sorted_players'])
    melted_df = unique_games_df.melt(id_vars=['total_games'], value_vars=['player1', 'player2'], var_name='player_role', value_name='player')

    # Group by player and sum the total games played
    leaderboard = melted_df.groupby('player').agg({
        'total_games': 'sum'
    }).reset_index()
    leaderboard = leaderboard.sort_values('total_games', ascending=False)

    # Create a bar chart
    source = ColumnDataSource(leaderboard)
    p = figure(x_range=leaderboard['player'], title='Total Games Played for Each Player',
               x_axis_label='Player', y_axis_label='Total Games Played', 
               height=700, width=700,  margin=(50, 50, 50, 50),
               toolbar_location=None)

    p.vbar(x='player', top='total_games', width=0.9, source=source,
           line_color='white', fill_color='navy')

    # Customize the plot
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.major_label_orientation = 1.0

    return p


def total_games_matrix(players_df, source):
    """
    Plots the total games played between each pair of players in a matrix plot.
    More precisely, the entry in the ith row and jth column is the total number of games played between the ith and jth players.
    """
    color_mapper = LinearColorMapper(palette=Inferno256, low=players_df['total_games'].min(), high=players_df['total_games'].max())
    players = players_df['player1'].unique()
    matrix_plot = figure(title='Total Games Played', x_range=players, y_range=players, 
                         x_axis_location='above', width=700, height=700, margin=(50, 50, 50, 50),
                         tools='hover,save', tooltips='@player1 vs @player2: @total_games', toolbar_location=None)
    matrix_plot.rect(x='player2', y='player1', width=1, height=1, source=source,
                     line_color=None, fill_color=transform('total_games', color_mapper))
    matrix_plot.xaxis.major_label_orientation = 1.0
    # matrix_plot.yaxis.major_label_orientation = 1.0
    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    matrix_plot.add_layout(color_bar, 'right')

    return matrix_plot


def total_games_solo_leaderboard(players_df, games_df):
    """
    Creates a leaderboard of players based on the total number of games played.
    """
    # Melt the DataFrame to have a single column for players
    players_df['sorted_players'] = players_df.apply(lambda row: tuple(sorted([row['player1'], row['player2']])), axis=1)
    unique_games_df = players_df.drop_duplicates(subset=['sorted_players'])
    melted_df = unique_games_df.melt(id_vars=['total_games'], value_vars=['player1', 'player2'], var_name='player_role', value_name='player')
    melted_df = melted_df[melted_df['total_games'] > 0]

    # Group by player and sum the total games played
    leaderboard = melted_df.groupby('player').agg({
        'total_games': 'sum'
    }).reset_index()

    # Compute the average games per day for each player
    # Melt the DataFrame to have a single column for players
    melted_df = games_df.melt(id_vars=['date'], value_vars=['player1', 'player2'], var_name='player_role', value_name='player')
    unique_player_days = melted_df.drop_duplicates(subset=['player', 'date'])

    # Calculate the number of unique days each player played
    player_days = unique_player_days.groupby('player')['date'].nunique().reset_index()
    player_days.columns = ['player', 'unique_days']

    # Group by player and date to get the total games played by each player on each day
    daily_games = melted_df.groupby(['player', 'date']).size().reset_index(name='games_played')

    # Calculate the average games played per day for each player
    avg_games_per_day = daily_games.groupby('player')['games_played'].mean().reset_index()
    avg_games_per_day.columns = ['player', 'avg_games']
    avg_games_per_day['avg_games'] = avg_games_per_day['avg_games'].round(2)
    avg_games_per_day = avg_games_per_day.sort_values('avg_games', ascending=False)
    leaderboard = leaderboard.merge(avg_games_per_day, on='player', how='left')

    # Sort the leaderboard by total games played and assign ranks
    leaderboard = leaderboard.sort_values(['avg_games', 'total_games'], ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)

    # Create the ColumnDataSource and DataTable
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player', title='Player'),
               TableColumn(field='avg_games', title='Average Games per Day'),
               TableColumn(field='total_games', title='Total Games Played')]
    
    data_table = DataTable(source=source, columns=columns, 
                           index_position=None, margin=(50, 50, 0, 50),
                           width=700, height=300)
    caveat = Div(text='<p><strong>Note:</strong> The average games per day only considers days when the player actually played, i.e., missed days do not penalize.</p>',
                 margin=(25, 50, 50, 50))
    return Column(data_table, caveat)
    

def total_games_pairs_leaderboard(players_df, games_df):
    """
    Creates a leaderboard of players based on the total number of games played.
    Ensures that "Player 1 vs Player 2" is considered the same as "Player 2 vs Player 1".
    """
    # Create a unique pair identifier
    players_df = players_df[players_df['total_games'] > 0].copy()
    players_df.loc[:, 'pair'] = players_df.apply(lambda row: tuple(sorted([row['player1'], row['player2']])), axis=1)

    # Group by the unique pair identifier and sum the total games played
    leaderboard = players_df.groupby('pair').agg({
        'player1': 'first',
        'player2': 'first',
        'total_games': 'max'
    }).reset_index(drop=True)

    # Compute the average games per day for each pair of players
    avg_games_per_day = []
    for _, row in leaderboard.iterrows():
        player1, player2 = row['player1'], row['player2']
        games_played = games_df[((games_df['player1'] == player1) & (games_df['player2'] == player2)) |
                                ((games_df['player1'] == player2) & (games_df['player2'] == player1))]
        days_played = games_played['date'].nunique()
        avg_games = row['total_games'] / days_played if days_played > 0 else 0
        avg_games_per_day.append(round(avg_games, 2))

    leaderboard['avg_games_per_day'] = avg_games_per_day

    
    leaderboard = leaderboard.sort_values(['avg_games_per_day', 'total_games'], ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard)+1)
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player1', title='Player 1'),
               TableColumn(field='player2', title='Player 2'),
               TableColumn(field='avg_games_per_day', title='Average Games per Day'),
               TableColumn(field='total_games', title='Total Games Played')]
    data_table = DataTable(source=source, columns=columns, 
                           index_position=None,  margin=(50, 50, 0, 50),
                           width=700, height=300)
    caveat = Div(text='<p><strong>Note:</strong> The average games per day for a pair only considers days when <em>both</em> players played.</p>',
                 margin=(25, 50, 50, 50))
    return Column(data_table, caveat)


def avg_games_line_graph(players_df, games_df):
    """
    Plots the average games played per day over time for each player in a line graph.

    Note: Only days where at least one game was played are considered.
    So, if a player did not play any games on a particular day, the value for that day
    will be the same as the previous day.
    """
    players = players_df['player1'].unique()
    num_players = len(players)
    colors = Category20[num_players] if num_players <= 20 else viridis(num_players)
    line_graph = figure(x_axis_label='Date', y_axis_label='Average Games Played per Day', title='Average Games Played per Day Over Time',
                        x_axis_type='datetime', margin=(50, 50, 50, 50),
                        width=1600, height=400, toolbar_location=None)

    # Add minor grid lines
    line_graph.xaxis.minor_tick_line_color = 'black'
    line_graph.yaxis.minor_tick_line_color = 'black'
    line_graph.xgrid.minor_grid_line_color = 'gray'
    line_graph.xgrid.minor_grid_line_alpha = 0.1
    line_graph.ygrid.minor_grid_line_color = 'gray'
    line_graph.ygrid.minor_grid_line_alpha = 0.1

    # add the lines with styling and tooltips
    # lines represent the average games played per day by each player over all the dates played
    all_dates = pd.date_range(start=games_df['date'].min(), end=games_df['date'].max())
    for idx, player in enumerate(players):
        games_played = games_df[(games_df['player1'] == player) | (games_df['player2'] == player)].sort_values('date')
        player_games = pd.DataFrame({'date': all_dates}).set_index('date')
        games_played = games_played.groupby('date').size()
        player_games['games_played'] = games_played.rolling(window=7, min_periods=1).mean()
        player_games['games_played'] = player_games['games_played'].ffill()
        player_source = ColumnDataSource(player_games.reset_index())
        line = line_graph.line('date', 'games_played', source=player_source, legend_label=player, 
                               name=player, line_width=3, color=colors[idx % len(colors)])
        hover = HoverTool(renderers=[line], tooltips=[('Player', player), ('Date', '@date{%F}'), ('Average Games', '@games_played{0.00}')], formatters={'@date': 'datetime'})
        line_graph.add_tools(hover)
    line_graph.add_layout(line_graph.legend[0], 'right')
    line_graph.legend.click_policy = 'hide'

    return line_graph


def total_games_line_graph(players_df, games_df):
    """
    Plots the total games played over time for each player in a line graph.
    """
    players = players_df['player1'].unique()
    num_players = len(players)
    colors = Category20[num_players] if num_players <= 20 else viridis(num_players)
    line_graph = figure(x_axis_label='Date', y_axis_label='Total Games Played', title='Total Games Played Over Time',
                        x_axis_type='datetime', margin=(50, 50, 50, 50),
                        width=1600, height=400, toolbar_location=None)

    # Add minor grid lines
    line_graph.xaxis.minor_tick_line_color = 'black'
    line_graph.yaxis.minor_tick_line_color = 'black'
    line_graph.xgrid.minor_grid_line_color = 'gray'
    line_graph.xgrid.minor_grid_line_alpha = 0.1
    line_graph.ygrid.minor_grid_line_color = 'gray'
    line_graph.ygrid.minor_grid_line_alpha = 0.1

    # add the lines with styling and tooltips
    # lines represent the cumulative games played by each player over all the dates played
    all_dates = pd.date_range(start=games_df['date'].min(), end=games_df['date'].max())
    for idx, player in enumerate(players):
        games_played = games_df[(games_df['player1'] == player) | (games_df['player2'] == player)].sort_values('date')
        player_games = pd.DataFrame({'date': all_dates}).set_index('date')
        games_played_count = games_played['date'].value_counts().sort_index()
        player_games['games_played'] = games_played_count
        player_games['games_played'] = player_games['games_played'].fillna(0)
        player_games['cumulative_sum'] = player_games['games_played'].cumsum()
        player_source = ColumnDataSource(player_games.reset_index())
        line = line_graph.line('date', 'cumulative_sum', source=player_source, legend_label=player, 
                               name=player, line_width=3, color=colors[idx % len(colors)])
        # hover = HoverTool(renderers=[line], tooltips=[('', player)])
        hover = HoverTool(renderers=[line], tooltips=[('Player', player), ('Date', '@date{%F}'), ('Total Games', '@cumulative_sum')], formatters={'@date': 'datetime'})
        line_graph.add_tools(hover)
    line_graph.add_layout(line_graph.legend[0], 'right')
    line_graph.legend.click_policy = 'hide'

    return line_graph


def total_games_dashboard(players_df, games_df, source):
    avg_solo_chart = avg_games_chart(games_df)
    total_solo_chart = total_games_chart(players_df, source)
    total_solo_leaderboard = total_games_solo_leaderboard(players_df, games_df)
    matrix_plot = total_games_matrix(players_df, source)
    pairs_leaderboard = total_games_pairs_leaderboard(players_df, games_df)
    avg_line_graph = avg_games_line_graph(players_df, games_df)
    total_line_graph = total_games_line_graph(players_df, games_df)
    return Column(Row(Column(avg_solo_chart, total_solo_chart, total_solo_leaderboard), Column(matrix_plot, pairs_leaderboard)), 
                  avg_line_graph,
                  total_line_graph)


def solo_wins_chart(players_df, source):
    """
    Plots the total number of wins for each player in a bar chart.
    """
    # Filter the DataFrame to include only rows where the player is player1
    solo_games_df = players_df[['player1', 'wins']].copy()
    leaderboard = solo_games_df.groupby('player1').agg({
        'wins': 'sum'
    }).reset_index()
    leaderboard.rename(columns={'player1': 'player'}, inplace=True)
    
    # color bars based on positivity of win differential
    color_palette = RdYlBu[11]
    leaderboard['color'] = [color_palette[0] if x >= 0 else color_palette[-1] for x in leaderboard['wins']]

    # Sort the leaderboard by total games played and assign ranks
    leaderboard = leaderboard.sort_values('wins', ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)

    # Create the ColumnDataSource and DataTable
    source = ColumnDataSource(leaderboard)
    p = figure(x_range=leaderboard['player'], title='Total Wins for Each Player',
               x_axis_label='Player', y_axis_label='Total Wins', 
               height=700, width=700,  margin=(50, 50, 50, 50),
               toolbar_location=None)

    p.vbar(x='player', top='wins', width=0.9, source=source,
           line_color='white', color='navy')

    # Customize the plot
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.major_label_orientation = 1.0

    return p


def solo_wins_percentage_chart(players_df, source):
    """
    Plots the win percentage for each player in a bar chart.
    """
    # Filter the DataFrame to include only rows where the player is player1
    solo_games_df = players_df[['player1', 'wins', 'losses']].copy()
    leaderboard = solo_games_df.groupby('player1').agg({
        'wins': 'sum',
        'losses': 'sum'
    }).reset_index()
    leaderboard.rename(columns={'player1': 'player'}, inplace=True)
    leaderboard['win_percentage'] = 100*(leaderboard['wins'] / (leaderboard['wins'] + leaderboard['losses'])).round(2)
    
    # color bars based on positivity of win differential
    color_palette = RdYlBu[11]
    leaderboard['color'] = [color_palette[0] if x >= 0 else color_palette[-1] for x in leaderboard['win_percentage']]

    # Sort the leaderboard by total games played and assign ranks
    leaderboard = leaderboard.sort_values('win_percentage', ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)

    # Create the ColumnDataSource and DataTable
    source = ColumnDataSource(leaderboard)
    p = figure(x_range=leaderboard['player'], title='Win Percentage for Each Player',
               x_axis_label='Player', y_axis_label='Win Percentage', 
               height=700, width=700,  margin=(50, 50, 50, 50),
               toolbar_location=None)

    p.vbar(x='player', top='win_percentage', width=0.9, source=source,
           line_color='white', color='navy')

    # Customize the plot
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.major_label_orientation = 1.0

    return p


def solo_wins_leaderboard(players_df, source):
    """
    Creates a leaderboard of players based on the total number of games played.
    """
    # Filter the DataFrame to include only rows where the player is player1
    solo_games_df = players_df.copy()
    leaderboard = solo_games_df.groupby('player1').agg({
        'wins': 'sum',
        'losses': 'sum',
        'win_differential': 'max'
    }).reset_index()
    leaderboard.rename(columns={'player1': 'player'}, inplace=True)
    leaderboard['win_percentage'] = 100*(leaderboard['wins'] / (leaderboard['wins'] + leaderboard['losses'])).round(2)

    # Sort the leaderboard by total games played and assign ranks
    leaderboard = leaderboard.sort_values(['win_percentage', 'wins'], ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)

    # Create the ColumnDataSource and DataTable
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player', title='Player'),
               TableColumn(field='wins', title='Wins'),
               TableColumn(field='losses', title='Losses'),
               TableColumn(field='win_percentage', title='Win %')]
    
    return DataTable(source=source, columns=columns,
                     index_position=None, margin=(50, 50, 50, 50),
                     width=700, height=300)


def head_to_head_matrix(players_df, source):
    players = players_df['player1'].unique()

    color_mapper = LinearColorMapper(palette=Plasma256, 
                                     low=players_df['win_differential'].min(), high=players_df['win_differential'].max(),
                                     nan_color='black')
    p = figure(title='Win Differentials', x_range=players, y_range=players, 
                x_axis_location='above', width=700, height=700, margin=(50, 50, 50, 50),
                tools='hover,save', tooltips='@player1 vs @player2: @win_differential', toolbar_location=None)
    p.rect(x='player2', y='player1', width=1, height=1, source=source,
           line_color=None, fill_color=transform('win_differential', color_mapper))
    p.xaxis.major_label_orientation = 1.0

    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p.add_layout(color_bar, 'right')
    return p


def head_to_head_leaderboard(players_df, source):
    """
    Creates a leaderboard of players based on the total number of games played.
    Ensures that "Player 1 vs Player 2" is considered the same as "Player 2 vs Player 1".
    """
    # Create a unique pair identifier
    players_df = players_df[(players_df['win_differential'] >= 0) & (players_df['total_games'] > 0)].copy()
    players_df.loc[:, 'pair'] = players_df.apply(lambda row: tuple(sorted([row['player1'], row['player2']])), axis=1)

    # Group by the unique pair identifier and sum the total games played
    leaderboard = players_df.groupby('pair').agg({
        'player1': 'first',
        'player2': 'first',
        'wins': 'max',
        'losses': 'min',
        'win_differential': 'max'
    }).reset_index(drop=True)
    leaderboard = leaderboard[(leaderboard['wins'] > 0) | leaderboard['losses'] > 0]
    leaderboard['record'] = leaderboard.apply(lambda row: f"{row['wins']} - {row['losses']}", axis=1)
    leaderboard['win_percentage'] = 100*(leaderboard['wins'] / (leaderboard['wins'] + leaderboard['losses'])).round(2)

    leaderboard = leaderboard.sort_values('win_differential', ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard)+1)
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player1', title='Player 1'),
               TableColumn(field='player2', title='Player 2'),
               TableColumn(field='record', title='Record'),
               TableColumn(field='win_percentage', title='Win %'),
               TableColumn(field='win_differential', title='Win Differential')]
    return DataTable(source=source, columns=columns, 
                     index_position=None,  margin=(50, 50, 50, 50),
                     width=700, height=300)


def solo_wins_line_graph(players_df, games_df):
    """
    Plots the total wins over time for each player in a line graph.
    """
    players = players_df['player1'].unique()
    num_players = len(players)
    colors = Category20[num_players] if num_players <= 20 else viridis(num_players)
    line_graph = figure(x_axis_label='Date', y_axis_label='Total Wins', title='Total Wins Over Time',
                        x_axis_type='datetime', margin=(50, 50, 50, 50),
                        width=1600, height=400, toolbar_location=None)

    # Add minor grid lines
    line_graph.xaxis.minor_tick_line_color = 'black'
    line_graph.yaxis.minor_tick_line_color = 'black'
    line_graph.xgrid.minor_grid_line_color = 'gray'
    line_graph.xgrid.minor_grid_line_alpha = 0.1
    line_graph.ygrid.minor_grid_line_color = 'gray'
    line_graph.ygrid.minor_grid_line_alpha = 0.1

    # add the lines with styling and tooltips
    # lines represent the cumulative wins by each player over all the dates played
    all_dates = pd.date_range(start=games_df['date'].min(), end=games_df['date'].max())
    for idx, player in enumerate(players):
        games_played = games_df[(games_df['player1'] == player) | (games_df['player2'] == player)].sort_values('date')
        player_games = pd.DataFrame({'date': all_dates}).set_index('date')
        games_played['wins'] = games_played.apply(lambda row: 1 if (row['player1'] == player and row['score1'] > row['score2']) or (row['player2'] == player and row['score2'] > row['score1']) else 0, axis=1)
        player_games = games_played.groupby('date')['wins'].sum().cumsum()
        player_source = ColumnDataSource(player_games.reset_index())
        line = line_graph.line('date', 'wins', source=player_source, legend_label=player, 
                               name=player, line_width=3, color=colors[idx % len(colors)])
        hover = HoverTool(renderers=[line], tooltips=[('Player', player), ('Date', '@date{%F}'), ('Total Wins', '@wins')], formatters={'@date': 'datetime'})
        line_graph.add_tools(hover)
    line_graph.add_layout(line_graph.legend[0], 'right')
    line_graph.legend.click_policy = 'hide'

    return line_graph


def solo_win_percentage_line_graph(players_df, games_df):
    """
    Plots the win percentage over time for each player in a line graph.
    """
    players = players_df['player1'].unique()
    num_players = len(players)
    colors = Category20[num_players] if num_players <= 20 else viridis(num_players)
    line_graph = figure(x_axis_label='Date', y_axis_label='Win Percentage', title='Win Percentage Over Time',
                        x_axis_type='datetime', margin=(50, 50, 50, 50),
                        width=1600, height=400, toolbar_location=None)

    # Add minor grid lines
    line_graph.xaxis.minor_tick_line_color = 'black'
    line_graph.yaxis.minor_tick_line_color = 'black'
    line_graph.xgrid.minor_grid_line_color = 'gray'
    line_graph.xgrid.minor_grid_line_alpha = 0.1
    line_graph.ygrid.minor_grid_line_color = 'gray'
    line_graph.ygrid.minor_grid_line_alpha = 0.1

    # add the lines with styling and tooltips
    # lines represent the win percentage by each player over all the dates played
    all_dates = pd.date_range(start=games_df['date'].min(), end=games_df['date'].max())
    for idx, player in enumerate(players):
        games_played = games_df[(games_df['player1'] == player) | (games_df['player2'] == player)].sort_values('date')
        player_games = pd.DataFrame({'date': all_dates}).set_index('date')
        games_played['wins'] = games_played.apply(lambda row: 1 if (row['player1'] == player and row['score1'] > row['score2']) or (row['player2'] == player and row['score2'] > row['score1']) else 0, axis=1)
        games_played_count = games_played['date'].value_counts().sort_index()
        wins_per_date = games_played.groupby('date')['wins'].sum().sort_index()
        player_games['games_played'] = games_played_count.reindex(player_games.index, fill_value=0)
        player_games['wins'] = wins_per_date.reindex(player_games.index, fill_value=0)
        player_games['cumulative_games_played'] = player_games['games_played'].cumsum()
        player_games['cumulative_wins'] = player_games['wins'].cumsum()        
        player_games['win_percentage'] = (player_games['cumulative_wins'] / player_games['cumulative_games_played'] * 100).fillna(0).round(2)
        player_source = ColumnDataSource(player_games.reset_index())
        line = line_graph.line('date', 'win_percentage', source=player_source, legend_label=player, 
                               name=player, line_width=3, color=colors[idx % len(colors)])
        hover = HoverTool(renderers=[line], tooltips=[('Player', player), ('Date', '@date{%F}'), ('Win Percentage', '@win_percentage{0.00}%')], formatters={'@date': 'datetime'})
        line_graph.add_tools(hover)
    line_graph.add_layout(line_graph.legend[0], 'right')
    line_graph.legend.click_policy = 'hide'

    return line_graph


def head_to_head_dashboard(players_df, games_df, source):
    total_wins_chart = solo_wins_chart(players_df, source)
    win_percentage_chart = solo_wins_percentage_chart(players_df, source)
    solo_leaderboard = solo_wins_leaderboard(players_df, source)
    matrix_plot = head_to_head_matrix(players_df, source)
    pairs_leaderboard = head_to_head_leaderboard(players_df, source)
    solo_wins_graph = solo_wins_line_graph(players_df, games_df)
    solo_win_percentage_graph = solo_win_percentage_line_graph(players_df, games_df)
    return Column(Row(Column(win_percentage_chart, total_wins_chart, solo_leaderboard), Column(matrix_plot, pairs_leaderboard)), 
                  solo_win_percentage_graph, 
                  solo_wins_graph)


def point_differential_chart(players_df, source):
    """
    Plots the average point differential for each player in a bar chart.
    """
    # Filter the DataFrame to include only rows where the player is player1
    solo_games_df = players_df[['player1', 'total_games', 'point_diff']].copy()
    leaderboard = solo_games_df.groupby('player1').agg({
        'point_diff': 'sum',
        'total_games': 'sum'
    }).reset_index()
    leaderboard['avg_point_diff'] = (leaderboard['point_diff'] / leaderboard['total_games']).round(1)
    leaderboard.rename(columns={'player1': 'player'}, inplace=True)
    
    # color bars based on positivity of point differential
    color_palette = RdYlBu[11]
    leaderboard['color'] = [color_palette[0] if x >= 0 else color_palette[-1] for x in leaderboard['point_diff']]

    # Sort the leaderboard by total games played and assign ranks
    leaderboard = leaderboard.sort_values('avg_point_diff', ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)

    # Create the ColumnDataSource and DataTable
    source = ColumnDataSource(leaderboard)
    p = figure(x_range=leaderboard['player'], title='Average Point Differential for Each Player',
               x_axis_label='Player', y_axis_label='Average Point Differential', 
               height=700, width=700,  margin=(50, 50, 50, 50),
               toolbar_location=None)

    p.vbar(x='player', top='avg_point_diff', width=0.9, source=source,
           line_color='white', color='color')

    # Customize the plot
    p.xgrid.grid_line_color = None
    p.y_range.start = leaderboard['avg_point_diff'].min() - (p.y_range.end - leaderboard['avg_point_diff'].max())
    p.xaxis.major_label_orientation = 1.2

    return p


def point_differential_solo_leaderboard(players_df, source):
    """
    Creates a leaderboard of players based on the total number of games played.
    """
    # Filter the DataFrame to include only rows where the player is player1
    solo_games_df = players_df[['player1', 'total_games', 'point_diff']]
    solo_games_df = solo_games_df[solo_games_df['total_games'] > 0]
    leaderboard = solo_games_df.groupby('player1').agg({
        'point_diff': 'sum',
        'total_games': 'sum'
    }).reset_index()
    leaderboard['avg_point_diff'] = (leaderboard['point_diff'] / leaderboard['total_games']).round(1)
    leaderboard.rename(columns={'player1': 'player'}, inplace=True)

    # Sort the leaderboard by total games played and assign ranks
    leaderboard = leaderboard.sort_values('avg_point_diff', ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)

    # Create the ColumnDataSource and DataTable
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player', title='Player'),
               TableColumn(field='avg_point_diff', title='Average'),
               TableColumn(field='point_diff', title='Total')]
    
    return DataTable(source=source, columns=columns, 
                     index_position=None, margin=(50, 50, 50, 50),
                     width=700, height=300)


def point_differential_matrix(players_df, source):
    players_df['avg_point_diff'] = (players_df['point_diff'] / players_df['total_games']).round(1)
    players = players_df['player1'].unique()

    source = ColumnDataSource(players_df)
    color_mapper = LinearColorMapper(palette=Plasma256, 
                                     low=players_df['avg_point_diff'].min(), high=players_df['avg_point_diff'].max(), 
                                     nan_color='black')
    p = figure(title='Average Point Differential', x_range=players, y_range=players, 
               x_axis_location='above', width=700, height=700, margin=(50, 50, 50, 50),
               tools='hover,save', tooltips='@player1 vs @player2: @avg_point_diff')
    p.rect(x='player2', y='player1', width=1, height=1, source=source,
           line_color=None, fill_color=transform('avg_point_diff', color_mapper))
    p.xaxis.major_label_orientation = 1.0
    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p.add_layout(color_bar, 'right')
    return p


def point_differential_pairs_leaderboard(players_df, source):
    """
    Creates a leaderboard of players based on the total number of games played.
    Ensures that "Player 1 vs Player 2" is considered the same as "Player 2 vs Player 1".
    """
    # Create a unique pair identifier
    players_df = players_df[(players_df['point_diff'] >= 0) & (players_df['total_games'] > 0)].copy()
    players_df.loc[:, 'pair'] = players_df.apply(lambda row: tuple(sorted([row['player1'], row['player2']])), axis=1)

    # Group by the unique pair identifier and sum the total games played
    leaderboard = players_df.groupby('pair').agg({
        'player1': 'first',
        'player2': 'first',
        'total_games': 'sum',
        'point_diff': 'max',
    }).reset_index(drop=True)
    leaderboard['avg_point_diff'] = (leaderboard['point_diff'] / leaderboard['total_games']).round(1)
    
    leaderboard = leaderboard.sort_values(['avg_point_diff', 'point_diff'], ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard)+1)
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player1', title='Player 1'),
               TableColumn(field='player2', title='Player 2'),
               TableColumn(field='avg_point_diff', title='Average'),
               TableColumn(field='point_diff', title='Total')]
    return DataTable(source=source, columns=columns, 
                     index_position=None,  margin=(50, 50, 50, 50),
                     width=700, height=300)


def point_differential_line_graph(players_df, games_df):
    """
    Plots the total point differential over time for each player in a line graph.
    """
    players = players_df['player1'].unique()
    num_players = len(players)
    colors = Category20[num_players] if num_players <= 20 else viridis(num_players)
    line_graph = figure(x_axis_label='Date', y_axis_label='Total Point Differential', title='Total Point Differential Over Time',
                        x_axis_type='datetime', margin=(50, 50, 50, 50),
                        width=1600, height=400, toolbar_location=None)

    # Add minor grid lines
    line_graph.xaxis.minor_tick_line_color = 'black'
    line_graph.yaxis.minor_tick_line_color = 'black'
    line_graph.xgrid.minor_grid_line_color = 'gray'
    line_graph.xgrid.minor_grid_line_alpha = 0.1
    line_graph.ygrid.minor_grid_line_color = 'gray'
    line_graph.ygrid.minor_grid_line_alpha = 0.1

    # add the lines with styling and tooltips
    # lines represent the cumulative point differential by each player over all the dates played
    all_dates = pd.date_range(start=games_df['date'].min(), end=games_df['date'].max())
    for idx, player in enumerate(players):
        games_played = games_df[(games_df['player1'] == player) | (games_df['player2'] == player)].sort_values('date')
        player_games = pd.DataFrame({'date': all_dates}).set_index('date')
        games_played['point_diff'] = games_played.apply(lambda row: row['score1'] - row['score2'] if row['player1'] == player else row['score2'] - row['score1'], axis=1)
        player_games['point_diff'] = games_played.groupby('date')['point_diff'].sum().cumsum().reindex(player_games.index, method='ffill').fillna(0)
        player_source = ColumnDataSource(player_games.reset_index())
        line = line_graph.line('date', 'point_diff', source=player_source, legend_label=player, 
                               name=player, line_width=3, color=colors[idx % len(colors)])
        hover = HoverTool(renderers=[line], tooltips=[('Player', player), ('Date', '@date{%F}'), ('Total Point Differential', '@point_diff{0}')], formatters={'@date': 'datetime'})
        line_graph.add_tools(hover)
    line_graph.add_layout(line_graph.legend[0], 'right')
    line_graph.legend.click_policy = 'hide'

    return line_graph


def avg_point_differential_line_graph(players_df, games_df):
    """
    Plots the average point differential over time for each player in a line graph.
    """
    players = players_df['player1'].unique()
    num_players = len(players)
    colors = Category20[num_players] if num_players <= 20 else viridis(num_players)
    line_graph = figure(x_axis_label='Date', y_axis_label='Average Point Differential', title='Average Point Differential Over Time',
                        x_axis_type='datetime', margin=(50, 50, 50, 50),
                        width=1600, height=400, toolbar_location=None)

    # Add minor grid lines
    line_graph.xaxis.minor_tick_line_color = 'black'
    line_graph.yaxis.minor_tick_line_color = 'black'
    line_graph.xgrid.minor_grid_line_color = 'gray'
    line_graph.xgrid.minor_grid_line_alpha = 0.1
    line_graph.ygrid.minor_grid_line_color = 'gray'
    line_graph.ygrid.minor_grid_line_alpha = 0.1

    # add the lines with styling and tooltips
    # lines represent the average point differential by each player over all the dates played
    all_dates = pd.date_range(start=games_df['date'].min(), end=games_df['date'].max())
    for idx, player in enumerate(players):
        games_played = games_df[(games_df['player1'] == player) | (games_df['player2'] == player)].sort_values('date')
        player_games = pd.DataFrame({'date': all_dates}).set_index('date')
        games_played['point_diff'] = games_played.apply(lambda row: row['score1'] - row['score2'] if row['player1'] == player else row['score2'] - row['score1'], axis=1)
        point_diff_cumsum = games_played.groupby('date')['point_diff'].sum().cumsum()
        games_played_count = games_played['date'].value_counts().sort_index().cumsum()
        player_games['cumulative_point_diff'] = point_diff_cumsum.reindex(player_games.index, method='ffill').fillna(0)
        player_games['cumulative_games_played'] = games_played_count.reindex(player_games.index, method='ffill').fillna(0)
        player_games['avg_point_diff'] = (player_games['cumulative_point_diff'] / player_games['cumulative_games_played']).fillna(0).round(1)
        player_source = ColumnDataSource(player_games.reset_index())
        line = line_graph.line('date', 'avg_point_diff', source=player_source, legend_label=player,
                               name=player, line_width=3, color=colors[idx % len(colors)])
        hover = HoverTool(renderers=[line], tooltips=[('Player', player), ('Date', '@date{%F}'), ('Average Point Differential', '@avg_point_diff{0.0}')], formatters={'@date': 'datetime'})
        line_graph.add_tools(hover)
    line_graph.add_layout(line_graph.legend[0], 'right')
    line_graph.legend.click_policy = 'hide'

    return line_graph


def point_differential_dashboard(players_df, games_df, source):
    solo_chart = point_differential_chart(players_df, source)
    solo_leaderboard = point_differential_solo_leaderboard(players_df, source)
    matrix_plot = point_differential_matrix(players_df, source)
    pairs_leaderboard = point_differential_pairs_leaderboard(players_df, source)
    point_diff_graph = point_differential_line_graph(players_df, games_df)
    avg_point_diff_graph = avg_point_differential_line_graph(players_df, games_df)
    return Column(Row(Column(solo_chart, solo_leaderboard), Column(matrix_plot, pairs_leaderboard)),
                  avg_point_diff_graph,
                  point_diff_graph)


def singles_history(games_df):
    """
    Creates a dashboard for the history of singles games.
    """
    games_df['score'] = games_df.apply(lambda row: f"{row['score1']}-{row['score2']}", axis=1)
    games_df = games_df.sort_values('date', ascending=False)
    source = ColumnDataSource(games_df)

    # Create a table of the games
    columns = [TableColumn(field='date', title='Date', formatter=DateFormatter(format='%Y-%m-%d')),
               TableColumn(field='player1', title='Player 1'),
               TableColumn(field='player2', title='Player 2'),
               TableColumn(field='score', title='Score')]
    title = Div(text="<h2>Singles Game History</h2>", margin=(50, 50, 0, 50))
    data_table = DataTable(source=source, columns=columns, 
                           index_position=None, margin=(0, 50, 50, 50),
                           width=700, height=300)
    return Column(title, data_table)


def doubles_history(games_df):
    """
    Creates a dashboard for the history of doubles games.
    """
    games_df['score'] = games_df.apply(lambda row: f"{row['score1']}-{row['score2']}", axis=1)
    games_df['team1'] = games_df.apply(lambda row: f"{row['player1']}<br>{row['player2']}", axis=1)
    games_df['team2'] = games_df.apply(lambda row: f"{row['player3']}<br>{row['player4']}", axis=1)
    games_df = games_df.sort_values('date', ascending=False)
    source = ColumnDataSource(games_df)

    # Define HTML template formatter
    template = """
    <div>
        <%= value %>
    </div>
    """
    html_formatter = HTMLTemplateFormatter(template=template)

    # Create a table of the games
    columns = [TableColumn(field='date', title='Date', formatter=DateFormatter(format='%Y-%m-%d')),
               TableColumn(field='team1', title='Team 1', formatter=html_formatter),
               TableColumn(field='team2', title='Team 2', formatter=html_formatter),
               TableColumn(field='score', title='Score')]
    title = Div(text="<h2>Doubles Game History</h2>", margin=(50, 50, 0, 50))
    data_table = DataTable(source=source, columns=columns, row_height=45,
                           index_position=None, margin=(0, 50, 50, 50),
                           width=700, height=300)
    
    # # Inject custom CSS for row height adjustment
    # custom_css = """
    # <style>
    # .bk-data-table tr {
    #     height: auto !important;
    # }

    # .bk-data-table td {
    #     white-space: normal !important;
    #     word-wrap: break-word;
    # }
    # </style>
    # """
    # css_div = Div(text=custom_css)
    return Column(title, data_table)
    

def history_dashboard(singles_games_df, doubles_games_df):
    singles_table = singles_history(singles_games_df)
    doubles_table = doubles_history(doubles_games_df)
    return Row(singles_table, doubles_table)


def main():
    # use the 'real' or 'mock' data
    data_type = 'real'
    if data_type == 'real':
        data_file = Path(__file__).parent.parent / 'badminton' / 'data' / 'real.csv'
        html_file = Path(__file__).parent.parent / 'badminton' / 'index.html'
    elif data_type == 'mock':
        data_file = Path(__file__).parent.parent / 'badminton' / 'data' / 'mock.csv'
        html_file = Path(__file__).parent.parent / 'badminton' / 'mock.html'

    # load the game data (only singles games)
    game_data = read_games(data_file)
    game_data['date'] = pd.to_datetime(game_data['date'])
    game_data['game_type'] = game_data.apply(lambda row: 'singles' if pd.isna(row['player3']) else 'doubles', axis=1)
    singles_game_data, doubles_game_data = game_data[game_data['game_type'] == 'singles'].copy(), game_data[game_data['game_type'] == 'doubles'].copy()

    # initialize the player data
    player_names = pd.unique(singles_game_data[['player1', 'player2']].values.ravel('K'))
    player_names = [name for name in player_names if pd.notna(name)]
    # having both the game_data and player_data dataframes is probably redundant; 
    # it can probably be condensed via groupby operations
    player_data = pd.DataFrame(0, index=pd.MultiIndex.from_product([player_names, player_names], names=['player1', 'player2']),
                               columns=['wins', 'losses', 'points_for', 'points_against', 'point_diff'], dtype=int)

    # calculate the stats
    for game in singles_game_data.itertuples():
        winner = game.player1 if game.score1 > game.score2 else game.player2
        loser = game.player1 if game.score1 < game.score2 else game.player2
        # win-loss record
        player_data.loc[(winner, loser), 'wins'] += 1
        player_data.loc[(loser, winner), 'losses'] += 1
        # point totals
        player_data.loc[(game.player1, game.player2), 'points_for'] += game.score1
        player_data.loc[(game.player1, game.player2), 'points_against'] += game.score2
        player_data.loc[(game.player2, game.player1), 'points_for'] += game.score2
        player_data.loc[(game.player2, game.player1), 'points_against'] += game.score1
        # point differential
        point_diff = abs(max(game.score1, game.score2) - min(game.score1, game.score2))
        player_data.loc[(winner, loser), 'point_diff'] += point_diff
        player_data.loc[(loser, winner), 'point_diff'] -= point_diff
    for game in doubles_game_data.itertuples():
        winner = (game.player1, game.player2) if game.score1 > game.score2 else (game.player2, game.player1)
        loser = (game.player1, game.player2) if game.score1 < game.score2 else (game.player2, game.player1)
    player_data['total_games'] = player_data['wins'] + player_data['losses']
    player_data['record'] = player_data['wins'].astype(str) + '-' + player_data['losses'].astype(str)
    player_data['win_differential'] = player_data['wins'] - player_data['losses']
    player_data.loc[player_data['total_games'] == 0, ['point_diff', 'win_differential']] = np.nan

    # plot the data in tabs
    player_data.reset_index(inplace=True)
    player_source = ColumnDataSource(player_data)
    plots = {'Total Games Played': total_games_dashboard(player_data, singles_game_data, player_source),
             'Wins': head_to_head_dashboard(player_data, singles_game_data, player_source),
             'Point Differentials': point_differential_dashboard(player_data, singles_game_data, player_source),
             'Game History': history_dashboard(singles_game_data, doubles_game_data)}
    tabs = Tabs(tabs=[TabPanel(child=p, title=title) for title, p in plots.items()])

    output_file(filename=html_file,
                title='Badminton Stats', mode='inline')
    save(tabs)


if __name__ == '__main__':
    main()