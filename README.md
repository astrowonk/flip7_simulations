This simulates the game Flip &. Draw 3 and Freeze behavior still to be implemented.

Usage:

```python
from flip7good import simulate_parallel,table_from_out,pipe_rate_error,Smartish,ExpectedPlayer,PointThresholdPlayer,Game
player_list = [
    PointThresholdPlayer(25),
    PointThresholdPlayer(30),
    ExpectedPlayer(),
    ExpectedPlayer(threshold=-1, leader_gap=40, threshold_shift=-1),
]

out, round_data = simulate_parallel(Game,10000,workers=10,player_list=player_list)
table_from_out(out)
```
