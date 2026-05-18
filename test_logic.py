from game.combat_entities import Rabbit, Slime, Bee, Fox, spawn_bush1_enemies, spawn_bush2_enemies
from game.overworld import OverworldPlayer, T_BUSH, T_BUSH2, T_BOSS
import game.battle, game.ui

print("All imports OK")

r = Rabbit()
print(f"Rabbit Lv{r.level}  HP={r.max_hp}  ATK={r.atk}  EXP_to_next={r.exp_to_next}")

s1 = spawn_bush1_enemies(r.level)
print(f"Bush1 enemies ({len(s1)}):", [(type(e).__name__, e.level, e.max_hp) for e in s1])

s2 = spawn_bush2_enemies(r.level)
print(f"Bush2 enemies ({len(s2)}):", [(type(e).__name__, e.level) for e in s2])

f = Fox(r.level)
f.plan_turn()
acts = [a["type"] for a in f.actions_this_turn]
print(f"Fox Lv{f.level}  HP={f.max_hp}  ATK={f.atk}  actions={acts}")

ow = OverworldPlayer(2, 10)
print(f"OW player col={ow.col()} row={ow.row()} tile={ow.current_tile()}")

# Test damage calc
from game.combat_entities import calc_attack_damage
results = [calc_attack_damage(10) for _ in range(20)]
crits  = sum(1 for d,c,m in results if c)
misses = sum(1 for d,c,m in results if m)
print(f"20 attacks: crits={crits} misses={misses} dmgs={[d for d,c,m in results]}")

print("\nAll checks passed!")
