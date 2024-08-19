class Player {
  constructor(name) {
    this.name = name
  }
}

class Game {
  constructor(score, date) {
    this.score = score
    this.date = date
  }

  get pointDifferential() {
    return Math.abs(this.score[0] - this.score[1])
  }
}

class SinglesGame extends Game {
  constructor(firstPlayer, secondPlayer, score, date) {
    super(score, date)
    this.firstPlayer = firstPlayer
    this.secondPlayer = secondPlayer
  }

  get winner() {
    return this.score[0] > this.score[1] ? this.firstPlayer : this.secondPlayer
  }

  get loser() {
    return this.score[0] < this.score[1] ? this.firstPlayer : this.secondPlayer
  }
}

class DoublesGame extends Game {
  constructor(firstTeam, secondTeam, score, date) {
    super(score, date)
    this.firstTeam = firstTeam
    this.secondTeam = secondTeam
  }

  get winner() {
    return this.score[0] > this.score[1] ? this.firstTeam : this.secondTeam
  }

  get loser() {
    return this.score[0] < this.score[1] ? this.firstTeam : this.secondTeam
  }
}

// player data
const PLAYERS = {
  'Emma Snyder': new Player('Emma Snyder'),
  'James Zhong': new Player('James Zhong'),
  'Jared DeLeo': new Player('Jared DeLeo'),
  'John Cobb': new Player('John Cobb'),
  'John David Clifton': new Player('John David Clifton'),
  'John Sterling': new Player('John Sterling'),
  'Kenny Powell': new Player('Kenny Powell'),
  'Owen Henderschedt': new Player('Owen Henderschedt'),
  'Sayantani Battacharya': new Player('Sayantani Battacharya'),
  'Sean Grate': new Player('Sean Grate'),
  'Seth Harward': new Player('Seth Harward'),
  'Tim Eller': new Player('Tim Eller'),
  'Tristan Salinas': new Player('Tristan Salinas')
}

// game data
const GAMES = [
  new SinglesGame(PLAYERS['Emma Snyder'], 
                  PLAYERS['James Zhong'], 
                  [21, 19],
                  new Date('2024-08-19')),
  new SinglesGame(PLAYERS['Jared DeLeo'], 
                  PLAYERS['John Cobb'], 
                 [15, 21],
                  new Date('2024-08-21')),
  new DoublesGame([PLAYERS['John David Clifton'], PLAYERS['John Sterling']], 
                  [PLAYERS['Kenny Powell'], PLAYERS['Owen Henderschedt']], 
                  [21, 18],
                  new Date('2024-08-19'))
]

function displayGames() {
  for (let game of GAMES) {
    let gameDiv = document.createElement('div')
    // gameDiv.classList.add('game')
    if (game instanceof SinglesGame) {
      var gameText = document.createTextNode(`${game.firstPlayer.name} vs. ${game.secondPlayer.name} on ${game.date.toDateString()}`)
    } else if (game instanceof DoublesGame) {
      var gameText = document.createTextNode(`${game.firstTeam[0].name} & ${game.firstTeam[1].name} vs. ${game.secondTeam[0].name} & ${game.secondTeam[1].name} on ${game.date.toDateString()}`)
    }
    gameDiv.appendChild(gameText)
    document.getElementById('games').appendChild(gameDiv)
  }
}