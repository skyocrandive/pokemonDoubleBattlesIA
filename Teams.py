from poke_env.teambuilder import Teambuilder
from poke_env.environment.pokemon import Pokemon
import numpy as np

class RandomTeamFromPool(Teambuilder):

    team_1 = """
Excadrill @ Choice Band  
Ability: Sand Rush  
Level: 50  
EVs: 252 Atk / 4 SpD / 252 Spe  
Adamant Nature  
- High Horsepower  
- Iron Head  
- Brick Break  
- X-Scissor  

Tyranitar @ Weakness Policy  
Ability: Sand Stream  
Level: 50  
EVs: 252 Atk / 4 SpD / 252 Spe  
Adamant Nature  
- Dragon Dance  
- Rock Slide  
- Crunch  
- Fire Punch  

Dragapult @ Light Clay  
Ability: Clear Body  
Level: 50  
EVs: 252 Atk / 4 SpD / 252 Spe  
Jolly Nature  
- Breaking Swipe  
- Light Screen  
- Reflect  
- Dragon Darts  

Togekiss @ Scope Lens  
Ability: Super Luck  
Level: 50  
EVs: 4 HP / 252 SpA / 252 Spe  
Timid Nature  
IVs: 0 Atk  
- Air Slash  
- Dazzling Gleam  
- Protect  
- Heat Wave 

Amoonguss @ Sitrus Berry  
Ability: Regenerator  
Level: 50  
EVs: 252 HP / 4 SpA / 252 SpD  
Calm Nature  
IVs: 0 Atk  
- Rage Powder  
- Protect  
- Spore  
- Pollen Puff   

Whimsicott @ Focus Sash  
Ability: Prankster  
Level: 50  
EVs: 252 HP / 252 Def / 4 SpA  
Bold Nature  
IVs: 0 Atk  
- Tailwind  
- Taunt  
- Moonblast  
- Charm  
"""

    def __init__(self):
        self.teams = [self.join_team(self.parse_showdown_team(self.team_1))]


    def yield_team(self):
        #return np.random.choice(self.teams)
        return self.teams[0]

#custom_builder = RandomTeamFromPool([team_1])