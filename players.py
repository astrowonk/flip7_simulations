import random

from game import BasePlayer, Deck, Game, get_value, norm_cards


class PointThresholdPlayer(BasePlayer):
    """Stop once greater or equal to a fixed point threshold per round, hit always on second chance card" """

    def __init__(self, threshold=25):
        super().__init__()
        self.threshold = threshold

    def __repr__(self):
        return f'Point Threshold {self.threshold} {self.unique_hash}'

    def decide_hit(self, _):
        if 'second_chance' in self.cards:
            return True
        elif self.get_total_value() >= self.threshold:
            return False
        return True


class RandomThresholdPlayer(PointThresholdPlayer):
    """Every round different threshold"""

    def __repr__(self):
        return f'Random Player {self.unique_hash}'

    def __init__(self):
        super().__init__(threshold=1)
        self.threshold = random.randint(1, 50)

    def new_round(self):
        super().new_round()
        self.threshold = random.randint(1, 50)


class CardThresholdPlayer(BasePlayer):
    """Stop after N cards"""

    def __init__(self, threshold=4):
        self.cards = []
        self.threshold = threshold

    def __repr__(self):
        return f'Card Limit {self.threshold} {self.unique_hash}'

    def decide_hit(self, _):
        if len([x for x in self.cards if x in norm_cards]) < self.threshold:
            return True
        return False


class ExpectedPlayer(BasePlayer):
    def __repr__(self):
        return f'Expected Value Player : {self.threshold} {self.threshold_shift} {self.leader_gap} {self.unique_hash}'

    def __init__(self, threshold=0, threshold_shift=0, leader_gap=-200):
        super().__init__()
        self.threshold = threshold
        self.threshold_shift = threshold_shift
        self.leader_gap = leader_gap

    def decide_hit(self, game):
        if (
            len(self.cards) == 0
        ):  # sometimes this bot wouldn't even take one card. I should probably change the deal logic
            return True  # an empty deck returns 0s, and you must get at least 1 card per round
        res = self.compute_expected_value(game.deck)
        threshold = self.threshold
        if game.check_late_game() and (self.check_leader(game) <= self.leader_gap):
            #   print('shifting threshold')
            threshold += self.threshold_shift
        if len(self.cards) == 0 and res['expected_value'] < threshold:
            print(game.deck.cards)
            raise ValueError
        if res['expected_value'] > threshold:
            return True
        return False


class CheaterPlayer(BasePlayer):
    """Cheats and knows the next card."""

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f'Cheater {self.unique_hash}'

    def decide_hit(self, game):
        assert game.deck, 'deck must not be empty'
        if game.deck.cards[-1] in self.cards.intersection(norm_cards):  # peeks at next card
            return False
        return True


class Smartish(BasePlayer):
    """Uses some simple rules based on expected value of a full deck to decide when to hit but ... doesn't do a great job."""

    def __init__(self, threshold=28):
        super().__init__()
        self.threshold = threshold

    def __repr__(self):
        return f'Smartish Player : {self.threshold} {self.unique_hash}'

    def decide_hit(self, game):
        if 'second_chance' in self.cards:
            return True

        if len(self.cards.intersection({'11', '12'})) == 2:
            return False
        elif len(self.cards) <= 2:
            return True
        elif len(self.cards) == 3:
            if self.cards == {'7', '8', '9'}:
                return True
            elif self.get_total_value() >= 24:
                return False

            return True
        elif len(self.cards) >= 4:
            if self.get_total_value() >= self.threshold:
                return False
            else:
                return True
        return True
