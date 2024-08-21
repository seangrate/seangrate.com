from collections import defaultdict
import datetime
import itertools as it
from pathlib import Path
from typing import Tuple

from pprint import pprint
import sys

from bokeh.plotting import figure, save
from bokeh.models import ColumnDataSource, DataTable, HoverTool, LinearColorMapper, ColorBar, \
                         TableColumn, TabPanel, Tabs, CheckboxGroup, Column, Row, \
                         SingleIntervalTicker, CustomJS
from bokeh.transform import transform, linear_cmap
from bokeh.palettes import Magma256, Inferno256, Plasma256, Category20, viridis, RdYlBu
from bokeh.io import output_file
import pandas as pd


class Player:
    def __init__(self, name: str):
        self.name = name


class Game:
    def __init__(self, score: Tuple[int], date: datetime):
        self.score = score
        self.date = date

    @property
    def point_differential(self) -> int:
        return abs(self.score[0] - self.score[1])
    

class SinglesGame(Game):
    def __init__(self, first_player, second_player, score: Tuple[int], date: datetime):
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
    def __init__(self, first_team: Tuple[Player], second_team: Tuple[Player], score: Tuple[int], date: datetime):
        super().__init__(score, date)
        self.first_team = first_team
        self.second_team = second_team

    @property
    def winner(self) -> Tuple[Player]:
        return self.first_team if self.score[0] > self.score[1] else self.second_team
    
    @property
    def loser(self) -> Tuple[Player]:
        return self.first_team if self.score[0] < self.score[1] else self.second_team
    

def total_games_chart(players, players_df, source):
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


def total_games_matrix(players, players_df, source):
    """
    Plots the total games played between each pair of players in a matrix plot.
    More precisely, the entry in the ith row and jth column is the total number of games played between the ith and jth players.
    """
    color_mapper = LinearColorMapper(palette=Inferno256, low=players_df['total_games'].min(), high=players_df['total_games'].max())
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


def total_games_solo_leaderboard(players_df, source):
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

    # Sort the leaderboard by total games played and assign ranks
    leaderboard = leaderboard.sort_values('total_games', ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)

    # Create the ColumnDataSource and DataTable
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player', title='Player'),
               TableColumn(field='total_games', title='Total Games Played')]
    
    return DataTable(source=source, columns=columns, 
                     index_position=None, margin=(0, 50, 50, 50),
                     width=700, height=300)


def total_games_pairs_leaderboard(players_df, source):
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
    
    leaderboard = leaderboard.sort_values('total_games', ascending=False)
    leaderboard['rank'] = range(1, len(leaderboard)+1)
    source = ColumnDataSource(leaderboard)
    columns = [TableColumn(field='rank', title='Rank'),
               TableColumn(field='player1', title='Player 1'),
               TableColumn(field='player2', title='Player 2'),
               TableColumn(field='total_games', title='Total Games Played')]
    return DataTable(source=source, columns=columns, 
                     index_position=None,  margin=(0, 50, 50, 50),
                     width=700, height=300)


def total_games_line_graph(players, players_df, games_df, source):
    """
    Plots the total games played over time for each player in a line graph.
    """
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
    lines = []
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
        lines.append(line)
        hover = HoverTool(renderers=[line], tooltips=[('', player)])
        line_graph.add_tools(hover)
    line_graph.add_layout(line_graph.legend[0], 'right')
    line_graph.legend.click_policy = 'hide'

    return line_graph


def total_games_dashboard(players, players_df, games_df, source):
    solo_chart = total_games_chart(players, players_df, source)
    solo_leaderboard = total_games_solo_leaderboard(players_df, source)
    matrix_plot = total_games_matrix(players, players_df, source)
    pairs_leaderboard = total_games_pairs_leaderboard(players_df, source)
    line_graph = total_games_line_graph(players, players_df, games_df, source)
    return Column(Row(Column(solo_chart, solo_leaderboard), Column(matrix_plot, pairs_leaderboard)), line_graph)


def head_to_head_dashboard(players, players_df, source):
    color_mapper = LinearColorMapper(palette=Inferno256, low=players_df['wins'].min(), high=players_df['wins'].max())

    p = figure(title='Head-to-Head Record', x_range=players, y_range=players, 
                x_axis_location='above', width=700, height=700, margin=(50, 50, 50, 50),
                tools='hover,save', tooltips='@player1 vs @player2: @record')

    p.rect(x='player2', y='player1', width=1, height=1, source=source,
           line_color=None, fill_color=transform('wins', color_mapper))

    p.xaxis.major_label_orientation = 1.0
    p.yaxis.major_label_orientation = 1.0

    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p.add_layout(color_bar, 'right')
    return p


def point_differential_chart(players, players_df, source):
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
    p.y_range.start = leaderboard['avg_point_diff'].min() - 1
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


def point_differential_matrix(players, players_df, source):
    color_mapper = LinearColorMapper(palette=RdYlBu[11][::-1], low=players_df['point_diff'].min(), high=players_df['point_diff'].max())
    p = figure(title='Average Point Differential', x_range=players, y_range=players, 
               x_axis_location='above', width=700, height=700, margin=(50, 50, 50, 50),
               tools='hover,save', tooltips='@player1 vs @player2: @point_diff')
    p.rect(x='player2', y='player1', width=1, height=1, source=source,
           line_color=None, fill_color=transform('point_diff', color_mapper))
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
    
    leaderboard = leaderboard.sort_values('point_diff', ascending=False)
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


def point_differential_dashboard(players, players_df, source):
    solo_chart = point_differential_chart(players, players_df, source)
    solo_leaderboard = point_differential_solo_leaderboard(players_df, source)
    matrix_plot = point_differential_matrix(players, players_df, source)
    pairs_leaderboard = point_differential_pairs_leaderboard(players_df, source)
    return Row(Column(solo_chart, solo_leaderboard), Column(matrix_plot, pairs_leaderboard))


def main():
    PLAYERS = {'Daniel Hodgins': Player('Daniel Hodgins'),
               'Emma Snyder': Player('Emma Snyder'),
               'James Zhong': Player('James Zhong'),
               'Jared DeLeo': Player('Jared DeLeo'),
               'John Cobb': Player('John Cobb'),
               'John David Clifton': Player('John David Clifton'),
               'John Sterling': Player('John Sterling'),
               'Kenny Powell': Player('Kenny Powell'),
               'Owen Henderschedt': Player('Owen Henderschedt'),
               'Sayantani Battacharya': Player('Sayantani Battacharya'),
               'Sean Grate': Player('Sean Grate'),
               'Seth Harward': Player('Seth Harward'),
               'Tim Eller': Player('Tim Eller'),
               'Tristan Salinas': Player('Tristan Salinas')}
    # """
    GAMES = [SinglesGame(PLAYERS['Sean Grate'], PLAYERS['John Sterling'], (2, 21), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['John Sterling'], PLAYERS['James Zhong'], (21, 11), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['John Sterling'], PLAYERS['James Zhong'], (21, 15), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['Sean Grate'], PLAYERS['James Zhong'], (15, 21), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['John David Clifton'], PLAYERS['Daniel Hodgins'], (21, 9), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['John Sterling'], PLAYERS['James Zhong'], (21, 14), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['John David Clifton'], PLAYERS['Sean Grate'], (24, 26), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['Sean Grate'], PLAYERS['John Sterling'], (7, 21), datetime.date(2024, 8, 20)),
             SinglesGame(PLAYERS['Sean Grate'], PLAYERS['John Sterling'], (13, 21), datetime.date(2024, 8, 20))]
    """
    GAMES = [DoublesGame((PLAYERS['John Cobb'], PLAYERS['Tim Eller']), (PLAYERS['James Zhong'], PLAYERS['Tristan Salinas']), (21, 2), datetime.date(2024, 12, 15)),
            SinglesGame(PLAYERS['Tim Eller'], PLAYERS['John Cobb'], (21, 8), datetime.date(2024, 12, 1)),
            SinglesGame(PLAYERS['Jared DeLeo'], PLAYERS['Sayantani Battacharya'], (21, 2), datetime.date(2024, 12, 11)),
            DoublesGame((PLAYERS['James Zhong'], PLAYERS['Sayantani Battacharya']), (PLAYERS['Owen Henderschedt'], PLAYERS['Emma Snyder']), (21, 5), datetime.date(2024, 11, 16)),
            SinglesGame(PLAYERS['James Zhong'], PLAYERS['Emma Snyder'], (21, 13), datetime.date(2024, 11, 25)),
            SinglesGame(PLAYERS['Tristan Salinas'], PLAYERS['Kenny Powell'], (21, 10), datetime.date(2024, 8, 23)),
            DoublesGame((PLAYERS['Sayantani Battacharya'], PLAYERS['Kenny Powell']), (PLAYERS['Tristan Salinas'], PLAYERS['Sean Grate']), (21, 7), datetime.date(2024, 10, 19)),
            SinglesGame(PLAYERS['Owen Henderschedt'], PLAYERS['Sean Grate'], (21, 5), datetime.date(2024, 11, 19)),
            DoublesGame((PLAYERS['Owen Henderschedt'], PLAYERS['Tim Eller']), (PLAYERS['John Cobb'], PLAYERS['Jared DeLeo']), (21, 20), datetime.date(2024, 8, 11)),
            SinglesGame(PLAYERS['John Cobb'], PLAYERS['Sean Grate'], (21, 1), datetime.date(2024, 12, 10)),
            SinglesGame(PLAYERS['Sean Grate'], PLAYERS['Seth Harward'], (21, 2), datetime.date(2024, 12, 11)),
            SinglesGame(PLAYERS['Tim Eller'], PLAYERS['Kenny Powell'], (21, 16), datetime.date(2024, 11, 29)),
            DoublesGame((PLAYERS['Seth Harward'], PLAYERS['John Sterling']), (PLAYERS['Sean Grate'], PLAYERS['John Cobb']), (21, 10), datetime.date(2024, 8, 9)),
            DoublesGame((PLAYERS['Sean Grate'], PLAYERS['Tim Eller']), (PLAYERS['John Sterling'], PLAYERS['Seth Harward']), (21, 13), datetime.date(2024, 10, 4)),
            DoublesGame((PLAYERS['Kenny Powell'], PLAYERS['John David Clifton']), (PLAYERS['Owen Henderschedt'], PLAYERS['Tim Eller']), (21, 13), datetime.date(2024, 11, 22)),
            SinglesGame(PLAYERS['John Sterling'], PLAYERS['Jared DeLeo'], (21, 16), datetime.date(2024, 8, 30)),
            DoublesGame((PLAYERS['Jared DeLeo'], PLAYERS['Tim Eller']), (PLAYERS['John David Clifton'], PLAYERS['John Cobb']), (21, 14), datetime.date(2024, 8, 11)),
            DoublesGame((PLAYERS['Jared DeLeo'], PLAYERS['Sayantani Battacharya']), (PLAYERS['Emma Snyder'], PLAYERS['John Cobb']), (21, 11), datetime.date(2024, 9, 19)),
            SinglesGame(PLAYERS['Tim Eller'], PLAYERS['Emma Snyder'], (21, 8), datetime.date(2024, 10, 7)),
            DoublesGame((PLAYERS['Jared DeLeo'], PLAYERS['John Sterling']), (PLAYERS['Tim Eller'], PLAYERS['Kenny Powell']), (21, 6), datetime.date(2024, 8, 12)),
            DoublesGame((PLAYERS['Seth Harward'], PLAYERS['Kenny Powell']), (PLAYERS['James Zhong'], PLAYERS['Tim Eller']), (21, 5), datetime.date(2024, 12, 3)),
            SinglesGame(PLAYERS['Tim Eller'], PLAYERS['Seth Harward'], (21, 20), datetime.date(2024, 12, 20)),
            SinglesGame(PLAYERS['Owen Henderschedt'], PLAYERS['John Cobb'], (21, 19), datetime.date(2024, 8, 3)),
            SinglesGame(PLAYERS['John David Clifton'], PLAYERS['Tim Eller'], (21, 15), datetime.date(2024, 10, 6)),
            SinglesGame(PLAYERS['Owen Henderschedt'], PLAYERS['John David Clifton'], (21, 9), datetime.date(2024, 8, 13)),
            SinglesGame(PLAYERS['Emma Snyder'], PLAYERS['Owen Henderschedt'], (21, 15), datetime.date(2024, 9, 1)),
            DoublesGame((PLAYERS['John Sterling'], PLAYERS['John Cobb']), (PLAYERS['Tim Eller'], PLAYERS['Owen Henderschedt']), (21, 15), datetime.date(2024, 11, 10)),
            SinglesGame(PLAYERS['Jared DeLeo'], PLAYERS['John David Clifton'], (21, 5), datetime.date(2024, 9, 17)),
            DoublesGame((PLAYERS['Sayantani Battacharya'], PLAYERS['John David Clifton']), (PLAYERS['James Zhong'], PLAYERS['Sean Grate']), (21, 17), datetime.date(2024, 8, 29)),
            SinglesGame(PLAYERS['John Sterling'], PLAYERS['John David Clifton'], (21, 17), datetime.date(2024, 9, 7)),
            DoublesGame((PLAYERS['Seth Harward'], PLAYERS['John Sterling']), (PLAYERS['Jared DeLeo'], PLAYERS['Emma Snyder']), (21, 9), datetime.date(2024, 8, 8)),
            DoublesGame((PLAYERS['Sean Grate'], PLAYERS['Sayantani Battacharya']), (PLAYERS['Tristan Salinas'], PLAYERS['John Sterling']), (21, 16), datetime.date(2024, 11, 14)),
            DoublesGame((PLAYERS['Jared DeLeo'], PLAYERS['John Sterling']), (PLAYERS['Tristan Salinas'], PLAYERS['Sean Grate']), (21, 5), datetime.date(2024, 9, 21)),
            DoublesGame((PLAYERS['James Zhong'], PLAYERS['John Sterling']), (PLAYERS['Sean Grate'], PLAYERS['Emma Snyder']), (21, 18), datetime.date(2024, 11, 20)),
            DoublesGame((PLAYERS['Tim Eller'], PLAYERS['John Sterling']), (PLAYERS['Tristan Salinas'], PLAYERS['Sayantani Battacharya']), (21, 5), datetime.date(2024, 8, 18)),
            SinglesGame(PLAYERS['Jared DeLeo'], PLAYERS['James Zhong'], (21, 17), datetime.date(2024, 9, 7)),
            SinglesGame(PLAYERS['Tim Eller'], PLAYERS['Seth Harward'], (21, 8), datetime.date(2024, 9, 3)),
            DoublesGame((PLAYERS['Kenny Powell'], PLAYERS['John David Clifton']), (PLAYERS['Owen Henderschedt'], PLAYERS['Tristan Salinas']), (21, 3), datetime.date(2024, 12, 1)),
            DoublesGame((PLAYERS['Sean Grate'], PLAYERS['Owen Henderschedt']), (PLAYERS['John Sterling'], PLAYERS['Emma Snyder']), (21, 3), datetime.date(2024, 10, 5)),
            SinglesGame(PLAYERS['John Sterling'], PLAYERS['Jared DeLeo'], (21, 5), datetime.date(2024, 9, 3)),
            SinglesGame(PLAYERS['John David Clifton'], PLAYERS['Sean Grate'], (21, 8), datetime.date(2024, 8, 3)),
            SinglesGame(PLAYERS['John Sterling'], PLAYERS['Sean Grate'], (21, 17), datetime.date(2024, 11, 1)),
            DoublesGame((PLAYERS['John David Clifton'], PLAYERS['Kenny Powell']), (PLAYERS['John Sterling'], PLAYERS['Emma Snyder']), (21, 2), datetime.date(2024, 12, 14)),
            DoublesGame((PLAYERS['Jared DeLeo'], PLAYERS['John Sterling']), (PLAYERS['John David Clifton'], PLAYERS['Sayantani Battacharya']), (21, 18), datetime.date(2024, 10, 10)),
            DoublesGame((PLAYERS['Sayantani Battacharya'], PLAYERS['John Sterling']), (PLAYERS['Owen Henderschedt'], PLAYERS['Tim Eller']), (21, 10), datetime.date(2024, 10, 23)),
            SinglesGame(PLAYERS['Tristan Salinas'], PLAYERS['John David Clifton'], (21, 11), datetime.date(2024, 11, 2)),
            DoublesGame((PLAYERS['Owen Henderschedt'], PLAYERS['Sayantani Battacharya']), (PLAYERS['Sean Grate'], PLAYERS['Tim Eller']), (21, 4), datetime.date(2024, 12, 16)),
            SinglesGame(PLAYERS['Kenny Powell'], PLAYERS['John Cobb'], (21, 3), datetime.date(2024, 8, 8)),
            DoublesGame((PLAYERS['Owen Henderschedt'], PLAYERS['John Sterling']), (PLAYERS['Sean Grate'], PLAYERS['John David Clifton']), (21, 3), datetime.date(2024, 9, 19)),
            DoublesGame((PLAYERS['Sayantani Battacharya'], PLAYERS['John Cobb']), (PLAYERS['Jared DeLeo'], PLAYERS['Owen Henderschedt']), (21, 10), datetime.date(2024, 9, 7)),
            DoublesGame((PLAYERS['John Cobb'], PLAYERS['Sayantani Battacharya']), (PLAYERS['Owen Henderschedt'], PLAYERS['Emma Snyder']), (21, 7), datetime.date(2024, 8, 16)),
            DoublesGame((PLAYERS['John David Clifton'], PLAYERS['Tim Eller']), (PLAYERS['Jared DeLeo'], PLAYERS['James Zhong']), (21, 8), datetime.date(2024, 9, 27)),
            SinglesGame(PLAYERS['Emma Snyder'], PLAYERS['Seth Harward'], (21, 15), datetime.date(2024, 12, 21)),
            DoublesGame((PLAYERS['James Zhong'], PLAYERS['Tristan Salinas']), (PLAYERS['Jared DeLeo'], PLAYERS['Owen Henderschedt']), (21, 5), datetime.date(2024, 11, 24)),
            SinglesGame(PLAYERS['Kenny Powell'], PLAYERS['John David Clifton'], (21, 10), datetime.date(2024, 11, 12)),
            SinglesGame(PLAYERS['Tim Eller'], PLAYERS['John Cobb'], (21, 11), datetime.date(2024, 12, 21)),
            DoublesGame((PLAYERS['Tristan Salinas'], PLAYERS['Owen Henderschedt']), (PLAYERS['Emma Snyder'], PLAYERS['Sayantani Battacharya']), (21, 15), datetime.date(2024, 12, 23)),
            SinglesGame(PLAYERS['Sean Grate'], PLAYERS['Owen Henderschedt'], (21, 12), datetime.date(2024, 10, 11)),
            SinglesGame(PLAYERS['Seth Harward'], PLAYERS['Emma Snyder'], (21, 18), datetime.date(2024, 12, 16)),
            DoublesGame((PLAYERS['James Zhong'], PLAYERS['Sayantani Battacharya']), (PLAYERS['Kenny Powell'], PLAYERS['Tristan Salinas']), (21, 6), datetime.date(2024, 10, 7)),
            DoublesGame((PLAYERS['Kenny Powell'], PLAYERS['Emma Snyder']), (PLAYERS['John Cobb'], PLAYERS['Sayantani Battacharya']), (21, 9), datetime.date(2024, 11, 16)),
            DoublesGame((PLAYERS['Kenny Powell'], PLAYERS['Tim Eller']), (PLAYERS['Tristan Salinas'], PLAYERS['Jared DeLeo']), (21, 2), datetime.date(2024, 11, 6)),
            DoublesGame((PLAYERS['Tristan Salinas'], PLAYERS['Tim Eller']), (PLAYERS['James Zhong'], PLAYERS['Owen Henderschedt']), (21, 17), datetime.date(2024, 12, 18)),
            DoublesGame((PLAYERS['Kenny Powell'], PLAYERS['Tim Eller']), (PLAYERS['Tristan Salinas'], PLAYERS['John Cobb']), (21, 4), datetime.date(2024, 10, 25)),
            DoublesGame((PLAYERS['Tim Eller'], PLAYERS['Sean Grate']), (PLAYERS['Tristan Salinas'], PLAYERS['John Sterling']), (21, 12), datetime.date(2024, 11, 14)),
            DoublesGame((PLAYERS['Seth Harward'], PLAYERS['Tim Eller']), (PLAYERS['Sayantani Battacharya'], PLAYERS['Tristan Salinas']), (21, 8), datetime.date(2024, 11, 21)),
            SinglesGame(PLAYERS['Owen Henderschedt'], PLAYERS['Emma Snyder'], (21, 17), datetime.date(2024, 11, 16)),
            SinglesGame(PLAYERS['Kenny Powell'], PLAYERS['John Sterling'], (21, 17), datetime.date(2024, 8, 23)),
            SinglesGame(PLAYERS['Seth Harward'], PLAYERS['Tristan Salinas'], (21, 13), datetime.date(2024, 8, 11)),
            DoublesGame((PLAYERS['Seth Harward'], PLAYERS['Tim Eller']), (PLAYERS['John Sterling'], PLAYERS['Emma Snyder']), (21, 14), datetime.date(2024, 10, 9)),
            SinglesGame(PLAYERS['Seth Harward'], PLAYERS['Emma Snyder'], (21, 19), datetime.date(2024, 8, 30)),
            DoublesGame((PLAYERS['John Sterling'], PLAYERS['Seth Harward']), (PLAYERS['John Cobb'], PLAYERS['Tim Eller']), (21, 20), datetime.date(2024, 8, 18)),
            SinglesGame(PLAYERS['Emma Snyder'], PLAYERS['Owen Henderschedt'], (21, 12), datetime.date(2024, 10, 3)),
            DoublesGame((PLAYERS['Emma Snyder'], PLAYERS['John Cobb']), (PLAYERS['Tim Eller'], PLAYERS['Jared DeLeo']), (21, 8), datetime.date(2024, 8, 28)),
            SinglesGame(PLAYERS['Tristan Salinas'], PLAYERS['Tim Eller'], (21, 10), datetime.date(2024, 8, 16)),
            SinglesGame(PLAYERS['Sayantani Battacharya'], PLAYERS['Kenny Powell'], (21, 5), datetime.date(2024, 12, 16)),
            SinglesGame(PLAYERS['Jared DeLeo'], PLAYERS['Owen Henderschedt'], (21, 17), datetime.date(2024, 10, 9)),
            SinglesGame(PLAYERS['Emma Snyder'], PLAYERS['Sean Grate'], (21, 4), datetime.date(2024, 11, 12)),
            SinglesGame(PLAYERS['Sean Grate'], PLAYERS['Kenny Powell'], (21, 11), datetime.date(2024, 12, 18)),
            DoublesGame((PLAYERS['James Zhong'], PLAYERS['Owen Henderschedt']), (PLAYERS['John Cobb'], PLAYERS['Sean Grate']), (21, 3), datetime.date(2024, 9, 13)),
            DoublesGame((PLAYERS['Sean Grate'], PLAYERS['Kenny Powell']), (PLAYERS['John Sterling'], PLAYERS['Emma Snyder']), (21, 1), datetime.date(2024, 9, 17)),
            SinglesGame(PLAYERS['John Cobb'], PLAYERS['Owen Henderschedt'], (21, 14), datetime.date(2024, 10, 7)),
            DoublesGame((PLAYERS['Tristan Salinas'], PLAYERS['Emma Snyder']), (PLAYERS['Kenny Powell'], PLAYERS['Owen Henderschedt']), (21, 8), datetime.date(2024, 11, 10)),
            SinglesGame(PLAYERS['John David Clifton'], PLAYERS['Sayantani Battacharya'], (21, 16), datetime.date(2024, 8, 23)),
            SinglesGame(PLAYERS['Sean Grate'], PLAYERS['Kenny Powell'], (21, 15), datetime.date(2024, 9, 9)),
            SinglesGame(PLAYERS['Sean Grate'], PLAYERS['Emma Snyder'], (21, 16), datetime.date(2024, 11, 13)),
            DoublesGame((PLAYERS['Sean Grate'], PLAYERS['John Sterling']), (PLAYERS['Jared DeLeo'], PLAYERS['Sayantani Battacharya']), (21, 2), datetime.date(2024, 11, 1)),
            SinglesGame(PLAYERS['John Sterling'], PLAYERS['Owen Henderschedt'], (21, 9), datetime.date(2024, 12, 8)),
            DoublesGame((PLAYERS['John David Clifton'], PLAYERS['Tim Eller']), (PLAYERS['Sayantani Battacharya'], PLAYERS['Owen Henderschedt']), (21, 13), datetime.date(2024, 12, 17)),
            DoublesGame((PLAYERS['James Zhong'], PLAYERS['Tristan Salinas']), (PLAYERS['Owen Henderschedt'], PLAYERS['Tim Eller']), (21, 9), datetime.date(2024, 9, 29)),
            SinglesGame(PLAYERS['Seth Harward'], PLAYERS['John Sterling'], (21, 18), datetime.date(2024, 9, 25)),
            DoublesGame((PLAYERS['John David Clifton'], PLAYERS['Seth Harward']), (PLAYERS['Owen Henderschedt'], PLAYERS['Sean Grate']), (21, 2), datetime.date(2024, 11, 18)),
            DoublesGame((PLAYERS['John Cobb'], PLAYERS['Owen Henderschedt']), (PLAYERS['Seth Harward'], PLAYERS['Emma Snyder']), (21, 11), datetime.date(2024, 12, 8)),
            DoublesGame((PLAYERS['Sayantani Battacharya'], PLAYERS['Emma Snyder']), (PLAYERS['John David Clifton'], PLAYERS['John Sterling']), (21, 13), datetime.date(2024, 12, 23)),
            DoublesGame((PLAYERS['Kenny Powell'], PLAYERS['James Zhong']), (PLAYERS['Tim Eller'], PLAYERS['John David Clifton']), (21, 11), datetime.date(2024, 9, 19)),
            DoublesGame((PLAYERS['Owen Henderschedt'], PLAYERS['John Sterling']), (PLAYERS['Seth Harward'], PLAYERS['Emma Snyder']), (21, 8), datetime.date(2024, 12, 16)),
            DoublesGame((PLAYERS['Seth Harward'], PLAYERS['Owen Henderschedt']), (PLAYERS['Emma Snyder'], PLAYERS['James Zhong']), (21, 19), datetime.date(2024, 11, 27)),
            SinglesGame(PLAYERS['Sayantani Battacharya'], PLAYERS['Kenny Powell'], (21, 15), datetime.date(2024, 10, 4)),
            DoublesGame((PLAYERS['John Cobb'], PLAYERS['Jared DeLeo']), (PLAYERS['Emma Snyder'], PLAYERS['Seth Harward']), (21, 14), datetime.date(2024, 9, 11)),
            SinglesGame(PLAYERS['Sayantani Battacharya'], PLAYERS['Kenny Powell'], (21, 18), datetime.date(2024, 9, 14))]
    """
            
    # calculate all the stats
    player_names = list(PLAYERS.keys())
    # having these two dataframes is probably redundant; it can probably be condensed via groupby operations
    player_data = pd.DataFrame(0, index=pd.MultiIndex.from_product([player_names, player_names], names=['player1', 'player2']),
                               columns=['wins', 'losses', 'points_for', 'points_against', 'point_diff'], dtype=int)
    game_data = pd.DataFrame([{'player1': game.first_player.name, 'player2': game.second_player.name, 'score': game.score, 'date': game.date} for game in GAMES if isinstance(game, SinglesGame)],
                             columns=['player1', 'player2', 'score', 'date'])
    for game in GAMES:
        if isinstance(game, SinglesGame):
            # update the player data
            winner, loser = game.winner.name, game.loser.name
            # win-loss record
            player_data.loc[(winner, loser), 'wins'] += 1
            player_data.loc[(loser, winner), 'losses'] += 1
            # point totals
            player_data.loc[(game.first_player.name, game.second_player.name), 'points_for'] += game.score[0]
            player_data.loc[(game.first_player.name, game.second_player.name), 'points_against'] += game.score[1]
            player_data.loc[(game.second_player.name, game.first_player.name), 'points_for'] += game.score[1]
            player_data.loc[(game.second_player.name, game.first_player.name), 'points_against'] += game.score[0]
            # point differential
            point_diff = abs(max(game.score) - min(game.score))
            player_data.loc[(winner, loser), 'point_diff'] += point_diff
            player_data.loc[(loser, winner), 'point_diff'] -= point_diff
    player_data['total_games'] = player_data['wins'] + player_data['losses']
    player_data['record'] = player_data['wins'].astype(str) + '-' + player_data['losses'].astype(str)

    # plot the data in tabs
    player_data.reset_index(inplace=True)
    player_source = ColumnDataSource(player_data)
    plots = {'Total Games Played': total_games_dashboard(player_names, player_data, game_data, player_source),
             'Head-to-Head Record': head_to_head_dashboard(player_names, player_data, player_source),
             'Point Differential': point_differential_dashboard(player_names, player_data, player_source)}
    tabs = Tabs(tabs=[TabPanel(child=p, title=title) for title, p in plots.items()])

    output_file(filename=Path(__file__).parent.parent / 'badminton' / 'index.html',
                title='Badminton Stats', mode='inline')
    save(tabs)


if __name__ == '__main__':
    main()