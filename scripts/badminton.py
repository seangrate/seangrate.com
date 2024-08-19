import datetime
from typing import Tuple

from bokeh.plotting import figure, save


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
    

def main():
    players = {'Emma Snyder': Player('Emma Snyder'),
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
    
    games = [SinglesGame(players['Emma Snyder'], 
                        players['James Zhong'], 
                        (21, 19),
                        datetime.date(2024, 8, 19)),
            SinglesGame(players['Jared DeLeo'], 
                        players['John Cobb'], 
                        (15, 21),
                        datetime.date(2024, 8, 21)),
            DoublesGame((players['John David Clifton'], players['John Sterling']), 
                        (players['Kenny Powell'], players['Owen Henderschedt']), 
                        (21, 18),
                        datetime.date(2024, 8, 19))]