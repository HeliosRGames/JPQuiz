import random
import os
import tkinter as tk
from tkinter import messagebox
import pygame
import sqlite3
import gc
from colorama import Fore
import threading

os.system('clear')
print("「できる」と信じれば、もう半分成功だよね？")
print("Loading files, please wait...")

file_load_order = ["nouns.txt", "verbs.txt", "adjectives.txt", "adverbs.txt", "misc.txt"]
folder_name = "japanese_words"
folder_path = sorted(os.listdir(folder_name), key=lambda x: file_load_order.index(x) if x in file_load_order else float('inf'))

def load_words():
    word_dict = {}
    for filename in folder_path:
        if filename.endswith(".txt"):
            with open(os.path.join(folder_name, filename), "r", encoding="utf-8") as f:
                words = [line.strip().split(", ") for line in f]
                word_dict[filename] = words
    return word_dict

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JPQuiz")
        self.root.geometry("1920x1080")
        self.root.attributes('-fullscreen', True)
        self.words = load_words()
        self.confetti_pieces = []
        self.GRAVITY = 0.5

        pygame.mixer.init()
        self.SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "audios")
        self.audios = {}
        for filename in os.listdir(self.SOUNDS_DIR):
            if filename.endswith((".mp3", ".wav", ".ogg")):  # Support multiple formats
                sound_name = os.path.splitext(filename)[0]  # Remove file extension
                self.audios[sound_name] = pygame.mixer.Sound(os.path.join(self.SOUNDS_DIR, filename))
        
        self.current_song = {"name": None}
        self.lifepoint_sfx = self.audios["lifepoint"]
        self.correct = self.audios["correct"]
        self.incorrect = self.audios["incorrect"]
        self.cheering = self.audios["cheering"]

        self.songon = tk.BooleanVar(root, value=True)

        self.hs_dict = {
            "quizgame_hs": 0,
            "timed_hs": 0,
            "noun_hs": 0,
            "verb_hs": 0,
            "adj_hs": 0,
            "adv_hs": 0,
            "misc_hs": 0,
            "pnun_hs": 0
        }
        self.hs_dict_keys = list(self.hs_dict.keys())
        self.load_database()

        self.current_word = None
        self.current_pronunciation = None
        self.current_meaning = None
        self.current_gamemode = None

        os.system('clear')
        #self.debug_print_stats_table()
        self.menu()
    
    def load_hs_vars(self):
        self.quizgame_hs = self.hs_dict[self.hs_dict_keys[0]]
        self.timed_hs = self.hs_dict[self.hs_dict_keys[1]]
        self.noun_hs = self.hs_dict[self.hs_dict_keys[2]]
        self.verb_hs = self.hs_dict[self.hs_dict_keys[3]]
        self.adj_hs = self.hs_dict[self.hs_dict_keys[4]]
        self.adv_hs = self.hs_dict[self.hs_dict_keys[5]]
        self.misc_hs = self.hs_dict[self.hs_dict_keys[6]]
        self.pnun_hs = self.hs_dict[self.hs_dict_keys[7]]

    def deleteall(self):
        for widget in root.winfo_children():
            widget.destroy()
        self.canvas = tk.Canvas(self.root, width=1920, height=1080, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)  # Make it fill the window
        self.canvas.lower(self.root)
        music_text, music_pos = self.is_songon()
        self.button_mute = tk.Button(root, text=music_text, font=("Lucida Console", 20), command=lambda: self.add_to_buttons_clicked(self.mute_song))
        self.button_mute.place(x=music_pos, y=0)

    def menu(self):
        self.play_song("spectralsummer.mp3")
        self.deleteall()
        
        jpquiz_label = tk.Label(root, text="JPQuiz v0.9", font=("Lucida Console", 45))
        jpquiz_label.pack(pady=60)

        menu_buttons = tk.Frame(root)
        menu_buttons.pack(pady=300)

        button_play = tk.Button(menu_buttons, text="Play!", width=30, font=("Lucida Console", 24), command=lambda: self.add_to_buttons_clicked(self.modeselect))
        button_play.pack()

        button_stats = tk.Button(menu_buttons, text="Stats", width=30, font=("Lucida Console", 24), command=lambda: self.add_to_buttons_clicked(self.statsboard))
        button_stats.pack()

        testing_button = tk.Button(menu_buttons, text="Help", width=30, font=("Lucida Console", 24), command=lambda: self.add_to_buttons_clicked(self.help_page))
        testing_button.pack()

        button_close = tk.Button(menu_buttons, text="Close", width=30, font=("Lucida Console", 24), command=lambda: self.add_to_buttons_clicked(self.save_and_exit))
        button_close.pack()

        
    
    def save_and_exit(self):
        for item in gc.get_objects():
            if isinstance(item, sqlite3.Connection):
                item.close()
        self.root.destroy()

    def add_to_buttons_clicked(self, func, *args):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()

        cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = 'JPQuiz Stats - Buttons Pressed'")

        conn.commit()
        #conn.close()

        self.root.after(0, func(*args))
    
    def add_to_games_played(self, func, *args):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()
        gamemode = self.return_game_id()
        cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = 'JPQuiz Stats - Games Played'")

        match gamemode:
            case "adj":
                category_name = "Adjectives Mode - Games Played"
            case "adv":
                category_name = "Adverbs Mode - Games Played"
            case "misc":
                category_name = "Miscellaneous Mode - Games Played"
            case "pnun":
                category_name = "No Pronunciation Mode - Games Played"
            case "noun":
                category_name = "Nouns Mode - Games Played"
            case "quizgame":
                category_name = "Standard Quiz Stats - Games Played"
            case "timed":
                category_name = "Timed Quiz Stats - Games Played"
            case "verb":
                category_name = "Verbs Mode - Games Played"
            case _:
                category_name = None

        if category_name:
            cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = ?", (category_name,))

        conn.commit()
        self.root.after(0, func(*args))

    def update_highest_streak(self):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()
        category_name = self.match_gamemode_longest_streak()
        if category_name:
            cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = ?", (category_name,))
        conn.commit()

    def match_gamemode_longest_streak(self):
        gamemode = self.return_game_id()

        match gamemode:
            case "adj":
                category_name = "Adjectives Mode - Longest Streak"
            case "adv":
                category_name = "Adverbs Mode - Longest Streak"
            case "misc":
                category_name = "Miscellaneous Mode - Longest Streak"
            case "pnun":
                category_name = "No Pronunciation Mode - Longest Streak"
            case "noun":
                category_name = "Nouns Mode - Longest Streak"
            case "quizgame":
                category_name = "Standard Quiz Stats - Longest Streak"
            case "timed":
                category_name = "Timed Quiz Stats - Longest Streak"
            case "verb":
                category_name = "Verbs Mode - Longest Streak"
            case _:
                category_name = None
        
        return category_name
    
    def update_highest_mult(self):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()
        category_name = self.match_gamemode_highest_mult()
        if category_name:
            cursor.execute("UPDATE stats SET value = ? WHERE stat_name = ?", (self.mult, category_name,))
        conn.commit()

    def match_gamemode_highest_mult(self):
        gamemode = self.return_game_id()

        match gamemode:
            case "adj":
                category_name = "Adjectives Mode - Highest Multiplier"
            case "adv":
                category_name = "Adverbs Mode - Highest Multiplier"
            case "misc":
                category_name = "Miscellaneous Mode - Highest Multiplier"
            case "pnun":
                category_name = "No Pronunciation Mode - Highest Multiplier"
            case "noun":
                category_name = "Nouns Mode - Highest Multiplier"
            case "quizgame":
                category_name = "Standard Quiz Stats - Highest Multiplier"
            case "timed":
                category_name = "Timed Quiz Stats - Highest Multiplier"
            case "verb":
                category_name = "Verbs Mode - Highest Multiplier"
            case _:
                category_name = None
        
        return category_name
    
    def make_highscores_table_equal_to_stats_table(self):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(HIGHSCORES)")
        highscore_names = [row[1] for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM HIGHSCORES")
        database_highscores = []
        for score_tuples in cursor.fetchall():
            for item in score_tuples:
                database_highscores.append(int(item))
        
        for index, name in enumerate(highscore_names):
            match name:
                case "adjectives_hs":
                    category_name = "Adjectives Mode - Highscore"
                case "adverbs_hs":
                    category_name = "Adverbs Mode - Highscore"
                case "misc_hs":
                    category_name = "Miscellaneous Mode - Highscore"
                case "pronunciation_hs":
                    category_name = "No Pronunciation Mode - Highscore"
                case "nouns_hs":
                    category_name = "Nouns Mode - Highscore"
                case "quizgame_hs":
                    category_name = "Standard Quiz Stats - Highscore"
                case "timed_hs":
                    category_name = "Timed Quiz Stats - Highscore"
                case "verbs_hs":
                    category_name = "Verbs Mode - Highscore"
            
            category_score = database_highscores[index]

            cursor.execute("UPDATE stats SET value = ? WHERE stat_name = ?", (category_score, category_name,))
            conn.commit()

    def find_highest_score(self):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()

        cursor.execute("SELECT stat_name, value FROM stats WHERE stat_name LIKE '% - Highscore'")
        highscores_names = cursor.fetchall()

        scores = []
        for item in highscores_names:
            scores.append(int(item[1]))

        scores.sort(reverse=True)
        top_score = int(scores[0])

        for item in highscores_names:
            if int(item[1]) == top_score:
                top_score_name = item[0]
        
        top_score_name = str(top_score_name.split(" - Highscore")[0])
        if "Stats" in str(top_score_name):
            top_score_name = str(top_score_name.split(" Stats")[0])
        
        entry = f"{top_score_name}: {top_score}"

        if top_score == 0:
            entry = "No highest score yet..."

        cursor.execute("UPDATE stats SET value = ? WHERE stat_name = 'JPQuiz Stats - Highest Score'", (entry,))
        conn.commit()

    def find_favorite_gamemode(self):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT stat_name, value FROM stats WHERE stat_name LIKE '% - Games Played'")
        gamemode_plays = cursor.fetchall()

        times_played = []

        for item in gamemode_plays:
            if item[0] != 'JPQuiz Stats - Total Games Played':
                times_played.append(item[1])
        
        times_played.sort(reverse=True)
        top_time = times_played[0]

        total_times_played = 0
        for time in times_played:
            total_times_played += int(time)

        cursor.execute("UPDATE stats SET value = ? WHERE stat_name = 'JPQuiz Stats - Total Games Played'", (total_times_played,))
        
        top_games = []
        for item in gamemode_plays:
            if item[1] == top_time:
                top_games.append(item[0])

        favorite_gamemode_name = random.choice(top_games)
        favorite_gamemode_number = int(times_played[0])

        favorite_gamemode_name = str(favorite_gamemode_name.split(" - Games Played")[0])
        if " Stats" in favorite_gamemode_name:
            favorite_gamemode_name = str(favorite_gamemode_name.split(" Stats")[0])
    
        if favorite_gamemode_number == 0:
            favorite_gamemode_name = "No favorite game mode yet..."
           
        cursor.execute("UPDATE stats SET value = ? WHERE stat_name = 'JPQuiz Stats - Favorite Gamemode'", (favorite_gamemode_name,))
        conn.commit()

    def load_database(self):
        self.load_database_hs()
        self.load_database_stats()
    
    def load_database_hs(self):
        load_data = sqlite3.connect("save.db")
        load_cursor = load_data.cursor()

        load_cursor.execute("""
            CREATE TABLE IF NOT EXISTS HIGHSCORES (
                quizgame_hs INTEGER NOT NULL DEFAULT 0,
                timed_hs INTEGER NOT NULL DEFAULT 0,
                nouns_hs INTEGER NOT NULL DEFAULT 0,
                verbs_hs INTEGER NOT NULL DEFAULT 0,
                adjectives_hs INTEGER NOT NULL DEFAULT 0,
                adverbs_hs INTEGER NOT NULL DEFAULT 0,
                misc_hs INTERGER NOT NULL DEFAULT 0,
                pronunciation_hs INTEGER NOT NULL DEFAULT 0
            )
        """)

        load_cursor.execute("SELECT COUNT(*) FROM HIGHSCORES")
        count = load_cursor.fetchone()[0]
        
        if count == 0:
            load_cursor.execute("INSERT INTO HIGHSCORES DEFAULT VALUES")
            load_data.commit()
        
        load_cursor.execute("SELECT * FROM HIGHSCORES")
        highscore_values = load_cursor.fetchall()
        
        #print statements are for debugging
        #print(f"from self.load_database_hs: here are the highscores loaded from save.db:")
        for item in highscore_values:
            for i, score in enumerate(item):
                #print("before:", self.hs_dict[self.hs_dict_keys[i]])
                self.hs_dict[self.hs_dict_keys[i]] = score
                #print("after:", self.hs_dict[self.hs_dict_keys[i]])

        #load_data.close()
        self.load_hs_vars()
    
    def load_database_stats(self):
        load_stats = sqlite3.connect("save.db")
        cursor = load_stats.cursor()
        self.stat_categories = ["JPQuiz Stats", "Standard Quiz Stats", "Timed Quiz Stats", "Nouns Mode", "Verbs Mode", "Adjectives Mode", "Adverbs Mode", "Miscellaneous Mode", "No Pronunciation Mode", "Review Mode", "Adverbs", "Verbs", "Adjectives", "Nouns", "Miscellaneous"]

        table_list = cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='stats'""").fetchall()
        if table_list == []:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    stat_name TEXT UNIQUE NOT NULL,
                    kanji_text TEXT,
                    value TEXT,
                    pronunciation TEXT,
                    correct_guess INTEGER,
                    incorrect_guess INTEGER,
                    viewed_total INTEGER
                )
            ''')
            self.create_all_stats()

        words_in_file, meanings = self.get_stat_name_word_from_statstable()

        existing_strings, existing_games = self.search_for_stat_name()
        for word in words_in_file:
            if word not in existing_strings:
                found_word = False
                for stat_tuple in meanings:
                    if isinstance(stat_tuple, str) and found_word == True:
                        break
                    if isinstance(stat_tuple, tuple):
                        if stat_tuple[2] == word:
                            kanji, kana, meaning = stat_tuple
                            found_word = True
                
                stat_data = {
                            "stat_name": f"{meaning}",
                            "kanji_text": f"{kanji}",
                            "pronunciation": f"{kana}",
                            "correct_guess": 0,
                            "incorrect_guess": 0,
                            "viewed_total": 0,
                            "value": 0
                            }
                self.update_stat(stat_data)
                print(f"'{word}' does not exist in the database, adding...")
        
        cursor.execute("SELECT stat_name FROM stats")
        existing_stat_names = cursor.fetchall()

        existing_names = []
        for item in existing_stat_names:
            if " - " not in item[0]:
                existing_names.append(item[0])
        
        for word in existing_names:
            if word not in words_in_file:
                cursor.execute("DELETE FROM stats WHERE stat_name = ?", (word,))
                print(f"'{word}' exists in database but not in .txt files, removing...")

        #self.debug_print_stats_table()

        cursor.execute("SELECT stat_name, kanji_text, value, pronunciation, correct_guess, incorrect_guess, viewed_total FROM stats")
        stats = cursor.fetchall()

        load_stats.commit()
        #load_stats.close()
        return stats

    def search_for_stat_name(self):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()

        cursor.execute("SELECT stat_name FROM stats")
        existing_names = cursor.fetchall()

        existing_strings = []
        existing_games = []

        for item in existing_names:
            try:
                if bool(": " in item[0]):
                    split_word_string_list = item[0].strip().split(": ")
                    split_word_string = split_word_string_list[1]
                    existing_strings.append(split_word_string)
                elif bool(" - " in item[0]):
                    raise IndexError
                else:
                    item = item[0].strip()
                    existing_strings.append(item)
            except IndexError:
                split_word_string_list = (item[0].strip())
                existing_games.append(split_word_string_list)
    
        #conn.close()
        return existing_strings, existing_games
    
    #---This function was reprogrammed by ChatGPT---#
     # Insert new update_stat here
    def update_stat(self, stat_data):
        """
        Updates or inserts a stat entry in the database.
        
        Parameters:
            stat_data (dict): A dictionary containing the following keys:
                - stat_name (str): Unique identifier (e.g., "JPQuiz Stats: Games Played").
                - kanji_text (str): Text in Kanji (if applicable).
                - value (str or int): The current value of the stat.
                - pronunciation (str): Pronunciation text (if applicable).
                - correct_guess (int): Count of correct guesses.
                - incorrect_guess (int): Count of incorrect guesses.
                - viewed_total (int): Number of times the stat was viewed.
        """
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO stats (stat_name, kanji_text, value, pronunciation, correct_guess, incorrect_guess, viewed_total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(stat_name) DO UPDATE SET
                kanji_text = excluded.kanji_text,
                value = excluded.value,
                pronunciation = excluded.pronunciation,
                correct_guess = excluded.correct_guess,
                incorrect_guess = excluded.incorrect_guess,
                viewed_total = excluded.viewed_total
        ''', (
            stat_data["stat_name"],
            stat_data.get("kanji_text", ""),
            stat_data.get("value", 0),
            stat_data.get("pronunciation", ""),
            stat_data.get("correct_guess", 0),
            stat_data.get("incorrect_guess", 0),
            stat_data.get("viewed_total", 0)
        ))
        conn.commit()
        #conn.close()
    
    # --- #

    #---This function was generated by ChatGPT, and then heavily modified by me ---#
    def create_all_stats(self):
    # Suppose you have a list of stat entries created by your stats_list_append
        for stat_tuple in self.stats_list_append():
            # Here we check if the tuple contains valid data (not a "SKIP" marker)
            if isinstance(stat_tuple, tuple) and "SKIP" not in stat_tuple:
                #this is for game data stats, like game highscores and whatnot
                stat_data = {
                    "stat_name": f"{stat_tuple[0]} - {stat_tuple[1]}",
                    "value": 0,        # Replace with your tracked value
                }
                self.update_stat(stat_data)

            elif isinstance(stat_tuple, list):
                for item in stat_tuple:
                    if isinstance(item, tuple):
                        #this is for the words
                        #{word_category_file}:
                        stat_data = {
                            "stat_name": f"{item[2]}",
                            "kanji_text": f"{item[0]}",
                            "pronunciation": f"{item[1]}",
                            "correct_guess": 0,
                            "incorrect_guess": 0,
                            "viewed_total": 0,
                            "value": 0
                                }
                        self.update_stat(stat_data)
            elif isinstance(stat_tuple, str):
                categories_concat = stat_tuple.split(" - ")
                word_category_file = categories_concat[0]
        
        #self.debug_print_stats_table()
    # --- #

    def create_new_stat_word(self, stat_tuple):
            if isinstance(stat_tuple, list):
                for item in stat_tuple:
                    if isinstance(item, str):
                        word_category_file = item
                    if isinstance(item, tuple):
                        #this is for the words
                        #{word_category_file}: 
                        stat_data = {
                            "stat_name": f"{item[2]}",
                            "kanji_text": f"{item[0]}",
                            "pronunciation": f"{item[1]}",
                            "correct_guess": 0,
                            "incorrect_guess": 0,
                            "viewed_total": 0,
                            "value": 0
                                }
                        self.update_stat(stat_data)

    #---This is a SQL debugging function for the 'stats' table that was generated by ChatGPT, and then modified by me---#
    def debug_print_stats_table(self):
        """
        Connects to the 'save.db' database and prints all rows in the 'stats' table
        with their corresponding column names for debugging purposes.
        """
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stats")
        
        # Get column names from the cursor description.
        columns = [desc[0] for desc in cursor.description]
        
        rows = cursor.fetchall()
        print("----- Stats Table Debug Info -----")
        for row in rows:
            # Create a dictionary mapping column names to their values for readability.
            stat_entry = dict(zip(columns, row))
            print("Stat Entry:")
            stathold = []
            for key, value in stat_entry.items():
                stathold.append(f"{key}: {value}")
            print(stathold)
            print("-" * 30)
        #conn.close()
    # --- #

    def get_stat_name_word_from_statstable(self):
        words = []
        words_full_definiton = []
        for stat_tuple in self.stats_list_append():
            if isinstance(stat_tuple, list):
                for item in stat_tuple:
                    words_full_definiton.append(item)
                    if isinstance(item, tuple):
                        #These are the words
                        words.append(item[2])
            if isinstance(stat_tuple, str):
                stat_tuple = stat_tuple.split("SKIP")
                stat_tuple = stat_tuple[0]
                words_full_definiton.append(stat_tuple)

        words_full_definiton = words_full_definiton[::-1]
        return words, words_full_definiton

    def stats_list_append(self, insert=False):
        self.sorted_line_lists = []

        self.jpquiz_stats = ["Total Games Played", "Games Quit", "Favorite Gamemode", "Highest Score", "Words Guessed Total", "Words Guessed Correctly", "Words Guessed Incorrectly", "Buttons Pressed"]
        self.gamemode_stats = ["Games Played", "Highscore", "Longest Streak", "Highest Multiplier"]
        self.gamemodes_exist = ["Standard Quiz Stats", "Timed Quiz Stats", "Nouns Mode", "Verbs Mode", "Adjectives Mode", "Adverbs Mode", "Miscellaneous Mode", "No Pronunciation Mode"]
        self.review_mode_stats = ["Words Reviewed"]
        word_categories = ["Adverbs", "Verbs", "Adjectives", "Nouns", "Miscellaneous"]
        def process_one():
            for category in self.stat_categories:
                if category not in word_categories:
                    if insert:
                        self.statsbox.insert(tk.END, category)
                        self.statsbox.itemconfig(tk.END, {'bg': 'grey'})
                    self.sorted_line_lists.append((f"{category}", "SKIP"))
                if category == "JPQuiz Stats":
                    for item in self.jpquiz_stats:
                        if insert:
                            self.statsbox.insert(tk.END, item)
                        self.sorted_line_lists.append((f"{category}", item))
                if category in self.gamemodes_exist:
                    for stats in self.gamemode_stats:
                        if insert:
                            self.statsbox.insert(tk.END, stats)
                        self.sorted_line_lists.append((f"{category}", stats))
                if category == "Review Mode":
                    for item in self.review_mode_stats:
                        if insert:
                            self.statsbox.insert(tk.END, item)
                        self.sorted_line_lists.append((f"{category}", item))

        def process_two():            
            for file in load_words():
                if file == 'adverbs.txt':
                    if insert:
                        self.statsbox.insert(tk.END, "Adverbs")
                        self.statsbox.itemconfig(tk.END, {'bg':'grey'})
                    self.sorted_line_lists.append("Adverbs - SKIP")
                elif file == 'verbs.txt':
                    if insert:
                        self.statsbox.insert(tk.END, "Verbs")
                        self.statsbox.itemconfig(tk.END, {'bg':'grey'})
                    self.sorted_line_lists.append("Verbs - SKIP")
                elif file == 'adjectives.txt':
                    if insert:
                        self.statsbox.insert(tk.END, "Adjectives")
                        self.statsbox.itemconfig(tk.END, {'bg':'grey'})
                    self.sorted_line_lists.append("Adjectives - SKIP")
                elif file == 'nouns.txt':
                    if insert:
                        self.statsbox.insert(tk.END, "Nouns")
                        self.statsbox.itemconfig(tk.END, {'bg':'grey'})
                    self.sorted_line_lists.append("Nouns - SKIP")
                elif file == 'misc.txt':
                    if insert:
                        self.statsbox.insert(tk.END, "Miscellaneous")
                        self.statsbox.itemconfig(tk.END, {'bg':'grey'})
                    self.sorted_line_lists.append("Miscellaneous - SKIP")

                linehold = []
                with open(os.path.join(folder_name, file), 'r', encoding='utf-8') as f:  # Open the file
                    lines = f.readlines()
                    for line in lines:
                        if line != "":
                            line_list = line.strip().split(", ")
                            linehold.append((line_list[0], line_list[1], line_list[2]))
                    linehold.sort(key=lambda x: x[2].strip().lower())  
                    self.sorted_line_lists.append(linehold)
        
                    for item in linehold:
                        sorted = f"{item[0]} - {item[2]}"
                        if insert:
                            self.statsbox.insert(tk.END, sorted)

        process_one()
        process_two()

        #print(self.sorted_line_lists)
        return self.sorted_line_lists
    
    # --- This function was modded by ChatGPT to add SQL --- #
    def stat_detail_select(self, event):
        selected_index = self.statsbox.curselection()
        selected_item = self.statsbox.get(selected_index)
        names, games = self.search_for_stat_name()

        #gamestat_indexs = self.statsbox.get(0, 42)
        #print(gamestat_indexs)

        #print(Fore.BLUE + str(names))
        #print(Fore.YELLOW + str(games))

        details_text = "No details found"

        # Check if the selected item belongs to the stat categories
        if selected_item in self.stat_categories:
            details_text = f"Category: {selected_item}"
        else:
            try:
                selected_item = self.get_part_of_str(selected_item, " - ", 1)
            except IndexError: 
                pass
            if selected_item in names:
                # Query the database for details of the stat
                conn = sqlite3.connect("save.db")
                cursor = conn.cursor()

                # Get the stat details from the database where stat_name matches
                cursor.execute("SELECT * FROM stats WHERE stat_name = ?", (selected_item,))
                stat_details = cursor.fetchone()
                
                if stat_details:
                    stat_name, kanji_text, value, pronunciation, correct_guess, incorrect_guess, viewed_total = stat_details
                    details_text = (
                        f"English Meaning: {stat_name}    "f"Correct Guesses: {correct_guess}\n"
                        f"Kanji Text: {kanji_text}        " f"Incorrect Guesses: {incorrect_guess}\n"
                        f"Pronunciation: {pronunciation}    "f"Viewed Total: {viewed_total}\n"
                        
                    )
                else:
                    details_text = f"No details found for {selected_item}"

                #conn.close()


            elif selected_item in self.jpquiz_stats:
                details_text = self.stat_detail_select_find_gamemodestat(self.jpquiz_stats, selected_item)
            elif selected_item in self.gamemode_stats:
                details_text = self.stat_detail_select_find_gamemodestat(self.gamemode_stats, selected_item)            
            elif selected_item in self.review_mode_stats:
                details_text = self.stat_detail_select_find_gamemodestat(self.review_mode_stats, selected_item)

        self.stats_detail.config(text=details_text)
    #---#
    def stat_detail_select_find_gamemodestat(self, modelist, selected_item):
        conn = sqlite3.connect("save.db")
        cursor = conn.cursor()
        category_and_name = []

        def for_item_in_gamestat_indexs(gamestat_indexs, provided_list, is_gamemode=False):
                gamestat_indexs_as_list = list(gamestat_indexs)
                gamestat_index = gamestat_indexs_as_list.index(selected_item)
                iteration_counter = 0
                if is_gamemode:
                    gamestat_index = self.statsbox.curselection()
                    if gamestat_index:
                        gamestat_index = gamestat_index[0]
                    #for future stats added, the 9 subtracted comes from the jpquiz items that come before the gamemodes. if more jpquiz stats are added in the future, this will break and will need to be adjusted
                    gamestat_index -= 9

                for item in gamestat_indexs:
                    if item not in provided_list:
                        category_name = item
                    if iteration_counter == gamestat_index:
                        category_and_name.append(category_name)
                        break
                    iteration_counter += 1

                category_and_name.append(selected_item)
                full_fetch_name = " - ".join(category_and_name)
                return full_fetch_name
            
        match modelist:
            #the numbers in the .get() methods need to be adjusted if more stats are added.
            case self.jpquiz_stats:
                gamestat_indexs = self.statsbox.get(0, 8)
                full_fetch_name = for_item_in_gamestat_indexs(gamestat_indexs, self.jpquiz_stats)
            case self.gamemode_stats:
                gamestat_indexs = self.statsbox.get(9, 48)
                full_fetch_name = for_item_in_gamestat_indexs(gamestat_indexs, self.gamemode_stats, True)
            case self.review_mode_stats:
                gamestat_indexs = self.statsbox.get(49, 50)
                full_fetch_name = for_item_in_gamestat_indexs(gamestat_indexs, self.review_mode_stats)

        cursor.execute("SELECT stat_name, value FROM stats WHERE stat_name = ?", (full_fetch_name,))
        relevant_stats_in_table = cursor.fetchone()

        if relevant_stats_in_table:
            stat_name, value = relevant_stats_in_table
            if "Highest Multiplier" in stat_name:
                value = str(value) + "x"
            details_text = (
                f"{stat_name}:\n" 
                f"{value}"
            )
        else:
            raise TypeError
        
        #conn.close()

        return details_text

    def statsboard(self):
        self.play_song("elevator.mp3")
        self.deleteall()
        self.make_highscores_table_equal_to_stats_table()
        self.find_favorite_gamemode()
        self.find_highest_score()

        stats_label = tk.Label(root, text="Stats Board", font=("Lucida Console", 35))
        stats_label.pack(pady=10)

        statsframe = tk.Frame(root)
        statsframe.pack(pady=10)

        self.statsbox = tk.Listbox(statsframe, height=20, width=105, selectmode=tk.SINGLE, font=("Lucida Console", 16))
        self.statsbox.pack(side=tk.LEFT, fill=tk.Y)

        self.stats_list_append(True)

        statsscroll = tk.Scrollbar(statsframe, orient=tk.VERTICAL, command=self.statsbox.yview)
        statsscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.stats_detail = tk.Label(root, text="Select a stat to see details", font=("Lucida Console", 16), justify="left", anchor="w", padx=10, pady=10, relief="sunken", width=78, height=5)
        self.stats_detail.pack(pady=10, padx=10)

        self.statsbox.bind("<<ListboxSelect>>", self.stat_detail_select)

        button_stats_back = tk.Button(root, text="Back", font=("Lucida Console", 24), command=lambda: self.add_to_buttons_clicked(self.menu))
        button_stats_back.pack()

    def show_results(self):
        game_id = self.return_game_id()

        #print(f"from self.show_results: here is game_id when it passes through me: {game_id}")

        if game_id != "review":
            self.highscore_check(game_id)
        if game_id == "timed":
            self.time_left = 0
        self.current_gamemode = None
        self.deleteall()

        show_results_label = tk.Label(root, text="Results:", font=("Lucida Console", 40))
        show_results_label.pack(pady=10)

        show_results_frame = tk.Frame(root)
        show_results_frame.pack()

        results_frame = tk.Frame(show_results_frame, relief="raised")
        results_frame.pack()

        self.resultsbox = tk.Listbox(results_frame, height=13, width=85, selectmode=tk.SINGLE, font=("Lucida Console", 16))
        self.resultsbox.pack(side=tk.LEFT, fill=tk.Y)

        resultsbox_scroll = tk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.resultsbox.yview)
        resultsbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.resultsbox.insert(tk.END, "Game History")
        self.resultsbox.itemconfig(tk.END, {'bg':'grey'})

        for item in self.words_viewed_list_global:
            self.resultsbox.insert(tk.END, item)
            if item.startswith("Correct"):
                self.resultsbox.itemconfig(tk.END, {'bg':'light green'})
            if item.startswith("Incorrect"):
                self.resultsbox.itemconfig(tk.END, {'bg':'light coral'})

        results_frame_labels = tk.Frame(show_results_frame, relief="raised", bd=2)
        results_frame_labels.pack(pady=10)

        if int(self.score) >= self.round_hs:
            self.round_hs = int(self.score)
        
        result_texts = [
            (f"Final Score: {int(self.score)}", 1, 1), (f"Highest Multiplier: {self.mult_round_hs}", 1, 2), (f"Highest Streak: {self.round_streak_hs}", 1, 3),
            (f"Highest Score in Round: {self.round_hs}", 2, 1), ( f"Correctly Guessed: {self.correctly_guessed}", 2, 2), (f"Incorrecly Guessed: {self.incorrectly_guessed}", 2, 3)
                        ]

        for name, rowint, colint in result_texts:
            result_label = tk.Label(results_frame_labels, text=name, font=("Lucida Console", 20))
            result_label.grid(row=rowint, column=colint, padx=18, pady=13)
        
        self.resultsbox.bind("<<ListboxSelect>>", self.block_listbox_clicks_results)

        results_button_frame = tk.Frame(show_results_frame)
        results_button_frame.pack()

        show_results_continue_button = tk.Button(results_button_frame, text="Continue to Main Menu", font=("Lucida Console", 20), command=lambda: self.add_to_buttons_clicked(self.menu))
        show_results_continue_button.grid(column=1, row=1, pady=25)

    def block_listbox_clicks_results(self, event):
        selected = self.resultsbox.curselection()
        for option in selected:
            self.resultsbox.selection_clear(option)
        
    def get_part_of_str(self, string, parameter, index_num):
        parts = string.strip().split(parameter)
        part = parts[index_num]
        return part
    
    def help_page(self):
        self.play_song("elevator.mp3")
        self.deleteall()

        help_folder_path = os.listdir("help")
        help_files = []

        for file in help_folder_path:
            if file.endswith(".txt"):
                help_files.append(open(os.path.join("help", file), "r", encoding="utf-8").read())

        help_label = tk.Label(root, text="Help Page", font=("Lucida Console", 45))
        help_label.pack(pady=30)

        help_frame = tk.Frame(root)
        help_frame.pack()
    
        help_frame_left = tk.Frame(help_frame, relief="raised", borderwidth=2, width=22, height=20)
        help_frame_right = tk.Frame(help_frame, relief="raised", borderwidth=2, width=22, height=20)
        help_frame_left.grid(row=1, column=1, padx=20)
        help_frame_right.grid(row=1, column=2, padx=20)

        how_to_play_label = tk.Label(help_frame_left, text="How to Play:", font=("Lucida Console", 35))
        how_to_play_label.pack(pady=10)

        how_to_play_textbox = tk.Text(help_frame_left, font=("Lucida Console", 13),wrap="word", relief="sunken")
        how_to_play_textbox.pack(padx=5, pady=5)

        how_to_play_textbox.insert(tk.END, help_files[0])
        how_to_play_textbox.config(state="disabled")

        how_to_customize_label = tk.Label(help_frame_right, text="Customization:", font=("Lucida Console", 35))
        how_to_customize_label.pack(pady=10)
        
        how_to_customize_textbox = tk.Text(help_frame_right, font=("Lucida Console", 13), wrap="word", relief="sunken")
        how_to_customize_textbox.pack(padx=5, pady=5)

        how_to_customize_textbox.insert(tk.END, help_files[1])
        how_to_customize_textbox.config(state="disabled")

        help_back = tk.Button(root, text="Back", font=("Lucida Console", 20), command=lambda: self.add_to_buttons_clicked(self.menu))
        help_back.pack(pady=30)

        pass

    def modeselect(self):
        self.deleteall()
        self.set_gamemode(None, False)

        modemenu_label = tk.Label(root, text="Select Gamemode:", font=("Lucida Console", 40))
        modemenu_label.pack(pady=60)

        modeframe = tk.Frame(root)
        modeframe.pack()

        button_quizgame = tk.Button(modeframe, text="Standard Quiz", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "quiz"))
        button_quizgame.grid(row=1, column=1, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="Timed Quiz", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "timed"))
        button_quizgame.grid(row=1, column=2, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="Nouns Only", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "nouns"))
        button_quizgame.grid(row=1, column=3, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="Verbs Only", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "verbs"))
        button_quizgame.grid(row=2, column=1, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="Adjectives Only", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "adjectives"))
        button_quizgame.grid(row=2, column=2, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="Adverbs Only", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "adverbs"))
        button_quizgame.grid(row=2, column=3, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="Miscellaneous Only", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "misc"))
        button_quizgame.grid(row=3, column=1, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="No Pronounciation", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "no-pronunciation"))
        button_quizgame.grid(row=3, column=2, pady=10, padx=10)

        button_quizgame = tk.Button(modeframe, text="Decks", font=("Lucida Console", 24), height=3, width=15, command=lambda: self.add_to_buttons_clicked(self.set_gamemode, "review-mode"))
        button_quizgame.grid(row=3, column=3, pady=10, padx=10)
        
        button_mode_back = tk.Button(self.root, text="Back", font=("Lucida Console", 24), command=lambda: self.add_to_buttons_clicked(self.menu))
        button_mode_back.pack()
    
    def set_gamemode(self, mode, moveon=True):
        self.current_gamemode = mode
        if moveon:
            self.game_settings()

    def game_settings(self):
        self.deleteall()
        game_id = self.return_game_id()

        self.words_viewed_list_global = []

        gamesetting_frame = tk.Frame(root)
        gamesetting_frame.pack(pady=25)

        gamesetting_label = tk.Label(gamesetting_frame, text="Game Settings: ", font=("Lucida Console", 40))
        gamesetting_label.grid(row=1, column=1)

        match game_id:
            case "quizgame":
                settext = "Standard Test "
                optionindex = 0
            case "timed":
                settext = "Timed Mode"
                optionindex = 1
            case "adj":
                settext = "Adjectives Only Mode"
                optionindex = 2
            case "adv":
                settext = "Adverbs Only Mode"
                optionindex = 3
            case "misc":
                settext = "Miscellaneous Only Mode"
                optionindex = 4
            case "noun":
                settext = "Nouns Only Mode"
                optionindex = 5
            case "verb":
                settext = "Verbs Only Mode"
                optionindex = 6
            case "pnun":
                settext = "No Pronunciation Mode"
                optionindex = 7
            case "review":
                settext = "Review Mode"
                optionindex = 8

        gamesetting_mode_label = tk.Label(gamesetting_frame, text=settext, font=("Lucida Console", 40))
        gamesetting_mode_label.grid(row=1, column=2)

        gamesetting_frame_grid = tk.Frame(root, relief="raised", borderwidth=2)
        gamesetting_frame_grid.pack(pady=20)

        self.insert_optionbox(gamesetting_frame_grid, optionindex)

        options_selected_frame = tk.Frame(root, relief="sunken", borderwidth=2)
        options_selected_frame.pack(pady=25)

        created_options_text = ""
        for item in range(0, self.optionBoxAmount):
            created_options_text += f"{item}: null\n"
        created_options_text = str(created_options_text)

        placeholderoptions = "this is a placeholder\nfor the options\nthat have been selected\nin the game"
        options_selected_label = tk.Label(options_selected_frame, text=created_options_text, font=("Lucida Console", 22), width=20, justify="left")
        options_selected_label.pack()

        gamesetting_frame_buttons = tk.Frame(root, relief="raised", borderwidth=2, width=12)
        gamesetting_frame_buttons.pack()

        gamesetting_start = tk.Button(gamesetting_frame_buttons, text="Start!", font=("Lucida Console", 32), command=lambda: self.add_to_buttons_clicked(self.game_skeleton))
        gamesetting_start.grid(row=1, column=1, pady=4, padx=4)

        gamesetting_back = tk.Button(gamesetting_frame_buttons, text="Back", font=("Lucida Console", 32), command=lambda: self.add_to_buttons_clicked(self.modeselect))
        gamesetting_back.grid(row=1, column=2, pady=4, padx=4)
    
    def getDecks(self):
        decks = ["Choose a deck:"]
        deck_files = os.listdir("decks")
        for file in deck_files:
            decks.append(file)
        
        return decks
    
    def getDeckName(self):
        pass
    
    def insert_optionbox(self, location, optionindex):
        optionBoxes = [1, 2, 1, 1, 1, 1, 1, 1, 1]
        options = [[["Question Amount Options", "10 Questions", "20 Questions", "30 Questions", "40 Questions", "50 Questions", "70 Questions", "100 Questions", "Infinite Questions", "Custom Amount"]], [["Time Amount Options", "1 Minute", "2 Minutes", "3 Minutes", "4 Minutes", "5 Minutes", "10 Minutes", "15 Minutes", "30 Minutes", "1 Hour"], ["Word Options", "Default Settings", "Default Settings, No Pronunciation", "Nouns Only", "Verbs Only", "Adverbs Only", "Adjectives Only", "Adverbs Only", "", ""]], [["Adjectives Only Options", "Default Settings", "Default Settings, No Pronunciation", "", "", "", "", "", "", ""]], [["Adverbs Only Options", "Default Settings", "Default Settings, No Pronunciation", "", "", "", "", "", "", ""]], [["Miscellaneous Only Options","Default Settings", "Default Settings, No Pronunciation", "", "", "", "", "", "", "", ""]], [["Nouns Only Options", "Default Settings", "Default Settings, No Pronunciation", "", "", "", "", "", "", ""]], [["Verbs Only Options", "Default Settings", "Default Settings, No Pronunciation", "", "", "", "", "", "", ""]], [["No Pronunciation Options", "Default Settings", "", "", "", "", "", "", "", ""]], [self.getDecks()]]
        self.optionBoxAmount = optionBoxes[optionindex]
        for x in range(0, self.optionBoxAmount):
            optionBox = tk.Listbox(location, font=("Lucida Console", 28), relief="ridge", borderwidth=4, width=30)
            optionBox.grid(row=1, column=x, padx=10, pady=10)
            isColored = True
            for option in options[optionindex][x]:
                if isinstance(option, list):
                    pass
                elif "Options" in option:   
                    optionBox.insert(tk.END, option)
                    optionBox.itemconfig(tk.END, {'bg':'grey'})
                else:
                    optionBox.insert(tk.END, option)
                    if isColored:
                        optionBox.itemconfig(tk.END, {'bg':'light grey'})
                        isColored = False
                    else:
                        optionBox.itemconfig(tk.END, {'bg':'white'})
                        isColored = True
        
    def optionbox_detail_select(self):
        pass

    def return_game_id(self):
        gamemode = self.current_gamemode
        if gamemode == "quiz":
            game_id = "quizgame"
            return game_id
        elif gamemode == "timed":
            game_id = "timed"
            return game_id
        elif gamemode == "nouns":
            game_id = "noun"
            return game_id
        elif gamemode == "verbs":
            game_id = "verb"
            return game_id
        elif gamemode == "adverbs":
            game_id = "adv"
            return game_id
        elif gamemode == "adjectives":
            game_id = "adj"
            return game_id
        elif gamemode == "misc":
            game_id = "misc"
            return game_id
        elif gamemode == "no-pronunciation":
            game_id = "pnun"
            return game_id
        elif gamemode == "review-mode":
            game_id = "review"
            return game_id
        else:
            game_id = None
            return game_id

    def game_skeleton(self):
        self.play_song("gummypeachrings.mp3")
        self.deleteall()
        game_id = self.return_game_id()
        #print("around line 1080: From self.game_skeleton():")
        #print(game_id)
        self.streak = 0
        self.score = 0
        self.mult = 1
        self.mult_round_hs = 1
        self.round_hs = 0
        self.correctly_guessed = 0
        self.incorrectly_guessed = 0
        self.round_streak_hs = 0

        setattr(self, f"{game_id}_label_word", tk.Label(root, text="", font=("Lucida Console", 18)))
        getattr(self, f"{game_id}_label_word").pack(pady=20)

        setattr(self, f"{game_id}_label_name", tk.Label(root, text="Word:", font=("Lucida Console", 20)))
        getattr(self, f"{game_id}_label_name").pack(pady=20)

        setattr(self, f"{game_id}_entry_answer", tk.Entry(root, font=("Lucida Console", 14)))
        getattr(self, f"{game_id}_entry_answer").pack(pady=20)

        setattr(self, f"{game_id}_frame1", tk.Frame(root))
        getattr(self, f"{game_id}_frame1").pack()

        setattr(self, f"{game_id}_button_quit", tk.Button(getattr(self, f"{game_id}_frame1"), text="Quit", font=("Lucida Console", 14), command=lambda: self.add_to_buttons_clicked(self.add_to_games_played, self.show_results)))
        getattr(self, f"{game_id}_button_quit").grid(row=1, column=1, pady=5)

        setattr(self, f"{game_id}_button_submit", tk.Button(getattr(self, f"{game_id}_frame1"), text="Submit", font=("Lucida Console", 14), command=lambda: self.add_to_buttons_clicked(self.check_answer)))
        getattr(self, f"{game_id}_button_submit").grid(row=1, column=2, pady=5)
        
        if game_id == "review":
            deck_name_label = tk.Label(root, text=f"Deck:\n{self.getDeckName()}", font=("Lucida Console", 30))
            deck_name_label.place(x=600, y=35)
        #    setattr(self, f"{game_id}_button_next", tk.Button(getattr(self, f"{game_id}_frame1"), text="Skip", font=("Lucida Console", 14), command=lambda: self.add_to_buttons_clicked(self.next_question, True)))
        #    getattr(self, f"{game_id}_button_next").grid(row=1, column=3, pady=5)

        if game_id == "timed":
            self.time_left = 600 + 1
            setattr(self, f"{game_id}_timer_label", tk.Label(root, text=f"10:00", font=("Lucida Console", 60)))
            getattr(self, f"{game_id}_timer_label").place(x=600, y=70)

            setattr(self, f"{game_id}_timer_name", tk.Label(root, text="Timer:", font=("Lucida Console", 30)))
            getattr(self, f"{game_id}_timer_name").place(x=655, y=35)

            self.countdown()
        if game_id != "review":
            setattr(self, f"{game_id}_streak_label", tk.Label(root, text=self.streak, font=("Lucida Console", 30)))
            getattr(self, f"{game_id}_streak_label").place(x=1180, y=50)

            setattr(self, f"{game_id}_streak_name", tk.Label(root, text="Streak:", font=("Lucida Console", 20)))
            getattr(self, f"{game_id}_streak_name").place(x=1170, y=10)

            setattr(self, f"{game_id}_score_label", tk.Label(root, text=self.score, font=("Lucida Console", 30)))
            getattr(self, f"{game_id}_score_label").place(x=1180, y=170)

            setattr(self, f"{game_id}_score_name", tk.Label(root, text="Score:", font=("Lucida Console", 20)))
            getattr(self, f"{game_id}_score_name").place(x=1175, y=130)

            setattr(self, f"{game_id}_mult_label", tk.Label(root, text=str(self.mult) + "x", font=("Lucida Console", 30)))
            getattr(self, f"{game_id}_mult_label").place(x=1325, y=170)

            setattr(self, f"{game_id}_mult_name", tk.Label(root, text="Multiplier:", font=("Lucida Console", 20)))
            getattr(self, f"{game_id}_mult_name").place(x=1275, y=130)

            setattr(self, f"{game_id}_hs_label", tk.Label(root, text=str(getattr(self, f"{game_id}_hs", 0)), font=("Lucida Console", 30)))
            getattr(self, f"{game_id}_hs_label").place(x=1300, y=50)

            setattr(self, f"{game_id}_hs_name", tk.Label(root, text="Highscore:", font=("Lucida Console", 20)))
            getattr(self, f"{game_id}_hs_name").place(x=1275, y=10)

        self.root.bind("<Return>", self.check_answer)
        self.next_question()
    
    def update_display(self):
        timer_minutes = self.time_left // 60
        timer_seconds = self.time_left % 60
        self.timed_timer_label.config(text=f"{timer_minutes:02}:{timer_seconds:02}")

    def countdown(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.update_display()
            self.root.after(1000, self.countdown) 
        elif self.return_game_id() != None:
            self.show_results()

    def play_song(self, songname):
        if self.current_song["name"] != songname:
            if pygame.mixer.music.get_busy():
                threading.Thread(target=self.fadeout_and_load, args=(songname,), daemon=True).start()
            else:
                self.load_and_play(songname)

    def fadeout_and_load(self, songname):
        pygame.mixer.music.fadeout(2000)
        pygame.time.wait(2000)
        self.load_and_play(songname)

    def load_and_play(self, songname):
        pygame.mixer.music.load(os.path.join(self.SOUNDS_DIR, songname))
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.4)
        self.current_song["name"] = songname

    def mute_song(self):
        if self.songon.get(): 
            pygame.mixer.music.set_volume(0)
            self.songon.set(False)
            self.button_mute.config(text="Muted!")
            self.button_mute.place(x=1803, y=0)
        else:
            pygame.mixer.music.set_volume(0.2)
            self.songon.set(True)
            self.button_mute.config(text="Mute music")
            self.button_mute.place(x=1746, y=0)
    
    def is_songon(self):
        if self.songon.get() == True:
            text = "Mute Music"
            pos = 1746
        if self.songon.get() == False:
            pos = 1803
            text = "Muted!"
        return text, pos
    
    def update_streak(self, number):
        getattr(self, f"{self.return_game_id()}_streak_label").config(text=str(number))

    def score_scramble(self, original, goto):
        game_id = self.return_game_id()
        try:
            if original < goto:
                original += 1
                generated = random.randint(int(original), int(goto))
                if goto > int(getattr(self, f"{game_id}_hs_label").cget("text")):
                    getattr(self, f"{game_id}_hs_label").config(text=generated)
                getattr(self, f"{game_id}_score_label").config(text=generated)
                self.root.after(10, self.score_scramble, original, goto)
            elif original > goto:
                original -= 1
                generated = random.randint(int(goto), int(original))
                getattr(self, f"{game_id}_score_label").config(text=generated)
                self.root.after(10, lambda: self.score_scramble(original, goto))
            else:
                getattr(self, f"{game_id}_score_label").config(text=int(original))
                if int(getattr(self, f"{game_id}_hs_label").cget("text")) < goto:
                    getattr(self, f"{game_id}_hs_label").config(text=str(goto))
        except AttributeError:
            pass

    def update_score(self, number, mult, lose=None):
        game_id = self.return_game_id()

        if lose:
            newscore = int(number - (25*(number/100)+25))
            if newscore < 0:
                newscore = 0
        else:
            newscore = round((100 * mult) + number, 1)

        if self.score > self.round_hs:
            self.round_hs = int(self.score)
        
        original_pass = self.score
        self.score = newscore
        
        self.score_scramble(original_pass, newscore)
        if game_id != "review":
            self.highscore_check(game_id)
    
    def update_mult(self, number):
        game_id = self.return_game_id()
        getattr(self, f"{game_id}_mult_label").config(text=str(number) + "x")
    
    def lifepoint_sound(self):
        if self.score > 0:
                self.lifepoint_sfx.set_volume(1.0)
                self.lifepoint_sfx.play()

    def highscore_check(self, gamemode):
        #print(f"around line 1260: from self.highscore_check: here is 'gamemode', which should be identical to 'game_id': {gamemode}")
        game_list_hs = ["quizgame", "timed", "noun", "verb", "adj", "adv", "misc", "pnun"]
        key = game_list_hs.index(gamemode) if gamemode in game_list_hs else None
        if key is not None:
            highscore_key = self.hs_dict_keys[key]
        else:
            print("from self.highscore_check: key was 'None' when it shouldn't have been.")
            conn = sqlite3.connect("save.db")
            conn.close()
            self.root.destroy()
            raise
        if self.score > self.hs_dict[highscore_key]:
            self.hs_dict[highscore_key] = self.score
            self.save_highscores()
        
    def save_highscores(self):
        load_data = sqlite3.connect("save.db")
        load_cursor = load_data.cursor()

        update_query = "UPDATE HIGHSCORES SET quizgame_hs = ?, timed_hs = ?, nouns_hs = ?, verbs_hs = ?, adjectives_hs = ?, adverbs_hs = ?, misc_hs = ?, pronunciation_hs = ?"
        #print(f"from self.save_highscores: self.hs_dict.values(): {self.hs_dict.values()}")
        load_cursor.execute(update_query, tuple(self.hs_dict.values()))
        #print(str(tuple(self.hs_dict.values())))
        #load_cursor.execute("SELECT * FROM HIGHSCORES")
        #print(f"from self.save_highscores: all highscores: {load_cursor.fetchall()}")
        load_data.commit()
        #load_data.close()
        self.start_confetti()
        self.load_database_hs()

    def streak_change(self, state):
        game_id = self.return_game_id()
        if game_id != "review":
            conn = sqlite3.connect("save.db")
            cursor = conn.cursor()
            gamemode_streak_stat = self.match_gamemode_longest_streak()
            cursor.execute("SELECT value FROM stats WHERE stat_name = ?", (gamemode_streak_stat,))
            current_gamemode_longest_streak = cursor.fetchone()
        if state == "correct":
            self.streak += 1
            if self.streak > self.round_streak_hs:
                self.round_streak_hs += 1
            if self.streak > int(current_gamemode_longest_streak[0]):
                self.update_highest_streak()
            if game_id != "review":
                self.update_streak(self.streak)
                self.update_score(self.score, self.mult)
                self.highscore_check(game_id)
            self.lifepoint_sound()
            if self.mult == 10:
                pass
            else:
                self.mult = round(self.mult + 0.1, 1)
            if self.mult > self.mult_round_hs:
                self.mult_round_hs = self.mult
            if game_id != "review":
                gamemode_mult_stat = self.match_gamemode_highest_mult()
                cursor.execute("SELECT value FROM stats WHERE stat_name = ?", (gamemode_mult_stat,))
                current_gamemode_highest_mult = cursor.fetchone()
                if self.mult > float(current_gamemode_highest_mult[0]):
                    self.update_highest_mult()
                self.update_mult(self.mult)
            
        if state == "incorrect" and game_id != "review":
            self.streak = 0
            self.mult = 1
            self.update_streak(self.streak)
            self.update_score(self.score, self.mult, True)
            self.lifepoint_sound()
            self.update_mult(self.mult)

    def pull_words(self, reviewmode):
        game_id = self.return_game_id()
        #print(f"from self.pull_words: this is the game id:{game_id}")
        match game_id:
            case "noun":
                file_choice = "nouns.txt"
            case "adv":
                file_choice = "adverbs.txt"
            case "verb":
                file_choice = "verbs.txt"
            case "adj":
                file_choice = "adjectives.txt"
            case "misc":
                file_choice = "misc.txt"
            case _:
                file_choice = random.choice(list(self.words.keys()))
        #print(f"from self.pull_words: this is the file choice: {file_choice}")
        if not reviewmode:
            word_entry = random.choice(self.words[file_choice])
        else:
            #will need to write a program that fetches all of the words that need to be reviewed
            print(f"from self.pull_words: feature not yet implemented...")
            conn = sqlite3.connect("save.db")
            conn.close()
            self.root.destroy()
            raise
        return word_entry

    def next_question(self, reviewmode=False):
        game_id = self.return_game_id()
        word_entry = self.pull_words(reviewmode)

        try:
            self.current_word, self.current_pronunciation, self.current_meaning = word_entry 
            if game_id != "pnun":
                getattr(self, f"{game_id}_label_word").config(text=(self.current_word, "(", self.current_pronunciation, ")"))
            else:
                getattr(self, f"{game_id}_label_word").config(text=(self.current_word))

            conn = sqlite3.connect("save.db")
            cursor = conn.cursor()

            cursor.execute("UPDATE stats SET viewed_total = viewed_total + 1 WHERE stat_name = ?", (self.current_meaning,))

            conn.commit()
            #conn.close()

            getattr(self, f"{game_id}_entry_answer").focus_set()
            getattr(self, f"{game_id}_entry_answer").delete(0, tk.END)

        except ValueError:
            conn = sqlite3.connect("save.db")
            conn.close()
            self.root.destroy()
            print("Incorrect Word Formatting detected in .txt files.")
            raise

        except AttributeError:
            pass

    def check_answer(self, event=None):
        previous_score = self.score
        #print(f"from self.check_answer: here is previous score: {previous_score}")
        game_id = self.return_game_id()
        user_answer = getattr(self, f"{game_id}_entry_answer").get().strip().lower()
        if user_answer == self.current_meaning.lower():
            self.correct.set_volume(0.3)
            self.correct.play()
            self.correctly_guessed += 1
            self.streak_change("correct")
            if game_id != "review":
                conn = sqlite3.connect("save.db")
                cursor = conn.cursor()

                cursor.execute("UPDATE stats SET correct_guess = correct_guess + 1 WHERE stat_name = ?", (self.current_meaning,))
                cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = 'JPQuiz Stats - Words Guessed Correctly'")
                cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = 'JPQuiz Stats - Words Guessed Total'")
                conn.commit()
                #conn.close()

                if self.score > 0:
                    points_earned = int(self.score - previous_score)
                else:
                    points_earned = 0
                
                rounded_score = int(self.score)

                insert_into_results = f"Correct: {self.current_meaning} - {self.current_word} - {self.current_pronunciation} | Points Earned: {points_earned} | Score: {rounded_score}"
                self.words_viewed_list_global.append(insert_into_results)
            messagebox.showinfo("Result", "Correct!")
        else:
            self.incorrect.set_volume(0.3)
            self.incorrect.play()
            self.incorrectly_guessed += 1
            self.streak_change("incorrect")
            if game_id != "review":
                conn = sqlite3.connect("save.db")
                cursor = conn.cursor()

                cursor.execute("UPDATE stats SET incorrect_guess = incorrect_guess + 1 WHERE stat_name = ?", (self.current_meaning,))
                cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = 'JPQuiz Stats - Words Guessed Incorrectly'")
                cursor.execute("UPDATE stats SET value = value + 1 WHERE stat_name = 'JPQuiz Stats - Words Guessed Total'")
                conn.commit()
                #conn.close()

                if self.score > 0:
                    points_earned = int(self.score - previous_score)
                else:
                    points_earned = 0

                insert_into_results = (f"Incorrect: {self.current_meaning} - {self.current_word} - {self.current_pronunciation} | Points Lost: {points_earned} | Score: {self.score}")
                self.words_viewed_list_global.append(insert_into_results)
           
            messagebox.showerror("Result", f"Wrong. The correct answer is: {self.current_meaning}")
        

        self.next_question()

    def create_confetti(self):
        """Creates confetti on both sides of the screen with random properties."""
        
        CONFETTI_COUNT = 100  # Adjust for fullscreen effect
        for _ in range(CONFETTI_COUNT):
            side = random.choice(["left", "right"])
            if side == "left":
                x = random.randint(0, 50)  # Spawn from left edge
                dx = random.uniform(3, 7)  # Move right
            else:
                x = random.randint(1870, 1920)  # Spawn from right edge
                dx = random.uniform(-7, -3)  # Move left

            y = random.randint(50, 1000)  # Random height
            size = random.randint(5, 15)  # Bigger confetti for visibility
            dy = random.uniform(-3, 2)  # Slight movement
            color = random.choice(["red", "blue", "green", "yellow", "purple", "orange"])

            confetti = self.canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="")
            self.confetti_pieces.append([confetti, dx, dy])  # Store confetti data

    def update_animation(self):
        """Updates the position of confetti, applying gravity and removing it when out of bounds."""
        for confetti in self.confetti_pieces[:]:  # Iterate over a copy
            confetti_id, dx, dy = confetti

            dy += self.GRAVITY  # Apply gravity
            self.canvas.move(confetti_id, dx, dy)
            confetti[2] = dy  # Update dy in list

            coords = self.canvas.coords(confetti_id)
            if not coords:
                self.confetti_pieces.remove(confetti)
                continue

            x1, y1, x2, y2 = coords

            if y1 > 1080 or x2 < 0 or x1 > 1920:
                self.canvas.delete(confetti_id)
                self.confetti_pieces.remove(confetti)

        if self.confetti_pieces:  # Keep updating while confetti exists
            self.root.after(20, self.update_animation)

    def start_confetti(self):
        """Start the confetti animation."""
        self.cheering.set_volume(0.2)
        self.cheering.play()
        self.create_confetti()
        self.update_animation()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
