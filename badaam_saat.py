from collections import defaultdict
import pytest
import gtts
from playsound import playsound


SUITE_CODES = {"s": "Spade", "h": "Heart", "c": "Club", "d": "Diamond"}


class BadaamSaat:
    def __init__(self, game_state, hand) -> None:
        self.hand = hand
        self.game_state = game_state

    def get_playable_cards(self):
        playable_cards = defaultdict(list)
        self.append_all_seven(playable_cards)

        for suite, (lo, hi) in self.game_state.items():
            if suite not in self.hand:
                continue
            for card in self.hand[suite]:
                if card == lo - 1 or card == hi + 1:
                    playable_cards[suite].append(card)

        return playable_cards

    def get_uncertain_count_in_suite(self, suite):
        lo_game, hi_game = self.game_state[suite] if suite in self.game_state else [7, 7]
        lo_hand, hi_hand = min(self.hand[suite]), max(self.hand[suite])
        return [
            self.get_uncertain_cards_lower(lo_hand, lo_game, suite),
            self.get_uncertain_cards_upper(hi_game, hi_hand, suite),
        ]

    def get_uncertain_cards_lower(self, lo_hand, lo_game, suite):
        uncertain_count = 0
        for card in range(lo_hand, lo_game):
            if not self.hand_contains(card, suite):
                uncertain_count += 1
        return uncertain_count

    def get_uncertain_cards_upper(self, hi_game, hi_hand, suite):
        uncertain_count = 0
        for card in range(hi_game + 1, hi_hand + 1):
            if not self.hand_contains(card, suite):
                uncertain_count += 1
        return uncertain_count

    def get_uncertain_counts(self):
        uncertain_count = {}
        for suite in self.hand:
            uncertain_count[suite] = self.get_uncertain_count_in_suite(suite)
        return uncertain_count

        # [S : 3, 2] count all uncertain cards not just max
        # [C : 4, 1]

    def draw_random_playable_card(self):
        for suite, cards in self.get_playable_cards().items():
            return cards[0], SUITE_CODES[suite]

    def pick_optimal_card(self):
        if len(self.get_playable_cards()) == 0:
            return "pass"

        uncertain_counts = self.get_uncertain_counts()

        optimal_card, max_uncertainity = self.pick_maximally_uncertain_card(uncertain_counts, self.get_playable_cards())
        if max_uncertainity == 0:
            print(f"{self.count_cards_in_hand()} page caution. definite")
            return self.draw_random_playable_card()

        print(f"{self.count_cards_in_hand()} page caution. Not definite")
        return optimal_card[0], SUITE_CODES[optimal_card[1]]

    def speak_card(self):
        result = self.pick_optimal_card()
        if result == "pass":
            tts = gtts.gTTS(f"Pass. No cards to play. Dhanyavadagalyu")
        else:
            card, suite = result
            tts = gtts.gTTS(f"I will play {card} of {suite}. Thank you")

        tts.save("py_speech.mp3")
        playsound("py_speech.mp3")

    def pick_maximally_uncertain_card(self, uncertain_counts, sorted_playable_cards):
        max_uncertainity = 0
        optimal_card = [None, None]

        for suite, cards in sorted_playable_cards.items():
            for card in cards:
                if card < 7:
                    uncertainty = uncertain_counts[suite][0]
                elif card > 7:
                    uncertainty = uncertain_counts[suite][1]
                elif card == 7:
                    uncertainty = 0

                if uncertainty > max_uncertainity:
                    max_uncertainity = uncertainty
                    optimal_card = [card, suite]

        return optimal_card, max_uncertainity

    def no_uncertain_cards(self, uncertain_counts):
        for suite in uncertain_counts:
            if max(uncertain_counts[suite]) != 0:
                return False
        return True

    def hand_contains(self, card, suite):
        return card in self.hand[suite]

    def append_all_seven(self, playable_cards):
        for suite, cards in self.hand.items():
            for card in cards:
                if card == 7:
                    playable_cards[suite].append(card)

    def sort_cards(self, hand):
        return {suite: sorted(cards) for suite, cards in hand}

    def count_cards_in_hand(self):
        count = 0
        for suite, cards in self.hand.items():
            count += len(cards)

        return count


game_state = {
    "h": [1, 11],
    "s": [1, 13],
    "c": [3, 12],
    "d": [3, 7],
}

hand = {
    "s": [5],
    "h": [1, 2, 4, 6],
    "c": [13],
    "d": [1, 2, 9, 13],
}


bs = BadaamSaat(game_state, hand)
print(bs.speak_card())


def test_should_play_7_if_no_other_card_there():
    game_state = {
        "s": [6, 8],
        "h": [3, 9],
        "c": [3, 10],
    }

    hand = {"d": [7]}

    bs = BadaamSaat(game_state, hand)
    assert bs.pick_optimal_card() == (7, "Diamond")


def test_should_pass_if_no_avaialabe_card():
    game_state = {
        "s": [6, 8],
        "h": [3, 9],
        "c": [3, 10],
    }

    hand = {
        "d": [3, 4, 5],
        "s": [3, 10],
    }

    bs = BadaamSaat(game_state, hand)
    assert bs.pick_optimal_card() == "pass"


def test__should_pick_suite_with_not_definate_cards():
    game_state = {
        "s": [7, 8],
        "h": [3, 9],
        "c": [3, 10],
    }

    hand = {
        "s": [6, 5, 4, 3, 2, 1],
        "h": [10, 13],
    }

    bs = BadaamSaat(game_state, hand)
    assert bs.pick_optimal_card() == (10, "Heart")


def should_not_forget_to_play_7_if_present():
    game_state = {
        "s": [7, 8],
        "h": [3, 9],
        "c": [3, 10],
    }

    hand = {
        "d": [7],
        "h": [11, 13],
    }

    bs = BadaamSaat(game_state, hand)
    assert bs.pick_optimal_card() == (7, "Heart")
