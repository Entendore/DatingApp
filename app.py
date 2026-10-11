import sys
import os
import json
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                               QProgressBar, QFrame, QMessageBox, QSizePolicy,
                               QRadioButton, QButtonGroup, QGridLayout, QLineEdit,
                               QTextEdit, QScrollArea, QComboBox, QInputDialog)
from PySide6.QtCore import (Qt, QTimer, Signal, QObject, QPoint, QEasingCurve, 
                            QPropertyAnimation, QSettings)
from PySide6.QtGui import (QFont, QColor, QCursor, 
                           QPixmap, QPainter, QPen, QBrush)

# ==========================================
# PERSISTENCE
# ==========================================
SAVE_FILE = "questmatch_save.json"

def save_game(state_dict):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(state_dict, f, indent=2)
    except Exception as e:
        print(f"Save failed: {e}")

def load_game():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None

# ==========================================
# GAME STATE
# ==========================================
class GameState(QObject):
    xp_changed = Signal(int)
    level_changed = Signal(int)
    gems_changed = Signal(int)
    quest_updated = Signal()
    level_up_triggered = Signal(int)
    achievement_unlocked = Signal(dict)
    streak_changed = Signal(int)
    inventory_changed = Signal()
    profile_changed = Signal()
    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.load_defaults()
        self.load_progress()

    def load_defaults(self):
        self.xp = 0
        self.level = 1
        self.gems = 100  # Now just a fun score counter - never spent!
        self.xp_to_next_level = 100
        self.streak = 3
        self.match_count = 0
        self.super_like_count = 0
        self.boost_active = False
        self.theme = "dark"
        self.sound_on = True
        self.last_login = ""
        
        # Profile
        self.player_name = "Adventurer"
        self.player_bio = "Looking for my player 2"
        self.player_avatar = "🧝‍♂️"
        self.equipped_border = "none"
        self.equipped_theme = "default"
        
        # Inventory - start with everything unlocked!
        self.inventory = {
            "avatars": ["🧝‍♂️", "🧙", "🧛", "🧚", "🦸", "🥷", "👑"],
            "borders": ["none", "gold", "rainbow", "fire"],
            "card_themes": ["default", "forest", "ocean", "galaxy"]
        }
        
        # Achievements
        self.achievements = [
            {"id": "first_match", "name": "First Blood", "desc": "Get your first match", "icon": "🩸", "unlocked": False},
            {"id": "level_5", "name": "Getting Serious", "desc": "Reach Level 5", "icon": "⭐", "unlocked": False},
            {"id": "super_5", "name": "Shooting Star", "desc": "Use 5 Super Likes", "icon": "🌠", "unlocked": False, "progress": 0, "target": 5},
            {"id": "streak_7", "name": "On Fire", "desc": "Maintain a 7-day streak", "icon": "🔥", "unlocked": False},
            {"id": "rich", "name": "Gem Collector", "desc": "Accumulate 500 gems", "icon": "💰", "unlocked": False}
        ]

        # Quests
        self.quests = [
            {"name": "Cast 5 Roses", "target": 5, "current": 0, "reward": 20, "done": False},
            {"name": "Find 1 Soulmate", "target": 1, "current": 0, "reward": 50, "done": False},
            {"name": "Play 1 Icebreaker", "target": 1, "current": 0, "reward": 30, "done": False}
        ]
        
        # Messages
        self.messages = {}
        
        # Leaderboard
        self.leaderboard = [
            {"name": "DragonSlayer99", "level": 42, "xp": 15420},
            {"name": "LoveWizard", "level": 38, "xp": 13200},
            {"name": "HeartHunter", "level": 31, "xp": 9800},
            {"name": "MysticRogue", "level": 27, "xp": 7500},
            {"name": "PaladinOfLove", "level": 22, "xp": 5100}
        ]

    def load_progress(self):
        data = load_game()
        if data:
            for key in ["xp", "level", "gems", "xp_to_next_level", "streak", 
                       "match_count", "super_like_count", "theme", "sound_on",
                       "last_login", "player_name", "player_bio", "player_avatar",
                       "equipped_border", "equipped_theme"]:
                if key in data:
                    setattr(self, key, data[key])
            if "inventory" in data:
                self.inventory = data["inventory"]
            if "achievements" in data:
                for saved_ach in data["achievements"]:
                    for ach in self.achievements:
                        if ach["id"] == saved_ach["id"]:
                            ach["unlocked"] = saved_ach["unlocked"]
                            if "progress" in saved_ach:
                                ach["progress"] = saved_ach["progress"]
            if "quests" in data:
                self.quests = data["quests"]
            if "messages" in data:
                self.messages = data["messages"]

    def save_progress(self):
        data = {
            "xp": self.xp, "level": self.level, "gems": self.gems,
            "xp_to_next_level": self.xp_to_next_level, "streak": self.streak,
            "match_count": self.match_count, "super_like_count": self.super_like_count,
            "theme": self.theme, "sound_on": self.sound_on, "last_login": self.last_login,
            "player_name": self.player_name, "player_bio": self.player_bio,
            "player_avatar": self.player_avatar, "equipped_border": self.equipped_border,
            "equipped_theme": self.equipped_theme, "inventory": self.inventory,
            "achievements": self.achievements, "quests": self.quests,
            "messages": self.messages
        }
        save_game(data)

    def add_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            self.gems += 20  # Gems as a fun score bonus
            self.level_changed.emit(self.level)
            self.level_up_triggered.emit(self.level)
            self.gems_changed.emit(self.gems)
            leveled = True
        self.xp_changed.emit(self.xp)
        self.check_achievements()
        if leveled or amount > 0:
            self.save_progress()

    def add_gems(self, amount):
        """Gems are now just a fun score - never spent!"""
        self.gems += amount
        self.gems_changed.emit(self.gems)
        self.check_achievements()
        self.save_progress()

    def update_quest(self, quest_index):
        if not self.quests[quest_index]["done"]:
            self.quests[quest_index]["current"] += 1
            if self.quests[quest_index]["current"] >= self.quests[quest_index]["target"]:
                self.quests[quest_index]["done"] = True
                self.add_gems(self.quests[quest_index]["reward"])
            self.quest_updated.emit()

    def check_achievements(self):
        for ach in self.achievements:
            if ach["unlocked"]: continue
            unlocked = False
            if ach["id"] == "first_match" and self.match_count >= 1: unlocked = True
            elif ach["id"] == "level_5" and self.level >= 5: unlocked = True
            elif ach["id"] == "super_5":
                ach["progress"] = self.super_like_count
                if ach["progress"] >= ach["target"]: unlocked = True
            elif ach["id"] == "streak_7" and self.streak >= 7: unlocked = True
            elif ach["id"] == "rich" and self.gems >= 500: unlocked = True
            
            if unlocked:
                ach["unlocked"] = True
                self.achievement_unlocked.emit(ach)
                self.save_progress()

    def claim_item(self, category, item_id):
        """Free claim - no cost!"""
        if item_id not in self.inventory[category]:
            self.inventory[category].append(item_id)
            self.inventory_changed.emit()
            self.save_progress()
            return True
        return False

# ==========================================
# MOCK DATA
# ==========================================
PROFILES = [
    {"name": "Luna", "age": 24, "bio": "Wizard in training. Loves potions and hiking.", "emoji": "🧙‍♀️"},
    {"name": "Kael", "age": 27, "bio": "Paladin seeking a healer. Will tank for you.", "emoji": "🛡️"},
    {"name": "Elara", "age": 22, "bio": "Bard looking for a duo partner. I bring the lute.", "emoji": "🎸"},
    {"name": "Thorne", "age": 29, "bio": "Rogue with a heart of gold. Stealth expert.", "emoji": "🗡️"},
    {"name": "Seraphina", "age": 25, "bio": "Cleric. I can resurrect you if you die on a date.", "emoji": "✨"},
    {"name": "Ragnar", "age": 31, "bio": "Barbarian. I lift. And I cook. Surprisingly.", "emoji": "🪓"},
    {"name": "Mira", "age": 26, "bio": "Ranger. My wolf approves of all my dates.", "emoji": "🏹"}
]

# Collection items - ALL FREE
COLLECTION_ITEMS = {
    "avatars": [
        {"id": "🧙", "name": "Wizard"},
        {"id": "🧛", "name": "Vampire"},
        {"id": "🧚", "name": "Fairy"},
        {"id": "🦸", "name": "Hero"},
        {"id": "🥷", "name": "Ninja"},
        {"id": "👑", "name": "Royalty"}
    ],
    "borders": [
        {"id": "gold", "name": "Gold Border"},
        {"id": "rainbow", "name": "Rainbow Border"},
        {"id": "fire", "name": "Fire Border"}
    ],
    "card_themes": [
        {"id": "forest", "name": "Forest Theme"},
        {"id": "ocean", "name": "Ocean Theme"},
        {"id": "galaxy", "name": "Galaxy Theme"}
    ]
}

AUTO_REPLIES = [
    "Haha that's so true! 😄",
    "Tell me more about that!",
    "I love that! What are you up to this weekend?",
    "Same here! We have so much in common 💫",
    "That's really cool. What's your favorite quest so far?",
    "Omg yes! 🙌",
    "You're funny 😂",
    "I'd love to go on an adventure with you sometime!"
]

# ==========================================
# UI COMPONENTS
# ==========================================
class FloatingText(QLabel):
    def __init__(self, text, parent_widget, color="#A6E3A1"):
        super().__init__(text, parent_widget)
        self.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold; background: transparent;")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.adjustSize()
        parent_rect = parent_widget.rect()
        self.move(parent_rect.center().x() - self.width()//2, parent_rect.center().y())
        self.raise_()
        
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(1500)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(self.pos().x(), self.pos().y() - 150))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()

class DraggableCard(QFrame):
    swiped = Signal(int)
    
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setObjectName("SwipeCard")
        self.profile = profile
        self.drag_start = None
        self.current_offset = QPoint(0, 0)
        self.setup_ui()
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.emoji_label = QLabel(self.profile["emoji"])
        self.emoji_label.setFont(QFont("Segoe UI Emoji", 72))
        self.emoji_label.setAlignment(Qt.AlignCenter)
        
        self.name_label = QLabel(f"{self.profile['name']}, {self.profile['age']}")
        self.name_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("color: #F5C2E7;")
        
        self.bio_label = QLabel(f'"{self.profile["bio"]}"')
        self.bio_label.setFont(QFont("Arial", 14))
        self.bio_label.setAlignment(Qt.AlignCenter)
        self.bio_label.setWordWrap(True)
        self.bio_label.setStyleSheet("color: #A6ADC8; font-style: italic;")

        self.like_indicator = QLabel("💚 LIKE")
        self.like_indicator.setFont(QFont("Arial", 32, QFont.Bold))
        self.like_indicator.setStyleSheet("color: #A6E3A1; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 10px;")
        self.like_indicator.setAlignment(Qt.AlignCenter)
        self.like_indicator.setVisible(False)
        
        self.pass_indicator = QLabel("❌ PASS")
        self.pass_indicator.setFont(QFont("Arial", 32, QFont.Bold))
        self.pass_indicator.setStyleSheet("color: #F38BA8; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 10px;")
        self.pass_indicator.setAlignment(Qt.AlignCenter)
        self.pass_indicator.setVisible(False)

        layout.addWidget(self.emoji_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.bio_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start = event.position().toPoint()
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        if self.drag_start is None:
            return
        delta = event.position().toPoint() - self.drag_start
        self.current_offset = delta
        rotation = delta.x() / 20
        self.setTransform(self.transform().fromTranslate(delta.x(), delta.y() / 3).rotate(rotation))
        
        if delta.x() > 50:
            self.like_indicator.setVisible(True)
            self.pass_indicator.setVisible(False)
        elif delta.x() < -50:
            self.pass_indicator.setVisible(True)
            self.like_indicator.setVisible(False)
        else:
            self.like_indicator.setVisible(False)
            self.pass_indicator.setVisible(False)

    def mouseReleaseEvent(self, event):
        if self.drag_start is None:
            return
        self.setCursor(QCursor(Qt.OpenHandCursor))
        
        threshold = 120
        if self.current_offset.x() > threshold:
            self.animate_swipe(1)
        elif self.current_offset.x() < -threshold:
            self.animate_swipe(-1)
        else:
            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(200)
            anim.setStartValue(self.pos())
            anim.setEndValue(QPoint(0, 0))
            anim.setEasingCurve(QEasingCurve.OutBack)
            anim.start()
            self.setTransform(self.transform().fromTranslate(0, 0).rotate(0))
            self.like_indicator.setVisible(False)
            self.pass_indicator.setVisible(False)
        
        self.drag_start = None
        self.current_offset = QPoint(0, 0)

    def animate_swipe(self, direction):
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setStartValue(self.pos())
        end_x = 800 if direction == 1 else -800
        anim.setEndValue(QPoint(end_x, self.pos().y()))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self.swiped.emit(direction))
        anim.start()

class MessageBubble(QFrame):
    def __init__(self, text, is_mine=False):
        super().__init__()
        self.setObjectName("MessageBubble")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setFont(QFont("Arial", 12))
        
        if is_mine:
            bubble.setStyleSheet("""
                background-color: #89B4FA;
                color: #1E1E2E;
                padding: 10px 15px;
                border-radius: 15px;
                border-bottom-right-radius: 5px;
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                background-color: #45475A;
                color: #CDD6F4;
                padding: 10px 15px;
                border-radius: 15px;
                border-bottom-left-radius: 5px;
            """)
            layout.addWidget(bubble)
            layout.addStretch()

# ==========================================
# SCREENS
# ==========================================
class HomeScreen(QWidget):
    def __init__(self, state: GameState):
        super().__init__()
        self.state = state
        self.setup_ui()
        self.state.quest_updated.connect(self.update_quests_ui)
        self.state.gems_changed.connect(self.update_header)
        self.state.streak_changed.connect(self.update_streak)

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # FLAT RATE BANNER
        banner = QLabel("✨ FLAT RATE • ALL FEATURES UNLOCKED ✨")
        banner.setObjectName("FlatRateBanner")
        banner.setAlignment(Qt.AlignCenter)
        layout.addWidget(banner)
        
        # Header
        self.header_layout = QHBoxLayout()
        self.streak_label = QLabel(f"🔥 {self.state.streak} Day Streak")
        self.streak_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.streak_label.setStyleSheet("color: #FAB387;")
        
        self.gem_label = QLabel(f"💎 {self.state.gems} (Score)")
        self.gem_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.gem_label.setStyleSheet("color: #89DCEB;")
        
        self.header_layout.addWidget(self.streak_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.gem_label)
        layout.addLayout(self.header_layout)

        # Level & XP
        level_frame = QFrame()
        level_frame.setObjectName("CardFrame")
        level_layout = QVBoxLayout(level_frame)
        
        self.level_label = QLabel(f"Level {self.state.level} {self.state.player_name}")
        self.level_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.level_label.setStyleSheet("color: #F9E2AF;")
        
        self.xp_bar = QProgressBar()
        self.xp_bar.setMaximum(self.state.xp_to_next_level)
        self.xp_bar.setValue(self.state.xp)
        self.xp_bar.setTextVisible(False)
        self.xp_bar.setFixedHeight(20)
        
        self.xp_text = QLabel(f"XP: {self.state.xp} / {self.state.xp_to_next_level}")
        self.xp_text.setAlignment(Qt.AlignCenter)

        level_layout.addWidget(self.level_label)
        level_layout.addWidget(self.xp_bar)
        level_layout.addWidget(self.xp_text)
        layout.addWidget(level_frame)

        # Daily Reward Button
        reward_btn = QPushButton("🎁 Claim Daily Reward")
        reward_btn.setObjectName("RewardBtn")
        reward_btn.clicked.connect(self.claim_reward)
        layout.addWidget(reward_btn)

        # Quests
        quest_title = QLabel("📜 Daily Quests")
        quest_title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(quest_title)

        self.quest_container = QVBoxLayout()
        layout.addLayout(self.quest_container)
        
        self.update_quests_ui()
        self.state.level_changed.connect(self.update_level_ui)
        self.state.xp_changed.connect(self.update_xp_ui)
        self.state.profile_changed.connect(self.update_level_ui)
        
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def claim_reward(self):
        from datetime import date
        today = date.today().isoformat()
        if self.state.last_login == today:
            FloatingText("Already claimed today!", self.window().centralWidget(), "#F38BA8")
            return
        
        rewards = [
            ("+20 XP", lambda: self.state.add_xp(20)),
            ("+50 💎", lambda: self.state.add_gems(50)),
            ("+100 XP", lambda: self.state.add_xp(100)),
            ("+30 💎", lambda: self.state.add_gems(30)),
            ("+200 XP", lambda: self.state.add_xp(200))
        ]
        
        prize_text, prize_func = random.choice(rewards)
        prize_func()
        self.state.last_login = today
        self.state.streak += 1
        self.state.streak_changed.emit(self.state.streak)
        self.state.save_progress()
        
        msg = QMessageBox(self)
        msg.setWindowTitle("🎁 Daily Reward!")
        msg.setText(f"Day {self.state.streak} Streak!\n\nYou received:\n{prize_text}")
        msg.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #F9E2AF; }")
        msg.exec()

    def update_header(self, gems): self.gem_label.setText(f"💎 {gems} (Score)")
    def update_streak(self, streak): self.streak_label.setText(f"🔥 {streak} Day Streak")
    def update_level_ui(self, *_): 
        self.level_label.setText(f"Level {self.state.level} {self.state.player_name}")
    def update_xp_ui(self, xp):
        self.xp_bar.setMaximum(self.state.xp_to_next_level)
        self.xp_bar.setValue(xp)
        self.xp_text.setText(f"XP: {xp} / {self.state.xp_to_next_level}")

    def update_quests_ui(self):
        while self.quest_container.count():
            child = self.quest_container.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        for i, quest in enumerate(self.state.quests):
            q_frame = QFrame()
            q_frame.setObjectName("CardFrame")
            q_layout = QHBoxLayout(q_frame)
            
            status = "✅" if quest["done"] else "⬜"
            text = f"{status} {quest['name']} ({quest['current']}/{quest['target']})"
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", 12))
            
            reward_lbl = QLabel(f"+{quest['reward']} 💎")
            reward_lbl.setStyleSheet("color: #89DCEB; font-weight: bold;")

            q_layout.addWidget(lbl)
            q_layout.addStretch()
            q_layout.addWidget(reward_lbl)
            self.quest_container.addWidget(q_frame)

class SwipeScreen(QWidget):
    def __init__(self, state: GameState, main_window):
        super().__init__()
        self.state = state
        self.main_window = main_window
        self.current_index = 0
        self.last_index = -1
        self.current_card = None
        self.is_animating = False
        
        self.boost_timer = QTimer(self)
        self.boost_timer.timeout.connect(self.update_boost)
        self.boost_time_left = 0
        
        self.setup_ui()
        self.show_next_profile()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.boost_bar = QProgressBar()
        self.boost_bar.setVisible(False)
        self.boost_bar.setTextVisible(False)
        self.boost_bar.setFixedHeight(10)
        self.boost_bar.setStyleSheet("QProgressBar::chunk { background-color: #F9E2AF; border-radius: 5px; }")
        layout.addWidget(self.boost_bar)

        self.card_container = QVBoxLayout()
        self.card_container.setAlignment(Qt.AlignCenter)
        layout.addLayout(self.card_container, stretch=1)

        # Power-up Buttons - ALL FREE NOW!
        power_layout = QHBoxLayout()
        self.btn_rewind = QPushButton("⏪ Rewind")
        self.btn_rewind.setObjectName("RewindBtn")
        self.btn_rewind.clicked.connect(self.rewind_action)
        
        self.btn_boost = QPushButton("🚀 Boost 15s")
        self.btn_boost.setObjectName("BoostBtn")
        self.btn_boost.clicked.connect(self.boost_action)
        
        power_layout.addWidget(self.btn_rewind)
        power_layout.addWidget(self.btn_boost)
        layout.addLayout(power_layout)

        # Main Action Buttons - NO GEM COSTS
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        self.btn_pass = QPushButton("❌ Pass")
        self.btn_pass.setObjectName("PassBtn")
        self.btn_pass.clicked.connect(lambda: self.swipe_action(-1))
        
        self.btn_like = QPushButton("🌹 Like (+10 XP)")
        self.btn_like.setObjectName("LikeBtn")
        self.btn_like.clicked.connect(lambda: self.swipe_action(1))
        
        self.btn_super = QPushButton("⭐ Super Like")
        self.btn_super.setObjectName("SuperBtn")
        self.btn_super.clicked.connect(self.super_action)

        btn_layout.addWidget(self.btn_pass)
        btn_layout.addWidget(self.btn_like)
        btn_layout.addWidget(self.btn_super)
        layout.addLayout(btn_layout)

    def show_next_profile(self):
        while self.card_container.count():
            child = self.card_container.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        if self.current_index < len(PROFILES):
            profile = PROFILES[self.current_index]
            self.current_card = DraggableCard(profile)
            self.current_card.swiped.connect(self.on_card_swiped)
            self.card_container.addWidget(self.current_card)
        else:
            lbl = QLabel("No more profiles nearby!\nCome back tomorrow.")
            lbl.setFont(QFont("Arial", 16))
            lbl.setAlignment(Qt.AlignCenter)
            self.card_container.addWidget(lbl)
            self.current_card = None

    def on_card_swiped(self, direction):
        self.swipe_action(direction)

    def swipe_action(self, direction):
        if not self.current_card or self.is_animating: return
        self.is_animating = True
        
        if hasattr(self.current_card, 'animate_swipe') and not self.current_card.drag_start:
            self.current_card.animate_swipe(direction)
            QTimer.singleShot(350, lambda: self.finish_swipe(direction))
        else:
            self.finish_swipe(direction)

    def finish_swipe(self, direction):
        self.last_index = self.current_index
        self.current_index += 1
        
        if direction == 1:
            self.state.add_xp(10)
            self.state.update_quest(0)
            FloatingText("+10 XP", self.main_window.centralWidget(), "#A6E3A1")
            
            match_chance = 1.0 if self.state.boost_active else 0.3
            if random.random() < match_chance:
                self.state.match_count += 1
                self.state.update_quest(1)
                self.state.add_xp(50)
                FloatingText("MATCH! +50 XP", self.main_window.centralWidget(), "#F5C2E7")
                if PROFILES[self.last_index]["name"] not in self.state.messages:
                    self.state.messages[PROFILES[self.last_index]["name"]] = []
                
        self.is_animating = False
        self.show_next_profile()

    def super_action(self):
        """Super Like - FREE! No gem cost."""
        if not self.current_card or self.is_animating: return
        self.state.super_like_count += 1
        self.state.add_xp(30)
        FloatingText("+30 XP", self.main_window.centralWidget(), "#89B4FA")
        
        self.state.match_count += 1
        self.state.update_quest(1)
        self.state.add_xp(50)
        FloatingText("SUPER MATCH! +50 XP", self.main_window.centralWidget(), "#F5C2E7")
        
        if PROFILES[self.current_index]["name"] not in self.state.messages:
            self.state.messages[PROFILES[self.current_index]["name"]] = []
        
        self.last_index = self.current_index
        self.current_index += 1
        self.show_next_profile()

    def rewind_action(self):
        """Rewind - FREE! No gem cost."""
        if self.last_index >= 0:
            self.current_index = self.last_index
            self.last_index = -1
            self.show_next_profile()
            FloatingText("Rewound!", self.main_window.centralWidget(), "#89DCEB")
        else:
            FloatingText("Nothing to rewind!", self.main_window.centralWidget(), "#F38BA8")

    def boost_action(self):
        """Boost - FREE! No gem cost."""
        if self.state.boost_active:
            FloatingText("Boost already active!", self.main_window.centralWidget(), "#F9E2AF")
            return
        self.state.boost_active = True
        self.boost_time_left = 15
        self.boost_timer.start(1000)
        self.boost_bar.setVisible(True)
        self.boost_bar.setMaximum(15)
        self.boost_bar.setValue(15)
        FloatingText("BOOST ACTIVATED!", self.main_window.centralWidget(), "#F9E2AF")

    def update_boost(self):
        self.boost_time_left -= 1
        self.boost_bar.setValue(self.boost_time_left)
        if self.boost_time_left <= 0:
            self.state.boost_active = False
            self.boost_timer.stop()
            self.boost_bar.setVisible(False)
            FloatingText("Boost Ended", self.main_window.centralWidget(), "#6C7086")

class ChatScreen(QWidget):
    def __init__(self, state: GameState):
        super().__init__()
        self.state = state
        self.current_match = None
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.match_list_widget = self.create_match_list()
        self.chat_widget = self.create_chat_view()
        
        self.main_layout.addWidget(self.match_list_widget)
        self.refresh_matches()

    def create_match_list(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("💬 Your Matches")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)

        self.matches_container = QVBoxLayout()
        layout.addLayout(self.matches_container)
        layout.addStretch()
        return widget

    def create_chat_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QFrame()
        header.setObjectName("CardFrame")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("BackBtn")
        self.back_btn.clicked.connect(self.show_match_list)
        
        self.match_name_label = QLabel("")
        self.match_name_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        h_layout.addWidget(self.back_btn)
        h_layout.addWidget(self.match_name_label)
        h_layout.addStretch()
        layout.addWidget(header)
        
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.addStretch()
        self.messages_scroll.setWidget(self.messages_container)
        layout.addWidget(self.messages_scroll, stretch=1)
        
        input_frame = QFrame()
        input_frame.setObjectName("CardFrame")
        input_frame.setFixedHeight(70)
        i_layout = QHBoxLayout(input_frame)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setFont(QFont("Arial", 12))
        self.message_input.returnPressed.connect(self.send_message)
        
        send_btn = QPushButton("Send")
        send_btn.setObjectName("LikeBtn")
        send_btn.clicked.connect(self.send_message)
        
        i_layout.addWidget(self.message_input)
        i_layout.addWidget(send_btn)
        layout.addWidget(input_frame)
        
        return widget

    def refresh_matches(self):
        while self.matches_container.count():
            child = self.matches_container.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if not self.state.messages:
            lbl = QLabel("No matches yet!\nStart swiping to find your soulmate.")
            lbl.setFont(QFont("Arial", 14))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #6C7086;")
            self.matches_container.addWidget(lbl)
            return

        for match_name in self.state.messages.keys():
            emoji = "💫"
            for p in PROFILES:
                if p["name"] == match_name:
                    emoji = p["emoji"]
                    break
            
            frame = QFrame()
            frame.setObjectName("CardFrame")
            f_layout = QHBoxLayout(frame)
            
            lbl = QLabel(f"{emoji} {match_name}")
            lbl.setFont(QFont("Arial", 14))
            
            msg_count = len(self.state.messages[match_name])
            count_lbl = QLabel(f"{msg_count} messages")
            count_lbl.setStyleSheet("color: #6C7086;")
            
            open_btn = QPushButton("Open 💬")
            open_btn.setObjectName("GameBtn")
            open_btn.clicked.connect(lambda checked, n=match_name: self.open_chat(n))

            f_layout.addWidget(lbl)
            f_layout.addStretch()
            f_layout.addWidget(count_lbl)
            f_layout.addWidget(open_btn)
            self.matches_container.addWidget(frame)

    def open_chat(self, match_name):
        self.current_match = match_name
        self.match_name_label.setText(f"💬 {match_name}")
        self.match_list_widget.hide()
        self.chat_widget.show()
        self.main_layout.addWidget(self.chat_widget)
        self.load_messages()

    def show_match_list(self):
        self.chat_widget.hide()
        self.main_layout.removeWidget(self.chat_widget)
        self.match_list_widget.show()
        self.refresh_matches()

    def load_messages(self):
        while self.messages_layout.count() > 1:
            child = self.messages_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        for msg in self.state.messages.get(self.current_match, []):
            bubble = MessageBubble(msg["text"], msg["is_mine"])
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        QTimer.singleShot(50, lambda: self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()))

    def send_message(self):
        text = self.message_input.text().strip()
        if not text or not self.current_match:
            return
        
        if self.current_match not in self.state.messages:
            self.state.messages[self.current_match] = []
        
        self.state.messages[self.current_match].append({"text": text, "is_mine": True})
        self.message_input.clear()
        
        bubble = MessageBubble(text, True)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        QTimer.singleShot(1500, self.auto_reply)
        self.state.save_progress()
        
        QTimer.singleShot(50, lambda: self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()))

    def auto_reply(self):
        if not self.current_match:
            return
        reply = random.choice(AUTO_REPLIES)
        self.state.messages[self.current_match].append({"text": reply, "is_mine": False})
        
        bubble = MessageBubble(reply, False)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.state.save_progress()
        
        QTimer.singleShot(50, lambda: self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()))

class CollectionScreen(QWidget):
    """Renamed from ShopScreen - ALL ITEMS FREE!"""
    def __init__(self, state: GameState):
        super().__init__()
        self.state = state
        self.setup_ui()
        self.state.inventory_changed.connect(self.refresh_collection)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🎁 Your Collection")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        
        subtitle = QLabel("All items free!")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #A6E3A1; font-style: italic;")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Tabs
        tab_layout = QHBoxLayout()
        self.tab_avatars = QPushButton("👤 Avatars")
        self.tab_borders = QPushButton("🖼️ Borders")
        self.tab_themes = QPushButton("🎨 Themes")
        
        for btn in [self.tab_avatars, self.tab_borders, self.tab_themes]:
            btn.setObjectName("TabBtn")
            btn.setCheckable(True)
        self.tab_avatars.setChecked(True)
        
        self.tab_avatars.clicked.connect(lambda: self.show_category("avatars"))
        self.tab_borders.clicked.connect(lambda: self.show_category("borders"))
        self.tab_themes.clicked.connect(lambda: self.show_category("card_themes"))
        
        tab_layout.addWidget(self.tab_avatars)
        tab_layout.addWidget(self.tab_borders)
        tab_layout.addWidget(self.tab_themes)
        layout.addLayout(tab_layout)

        # Items container
        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.items_widget = QWidget()
        self.items_layout = QGridLayout(self.items_widget)
        self.items_scroll.setWidget(self.items_widget)
        layout.addWidget(self.items_scroll, stretch=1)
        
        self.current_category = "avatars"
        self.refresh_collection()

    def show_category(self, category):
        self.current_category = category
        for btn in [self.tab_avatars, self.tab_borders, self.tab_themes]:
            btn.setChecked(False)
        if category == "avatars": self.tab_avatars.setChecked(True)
        elif category == "borders": self.tab_borders.setChecked(True)
        else: self.tab_themes.setChecked(True)
        self.refresh_collection()

    def refresh_collection(self):
        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        items = COLLECTION_ITEMS.get(self.current_category, [])
        for i, item in enumerate(items):
            owned = item["id"] in self.state.inventory[self.current_category]
            frame = self.create_item_card(item, owned)
            row, col = divmod(i, 2)
            self.items_layout.addWidget(frame, row, col)

    def create_item_card(self, item, owned):
        frame = QFrame()
        frame.setObjectName("CardFrame")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        
        preview = QLabel(item["id"])
        preview.setFont(QFont("Segoe UI Emoji", 36))
        preview.setAlignment(Qt.AlignCenter)
        
        name = QLabel(item["name"])
        name.setFont(QFont("Arial", 12, QFont.Bold))
        name.setAlignment(Qt.AlignCenter)
        
        btn = QPushButton("Claimed ✓" if owned else "✨ Claim Free")
        btn.setObjectName("OwnedBtn" if owned else "ClaimBtn")
        btn.setEnabled(not owned)
        if not owned:
            btn.clicked.connect(lambda: self.claim_item(item))
        
        layout.addWidget(preview)
        layout.addWidget(name)
        layout.addWidget(btn)
        return frame

    def claim_item(self, item):
        """Free claim - no cost!"""
        self.state.claim_item(self.current_category, item["id"])
        FloatingText(f"Got {item['name']}!", self.window().centralWidget(), "#A6E3A1")

class ProfileScreen(QWidget):
    def __init__(self, state: GameState):
        super().__init__()
        self.state = state
        self.setup_ui()
        self.state.achievement_unlocked.connect(self.show_achievement_popup)
        self.state.profile_changed.connect(self.refresh_profile)
        self.state.inventory_changed.connect(self.refresh_profile)

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)

        self.avatar_label = QLabel(self.state.player_avatar)
        self.avatar_label.setFont(QFont("Segoe UI Emoji", 80))
        self.avatar_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.avatar_label)

        self.name_label = QLabel(self.state.player_name)
        self.name_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_label)

        self.bio_label = QLabel(f'"{self.state.player_bio}"')
        self.bio_label.setFont(QFont("Arial", 12))
        self.bio_label.setAlignment(Qt.AlignCenter)
        self.bio_label.setWordWrap(True)
        self.bio_label.setStyleSheet("color: #A6ADC8; font-style: italic;")
        layout.addWidget(self.bio_label)

        edit_btn = QPushButton("✏️ Edit Profile")
        edit_btn.setObjectName("GameBtn")
        edit_btn.clicked.connect(self.edit_profile)
        layout.addWidget(edit_btn)

        stats_frame = QFrame()
        stats_frame.setObjectName("CardFrame")
        stats_layout = QVBoxLayout(stats_frame)
        
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Arial", 13))
        self.stats_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.stats_label)
        layout.addWidget(stats_frame)

        ach_title = QLabel("🏆 Achievements")
        ach_title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(ach_title)

        self.ach_grid = QGridLayout()
        layout.addLayout(self.ach_grid)
        
        self.refresh_profile()
        
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def edit_profile(self):
        new_name, ok = QInputDialog.getText(self, "Edit Name", "Your name:", text=self.state.player_name)
        if ok and new_name.strip():
            self.state.player_name = new_name.strip()
        
        new_bio, ok = QInputDialog.getText(self, "Edit Bio", "Your bio:", text=self.state.player_bio)
        if ok and new_bio.strip():
            self.state.player_bio = new_bio.strip()
        
        if len(self.state.inventory["avatars"]) > 1:
            avatar, ok = QInputDialog.getItem(self, "Choose Avatar", "Avatar:", 
                                              self.state.inventory["avatars"], 0, False)
            if ok:
                self.state.player_avatar = avatar
        
        self.state.profile_changed.emit()
        self.state.save_progress()

    def refresh_profile(self):
        self.avatar_label.setText(self.state.player_avatar)
        self.name_label.setText(self.state.player_name)
        self.bio_label.setText(f'"{self.state.player_bio}"')
        
        self.stats_label.setText(
            f"Level: {self.state.level} | 💎 Score: {self.state.gems}\n"
            f"Matches: {self.state.match_count} | Streak: 🔥 {self.state.streak}\n"
            f"Title: {self.get_title()}"
        )
        
        while self.ach_grid.count():
            child = self.ach_grid.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        for i, ach in enumerate(self.state.achievements):
            frame = QFrame()
            frame.setObjectName("AchFrame")
            if not ach["unlocked"]: 
                frame.setStyleSheet("background-color: #313244; opacity: 0.5;")
            f_layout = QVBoxLayout(frame)
            f_layout.setAlignment(Qt.AlignCenter)
            
            icon = QLabel(ach["icon"])
            icon.setFont(QFont("Segoe UI Emoji", 24))
            icon.setAlignment(Qt.AlignCenter)
            
            name = QLabel(ach["name"])
            name.setFont(QFont("Arial", 9, QFont.Bold))
            name.setAlignment(Qt.AlignCenter)
            name.setWordWrap(True)
            
            f_layout.addWidget(icon)
            f_layout.addWidget(name)
            
            row, col = divmod(i, 3)
            self.ach_grid.addWidget(frame, row, col)

    def get_title(self):
        if self.state.level >= 10: return "Grandmaster of Love"
        if self.state.level >= 5: return "Heart Hunter"
        return "Novice Dater"

    def show_achievement_popup(self, ach):
        msg = QMessageBox(self)
        msg.setWindowTitle("🏆 Achievement Unlocked!")
        msg.setText(f"{ach['icon']} {ach['name']}\n\n{ach['desc']}")
        msg.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #F9E2AF; }")
        msg.exec()

class LeaderboardScreen(QWidget):
    def __init__(self, state: GameState):
        super().__init__()
        self.state = state
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("🏆 Global Leaderboard")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        all_players = self.state.leaderboard.copy()
        all_players.append({
            "name": f"{self.state.player_name} (You)",
            "level": self.state.level,
            "xp": self.state.xp + (self.state.level - 1) * 1000,
            "is_you": True
        })
        all_players.sort(key=lambda x: x["xp"], reverse=True)
        
        for rank, player in enumerate(all_players, 1):
            frame = QFrame()
            if player.get("is_you"):
                frame.setObjectName("YouFrame")
            else:
                frame.setObjectName("CardFrame")
            
            f_layout = QHBoxLayout(frame)
            
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            rank_lbl = QLabel(medal)
            rank_lbl.setFont(QFont("Arial", 18))
            rank_lbl.setFixedWidth(50)
            
            name_lbl = QLabel(player["name"])
            name_lbl.setFont(QFont("Arial", 14, QFont.Bold))
            
            stats_lbl = QLabel(f"Lvl {player['level']} | {player['xp']} XP")
            stats_lbl.setStyleSheet("color: #89DCEB;")
            
            f_layout.addWidget(rank_lbl)
            f_layout.addWidget(name_lbl)
            f_layout.addStretch()
            f_layout.addWidget(stats_lbl)
            content_layout.addWidget(frame)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

class SettingsScreen(QWidget):
    def __init__(self, state: GameState, main_window):
        super().__init__()
        self.state = state
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("⚙️ Settings")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        layout.addWidget(title)

        # FLAT RATE INFO BOX
        info_frame = QFrame()
        info_frame.setObjectName("FlatRateFrame")
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("✨ Flat Rate Edition ✨")
        info_title.setFont(QFont("Arial", 16, QFont.Bold))
        info_title.setAlignment(Qt.AlignCenter)
        info_title.setStyleSheet("color: #A6E3A1;")
        
        info_items = [
            "✓ All features unlocked",
            "✓ No premium tiers",
            "✓ No hidden costs",
            "✓ No subscriptions",
            "✓ Everything is free forever"
        ]
        
        info_layout.addWidget(info_title)
        for item in info_items:
            lbl = QLabel(item)
            lbl.setFont(QFont("Arial", 12))
            lbl.setAlignment(Qt.AlignCenter)
            info_layout.addWidget(lbl)
        layout.addWidget(info_frame)

        # Theme
        theme_frame = QFrame()
        theme_frame.setObjectName("CardFrame")
        t_layout = QHBoxLayout(theme_frame)
        t_layout.addWidget(QLabel("🎨 Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark (Catppuccin)", "Light", "Ocean"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        t_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_frame)

        # Sound
        sound_frame = QFrame()
        sound_frame.setObjectName("CardFrame")
        s_layout = QHBoxLayout(sound_frame)
        s_layout.addWidget(QLabel("🔊 Sound Effects"))
        self.sound_btn = QPushButton("ON" if self.state.sound_on else "OFF")
        self.sound_btn.setObjectName("LikeBtn" if self.state.sound_on else "PassBtn")
        self.sound_btn.setFixedWidth(80)
        self.sound_btn.clicked.connect(self.toggle_sound)
        s_layout.addWidget(self.sound_btn)
        layout.addWidget(sound_frame)

        # Reset
        reset_btn = QPushButton("🗑️ Reset All Progress")
        reset_btn.setObjectName("PassBtn")
        reset_btn.clicked.connect(self.reset_progress)
        layout.addWidget(reset_btn)

        # About
        about_frame = QFrame()
        about_frame.setObjectName("CardFrame")
        a_layout = QVBoxLayout(about_frame)
        a_layout.addWidget(QLabel("QuestMatch v4.0 - Flat Rate Edition"))
        a_layout.addWidget(QLabel("A gamified dating prototype"))
        a_layout.addWidget(QLabel("Built with PySide6"))
        a_layout.addWidget(QLabel(""))
        about_lbl = QLabel("One price. All features. Forever. 💚")
        about_lbl.setStyleSheet("color: #A6E3A1; font-weight: bold; font-style: italic;")
        about_lbl.setAlignment(Qt.AlignCenter)
        a_layout.addWidget(about_lbl)
        layout.addWidget(about_frame)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def change_theme(self, theme_name):
        theme_map = {
            "Dark (Catppuccin)": "dark",
            "Light": "light",
            "Ocean": "ocean"
        }
        self.state.theme = theme_map.get(theme_name, "dark")
        self.state.theme_changed.emit(self.state.theme)
        self.state.save_progress()

    def toggle_sound(self):
        self.state.sound_on = not self.state.sound_on
        self.sound_btn.setText("ON" if self.state.sound_on else "OFF")
        self.sound_btn.setObjectName("LikeBtn" if self.state.sound_on else "PassBtn")
        self.sound_btn.style().unpolish(self.sound_btn)
        self.sound_btn.style().polish(self.sound_btn)
        self.state.save_progress()

    def reset_progress(self):
        reply = QMessageBox.question(self, "Reset Progress", 
                                     "Are you sure? This will delete ALL your progress!",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            QMessageBox.information(self, "Reset", "Progress reset. Restart the app.")

# ==========================================
# MAIN WINDOW
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuestMatch v4 - Flat Rate Edition")
        self.resize(450, 900)
        
        self.state = GameState()
        self.state.level_up_triggered.connect(self.show_level_up)
        self.state.theme_changed.connect(self.apply_theme)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(HomeScreen(self.state))
        self.stack.addWidget(SwipeScreen(self.state, self))
        self.stack.addWidget(ChatScreen(self.state))
        self.stack.addWidget(CollectionScreen(self.state))  # Renamed from Shop
        self.stack.addWidget(ProfileScreen(self.state))
        self.stack.addWidget(LeaderboardScreen(self.state))
        self.stack.addWidget(SettingsScreen(self.state, self))
        main_layout.addWidget(self.stack, stretch=1)

        nav_bar = QFrame()
        nav_bar.setObjectName("NavBar")
        nav_bar.setFixedHeight(70)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(5, 10, 5, 10)

        buttons = [
            ("🏠", 0), ("🔥", 1), ("💬", 2), ("🎁", 3),
            ("👤", 4), ("🏆", 5), ("⚙️", 6)
        ]

        for text, index in buttons:
            btn = QPushButton(text)
            btn.setObjectName("NavBtn")
            btn.setCheckable(True)
            btn.setFont(QFont("Segoe UI Emoji", 16))
            btn.clicked.connect(lambda checked, i=index: self.stack.setCurrentIndex(i))
            nav_layout.addWidget(btn)
            if index == 0: btn.setChecked(True)

        main_layout.addWidget(nav_bar)
        
        self.apply_theme(self.state.theme)

    def apply_theme(self, theme):
        if theme == "dark":
            self.setStyleSheet(DARK_THEME)
        elif theme == "light":
            self.setStyleSheet(LIGHT_THEME)
        elif theme == "ocean":
            self.setStyleSheet(OCEAN_THEME)

    def show_level_up(self, level):
        msg = QMessageBox(self)
        msg.setWindowTitle("🎉 LEVEL UP! 🎉")
        msg.setText(f"Congratulations!\nYou reached Level {level}!\n\n+20 💎 Score bonus!")
        msg.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #F9E2AF; }")
        msg.exec()

# ==========================================
# THEMES
# ==========================================
DARK_THEME = """
    QMainWindow, QWidget { background-color: #1E1E2E; color: #CDD6F4; font-family: 'Segoe UI', Arial, sans-serif; }
    #CardFrame { background-color: #313244; border-radius: 15px; padding: 15px; margin: 5px 0px; }
    #SwipeCard { background-color: #45475A; border-radius: 20px; border: 2px solid #585B70; padding: 20px; min-height: 350px; }
    #AchFrame { background-color: #313244; border-radius: 10px; padding: 10px; margin: 5px; min-width: 80px; min-height: 80px; }
    #YouFrame { background-color: #45475A; border: 2px solid #F9E2AF; border-radius: 15px; padding: 15px; margin: 5px 0px; }
    #FlatRateBanner { 
        background-color: #A6E3A1; color: #1E1E2E; padding: 12px; 
        border-radius: 10px; font-weight: bold; font-size: 14px; 
    }
    #FlatRateFrame { 
        background-color: #313244; border: 2px solid #A6E3A1; 
        border-radius: 15px; padding: 20px; margin: 10px 0px; 
    }
    QProgressBar { border: 2px solid #585B70; border-radius: 10px; background-color: #1E1E2E; }
    QProgressBar::chunk { background-color: #A6E3A1; border-radius: 8px; }
    QPushButton { border: none; border-radius: 12px; padding: 12px 15px; font-size: 13px; font-weight: bold; color: #1E1E2E; }
    #PassBtn { background-color: #F38BA8; }
    #LikeBtn { background-color: #A6E3A1; }
    #SuperBtn { background-color: #89B4FA; }
    #RewindBtn { background-color: #FAB387; }
    #BoostBtn { background-color: #F9E2AF; }
    #GameBtn { background-color: #CBA6F7; }
    #RewardBtn { background-color: #F9E2AF; font-size: 16px; padding: 15px; }
    #ClaimBtn { background-color: #A6E3A1; }
    #OwnedBtn { background-color: #6C7086; }
    #TabBtn { background-color: #45475A; color: #CDD6F4; }
    #TabBtn:checked { background-color: #89B4FA; color: #1E1E2E; }
    #BackBtn { background-color: #45475A; color: #CDD6F4; padding: 8px 15px; }
    QLineEdit { background-color: #313244; color: #CDD6F4; border: 2px solid #585B70; border-radius: 10px; padding: 10px; font-size: 14px; }
    QComboBox { background-color: #313244; color: #CDD6F4; border: 2px solid #585B70; border-radius: 10px; padding: 8px; }
    QScrollArea { background-color: transparent; }
    #NavBar { background-color: #181825; border-top: 2px solid #313244; }
    #NavBtn { background-color: transparent; color: #6C7086; font-size: 16px; padding: 5px; border-radius: 8px; }
    #NavBtn:checked { color: #CDD6F4; background-color: #313244; }
"""

LIGHT_THEME = """
    QMainWindow, QWidget { background-color: #F5F5F5; color: #333333; font-family: 'Segoe UI', Arial, sans-serif; }
    #CardFrame { background-color: #FFFFFF; border-radius: 15px; padding: 15px; margin: 5px 0px; border: 1px solid #E0E0E0; }
    #SwipeCard { background-color: #FFFFFF; border-radius: 20px; border: 2px solid #E0E0E0; padding: 20px; min-height: 350px; }
    #AchFrame { background-color: #FFFFFF; border-radius: 10px; padding: 10px; margin: 5px; border: 1px solid #E0E0E0; }
    #YouFrame { background-color: #FFF9E6; border: 2px solid #F9E2AF; border-radius: 15px; padding: 15px; margin: 5px 0px; }
    #FlatRateBanner { 
        background-color: #4CAF50; color: white; padding: 12px; 
        border-radius: 10px; font-weight: bold; font-size: 14px; 
    }
    #FlatRateFrame { 
        background-color: #E8F5E9; border: 2px solid #4CAF50; 
        border-radius: 15px; padding: 20px; margin: 10px 0px; 
    }
    QProgressBar { border: 2px solid #E0E0E0; border-radius: 10px; background-color: #F5F5F5; }
    QProgressBar::chunk { background-color: #4CAF50; border-radius: 8px; }
    QPushButton { border: none; border-radius: 12px; padding: 12px 15px; font-size: 13px; font-weight: bold; color: white; }
    #PassBtn { background-color: #E57373; }
    #LikeBtn { background-color: #4CAF50; }
    #SuperBtn { background-color: #64B5F6; }
    #RewindBtn { background-color: #FFB74D; }
    #BoostBtn { background-color: #FFD54F; color: #333; }
    #GameBtn { background-color: #BA68C8; }
    #RewardBtn { background-color: #FFD54F; color: #333; font-size: 16px; padding: 15px; }
    #ClaimBtn { background-color: #4CAF50; }
    #OwnedBtn { background-color: #BDBDBD; }
    #TabBtn { background-color: #E0E0E0; color: #333; }
    #TabBtn:checked { background-color: #64B5F6; color: white; }
    #BackBtn { background-color: #E0E0E0; color: #333; padding: 8px 15px; }
    QLineEdit { background-color: #FFFFFF; color: #333; border: 2px solid #E0E0E0; border-radius: 10px; padding: 10px; }
    QComboBox { background-color: #FFFFFF; color: #333; border: 2px solid #E0E0E0; border-radius: 10px; padding: 8px; }
    #NavBar { background-color: #FFFFFF; border-top: 2px solid #E0E0E0; }
    #NavBtn { background-color: transparent; color: #999; font-size: 16px; padding: 5px; border-radius: 8px; }
    #NavBtn:checked { color: #333; background-color: #E0E0E0; }
"""

OCEAN_THEME = """
    QMainWindow, QWidget { background-color: #0A1929; color: #B2EBF2; font-family: 'Segoe UI', Arial, sans-serif; }
    #CardFrame { background-color: #132F4C; border-radius: 15px; padding: 15px; margin: 5px 0px; }
    #SwipeCard { background-color: #173A5E; border-radius: 20px; border: 2px solid #2E5A88; padding: 20px; min-height: 350px; }
    #AchFrame { background-color: #132F4C; border-radius: 10px; padding: 10px; margin: 5px; }
    #YouFrame { background-color: #173A5E; border: 2px solid #FFD54F; border-radius: 15px; padding: 15px; margin: 5px 0px; }
    #FlatRateBanner { 
        background-color: #4DD0E1; color: #0A1929; padding: 12px; 
        border-radius: 10px; font-weight: bold; font-size: 14px; 
    }
    #FlatRateFrame { 
        background-color: #173A5E; border: 2px solid #4DD0E1; 
        border-radius: 15px; padding: 20px; margin: 10px 0px; 
    }
    QProgressBar { border: 2px solid #2E5A88; border-radius: 10px; background-color: #0A1929; }
    QProgressBar::chunk { background-color: #4DD0E1; border-radius: 8px; }
    QPushButton { border: none; border-radius: 12px; padding: 12px 15px; font-size: 13px; font-weight: bold; color: #0A1929; }
    #PassBtn { background-color: #EF5350; color: white; }
    #LikeBtn { background-color: #4DD0E1; }
    #SuperBtn { background-color: #64B5F6; }
    #RewindBtn { background-color: #FFB74D; }
    #BoostBtn { background-color: #FFD54F; }
    #GameBtn { background-color: #BA68C8; color: white; }
    #RewardBtn { background-color: #FFD54F; font-size: 16px; padding: 15px; }
    #ClaimBtn { background-color: #4DD0E1; }
    #OwnedBtn { background-color: #546E7A; color: white; }
    #TabBtn { background-color: #173A5E; color: #B2EBF2; }
    #TabBtn:checked { background-color: #4DD0E1; color: #0A1929; }
    #BackBtn { background-color: #173A5E; color: #B2EBF2; padding: 8px 15px; }
    QLineEdit { background-color: #132F4C; color: #B2EBF2; border: 2px solid #2E5A88; border-radius: 10px; padding: 10px; }
    QComboBox { background-color: #132F4C; color: #B2EBF2; border: 2px solid #2E5A88; border-radius: 10px; padding: 8px; }
    #NavBar { background-color: #0A1929; border-top: 2px solid #132F4C; }
    #NavBtn { background-color: transparent; color: #546E7A; font-size: 16px; padding: 5px; border-radius: 8px; }
    #NavBtn:checked { color: #B2EBF2; background-color: #132F4C; }
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())