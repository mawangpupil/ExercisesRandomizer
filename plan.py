"""
plan.py — Генератор плана тренировок
Запускать из папки, в которой находится папка "Exercises".
Создаёт файл workout_plan.html рядом с plan.py.
"""

import os
import re
import random
import json

FOLDER = "Exercises"
OUTPUT = "workout_plan.html"


# ──────────────────────────────────────────────
# Парсинг exercises.txt
# ──────────────────────────────────────────────

def parse_exercises_file():
    path = os.path.join(FOLDER, "exercises.txt")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Делим на блок упражнений и блок приростов
    split_marker = "Увеличения через каждый выходной:"
    if split_marker not in content:
        raise ValueError("Не найден маркер 'Увеличения через каждый выходной:' в exercises.txt")

    ex_part, inc_part = content.split(split_marker, 1)

    # ── Упражнения ──
    # Формат строки: "1. Название MIN-MAX единица"
    exercises = {}
    for line in ex_part.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(\d+)\.\s+(.+?)\s+(\d+)-(\d+)\s+(.+)$', line)
        if m:
            idx      = int(m.group(1))
            name     = m.group(2).strip()
            min_val  = int(m.group(3))
            max_val  = int(m.group(4))
            unit     = m.group(5).strip()
            exercises[idx] = {
                "name": name,
                "min":  min_val,
                "max":  max_val,
                "unit": unit,
            }

    # ── Приросты ──
    # Формат строки: "1. +4 секунды"
    increments = {}
    for line in inc_part.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(\d+)\.\s+\+(\d+)', line)
        if m:
            idx = int(m.group(1))
            d   = int(m.group(2))
            increments[idx] = d

    if len(exercises) != 15:
        raise ValueError(f"Ожидалось 15 упражнений, найдено {len(exercises)}")
    if len(increments) != 15:
        raise ValueError(f"Ожидалось 15 приростов, найдено {len(increments)}")

    return exercises, increments


# ──────────────────────────────────────────────
# Чтение текущей недели
# ──────────────────────────────────────────────

def read_week():
    path = os.path.join(FOLDER, "week.txt")
    with open(path, encoding="utf-8") as f:
        return int(f.read().strip())


# ──────────────────────────────────────────────
# Подсчёт текущего числа повторений / секунд
# ──────────────────────────────────────────────

def calc_n(ex: dict, d: int, week: int) -> int:
    return min(ex["min"] + d * week, ex["max"])


# ──────────────────────────────────────────────
# Сканирование папки
# ──────────────────────────────────────────────

def get_images() -> list[str]:
    return sorted(
        [f for f in os.listdir(FOLDER) if re.match(r'^\d+\.png$', f, re.IGNORECASE)],
        key=lambda x: int(re.match(r'^(\d+)', x).group(1))
    )

def get_mp3s() -> list[str]:
    return sorted(
        [f for f in os.listdir(FOLDER) if f.lower().endswith(".mp3")]
    )


# ──────────────────────────────────────────────
# Генерация тренировок
# 5 секций × 3 упражнения → 3 тренировки × 5 упражнений
# ──────────────────────────────────────────────

SECTIONS = [
    [1,  2,  3 ],   # Кардио-разминка
    [4,  5,  6 ],   # Жим / кор
    [7,  8,  9 ],   # Пресс
    [10, 11, 12],   # Спина / ягодицы
    [13, 14, 15],   # Планка / шея
]

def generate_workouts() -> list[list[int]]:
    """
    Возвращает список из 3 тренировок.
    Каждая тренировка — список из 5 индексов упражнений (по одному из секции).
    Упражнения не повторяются между тренировками.
    """
    workouts = [[], [], []]
    for section in SECTIONS:
        order = section.copy()
        random.shuffle(order)
        for i in range(3):
            workouts[i].append(order[i])
    return workouts


# ──────────────────────────────────────────────
# HTML-генерация
# ──────────────────────────────────────────────

def build_html(exercises: dict, increments: dict, week: int) -> str:
    images  = get_images()
    mp3s    = get_mp3s()
    workouts = generate_workouts()

    # Рассчитать N для каждого упражнения
    computed = {}
    for idx, ex in exercises.items():
        computed[idx] = {
            "name": ex["name"],
            "unit": ex["unit"],
            "n":    calc_n(ex, increments[idx], week),
        }

    # ── HTML-карточки тренировок ──
    workout_cards_html = ""
    workout_names = ["Тренировка А", "Тренировка Б", "Тренировка В"]
    workout_icons = ["🔥", "⚡", "💪"]

    for wi, (wname, wicon, ex_ids) in enumerate(zip(workout_names, workout_icons, workouts)):
        rows = ""
        for ex_idx in ex_ids:
            ex = computed[ex_idx]
            rows += f"""
              <tr>
                <td class="td-num">{ex_idx}</td>
                <td class="td-name">{ex['name']}</td>
                <td class="td-reps"><span class="rep-n">{ex['n']}</span><span class="unit">{ex['unit']}</span></td>
              </tr>"""
        workout_cards_html += f"""
        <div class="card workout-card" data-workout="{wi}">
          <div class="card-header">
            <span class="card-icon">{wicon}</span>
            <span class="card-title">{wname}</span>
          </div>
          <table class="ex-table">
            <thead>
              <tr>
                <th class="th-num">#</th>
                <th class="th-name">Упражнение</th>
                <th class="th-reps">Объём</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    images_json = json.dumps(images)
    mp3s_json   = json.dumps(mp3s)
    folder      = FOLDER

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Тренировочный план · Неделя {week}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Nunito:wght@400;600;700;900&display=swap');

:root {{
  --bg:        #0d0d0f;
  --surface:   #18181c;
  --border:    #2a2a32;
  --accent:    #ff4d4d;
  --accent2:   #ffb347;
  --teal:      #3ff0c0;
  --text:      #e8e8ec;
  --muted:     #7a7a8a;
  --radius:    14px;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'Nunito', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
}}

/* ── Noise grain overlay ── */
body::before {{
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 1000;
  opacity: 0.35;
}}

/* ── Layout ── */
.container {{
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 20px 60px;
}}

/* ── Header ── */
.site-header {{
  text-align: center;
  margin-bottom: 36px;
  position: relative;
}}
.site-header h1 {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2.8rem, 8vw, 5rem);
  letter-spacing: 0.05em;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}}
.week-label {{
  display: inline-block;
  margin-top: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px 14px;
}}

/* ── Hero image ── */
.hero-wrap {{
  text-align: center;
  margin-bottom: 36px;
}}
.hero-img {{
  max-height: 320px;
  max-width: min(700px, 100%);
  width: auto;
  border-radius: var(--radius);
  box-shadow: 0 0 0 1px var(--border), 0 20px 60px rgba(255, 77, 77, 0.25);
  display: none;           /* shown by JS once src is set */
  margin: 0 auto;
  object-fit: cover;
  transition: opacity 0.4s;
}}

/* ── Player ── */
.player-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  max-width: 680px;
  margin: 0 auto 44px;
}}
.player-card .section-title {{
  margin-bottom: 14px;
}}
.now-playing {{
  font-size: 0.78rem;
  color: var(--muted);
  margin-bottom: 10px;
  min-height: 1em;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}}
.now-playing span {{ color: var(--teal); }}
audio {{
  width: 100%;
  height: 36px;
  margin-bottom: 14px;
  accent-color: var(--accent);
  border-radius: 8px;
}}
.playlist {{
  list-style: none;
  max-height: 150px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}}
.playlist li {{
  padding: 7px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.88rem;
  color: var(--muted);
  font-weight: 600;
  transition: background 0.15s, color 0.15s;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.playlist li::before {{ content: '♪'; font-size: 0.7em; opacity: 0.5; }}
.playlist li:hover {{ background: var(--border); color: var(--text); }}
.playlist li.active {{ background: rgba(255,77,77,0.15); color: var(--accent); }}
.playlist li.active::before {{ opacity: 1; }}
.no-music {{ color: var(--muted); font-size: 0.88rem; }}

/* ── Section title ── */
.section-title {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.5rem;
  letter-spacing: 0.1em;
  color: var(--accent2);
  margin-bottom: 20px;
}}
.section-title small {{
  font-family: 'Nunito', sans-serif;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  display: block;
  margin-top: 2px;
}}

/* ── Workouts grid ── */
.workouts-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 20px;
}}

/* ── Card ── */
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.card:hover {{
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}}

.card-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(90deg, rgba(255,77,77,0.08) 0%, transparent 100%);
}}
.card-icon {{ font-size: 1.3rem; }}
.card-title {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.25rem;
  letter-spacing: 0.08em;
  color: var(--text);
}}

.ex-table {{
  width: 100%;
  border-collapse: collapse;
}}
.ex-table thead tr {{
  background: rgba(255,255,255,0.03);
}}
.ex-table th {{
  padding: 8px 12px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  text-align: left;
  border-bottom: 1px solid var(--border);
}}
.ex-table td {{
  padding: 10px 12px;
  font-size: 0.88rem;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  vertical-align: middle;
}}
.ex-table tbody tr:last-child td {{ border-bottom: none; }}
.ex-table tbody tr:hover td {{ background: rgba(255,255,255,0.025); }}

.th-num, .td-num {{
  width: 30px;
  color: var(--muted);
  font-size: 0.78rem;
}}
.td-reps {{
  color: var(--teal);
  font-weight: 700;
  white-space: normal;
  width: 68px;
  min-width: 68px;
  max-width: 68px;
  padding-right: 12px;
  text-align: center;
  vertical-align: middle;
  line-height: 1.2;
}}
.rep-n {{
  display: block;
  font-size: 1rem;
  color: var(--teal);
  font-weight: 800;
}}
.unit {{
  display: block;
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--muted);
  white-space: normal;
  word-break: break-word;
}}

/* ── Stagger animation ── */
@keyframes fadeUp {{
  from {{ opacity: 0; transform: translateY(18px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
.workout-card {{
  animation: fadeUp 0.45s ease both;
}}
.workout-card[data-workout="0"] {{ animation-delay: 0.05s; }}
.workout-card[data-workout="1"] {{ animation-delay: 0.15s; }}
.workout-card[data-workout="2"] {{ animation-delay: 0.25s; }}
</style>
</head>
<body>
<div class="container">

  <!-- ── Header ── -->
  <header class="site-header">
    <div class="week-label">Неделя {week}</div>
  </header>

  <!-- ── Hero image ── -->
  <div class="hero-wrap">
    <img id="hero" class="hero-img" alt="">
  </div>

  <!-- ── Music player ── -->
  <div class="player-card">
    <audio id="audio-player" controls></audio>
    <ul class="playlist" id="playlist"></ul>
  </div>

  <!-- ── Workouts ── -->
  <div class="section-title">
    Тренировки
  </div>
  <div class="workouts-grid">
    {workout_cards_html}
  </div>

</div><!-- /container -->

<script>
const FOLDER  = "{folder}";
const images  = {images_json};
const mp3s    = {mp3s_json};

// ── Random hero image ──
const heroEl = document.getElementById('hero');
if (images.length > 0) {{
  const pick = images[Math.floor(Math.random() * images.length)];
  heroEl.src = FOLDER + '/' + pick;
  heroEl.onload = () => {{ heroEl.style.display = 'block'; }};
}}

// ── Audio player ──
const audio    = document.getElementById('audio-player');
const plUl     = document.getElementById('playlist');
let   current  = 0;

function playTrack(i) {{
  current  = i;
  audio.src = FOLDER + '/' + mp3s[i];
  audio.play();
  document.querySelectorAll('.playlist li').forEach((el, j) => {{
    el.classList.toggle('active', j === i);
  }});
}}

if (mp3s.length > 0) {{
  mp3s.forEach((track, i) => {{
    const li  = document.createElement('li');
    li.textContent = track.replace(/\\.mp3$/i, '');
    li.onclick = () => playTrack(i);
    plUl.appendChild(li);
  }});
  // Auto-start a random track
  playTrack(Math.floor(Math.random() * mp3s.length));

  audio.addEventListener('ended', () => {{
    playTrack((current + 1) % mp3s.length);
  }});
}} else {{
  plUl.innerHTML = '<li class="no-music">MP3-файлы не найдены в папке Exercises</li>';
}}
</script>
</body>
</html>"""

    return html


# ──────────────────────────────────────────────
# Точка входа
# ──────────────────────────────────────────────

def main():
    if not os.path.isdir(FOLDER):
        print(f"[ОШИБКА] Папка '{FOLDER}' не найдена. "
              f"Запустите plan.py из папки, в которой находится '{FOLDER}'.")
        return

    print("Читаю exercises.txt …")
    exercises, increments = parse_exercises_file()

    print("Читаю week.txt …")
    week = read_week()
    print(f"  Текущая неделя: {week}")

    print("Формирую тренировки …")
    html = build_html(exercises, increments, week)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ Готово! Открой файл: {OUTPUT}")
    print("   (Просто дважды кликни на workout_plan.html)")


if __name__ == "__main__":
    main()
