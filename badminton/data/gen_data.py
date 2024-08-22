import datetime
from pathlib import Path
import random

def main():
    PLAYERS = ('Daniel Hodgins',
               'Emma Snyder',
               'James Zhong',
               'Jared DeLeo',
               'John Cobb',
               'John David Clifton',
               'John Sterling',
               'Kenny Powell',
               'Owen Henderschedt',
               'Sayantani Battacharya',
               'Sean Grate',
               'Seth Harward',
               'Tim Eller',
               'Tristan Salinas')
    
    singles_prob = 0.75
    num_games = 1000
    with open(Path(__file__).parent / 'mock.csv', 'w') as f:
        f.write('player1,player2,player3,player4,score1,score2,date\n')
        for idx in range(num_games):
            players = random.sample(PLAYERS, 4)
            if random.random() < singles_prob:
                f.write(f'{players[0]},{players[1]},,,21,{random.randint(0, 20)},{datetime.date(2024, random.randint(8, 12), random.randint(1, 30))}\n')
            else:
                f.write(f'{players[0]},{players[1]},{players[2]},{players[3]},21,{random.randint(0, 20)},{datetime.date(2024, random.randint(8, 12), random.randint(1, 30))}\n')


if __name__ == '__main__':
    main()