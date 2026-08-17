from __future__ import annotations

import random
from collections import Counter, defaultdict, deque
from secrets import token_urlsafe

from tqdm.autonotebook import tqdm

norm_cards = {str(x) for x in range(13)}


def get_value(card):

    try:
        value = int(card.replace('+', ''))
    except:
        value = 0
    return value


class BasePlayer:
    stopped = False
    flip7 = False
    busted = False
    had_second_chance = False

    def __init__(self):
        self.cards = set()
        self.card_history = []
        self.unique_hash = token_urlsafe(8)
        self.frozen = True

    def deal(self, card):
        self.card_history.append(card)
        if self.stopped:
            return
        if card in self.cards.intersection(norm_cards):
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
        self.frozen = False

        self.cards = set()
        self.card_history = []

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
            return (
                self.get_total_value() + 15
            )  # 15 is based on the simulation and how much the second chance card is worth per round
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

    def decide_hit(self, game: Game):
        pass

    def check_leader(self, game: Game):
        myscore = game.player_scores[self]['score']
        leader = max([x['score'] for x in game.player_scores.values()])

        return myscore - leader


def make_deck(use_freeze=True):
    cards = [
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
        *['second_chance'] * 3,
        *['draw_3'] * 3,
    ]
    if use_freeze:
        cards += ['freeze'] * 3
    return cards


class Deck:
    cards = None

    def __init__(self, use_freeze=True):
        self.use_freeze = use_freeze
        self.shuffle()

    def shuffle(self):
        """Shuffle deck"""
        # print('Shuffling')
        self.cards = make_deck(self.use_freeze)
        random.shuffle(self.cards)

    def deal(self, player: BasePlayer, game: Game, card=None):
        if not self.cards:
            #  print('shuffle')
            self.shuffle()
        if player.busted or player.stopped:
            return
        if not card:
            card = self.cards.pop()
        else:
            self.cards.remove(card)
        if card == 'freeze':
            player.card_history.append('freeze')
            frozen_player = game.decide_freeze(player)
            frozen_player.stopped = True
            frozen_player.frozen = True
        #   print(f'{player} has frozen {frozen_player} in round {game.round_num}')

        else:
            player.deal(card)
        if not self.cards:
            self.shuffle()

    def compute_card_probs(self):
        c = Counter(self.cards)
        total = sum(c.values())
        return {key: val / total for key, val in c.items()}


class Game:
    def __init__(self, player_list: list[BasePlayer], use_freeze=True):
        self.player_list = deque(player_list)
        self.round_data = []
        self.scoreboard = {str(x): 0 for x in player_list}
        self.use_freeze = use_freeze

    def prep_game(self):
        self.player_scores = {player: defaultdict(int) for player in self.player_list}
        self.deck = Deck(self.use_freeze)
        self.round_num = 1
        self.round_data = []

    def decide_freeze(self, player: BasePlayer):
        """decide who to freeze, need player so don't freeze self?"""

        second_chance = sorted(
            [
                p
                for p in self.player_list
                if 'second_chance' in p.cards and p != player and not p.stopped
            ],
            key=lambda p: p.get_total_value(),
        )
        if second_chance:
            #    print(f'second chance found for {second_chance[-1]}')
            return second_chance[-1]
        else:
            top_players = sorted(
                [
                    player_tuple
                    for player_tuple in self.player_scores.items()
                    if not player_tuple[0].stopped and (player_tuple[0] != player)
                ],
                key=lambda x: x[1]['score'] + x[0].get_total_value(),
            )
            if top_players:
                #      print(f'top player is {top_players[-1][0]}')
                return top_players[-1][0]

        #    print('must self freeze')
        return player

    def play_round(self):
        # print(f' New round {self.round_num} & late game {self.check_late_game()}')
        while not all(p.stopped for p in self.player_scores.keys()):
            if any(p.flip7 for p in self.player_scores.keys()):
                break
            for player in self.player_list:
                if player.stopped:
                    continue
                if player.decide_hit(self):
                    # print(f'Dealing to {player}')
                    self.deck.deal(player, self)

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
                'stopped': player.stopped,
                'frozen': player.frozen,
                'round': self.round_num,
                'flip7': player.flip7,
                'hand_size': len(player.cards),
                'hand': ','.join(player.cards),
                'card_history': ','.join(player.card_history),
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
            #   print(f'First player to play is {self.player_list[0]}')

            self.round_data.extend(self.play_round())
            self.player_list.rotate()
            if i > 50:
                break

        scores = {str(player): data['score'] for player, data in self.player_scores.items()}

        #  print('GAME FINISHED:', scores)
        i = 0
        while True:
            i += 1
            scores = [d['score'] for d in self.player_scores.values()]
            max_score = max(scores)

            if scores.count(max_score) == 1:
                break
            #   print('TIE BREAK', scores)

            # break ties
            if i > 20:
                print(scores)
                assert False, "Can't Break Tie"

            self.round_data.extend(self.play_round())
            self.player_list.rotate()
        #  print(f'First player to play is {self.player_list[0]}')

    def check_late_game(self, threshold=150):
        if max([x['score'] for x in self.player_scores.values()]) > threshold:
            return True
        return False

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
