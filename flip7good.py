from __future__ import annotations

import random
from collections import Counter, defaultdict
from secrets import token_urlsafe

from tqdm.autonotebook import tqdm

norm_cards = {str(x) for x in range(13)}


def get_value(card):

    try:
        value = int(card.replace('+', ''))
    except:
        value = 0
    return value


def make_deck():
    return [
        *['0'] * 1,
        *['1'] * 1,
        *['2'] * 2,
        *['3'] * 3,
        *['4'] * 4,
        *['5'] * 5,
        *['6'] * 6,
        *['7'] * 7,
        *['8'] * 8,
        *['9'] * 9,
        *['10'] * 10,
        *['11'] * 11,
        *['12'] * 12,
        'x2',
        '+2',
        '+4',
        '+6',
        '+8',
        '+10',
        *['freeze'] * 3,
        *['second_chance'] * 3,
        *['draw_3'] * 3,
    ]


class Deck:
    cards = None

    def __init__(self):
        self.shuffle()

    def shuffle(self):
        """Shuffle deck"""
        # print('Shuffling')
        self.cards = make_deck()
        random.shuffle(self.cards)

    def deal(self, player: BasePlayer, card=None):
        if not self.cards:
            self.shuffle()
        if player.busted or player.stopped:
            return
        if not card:
            card = self.cards.pop()
        else:
            self.cards.remove(card)
        player.deal(card)

    def compute_card_probs(self):
        c = Counter(self.cards)
        total = sum(c.values())
        return {key: val / total for key, val in c.items()}


class BasePlayer:
    stopped = False
    flip7 = False
    busted = False
    had_second_chance = False

    def __init__(self):
        self.cards = set()
        self.unique_hash = token_urlsafe(4)

    def deal(self, card):
        if self.stopped:
            return
        if card in self.cards:
            if 'second_chance' in self.cards:
                self.cards.remove('second_chance')
                return
            else:
                self.busted = True
                self.stopped = True
        self.cards.add(card)
        if len([x for x in self.cards if x in norm_cards]) == 7:
            self.flip7 = True
            self.stopped = True

    #   print(f'Busted:{self.busted}')
    # print(self.get_total_value())

    def new_round(self):
        self.stopped = False
        self.flip7 = False
        self.busted = False
        self.had_second_chance = False

        self.cards = set()

    def get_total_value(self):
        if self.busted:
            return 0

        mynormcards = [x for x in self.cards if x in norm_cards]
        norm_value = sum(get_value(x) for x in mynormcards)
        if 'x2' in self.cards:
            norm_value = norm_value * 2
        value = norm_value
        if self.flip7:
            value = value + 15
        value += sum(get_value(x) for x in self.cards if x not in norm_cards)
        return value

    def get_card_value(self, card):
        mult = 1
        if 'x2' in self.cards and card in norm_cards:
            mult = 2
        if card in norm_cards and card in self.cards and ('second_chance' not in self.cards):
            return 0
        elif card == 'x2':
            return sum(get_value(x) for x in self.cards if x in norm_cards) * 2
        elif card == 'second_chance':
            return self.get_total_value() + 10
        else:
            return self.get_total_value() + get_value(card) * mult

    def compute_expected_value(self, deck: Deck):
        probs = deck.compute_card_probs()
        current_value = self.get_total_value()
        out = 0
        bust_prob = 0
        can_bust = 'second_chance' not in self.cards
        for card, prob in probs.items():
            if can_bust and card in norm_cards and card in self.cards:
                bust_prob += prob
            val = self.get_card_value(card)
            out += prob * val
        return {
            'expected_future_score': out,
            'current_value': current_value,
            'expected_value': (out - current_value),
            'bust_prob': bust_prob,
        }

    def decide_hit(self):
        pass


class SimplePlayer(BasePlayer):
    def __init__(self, threshold=25):
        self.cards = set()
        self.threshold = threshold
        self.unique_hash = token_urlsafe(4)

    def __repr__(self):
        return f'Point Threshold {self.threshold} {self.unique_hash}'

    def decide_hit(self, deck):
        if 'second_chance' in self.cards:
            return True
        elif self.get_total_value() >= self.threshold:
            return False
        return True


class RandomPlayer(SimplePlayer):
    def __repr__(self):
        return f'Random Player {self.unique_hash}'

    def __init__(self):
        super().__init__(threshold=1)
        self.threshold = random.randint(1, 50)

    def new_round(self):
        super().new_round()
        self.threshold = random.randint(1, 50)


class CardThreshold(BasePlayer):
    def __init__(self, threshold=4):
        self.cards = []
        self.threshold = threshold
        self.unique_hash = token_urlsafe(4)

    def __repr__(self):
        return f'Card Limit {self.threshold} {self.unique_hash}'

    def decide_hit(self, _):
        if len([x for x in self.cards if x in norm_cards]) < self.threshold:
            return True
        return False


class ExpectedPlayer(BasePlayer):
    def __repr__(self):
        return f'Expected Value Player : {self.threshold} {self.unique_hash}'

    def __init__(self, threshold=0):
        super().__init__()
        self.threshold = threshold

    def decide_hit(self, deck):
        res = self.compute_expected_value(deck)
        if res['expected_value'] > self.threshold:
            return True
        return False


class Smartish(BasePlayer):
    def __init__(self, threshold=28):
        super().__init__()
        self.threshold = threshold

    def __repr__(self):
        return f'Smartish Player : {self.threshold} {self.unique_hash}'

    def decide_hit(self, deck):
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


class Game:
    def __init__(self, player_list: list[BasePlayer]):
        self.player_list = player_list
        self.round_data = []

    def prep_game(self):
        self.player_scores = {player: defaultdict(int) for player in self.player_list}
        for player in self.player_list:
            player.new_round()
        self.deck = Deck()
        self.round_num = 1
        self.round_data = []

    def round(self, i=0):

        while not all(p.stopped for p in self.player_scores.keys()):
            if any(p.flip7 for p in self.player_scores.keys()):
                break
            for player, d in self.player_scores.items():
                if player.stopped:
                    continue
                if player.decide_hit(self.deck):
                    # print(f'Dealing to {player}')
                    self.deck.deal(player)

                    #      print(player.cards)
                    if 'second_chance' in player.cards:
                        #    print(player, 'second chance help')
                        player.had_second_chance = True
                else:
                    player.stopped = True
        #    print(f'End Round {self.round_num}')
        #   print(len(self.deck.cards))
        round_data = []
        for player in self.player_list:
            # print(score)
            self.player_scores[player]['score'] += player.get_total_value()
            self.player_scores[player]['busted'] += player.busted
            self.player_scores[player]['rounds'] += 1
            round_data.append({
                'player': str(player),
                'score': player.get_total_value(),
                'second_chance_flag': player.had_second_chance,
                'busted': player.busted,
                'round': self.round_num,
                'flip7': player.flip7,
                'hand_size': len(player.cards),
                'hand': ','.join(player.cards),
            })
            player.new_round()

        self.round_num += 1

        return round_data

    def play_game(self):
        i = 0
        self.prep_game()
        while all(
            score < 200 for score in [val['score'] for val in self.player_scores.values()]
        ):
            i += 1
            self.round_data.extend(self.round())
            if i > 50:
                break
        while (
            Counter([val['score'] for val in self.player_scores.values()]).most_common()[0][1]
            > 1
        ):
            # break ties
            self.round_data.extend(self.round())

    def simulate(self, n=100, save_round_data=False):
        out = []
        all_round_data = []
        for i in tqdm(range(n)):
            self.play_game()
            d = [
                {
                    'name': str(key),
                    'score': val['score'],
                    'game': i,
                    'busted': val['busted'],
                    'rounds': val['rounds'],
                }
                for key, val in self.player_scores.items()
            ]
            out.extend(d)
            if save_round_data:
                round_data = self.round_data.copy()
                for round in round_data:
                    round['game'] = i
                all_round_data.extend(round_data)
        return out, all_round_data
