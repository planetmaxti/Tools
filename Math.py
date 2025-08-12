#!/usr/bin/env python3
"""
Math Sprint — a speed-based mental math game.

- Pick a difficulty
- You have N seconds to answer as many as you can
- Points scale with speed + streaks
- High score is saved locally

Run: python math_sprint.py
"""

from __future__ import annotations
import json
import math
import os
import random
import time
from dataclasses import dataclass
from typing import Tuple, Callable, List

HIGHSCORE_FILE = os.path.join(os.path.expanduser("~"), ".math_sprint_highscore.json")

@dataclass
class Difficulty:
    name: str
    n_min: int
    n_max: int
    ops: Tuple[str, ...]
    round_seconds: int

DIFFICULTIES = [
    Difficulty("Easy",    0,   10, ("+", "-"),                60),
    Difficulty("Normal",  1,   20, ("+", "-", "*"),           75),
    Difficulty("Hard",    2,   50, ("+", "-", "*", "÷"),      90),
    Difficulty("Insane",  5,  120, ("+", "-", "*", "÷", "+"), 120),
]

def load_highscore() -> dict:
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}

def save_highscore(best: dict) -> None:
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(best, f, indent=2)
    except Exception:
        pass

def pick_difficulty() -> Difficulty:
    print("Choose difficulty:")
    for i, d in enumerate(DIFFICULTIES, 1):
        print(f"  {i}. {d.name}  (range {d.n_min}..{d.n_max}, ops {', '.join(d.ops)}, {d.round_seconds}s)")
    while True:
        choice = input("Enter 1-4: ").strip()
        if choice in {"1","2","3","4"}:
            return DIFFICULTIES[int(choice)-1]
        print("Invalid choice.")

def make_problem(d: Difficulty) -> Tuple[str, int]:
    op = random.choice(d.ops)
    a = random.randint(d.n_min, d.n_max)
    b = random.randint(d.n_min, d.n_max)

    if op == "+":
        return f"{a} + {b}", a + b
    if op == "-":
        # bias to non-negative results
        a, b = max(a, b), min(a, b)
        return f"{a} - {b}", a - b
    if op == "*":
        return f"{a} × {b}", a * b
    if op == "÷":
        # ensure clean division
        b = random.randint(max(1, d.n_min), max(1, d.n_max))
        ans = random.randint(d.n_min, d.n_max)
        a = ans * b
        return f"{a} ÷ {b}", ans
    # fallback (shouldn't happen)
    return f"{a} + {b}", a + b

def points_for(answer_time: float, correct: bool, streak: int) -> int:
    if not correct:
        return 0
    # Base points
    pts = 100
    # Speed bonus: up to +150 if <= 1s; decays to 0 by 5s
    speed_bonus = max(0.0, 150.0 * (1.0 - min(answer_time, 5.0) / 5.0))
    # Streak bonus: +10% per correct in a row (cap 50%)
    streak_bonus_mult = 1.0 + min(0.5, 0.10 * streak)
    total = int(round((pts + speed_bonus) * streak_bonus_mult))
    return total

def fmt_time(s: float) -> str:
    return f"{s:.2f}s"

def game_round(d: Difficulty) -> Tuple[int, int, List[float]]:
    end_time = time.perf_counter() + d.round_seconds
    score = 0
    asked = 0
    streak = 0
    times: List[float] = []
    try:
        while time.perf_counter() < end_time:
            remaining = end_time - time.perf_counter()
            q, ans = make_problem(d)
            print(f"\n[{int(remaining)}s left]  {q} = ?")
            t0 = time.perf_counter()
            user_in = input("> ").strip()
            t1 = time.perf_counter()
            t = t1 - t0
            times.append(t)
            asked += 1

            try:
                user_ans = int(user_in)
                correct = (user_ans == ans)
            except ValueError:
                correct = False

            if correct:
                streak += 1
                gained = points_for(t, True, streak)
                score += gained
                print(f"✓ Correct in {fmt_time(t)}  +{gained} (streak {streak})")
            else:
                print(f"✗ Wrong (answer: {ans})  (+0)")
                streak = 0
    except KeyboardInterrupt:
        print("\n⏹ Interrupted — scoring what you have...")

    return score, asked, times

def round_summary(score: int, asked: int, times: List[float]) -> str:
    if times:
        avg_t = sum(times) / len(times)
        best = min(times)
        worst = max(times)
    else:
        avg_t = best = worst = float("nan")
    return (
        f"\n=== Round Summary ===\n"
        f"Questions answered: {asked}\n"
        f"Score: {score}\n"
        f"Avg time/Q: {fmt_time(avg_t) if not math.isnan(avg_t) else '—'}\n"
        f"Best: {fmt_time(best) if not math.isnan(best) else '—'}   "
        f"Worst: {fmt_time(worst) if not math.isnan(worst) else '—'}\n"
    )

def maybe_update_highscore(diff_name: str, score: int) -> Tuple[bool, int]:
    hs = load_highscore()
    best = int(hs.get(diff_name, 0))
    if score > best:
        hs[diff_name] = score
        save_highscore(hs)
        return True, score
    return False, best

def main():
    print("🧠 Math Sprint — how fast can you think?")
    d = pick_difficulty()
    print(f"\nGo! You have {d.round_seconds} seconds on {d.name}…")
    score, asked, times = game_round(d)
    print(round_summary(score, asked, times))
    improved, ref = maybe_update_highscore(d.name, score)
    if improved:
        print(f"🏆 NEW {d.name} high score: {ref} — nice!")
    else:
        print(f"Best {d.name} high score: {ref}")
    print("\nPlay again? (y/n)")
    if input("> ").strip().lower().startswith("y"):
        print()
        main()
    else:
        print("Thanks for playing!")

if __name__ == "__main__":
    random.seed()
    main()