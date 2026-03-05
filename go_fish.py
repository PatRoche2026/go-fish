#!/usr/bin/env python3
"""
Go Fish — Command-Line Card Game
Play Go Fish against a computer opponent.
Built for MIT Sloan 15.573 (GenAI for Managers)
"""

import random
import sys
import time
from collections import Counter

# Fix Windows terminal encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# CONSTANTS
# ============================================================

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♦", "♣"]
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

RANK_NAMES = {
    "2": "2s", "3": "3s", "4": "4s", "5": "5s", "6": "6s",
    "7": "7s", "8": "8s", "9": "9s", "10": "10s",
    "J": "Jacks", "Q": "Queens", "K": "Kings", "A": "Aces",
}

HAND_SIZE = 7  # Cards dealt to each player (standard for 2 players)


# ============================================================
# CARD & DECK
# ============================================================

class Card:
    __slots__ = ("rank", "suit")

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        color = RED if self.suit in ("♥", "♦") else ""
        reset = RESET if color else ""
        return f"[{color}{self.rank}{self.suit}{reset}]"

    def __eq__(self, other):
        return isinstance(other, Card) and self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))


class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for r in RANKS for s in SUITS]
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

    def __len__(self):
        return len(self.cards)


# ============================================================
# PLAYER
# ============================================================

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.books = []

    def add_cards(self, cards):
        if isinstance(cards, Card):
            cards = [cards]
        self.hand.extend(cards)
        self._check_books()

    def remove_rank(self, rank):
        """Remove and return all cards of a given rank from hand."""
        matched = [c for c in self.hand if c.rank == rank]
        self.hand = [c for c in self.hand if c.rank != rank]
        return matched

    def has_rank(self, rank):
        return any(c.rank == rank for c in self.hand)

    def ranks_in_hand(self):
        return sorted(set(c.rank for c in self.hand), key=lambda r: RANKS.index(r))

    def rank_counts(self):
        return Counter(c.rank for c in self.hand)

    def _check_books(self):
        """Check for and remove completed books (4 of a kind)."""
        counts = self.rank_counts()
        for rank, count in counts.items():
            if count == 4:
                self.hand = [c for c in self.hand if c.rank != rank]
                self.books.append(rank)
                return rank  # Return the completed book rank
        return None

    def sort_hand(self):
        self.hand.sort(key=lambda c: (RANKS.index(c.rank), SUITS.index(c.suit)))

    def show_hand(self):
        self.sort_hand()
        cards_str = "  ".join(repr(c) for c in self.hand)
        return cards_str if self.hand else f"{DIM}(empty){RESET}"


# ============================================================
# COMPUTER AI
# ============================================================

class ComputerPlayer(Player):
    def __init__(self):
        super().__init__("Computer")
        self.memory = {}  # rank -> last_asked_turn (tracks what human asked for)
        self.denied = set()  # ranks denied on last ask

    def remember_human_asked(self, rank, turn):
        """Remember that the human asked for this rank (human likely still has it)."""
        self.memory[rank] = turn

    def forget_rank(self, rank):
        """Forget a rank (e.g., human completed a book or we got the cards)."""
        self.memory.pop(rank, None)
        self.denied.discard(rank)

    def choose_rank(self, turn):
        """Pick a rank to ask for. Strategy:
        1. Ask for ranks where we have 3 (close to a book)
        2. Ask for ranks the human recently asked for (we know they have them)
        3. Random from hand
        """
        if not self.hand:
            return None

        counts = self.rank_counts()
        available = self.ranks_in_hand()

        # Priority 1: Almost-complete books
        for rank in available:
            if counts[rank] == 3:
                return rank

        # Priority 2: Ranks we know the human has (from their asks)
        known_ranks = [r for r in available if r in self.memory and r not in self.denied]
        if known_ranks:
            # Pick the one they asked for most recently
            return max(known_ranks, key=lambda r: self.memory[r])

        # Priority 3: Ranks with 2 cards
        for rank in available:
            if counts[rank] == 2:
                return rank

        # Fallback: random
        self.denied.clear()  # Reset denied when falling back
        return random.choice(available)


# ============================================================
# GAME
# ============================================================

class GoFishGame:
    def __init__(self):
        self.deck = Deck()
        self.human = Player("You")
        self.computer = ComputerPlayer()
        self.turn_count = 0
        self.game_log = []

    # ---- Setup ----

    def deal(self):
        for _ in range(HAND_SIZE):
            self.human.add_cards(self.deck.draw())
            self.computer.add_cards(self.deck.draw())

    # ---- Display ----

    def print_header(self):
        print(f"\n{'='*50}")
        print(f"{CYAN}{BOLD}  🐟  G O   F I S H  🐟{RESET}")
        print(f"{'='*50}")

    def print_status(self):
        print(f"\n{DIM}{'─'*50}{RESET}")
        print(f"  {CYAN}Deck:{RESET} {len(self.deck)} cards remaining")
        print(f"  {GREEN}Your books ({len(self.human.books)}):{RESET} ", end="")
        if self.human.books:
            print("  ".join(f"[{RANK_NAMES[r]}]" for r in self.human.books))
        else:
            print(f"{DIM}none yet{RESET}")
        print(f"  {RED}Computer books ({len(self.computer.books)}):{RESET} ", end="")
        if self.computer.books:
            print("  ".join(f"[{RANK_NAMES[r]}]" for r in self.computer.books))
        else:
            print(f"{DIM}none yet{RESET}")
        print(f"  {DIM}Computer hand: {len(self.computer.hand)} cards{RESET}")
        print(f"{DIM}{'─'*50}{RESET}")

    def print_hand(self):
        print(f"\n  {BOLD}Your hand:{RESET}  {self.human.show_hand()}")
        ranks = self.human.ranks_in_hand()
        print(f"  {DIM}Ranks: {', '.join(ranks)}{RESET}")

    # ---- Draw logic ----

    def draw_if_empty(self, player):
        """If a player's hand is empty and deck has cards, draw one."""
        if not player.hand and self.deck:
            card = self.deck.draw()
            if card:
                player.add_cards(card)
                if player == self.human:
                    print(f"  {DIM}Hand was empty — drew {repr(card)}{RESET}")
                else:
                    print(f"  {DIM}Computer's hand was empty — drew a card{RESET}")
                return True
        return False

    # ---- Human turn ----

    def human_turn(self):
        self.draw_if_empty(self.human)
        if not self.human.hand:
            return False  # Can't play

        while True:
            self.print_hand()
            valid_ranks = self.human.ranks_in_hand()

            print(f"\n  {BOLD}Ask the computer for a rank:{RESET} ", end="")
            choice = input().strip().upper()

            # Normalize input
            if choice == "ACE" or choice == "ACES":
                choice = "A"
            elif choice == "JACK" or choice == "JACKS":
                choice = "J"
            elif choice == "QUEEN" or choice == "QUEENS":
                choice = "Q"
            elif choice == "KING" or choice == "KINGS":
                choice = "K"

            if choice not in RANKS:
                print(f"  {RED}Invalid rank. Enter one of: {', '.join(valid_ranks)}{RESET}")
                continue
            if choice not in valid_ranks:
                print(f"  {RED}You don't have any {RANK_NAMES[choice]}! Pick a rank from your hand.{RESET}")
                continue

            # Valid ask
            self.turn_count += 1
            self.computer.remember_human_asked(choice, self.turn_count)
            print(f"\n  {BOLD}You:{RESET} \"Got any {RANK_NAMES[choice]}?\"")
            time.sleep(0.5)

            if self.computer.has_rank(choice):
                taken = self.computer.remove_rank(choice)
                self.computer.forget_rank(choice)
                print(f"  {GREEN}Computer hands over {len(taken)} card(s): {' '.join(repr(c) for c in taken)}{RESET}")
                self.human.add_cards(taken)
                self._announce_books(self.human)

                # Go again if got cards and still have a hand
                if self.human.hand and not self._is_game_over():
                    print(f"\n  {CYAN}You got what you asked for — go again!{RESET}")
                    self.draw_if_empty(self.human)
                    continue
                return True
            else:
                print(f"  {YELLOW}Computer: \"Go Fish!\" 🐟{RESET}")
                time.sleep(0.3)
                drawn = self.deck.draw()
                if drawn:
                    print(f"  You drew: {repr(drawn)}")
                    self.human.add_cards(drawn)
                    self._announce_books(self.human)
                    if drawn.rank == choice and self.human.hand and not self._is_game_over():
                        print(f"  {CYAN}You drew what you asked for — go again!{RESET}")
                        self.draw_if_empty(self.human)
                        continue
                else:
                    print(f"  {DIM}Deck is empty — nothing to draw.{RESET}")
                return True

    # ---- Computer turn ----

    def computer_turn(self):
        self.draw_if_empty(self.computer)
        if not self.computer.hand:
            return False  # Can't play

        while True:
            rank = self.computer.choose_rank(self.turn_count)
            if not rank:
                return False

            time.sleep(0.8)
            print(f"\n  {BOLD}Computer:{RESET} \"Got any {RANK_NAMES[rank]}?\"")
            time.sleep(0.4)

            if self.human.has_rank(rank):
                taken = self.human.remove_rank(rank)
                print(f"  {RED}You hand over {len(taken)} card(s): {' '.join(repr(c) for c in taken)}{RESET}")
                self.computer.add_cards(taken)
                self.computer.forget_rank(rank)
                self.computer.denied.discard(rank)
                self._announce_books(self.computer)

                if self.computer.hand and not self._is_game_over():
                    print(f"  {CYAN}Computer got what it asked for — goes again!{RESET}")
                    self.draw_if_empty(self.computer)
                    continue
                return True
            else:
                print(f"  {GREEN}You: \"Go Fish!\" 🐟{RESET}")
                self.computer.denied.add(rank)
                drawn = self.deck.draw()
                if drawn:
                    print(f"  {DIM}Computer draws a card.{RESET}")
                    go_again = drawn.rank == rank
                    self.computer.add_cards(drawn)
                    self._announce_books(self.computer)
                    if go_again and self.computer.hand and not self._is_game_over():
                        print(f"  {CYAN}Computer drew what it asked for — goes again!{RESET}")
                        self.computer.denied.discard(rank)
                        self.draw_if_empty(self.computer)
                        continue
                else:
                    print(f"  {DIM}Deck is empty — nothing to draw.{RESET}")
                return True

    # ---- Book announcements ----

    def _announce_books(self, player):
        """Check and announce any new books."""
        # Books are auto-collected in Player._check_books via add_cards
        # We need to detect new ones by checking if books changed
        # Actually _check_books is called in add_cards, so just check last book
        pass  # Books are announced inline when _check_books triggers

    def _check_and_announce(self, player):
        """Explicitly check for books and announce."""
        counts = player.rank_counts()
        for rank, count in counts.items():
            if count == 4:
                player.hand = [c for c in player.hand if c.rank != rank]
                player.books.append(rank)
                name = "You" if player == self.human else "Computer"
                color = GREEN if player == self.human else RED
                print(f"\n  {color}{BOLD}📚 {name} completed a book of {RANK_NAMES[rank]}!{RESET}")

    # ---- Game state ----

    def _is_game_over(self):
        if len(self.human.books) + len(self.computer.books) >= 13:
            return True
        if not self.human.hand and not self.computer.hand and not self.deck:
            return True
        return False

    # ---- Main loop ----

    def play(self):
        self.print_header()
        print(f"\n  {DIM}Shuffling and dealing {HAND_SIZE} cards each...{RESET}")
        self.deal()
        time.sleep(0.5)

        # Monkey-patch _check_books to announce
        original_human_check = self.human._check_books
        original_computer_check = self.computer._check_books

        def human_check_books():
            result = Player._check_books(self.human)
            if result:
                print(f"\n  {GREEN}{BOLD}📚 You completed a book of {RANK_NAMES[result]}!{RESET}")
            return result

        def computer_check_books():
            result = Player._check_books(self.computer)
            if result:
                print(f"\n  {RED}{BOLD}📚 Computer completed a book of {RANK_NAMES[result]}!{RESET}")
            return result

        self.human._check_books = human_check_books
        self.computer._check_books = computer_check_books

        human_goes_first = random.choice([True, False])
        if human_goes_first:
            print(f"  {CYAN}You go first!{RESET}")
        else:
            print(f"  {CYAN}Computer goes first!{RESET}")

        current_is_human = human_goes_first

        while not self._is_game_over():
            self.print_status()

            if current_is_human:
                print(f"\n  {GREEN}{BOLD}── YOUR TURN ──{RESET}")
                self.human_turn()
            else:
                print(f"\n  {RED}{BOLD}── COMPUTER'S TURN ──{RESET}")
                self.computer_turn()

            current_is_human = not current_is_human

        # ---- Game over ----
        self._end_game()

    def _end_game(self):
        print(f"\n{'='*50}")
        print(f"{BOLD}{CYAN}  🏆  GAME OVER  🏆{RESET}")
        print(f"{'='*50}")
        print(f"\n  {GREEN}Your books ({len(self.human.books)}):{RESET} ", end="")
        print("  ".join(f"[{RANK_NAMES[r]}]" for r in self.human.books) if self.human.books else "none")
        print(f"  {RED}Computer books ({len(self.computer.books)}):{RESET} ", end="")
        print("  ".join(f"[{RANK_NAMES[r]}]" for r in self.computer.books) if self.computer.books else "none")

        h, c = len(self.human.books), len(self.computer.books)
        print()
        if h > c:
            print(f"  {GREEN}{BOLD}🎉 YOU WIN! {h} to {c} 🎉{RESET}")
        elif c > h:
            print(f"  {RED}{BOLD}Computer wins. {c} to {h}.{RESET}")
        else:
            print(f"  {YELLOW}{BOLD}It's a tie! {h} to {c}.{RESET}")
        print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        game = GoFishGame()
        game.play()
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Thanks for playing! 🐟{RESET}\n")
    except EOFError:
        print(f"\n\n  {DIM}Game ended.{RESET}\n")
