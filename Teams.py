from poke_env.teambuilder import Teambuilder


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

    team_2 = """
Regieleki @ Magnet  
Ability: Transistor  
Level: 50  
EVs: 60 HP / 148 Def / 252 SpA / 4 SpD / 44 Spe  
Modest Nature  
IVs: 0 Atk  
- Electroweb  
- Thunderbolt  
- Volt Switch  
- Protect  

Incineroar @ Mago Berry  
Ability: Intimidate  
Level: 50  
EVs: 236 HP / 28 Atk / 84 Def / 148 SpD / 12 Spe  
Careful Nature  
- Darkest Lariat  
- Flare Blitz  
- Parting Shot  
- Snarl  

Urshifu @ Focus Sash  
Ability: Unseen Fist  
Level: 50  
EVs: 252 Atk / 4 SpD / 252 Spe  
Jolly Nature  
- Wicked Blow  
- Close Combat  
- Sucker Punch  
- Detect  

Tapu Fini @ Sitrus Berry  
Ability: Misty Surge  
Level: 50  
EVs: 252 HP / 36 Def / 116 SpA / 52 SpD / 52 Spe  
Modest Nature  
IVs: 0 Atk  
- Muddy Water  
- Moonblast  
- Calm Mind  
- Protect  

Kartana @ Assault Vest  
Ability: Beast Boost  
Level: 50  
EVs: 92 HP / 108 Atk / 4 Def / 116 SpA / 188 Spe  
- Sacred Sword  
- Smart Strike  
- Leaf Blade  
- Aerial Ace  

Mamoswine @ Life Orb  
Ability: Oblivious  
Level: 50  
EVs: 108 HP / 236 Atk / 4 Def / 4 SpD / 156 Spe  
Adamant Nature  
- Stomping Tantrum  
- Icicle Crash  
- Ice Shard  
- Protect  
"""

    def __init__(self):
        self.teams = [self.join_team(self.parse_showdown_team(self.team_2))]


    def yield_team(self):
        #return np.random.choice(self.teams)
        return self.teams[0]

#custom_builder = RandomTeamFromPool([team_1])