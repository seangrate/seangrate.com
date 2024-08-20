from collections import defaultdict
import datetime
import itertools as it
from pathlib import Path
from typing import Tuple

from pprint import pprint
import sys

from bokeh.plotting import figure, save
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper, ColorBar, TabPanel, Tabs
from bokeh.transform import transform
from bokeh.palettes import Magma256
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
    


def plot_total_games(players, players_df, source):
    color_mapper = LinearColorMapper(palette=Magma256, low=players_df['total_games'].min(), high=players_df['total_games'].max())
    p = figure(title='Total Games Played', x_range=players, y_range=players, 
               x_axis_location='above', width=800, height=800,
               tools='hover,save', tooltips='@player1 vs @player2: @total_games')

    p.rect(x='player2', y='player1', width=1, height=1, source=source,
           line_color=None, fill_color=transform('total_games', color_mapper))

    p.xaxis.major_label_orientation = 1.0
    p.yaxis.major_label_orientation = 1.0

    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p.add_layout(color_bar, 'right')

    return p


def plot_head_to_head(players, players_df, source):
    color_mapper = LinearColorMapper(palette=Magma256, low=players_df['wins'].min(), high=players_df['wins'].max())

    p = figure(title='Head-to-Head Record', x_range=players, y_range=players, 
                x_axis_location='above', width=800, height=800,
                tools='hover,save', tooltips='@player1 vs @player2: @record')

    p.rect(x='player2', y='player1', width=1, height=1, source=source,
           line_color=None, fill_color=transform('wins', color_mapper))

    p.xaxis.major_label_orientation = 1.0
    p.yaxis.major_label_orientation = 1.0

    color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))
    p.add_layout(color_bar, 'right')

    return p


def plot_point_differential(players, players_df, source):
    color_mapper_diff = LinearColorMapper(palette=Magma256, low=players_df['point_diff'].min(), high=players_df['point_diff'].max())

    p = figure(title='Point Differential', x_range=players, y_range=players, 
               x_axis_location='above', width=800, height=800,
               tools='hover,save', tooltips='@player1 vs @player2: @point_diff')

    p.rect(x='player2', y='player1', width=1, height=1, source=source,
           line_color=None, fill_color=transform('point_diff', color_mapper_diff))

    p.xaxis.major_label_orientation = 1.0
    p.yaxis.major_label_orientation = 1.0

    color_bar = ColorBar(color_mapper=color_mapper_diff, location=(0, 0))
    p.add_layout(color_bar, 'right')

    return p


def main():
    PLAYERS = {'Emma Snyder': Player('Emma Snyder'),
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

    # calculate all the stats
    player_names = list(PLAYERS.keys())
    data = pd.DataFrame(0, index=pd.MultiIndex.from_product([player_names, player_names], names=['player1', 'player2']),
                        columns=['wins', 'losses', 'points_for', 'points_against', 'point_diff'], dtype=int)
    for game in GAMES:
        if isinstance(game, SinglesGame):
            winner, loser = game.winner.name, game.loser.name
            # win-loss record
            data.loc[(winner, loser), 'wins'] += 1
            data.loc[(loser, winner), 'losses'] += 1
            # point totals
            data.loc[(game.first_player.name, game.second_player.name), 'points_for'] += game.score[0]
            data.loc[(game.first_player.name, game.second_player.name), 'points_against'] += game.score[1]
            data.loc[(game.second_player.name, game.first_player.name), 'points_for'] += game.score[1]
            data.loc[(game.second_player.name, game.first_player.name), 'points_against'] += game.score[0]
            # point differential
            point_diff = abs(max(game.score) - min(game.score))
            data.loc[(winner, loser), 'point_diff'] += point_diff
            data.loc[(loser, winner), 'point_diff'] -= point_diff
    data['total_games'] = data['wins'] + data['losses']
    data['record'] = data['wins'].astype(str) + '-' + data['losses'].astype(str)

    # plot the data in tabs
    data.reset_index(inplace=True)
    source = ColumnDataSource(data)
    plots = {'Total Games Played': plot_total_games(player_names, data, source),
             'Head-to-Head Record': plot_head_to_head(player_names, data, source),
             'Point Differential': plot_point_differential(player_names, data, source)}
    tabs = Tabs(tabs=[TabPanel(child=p, title=title) for title, p in plots.items()])

    output_file(filename=Path(__file__).parent.parent / 'badminton' / 'stats.html',
                title='Badminton Stats', mode='inline')
    save(tabs)


if __name__ == '__main__':
    main()