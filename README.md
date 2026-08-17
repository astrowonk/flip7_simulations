This simulates the game Flip &. Draw 3 and Freeze behavior still to be implemented.

Usage:

```python

from simulate import simulate_parallel
from analysis import table_from_out
from game import Game
from players import PointThresholdPlayer,ExpectedPlayer



player_list = [
    PointThresholdPlayer(25),
    PointThresholdPlayer(30),
    ExpectedPlayer(),
    ExpectedPlayer(threshold=-1, leader_gap=40, threshold_shift=-1),
]

out, round_data = simulate_parallel(Game,10000,workers=10,player_list=player_list)
table_from_out(out) #requries polars and great_tablesß
```

Bot styles:

- PointThresholdPlayer - In every round stops when points >= a specific threshold
- ExpectedPlayer - Using full deck knowledge (e.g. card counting), hit only when expected value > threshold. Dynamic settings can loosen the threshold when late in a game.
- CardThresholdPlayer - hits until >= a fixed card limit
- CheaterPlayer - knows next card by peeking at the Deck. Never busts
- SmartishPlayer - I tried to implement some simple rules based on expectation values of a full deck but ... This bot doesn't really do well and 1 v 1 is tied with a CardThresholdPlayer
