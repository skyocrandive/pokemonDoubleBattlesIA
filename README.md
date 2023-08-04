<br/>
<p align="center">
  <a href="https://github.com/skyocrandive/pokemonDoubleBattlesIA">

  <h3 align="center">Pokemon Double Battles IA</h3>
</a>
</p>
<div align="center">

  ![Contributors](https://img.shields.io/github/contributors/skyocrandive/pokemonDoubleBattlesIA?color=dark-green)
  ![Forks](https://img.shields.io/github/forks/skyocrandive/pokemonDoubleBattlesIA?style=social)
  ![Stargazers](https://img.shields.io/github/stars/skyocrandive/pokemonDoubleBattlesIA?style=social)
  ![Issues](https://img.shields.io/github/issues/skyocrandive/pokemonDoubleBattlesIA) 
  
</div>

## About The Project
The AI is capable of double battles from generation 8 and below with the exclusion of generational mechanics (Dynamax, z-moves, mega-evolutions).
Pokemon teams assigned to the AI are relative to the VGC 2021 battle format (generation 8, series 7).
This project contains four AI players:
* **DoublesRandomPlayer**: not predictable but not at all effective
* **DoublesMaxDamagePlayer**: very predictable, always aims to do maximum damage.
* **DoublesTrueMaxDamagePlayer**: has more knowledge of the complexities of game mechanics than the previous one (skills, objects, terrain, weather). It is able to more accurately calculate the damage of individual moves.
* **SmartPlayer**: player able to use Protect, change Pokemon in case of an unfavorable matchup, select an action with some variance to make the AI less predictable.The player is not very predictable and acts by trying to use all the knowledge it can get even during the battle itself. It is not constrained in the use of attack moves (unless it is certain that it can defeat the opponent with a priority move).

## Built With

Android App developed with Android Studio and written entirely in Java.

* [PyCharm](https://www.jetbrains.com/pycharm/)
* [Python](https://www.python.org/)

## Getting Started

Follow these instructions to set up your project locally.

### Prerequisites

* Python 3
* node

### Installation
1. Install poke-env
```sh
pip install poke-env
```

2. Clone the repo
```sh
git clone https://github.com/skyocrandive/pokemonDoubleBattlesIA.git
```

3.  Clone Pokemon Showdown repo
```sh
git clone https://github.com/smogon/pokemon-showdown.git
cd pokemon-showdown
npm install
```

## Usage
 1. Start Pokemon Showdown local server
```sh
node pokemon-showdown start --no-security
```
Go to http://localhost:8000

2. Select Pokemon Showdown username</br>
Click choose name</br>
Insert username</br>
</br>
3. Create your own Pokemon team</br>
Click Teambuilder</br>
New Team</br>
Select Format gen8vgc2021</br>
If you want to use the same team as the AI, paste the code in "base_team.txt" inside the textarea after pressing import/export.</br>
</br>
4. Run MainBattleStarter.py</br>
```sh
python3 MainBattleStarter.py
```

## Authors

* **Cristiano Arnaudo** - *Studente Ingegneria Informatica a Bologna* - [Cristiano Arnaudo](https://github.com/skyocrandive)
* **Andrea Munari** - *Studente Ingegneria Informatica a Bologna* - [Andrea Munari](https://github.com/AndreaMunari)

## Acknowledgements

* [Pokemon Showdown](https://github.com/smogon/pokemon-showdown)
* [poke-env](https://github.com/hsahovic/poke-env)