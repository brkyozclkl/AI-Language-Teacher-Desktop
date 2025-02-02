from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QProgressBar, QHBoxLayout,
                               QComboBox, QCheckBox, QSlider, QDialog, QMessageBox, QListWidget, QTabWidget, QGroupBox, QLineEdit, QRadioButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import speech_recognition as sr
from gtts import gTTS
from googletrans import Translator
import os
import tempfile
import pygame
import time
import json
import random
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl
import webbrowser

class SpeechRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio, language='en-US')
                self.finished.emit(text)
            except Exception as e:
                self.error.emit(str(e))

class SpeechTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.mixer.init()
        self.temp_audio_file = None
        self.current_score = 0
        self.total_attempts = 0
        self.translator = Translator()
        self.speech_rate = 1.0  # Normal hız
        self.favorite_sentences = []
        self.category_stats = {}
        self.daily_stats = {}
        self.practice_start_time = time.time()  # Başlangıç zamanını ayarla
        
        # Yeni özellikler
        self.current_mode = "practice"  # practice, detailed, exam, review
        # Video kütüphanesi - Online kaynaklar
        self.video_library = {
            "Greetings": {
                "title": "Common Greetings",
                "url": "https://www.youtube.com/watch?v=LBmByyFkRlo",  # Örnek bir YouTube videosu
                "description": "Learn common English greetings and introductions",
                "type": "youtube"
            },
            "Business Meeting": {
                "title": "Business Meeting Phrases",
                "url": "https://www.youtube.com/watch?v=aDh3090PDHE",  # Örnek bir YouTube videosu
                "description": "Essential phrases for business meetings",
                "type": "youtube"
            },
            "Daily Conversations": {
                "title": "Everyday Conversations",
                "url": "https://www.youtube.com/watch?v=ZY1fDMwwYxk",  # Örnek bir YouTube videosu
                "description": "Practice everyday conversation scenarios",
                "type": "youtube"
            },
            "Job Interview": {
                "title": "Job Interview Practice",
                "url": "https://www.youtube.com/watch?v=HG68Ymazo18",  # Örnek bir YouTube videosu
                "description": "Common job interview questions and responses",
                "type": "youtube"
            }
        }
        self.audio_library = {
            "Pronunciation": {
                "title": "Basic Pronunciation",
                "files": {
                    "th_sound.mp3": "Practice 'th' sound",
                    "r_sound.mp3": "Practice 'r' sound",
                    "ed_endings.mp3": "Practice '-ed' endings"
                }
            },
            "Intonation": {
                "title": "Intonation Patterns",
                "files": {
                    "questions.mp3": "Question intonation",
                    "statements.mp3": "Statement intonation",
                    "emphasis.mp3": "Word emphasis"
                }
            },
            "Rhythm": {
                "title": "Speech Rhythm",
                "files": {
                    "word_stress.mp3": "Word stress patterns",
                    "sentence_rhythm.mp3": "Sentence rhythm",
                    "connected_speech.mp3": "Connected speech"
                }
            }
        }
        self.achievements = []
        self.daily_practice_time = 0
        self.learned_words = set()
        self.dialog_scenarios = {
            "Restaurant": [
                ("Customer", "I'd like to make a reservation for tonight."),
                ("Waiter", "What time would you like to come?"),
                ("Customer", "Around 7 PM, for two people."),
                ("Waiter", "Let me check our availability.")
            ],
            "Job Interview": [
                ("Interviewer", "Tell me about your previous experience."),
                ("Candidate", "I have worked in software development for five years."),
                ("Interviewer", "What are your career goals?"),
                ("Candidate", "I aim to develop my leadership skills.")
            ]
        }
        self.role_play_scenarios = {
            "Shopping": {
                "setting": "You are at a clothing store",
                "roles": ["Customer", "Shop Assistant"],
                "objectives": ["Ask about sizes", "Discuss prices", "Make a purchase"]
            },
            "Travel": {
                "setting": "You are at an airport",
                "roles": ["Passenger", "Check-in Staff"],
                "objectives": ["Check in luggage", "Get boarding pass", "Ask about delays"]
            }
        }
        
        # IPA sözlüğü - Zor kelimeler için
        self.ipa_dict = {
            "thought": "θɔːt",
            "through": "θruː",
            "enough": "ɪˈnʌf",
            "question": "ˈkwes.tʃən",
            # Daha fazla kelime eklenebilir
        }
        
        # Örnek cümleleri kategorilere ayırıyoruz
        self.example_sentences = [
            # Temel Günlük Konuşmalar (B1)
            "I've been learning English for about three years now.",
            "Could you recommend a good restaurant in this area?",
            "I'm thinking about taking a vacation next month.",
            "What kind of music do you usually listen to?",
            "I'd rather stay at home than go out tonight.",
            "How often do you exercise during the week?",
            "Can you tell me how to get to the nearest subway station?",
            "What's your favorite way to spend weekends?",
            "I usually wake up early to go jogging.",
            "Do you prefer cooking at home or eating out?",
            
            # İş ve Profesyonel Hayat (B1-B2)
            "I have a job interview tomorrow morning at 9 AM.",
            "Could you explain how this software works?",
            "We need to submit the project by the end of this week.",
            "I'm considering applying for a master's degree program.",
            "The meeting has been rescheduled for next Wednesday.",
            "I'd like to discuss my career development opportunities.",
            "Our team has been working on this project for six months.",
            "The company is implementing new policies next quarter.",
            "Could you forward me the meeting minutes?",
            "We should prioritize customer satisfaction.",
        
            # Akademik ve Eğitim (B2)
            "The research paper needs to be peer-reviewed.",
            "I'm writing my thesis on renewable energy.",
            "The professor's lecture was very enlightening.",
            "We need to analyze the data before drawing conclusions.",
            "The experiment yielded unexpected results.",
            "The literature review should be comprehensive.",
            "Students must submit their assignments by Friday.",
            "The academic conference will be held virtually.",
            "This theory has been widely debated in academia.",
            "The study's methodology needs to be refined.",
            
            # Sosyal Konular ve Güncel Olaylar (B2)
            "What's your opinion on environmental protection?",
            "Social media has changed the way we communicate.",
            "We should focus more on renewable energy sources.",
            "Many people are working remotely due to the pandemic.",
            "Technology has greatly influenced our daily lives.",
            "The government is implementing new policies.",
            "Public transportation should be more accessible.",
            "Mental health awareness is increasingly important.",
            "Income inequality remains a significant issue.",
            "Education should be accessible to everyone.",
            
            # Kültür ve Sanat (B2)
            "This exhibition features works from local artists.",
            "The film explores themes of identity and belonging.",
            "Classical music helps me concentrate while studying.",
            "The author's writing style is quite sophisticated.",
            "This play has received excellent reviews from critics.",
            "Modern art challenges traditional perspectives.",
            "The museum is hosting a special exhibition.",
            "Photography can capture powerful emotions.",
            "The concert venue has excellent acoustics.",
            "Street art adds character to urban spaces.",
            
            # Seyahat ve Deneyimler (B1-B2)
            "Have you ever tried traditional Japanese cuisine?",
            "The historical sites in Rome are breathtaking.",
            "I'm planning to backpack through Europe next summer.",
            "What's the most memorable trip you've ever taken?",
            "Living abroad has broadened my perspective.",
            "The local customs are fascinating to learn about.",
            "Travel insurance is essential for long trips.",
            "The scenic route offers beautiful views.",
            "I prefer staying in hostels while traveling.",
            "Cultural exchange programs are very enriching.",
            
            # Duygular ve Kişisel Gelişim (B2)
            "I feel overwhelmed by all these responsibilities.",
            "It's important to maintain a work-life balance.",
            "The situation is more complex than it appears.",
            "I've been reflecting on my career choices lately.",
            "Sometimes it's better to trust your intuition.",
            "Personal growth requires stepping out of your comfort zone.",
            "Mindfulness helps reduce stress and anxiety.",
            "Setting boundaries is essential for mental health.",
            "It's okay to ask for help when needed.",
            "Self-reflection leads to better understanding.",
            
            # Bilim ve Teknoloji (B2)
            "Artificial intelligence is transforming many industries.",
            "Scientists are making progress in cancer research.",
            "The latest smartphone features are quite impressive.",
            "Cybersecurity is becoming increasingly important.",
            "Space exploration continues to fascinate people.",
            "Quantum computing could revolutionize technology.",
            "Renewable energy technology is advancing rapidly.",
            "Data privacy is a growing concern.",
            "Virtual reality has many practical applications.",
            "Biotechnology offers promising medical solutions.",
            
            # Çevre ve Sürdürülebilirlik (B2)
            "We should reduce our plastic consumption.",
            "Climate change affects everyone on the planet.",
            "Many species are at risk of extinction.",
            "Sustainable living is becoming more popular.",
            "Urban farming could help reduce carbon emissions.",
            "Recycling programs need more support.",
            "Ocean pollution is a serious environmental threat.",
            "Green energy investments are increasing.",
            "Biodiversity is essential for ecosystem health.",
            "Conservation efforts require global cooperation.",
            
            # İş İletişimi (B2)
            "Could you please clarify the project requirements?",
            "We need to optimize our workflow processes.",
            "The quarterly report shows positive growth.",
            "Customer feedback has been largely positive.",
            "Let's schedule a follow-up meeting next week.",
            "The proposal needs some minor revisions.",
            "Our marketing strategy needs updating.",
            "Team collaboration is essential for success.",
            "The deadline is approaching quickly.",
            "We should focus on long-term sustainability.",
            
            # Sağlık ve Wellness (B1-B2)
            "Regular exercise improves mental health.",
            "A balanced diet is essential for good health.",
            "Getting enough sleep affects productivity.",
            "Stress management techniques can be very helpful.",
            "Alternative medicine is gaining popularity.",
            "Regular check-ups are important for prevention.",
            "Mental health is as important as physical health.",
            "Yoga helps improve flexibility and balance.",
            "Meditation can reduce anxiety levels.",
            "Healthy habits lead to better quality of life."
        ]
        
        self.current_sentence_index = 0
        self.load_progress()
        self.init_ui()
        self.init_study_modes()
        self.init_multimedia_support()
        self.init_statistics_tracking()
        
        # Genişletilmiş diyalog senaryoları
        self.dialog_scenarios.update({
            "Hotel Check-in": [
                ("Guest", "I have a reservation for tonight."),
                ("Receptionist", "Could I have your name, please?"),
                ("Guest", "Yes, it's John Smith."),
                ("Receptionist", "How many nights will you be staying with us?")
            ],
            "Doctor's Appointment": [
                ("Doctor", "What seems to be the problem?"),
                ("Patient", "I've been having headaches for the past week."),
                ("Doctor", "How often do they occur?"),
                ("Patient", "Almost every day, especially in the morning.")
            ],
            "Shopping for Clothes": [
                ("Customer", "Do you have this shirt in a different size?"),
                ("Sales Assistant", "What size are you looking for?"),
                ("Customer", "I need a medium."),
                ("Sales Assistant", "Let me check in the back.")
            ],
            "Coffee Shop": [
                ("Barista", "What can I get for you today?"),
                ("Customer", "I'd like a large cappuccino, please."),
                ("Barista", "Would you like any food with that?"),
                ("Customer", "Yes, a chocolate croissant, please.")
            ]
        })
        
        # Genişletilmiş rol yapma senaryoları
        self.role_play_scenarios.update({
            "Job Interview": {
                "setting": "You are interviewing for your dream job",
                "roles": ["Interviewer", "Job Candidate"],
                "objectives": ["Discuss experience", "Ask about company culture", "Negotiate salary"]
            },
            "Customer Service": {
                "setting": "You are handling a customer complaint",
                "roles": ["Customer Service Rep", "Customer"],
                "objectives": ["Listen to complaint", "Offer solution", "Ensure satisfaction"]
            },
            "Restaurant Review": {
                "setting": "You are a food critic visiting a new restaurant",
                "roles": ["Food Critic", "Restaurant Manager"],
                "objectives": ["Discuss menu", "Rate service", "Give feedback"]
            },
            "Travel Agency": {
                "setting": "You are planning a vacation",
                "roles": ["Travel Agent", "Client"],
                "objectives": ["Discuss destinations", "Set budget", "Plan itinerary"]
            }
        })
        
    def init_ui(self):
        """Ana arayüzü başlat"""
        layout = QVBoxLayout(self)
        
        # Tab widget oluştur
        self.tabs = QTabWidget()
        
        # Tab'ları oluştur
        self.practice_tab = QWidget()
        self.exam_prep_tab = QWidget()
        self.tools_tab = QWidget()
        self.analysis_tab = QWidget()
        self.business_tab = QWidget()
        
        # Tab'ları başlat
        self.init_practice_tab()
        self.init_exam_prep_tab()
        self.init_tools_tab()
        self.init_analysis_tab()
        self.init_business_tab()  # Bu satır kalacak
        
        # Tab'ları ekle
        self.tabs.addTab(self.practice_tab, "Pratik")
        self.tabs.addTab(self.exam_prep_tab, "Sınav Hazırlık") 
        self.tabs.addTab(self.tools_tab, "Araçlar")
        self.tabs.addTab(self.analysis_tab, "Analiz")
        self.tabs.addTab(self.business_tab, "İş İngilizcesi")
        
        layout.addWidget(self.tabs)
        
    def init_business_tab(self):
        """İş İngilizcesi sekmesini başlat"""
        layout = QVBoxLayout(self.business_tab)
        
        # Başlık
        title = QLabel("İş İngilizcesi Pratik")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Kategori seçimi
        category_group = QGroupBox("Kategori")
        category_layout = QVBoxLayout()
        
        self.business_category = QComboBox()
        self.business_category.addItems([
            "E-posta Yazma",
            "Toplantı İfadeleri",
            "Sunum Teknikleri",
            "Müzakere Becerileri",
            "Telefon Görüşmeleri"
        ])
        category_layout.addWidget(self.business_category)
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)
        
        # Pratik başlatma butonu
        start_button = QPushButton("Pratik Başlat")
        start_button.clicked.connect(self.start_business_practice)
        layout.addWidget(start_button)
        
        # Boşluk ekle
        layout.addStretch()
        
    def on_tab_changed(self, index):
        """Sekme değiştiğinde çağrılır"""
        tab_name = self.tabs.tabText(index)
        self.status_label.setText(f"Aktif Sekme: {tab_name}")
        
        # Sekmeye özel hazırlıkları yap
        if tab_name == "Pratik":
            self.load_practice_data()
        elif tab_name == "Sınav Hazırlık":
            self.load_exam_prep_data()
        elif tab_name == "Araçlar":
            self.load_tools_data()
        elif tab_name == "Analiz":
            self.update_analysis()
        elif tab_name == "İş İngilizcesi":
            self.load_business_data()
            
    def load_practice_data(self):
        """Pratik verilerini yükle"""
        self.update_progress_label()
        self.update_practice_time()
        
    def load_flashcards(self):
        """Seçilen kategoriye göre kartları filtrele ve yükle"""
        category = self.flashcard_category_combo.currentText()
        all_cards = self.load_flashcard_data()  # Tüm kartları yükle
        
        if category == "Tüm Kartlar":
            filtered_cards = all_cards
        elif category == "Yeni Kartlar":
            filtered_cards = [card for card in all_cards if card["difficulty"] == "hard"]
        elif category == "Öğrenilen":
            filtered_cards = [card for card in all_cards if card["difficulty"] == "easy"]
        else:  # Zor
            filtered_cards = [card for card in all_cards if card["difficulty"] == "medium"]
            
        self.flashcards = filtered_cards
        self.current_card_index = 0
        self.cards_flipped = False
        self.show_current_card()
        self.update_flashcard_stats()

    def init_flashcards_tab(self):
        """Kelime kartları sekmesi"""
        layout = QVBoxLayout(self.flashcards_tab)
        
        # Üst kontrol paneli
        control_panel = QHBoxLayout()
        
        # Kategori seçimi
        self.flashcard_category_combo = QComboBox()
        self.flashcard_category_combo.addItems(["Tüm Kartlar", "Yeni Kartlar", "Öğrenilen", "Zor"])
        self.flashcard_category_combo.currentTextChanged.connect(self.load_flashcards)
        control_panel.addWidget(QLabel("Kategori:"))
        control_panel.addWidget(self.flashcard_category_combo)
        
        # Kart kontrolleri
        self.prev_card_button = QPushButton("Önceki")
        self.next_card_button = QPushButton("Sonraki")
        self.flip_card_button = QPushButton("Çevir")
        
        self.prev_card_button.clicked.connect(self.show_previous_card)
        self.next_card_button.clicked.connect(self.show_next_card)
        self.flip_card_button.clicked.connect(self.flip_card)
        
        control_panel.addWidget(self.prev_card_button)
        control_panel.addWidget(self.flip_card_button)
        control_panel.addWidget(self.next_card_button)
        
        layout.addLayout(control_panel)
        
        # Kart görüntüleme alanı
        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        self.card_display.setMinimumHeight(200)
        self.card_display.setStyleSheet("QTextEdit { background-color: white; border: 2px solid #ccc; border-radius: 10px; font-size: 18px; padding: 20px; }")
        layout.addWidget(self.card_display)
        
        # Alt kontrol paneli
        bottom_panel = QHBoxLayout()
        
        # Zorluk derecelendirme butonları
        self.easy_btn = QPushButton("Kolay")
        self.medium_btn = QPushButton("Orta")
        self.hard_btn = QPushButton("Zor")
        
        self.easy_btn.clicked.connect(lambda: self.rate_card("easy"))
        self.medium_btn.clicked.connect(lambda: self.rate_card("medium"))
        self.hard_btn.clicked.connect(lambda: self.rate_card("hard"))
        
        bottom_panel.addWidget(self.easy_btn)
        bottom_panel.addWidget(self.medium_btn)
        bottom_panel.addWidget(self.hard_btn)
        
        layout.addLayout(bottom_panel)
        
        # İstatistik paneli
        stats_panel = QHBoxLayout()
        self.cards_remaining_label = QLabel("Kalan Kart: 0")
        self.cards_learned_label = QLabel("Öğrenilen: 0")
        stats_panel.addWidget(self.cards_remaining_label)
        stats_panel.addWidget(self.cards_learned_label)
        layout.addLayout(stats_panel)
        
        # Yeni kart ekleme butonu
        add_card_button = QPushButton("Yeni Kart Ekle")
        add_card_button.clicked.connect(self.show_add_card_dialog)
        layout.addWidget(add_card_button)
        
        # Kart verilerini yükle
        self.current_card_index = 0
        self.cards_flipped = False
        self.flashcards = self.load_flashcard_data()
        self.show_current_card()

    def show_current_card(self):
        """Mevcut kartı göster"""
        if not self.flashcards:
            self.card_display.setText("Kart bulunamadı!")
            self.update_flashcard_stats()
            return
            
        if self.current_card_index >= len(self.flashcards):
            self.current_card_index = len(self.flashcards) - 1
            
        card = self.flashcards[self.current_card_index]
        display_text = card["front"] if not self.cards_flipped else card["back"]
        
        # Kartın görünümünü zenginleştir
        html_text = f"""
        <div style='text-align: center; margin: 20px;'>
            <h2 style='color: #2c3e50;'>{display_text}</h2>
            <p style='color: #7f8c8d;'>Kart {self.current_card_index + 1} / {len(self.flashcards)}</p>
        </div>
        """
        self.card_display.setHtml(html_text)
        self.update_flashcard_stats()

    def load_flashcard_data(self):
        """Kelime kartı verilerini yükle"""
        try:
            if os.path.exists('flashcards.json'):
                with open('flashcards.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Kelime kartları yüklenirken hata: {str(e)}")
        
        # Varsayılan kartlar
        return [
            {"front": "Hello", "back": "Merhaba", "difficulty": "easy"},
            {"front": "Good morning", "back": "Günaydın", "difficulty": "easy"},
            {"front": "Thank you", "back": "Teşekkür ederim", "difficulty": "easy"},
            {"front": "You're welcome", "back": "Rica ederim", "difficulty": "medium"},
            {"front": "How are you?", "back": "Nasılsın?", "difficulty": "easy"},
            {"front": "Nice to meet you", "back": "Tanıştığıma memnun oldum", "difficulty": "medium"},
            {"front": "Goodbye", "back": "Hoşça kal", "difficulty": "easy"},
            {"front": "See you later", "back": "Görüşürüz", "difficulty": "easy"},
            {"front": "Have a good day", "back": "İyi günler", "difficulty": "easy"},
            {"front": "Good night", "back": "İyi geceler", "difficulty": "easy"}
        ]
        
    def save_flashcard_data(self):
        """Kelime kartı verilerini kaydet"""
        try:
            with open('flashcards.json', 'w', encoding='utf-8') as f:
                json.dump(self.flashcards, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Kelime kartları kaydedilirken hata: {str(e)}")
            
    def show_next_card(self):
        """Sonraki karta geç"""
        if self.current_card_index < len(self.flashcards) - 1:
            self.current_card_index += 1
            self.cards_flipped = False
            self.show_current_card()
            
    def show_previous_card(self):
        """Önceki karta dön"""
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.cards_flipped = False
            self.show_current_card()
            
    def flip_card(self):
        """Kartı çevir"""
        self.cards_flipped = not self.cards_flipped
        self.show_current_card()
        
    def rate_card(self, difficulty):
        """Kartın zorluğunu değerlendir"""
        if self.flashcards:
            self.flashcards[self.current_card_index]["difficulty"] = difficulty
            self.save_flashcard_data()
            self.show_next_card()
            
    def update_flashcard_stats(self):
        """Kart istatistiklerini güncelle"""
        total_cards = len(self.flashcards)
        learned_cards = sum(1 for card in self.flashcards if card["difficulty"] == "easy")
        remaining_cards = total_cards - learned_cards
        
        self.cards_remaining_label.setText(f"Kalan Kart: {remaining_cards}")
        self.cards_learned_label.setText(f"Öğrenilen: {learned_cards}")
        
    def show_add_card_dialog(self):
        """Yeni kart ekleme diyaloğunu göster"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Kart Ekle")
        layout = QVBoxLayout(dialog)
        
        # İngilizce kelime/cümle girişi
        front_label = QLabel("İngilizce:")
        front_input = QLineEdit()
        layout.addWidget(front_label)
        layout.addWidget(front_input)
        
        # Türkçe karşılık girişi
        back_label = QLabel("Türkçe:")
        back_input = QLineEdit()
        layout.addWidget(back_label)
        layout.addWidget(back_input)
        
        # Zorluk seviyesi seçimi
        difficulty_label = QLabel("Zorluk:")
        difficulty_combo = QComboBox()
        difficulty_combo.addItems(["easy", "medium", "hard"])
        layout.addWidget(difficulty_label)
        layout.addWidget(difficulty_combo)
        
        # Butonlar
        button_box = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        cancel_btn = QPushButton("İptal")
        
        save_btn.clicked.connect(lambda: self.add_new_card(
            dialog,
            front_input.text(),
            back_input.text(),
            difficulty_combo.currentText()
        ))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)
        
        dialog.exec_()
        
    def add_new_card(self, dialog, front, back, difficulty):
        """Yeni kart ekle"""
        if not front or not back:
            QMessageBox.warning(dialog, "Hata", "Lütfen tüm alanları doldurun.")
            return
            
        new_card = {
            "front": front,
            "back": back,
            "difficulty": difficulty
        }
        
        self.flashcards.append(new_card)
        self.save_flashcard_data()
        self.update_flashcard_stats()
        dialog.accept()
        
        QMessageBox.information(self, "Başarılı", "Yeni kart eklendi!")
        
    def update_practice_time(self):
        """Pratik süresini güncelle"""
        if not hasattr(self, 'practice_start_time') or self.practice_start_time is None:
            self.practice_start_time = time.time()
            self.practice_time_label.setText("Bugünkü Pratik: 0 dk")
            return
            
        elapsed = time.time() - self.practice_start_time
        self.practice_time_label.setText(f"Bugünkü Pratik: {int(elapsed/60)} dk")
    
    def update_progress_label(self):
        """İlerleme etiketini güncelle"""
        if hasattr(self, 'progress_label'):
            if not hasattr(self, 'total_attempts'):
                self.total_attempts = 0
            if not hasattr(self, 'current_score'):
                self.current_score = 0
                
            if self.total_attempts > 0:
                progress = (self.current_score / self.total_attempts)
            else:
                progress = 0
                
            self.progress_label.setText(f"İlerleme: {progress:.1f}%")
    
    def next_sentence(self):
        """Sonraki cümleye geç"""
        category = self.category_combo.currentText()
        
        if category == "Tüm Kategoriler":
            # Rastgele bir cümle seç
            self.current_sentence_index = random.randint(0, len(self.example_sentences) - 1)
        else:
            # Kategori indekslerini bul
            category_indices = {
                "Temel Günlük Konuşmalar (B1)": (0, 10),
                "İş ve Profesyonel Hayat (B1-B2)": (10, 20),
                "Akademik ve Eğitim (B2)": (20, 30),
                "Sosyal Konular ve Güncel Olaylar (B2)": (30, 40),
                "Kültür ve Sanat (B2)": (40, 50),
                "Seyahat ve Deneyimler (B1-B2)": (50, 60),
                "Duygular ve Kişisel Gelişim (B2)": (60, 70),
                "Bilim ve Teknoloji (B2)": (70, 80),
                "Çevre ve Sürdürülebilirlik (B2)": (80, 90),
                "İş İletişimi (B2)": (90, 100),
                "Sağlık ve Wellness (B1-B2)": (100, 110)
            }
            
            # Seçilen kategoriden rastgele bir cümle seç
            start_idx, end_idx = category_indices[category]
            self.current_sentence_index = random.randint(start_idx, end_idx - 1)
        
        self.example_text.setText(self.example_sentences[self.current_sentence_index])
        self.result_text.clear()
        self.accuracy_bar.setValue(0)
        self.feedback_label.clear()
        self.translation_text.clear()
        self.update_pronunciation_tips()

    def cleanup_temp_file(self):
        """Geçici ses dosyasını temizle"""
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                pygame.mixer.music.unload()
                os.unlink(self.temp_audio_file)
                self.temp_audio_file = None
            except:
                pass
        
    def play_text(self):
        """Örnek metni seslendir"""
        try:
            self.cleanup_temp_file()
            text = self.example_text.toPlainText()
            tts = gTTS(text=text, lang='en', slow=(self.speech_rate < 0.8))
            
            # Geçici dosyaya kaydet
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            self.temp_audio_file = temp_file.name
            
            tts.save(self.temp_audio_file)
            time.sleep(0.5)
            
            pygame.mixer.music.load(self.temp_audio_file)
            pygame.mixer.music.set_volume(min(self.speech_rate, 1.0))
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
        except Exception as e:
            self.feedback_label.setText(f"Ses oynatma hatası: {str(e)}")
    
    def start_recording(self):
        """Ses kaydını başlat"""
        self.record_button.setEnabled(False)
        self.record_button.setText("Dinleniyor...")
        
        self.speech_thread = SpeechRecognitionThread()
        self.speech_thread.finished.connect(self.on_recording_finished)
        self.speech_thread.error.connect(self.on_recording_error)
        self.speech_thread.start()
    
    def on_recording_finished(self, text):
        """Ses tanıma tamamlandığında çağrılır"""
        self.record_button.setEnabled(True)
        
        # Benzerlik oranını hesapla
        similarity = self.calculate_similarity(text.lower(), self.example_text.toPlainText().lower())
        
        # Sonuçları göster
        self.result_text.setText(f"Söylediğiniz: {text}")
        self.accuracy_bar.setValue(int(similarity))
        
        # Geri bildirim ver ve butonları ayarla
        if similarity >= 90:
            feedback = "Mükemmel! 🌟 Sonraki cümleye geçebilirsiniz."
            self.record_button.setText("Tekrar Dene")
            # Sonraki cümleye geçişe izin ver
            self.next_button.setEnabled(True)
        elif similarity >= 75:
            feedback = "Çok iyi! ⭐ Biraz daha pratik yapabilirsiniz."
            self.record_button.setText("Tekrar Dene")
            # Sonraki cümleye geçişe izin ver
            self.next_button.setEnabled(True)
        elif similarity >= 60:
            feedback = "İyi 👍 Biraz daha pratik yapın. Tekrar deneyin."
            self.record_button.setText("Tekrar Dene")
            # Aynı cümlede kal
            self.next_button.setEnabled(False)
        else:
            feedback = "Tekrar denemelisiniz 🔄"
            self.record_button.setText("Tekrar Dene")
            # Aynı cümlede kal
            self.next_button.setEnabled(False)
        
        self.feedback_label.setText(feedback)
        
        # İstatistikleri güncelle
        self.update_statistics(similarity)

    def on_recording_error(self, error):
        """Ses tanıma hatası olduğunda çağrılır"""
        self.record_button.setEnabled(True)
        self.record_button.setText("Konuşmaya Başla")
        self.result_text.setText(f"Hata: {error}")
    
    def translate_text(self):
        """Metni çevir"""
        try:
            translator = Translator()
            text = self.example_text.toPlainText()
            translation = translator.translate(text, dest='tr')
            self.translation_text.setText(translation.text)
        except Exception as e:
            self.translation_text.setText(f"Çeviri hatası: {str(e)}")
    
    def change_category(self):
        """Kategori değiştiğinde cümleleri güncelle"""
        category = self.category_combo.currentText()
        
        # Kategori başlıklarını ve indekslerini belirle
        category_indices = {
            "Temel Günlük Konuşmalar (B1)": (0, 10),
            "İş ve Profesyonel Hayat (B1-B2)": (10, 20),
            "Akademik ve Eğitim (B2)": (20, 30),
            "Sosyal Konular ve Güncel Olaylar (B2)": (30, 40),
            "Kültür ve Sanat (B2)": (40, 50),
            "Seyahat ve Deneyimler (B1-B2)": (50, 60),
            "Duygular ve Kişisel Gelişim (B2)": (60, 70),
            "Bilim ve Teknoloji (B2)": (70, 80),
            "Çevre ve Sürdürülebilirlik (B2)": (80, 90),
            "İş İletişimi (B2)": (90, 100),
            "Sağlık ve Wellness (B1-B2)": (100, 110)
        }
        
        if category == "Tüm Kategoriler":
            # Rastgele bir cümle seç
            self.current_sentence_index = random.randint(0, len(self.example_sentences) - 1)
        else:
            # Seçilen kategoriden rastgele bir cümle seç
            start_idx, end_idx = category_indices[category]
            self.current_sentence_index = random.randint(start_idx, end_idx - 1)
        
        self.example_text.setText(self.example_sentences[self.current_sentence_index])
        self.result_text.clear()
        self.accuracy_bar.setValue(0)
        self.feedback_label.clear()
        self.translation_text.clear()

    def toggle_favorite(self):
        """Mevcut cümleyi favorilere ekle/çıkar"""
        current_sentence = self.example_text.toPlainText()
        if current_sentence in self.favorite_sentences:
            self.favorite_sentences.remove(current_sentence)
            self.favorite_button.setText("❤️ Favorilere Ekle")
        else:
            self.favorite_sentences.append(current_sentence)
            self.favorite_button.setText("💔 Favorilerden Çıkar")
        self.save_favorites()
    
    def save_favorites(self):
        """Favori cümleleri kaydet"""
        try:
            with open('favorite_sentences.json', 'w') as f:
                json.dump(self.favorite_sentences, f)
        except Exception as e:
            print(f"Favoriler kaydedilirken hata: {str(e)}")
    
    def load_favorites(self):
        """Favori cümleleri yükle"""
        try:
            if os.path.exists('favorite_sentences.json'):
                with open('favorite_sentences.json', 'r') as f:
                    self.favorite_sentences = json.load(f)
        except Exception as e:
            print(f"Favoriler yüklenirken hata: {str(e)}")
    
    def update_speech_rate(self):
        """Ses hızını güncelle"""
        self.speech_rate = self.speed_slider.value() / 100.0
    
    def show_statistics(self):
        """İstatistikleri göster"""
        average_score = self.current_score/self.total_attempts if self.total_attempts > 0 else 0
        stats_text = f"""
        Genel İstatistikler:
        -------------------
        Toplam Pratik: {self.total_attempts}
        Ortalama Puan: {average_score:.2f}%
        
        Kategori Bazlı Başarı:
        ---------------------
        {self.get_category_stats()}
        
        Son 7 Gün:
        ----------
        {self.get_daily_stats()}
        """
        self.result_text.setText(stats_text)
    
    def get_category_stats(self):
        """Kategori bazlı istatistikleri getir"""
        stats = ""
        for category, data in self.category_stats.items():
            if data['attempts'] > 0:
                avg_score = data['total_score'] / data['attempts']
                stats += f"{category}: {avg_score:.2f}% ({data['attempts']} deneme)\n"
        return stats if stats else "Henüz kategori verisi yok"
    
    def get_daily_stats(self):
        """Günlük istatistikleri getir"""
        stats = ""
        for date, data in sorted(self.daily_stats.items())[-7:]:
            if data['attempts'] > 0:
                avg_score = data['total_score'] / data['attempts']
                stats += f"{date}: {avg_score:.2f}% ({data['attempts']} deneme)\n"
        return stats if stats else "Henüz günlük veri yok"
    
    def update_pronunciation_tips(self):
        """Telaffuz ipuçlarını güncelle"""
        # Mevcut cümle için telaffuz ipuçlarını göster
        tips = [
            "Kelimeleri net ve anlaşılır şekilde söyleyin",
            "Doğru vurgu ve tonlamaya dikkat edin",
            "Duraksama ve noktalama işaretlerine uyun",
            "Kelimeleri doğal bir hızda söyleyin"
        ]
        self.pronunciation_tips.setText("\n".join(tips))
    
    def closeEvent(self, event):
        """Widget kapatıldığında geçici dosyaları temizle"""
        self.cleanup_temp_file()
        self.save_progress()
        super().closeEvent(event)

    def init_study_modes(self):
        """Çalışma modlarını başlat"""
        mode_layout = QHBoxLayout()
        self.mode_label = QLabel("Study Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Quick Practice", "Detailed Learning", "Exam Mode", "Review Mode"])
        self.mode_combo.currentTextChanged.connect(self.change_study_mode)
        
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo)
        self.layout().insertLayout(1, mode_layout)
        
    def init_multimedia_support(self):
        """Multimedya desteğini başlat"""
        media_layout = QHBoxLayout()
        
        # Video butonu
        self.video_button = QPushButton("Watch Example")
        self.video_button.clicked.connect(self.show_example_video)
        
        # Ses kütüphanesi butonu
        self.audio_library_button = QPushButton("Audio Library")
        self.audio_library_button.clicked.connect(self.open_audio_library)
        
        # İnteraktif alıştırmalar butonu
        self.interactive_button = QPushButton("Interactive Exercises")
        self.interactive_button.clicked.connect(self.start_interactive_exercise)
        
        media_layout.addWidget(self.video_button)
        media_layout.addWidget(self.audio_library_button)
        media_layout.addWidget(self.interactive_button)
        
        self.layout().addLayout(media_layout)
        
    def init_statistics_tracking(self):
        """İstatistik takip sistemini başlat"""
        stats_layout = QVBoxLayout()
        
        # Günlük pratik süresi
        self.practice_time_label = QLabel("Today's Practice: 0 minutes")
        
        # Öğrenilen kelimeler
        self.learned_words_label = QLabel("Learned Words: 0")
        
        # Başarı rozetleri
        self.achievements_label = QLabel("Achievements: 0")
        
        stats_layout.addWidget(self.practice_time_label)
        stats_layout.addWidget(self.learned_words_label)
        stats_layout.addWidget(self.achievements_label)
        
        self.layout().addLayout(stats_layout)
        
    def change_study_mode(self, mode):
        """Çalışma modunu değiştir"""
        if mode == "Quick Practice":
            self.current_mode = "practice"
            if hasattr(self, 'instruction_label'):
                self.instruction_label.setText("Read the sentence aloud:")
        elif mode == "Detailed Learning":
            self.current_mode = "detailed"
            if hasattr(self, 'instruction_label'):
                self.instruction_label.setText("Study the sentence carefully and practice pronunciation:")
        elif mode == "Exam Mode":
            self.current_mode = "exam"
            if hasattr(self, 'instruction_label'):
                self.instruction_label.setText("Complete the speaking test:")
        else:  # Review Mode
            self.current_mode = "review"
            if hasattr(self, 'instruction_label'):
                self.instruction_label.setText("Review previous sentences:")
            
    def start_dialog_practice(self):
        """Diyalog pratiğini başlat"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Dialog Practice")
        dialog.setMinimumSize(600, 500)
        layout = QVBoxLayout(dialog)
        
        # Senaryo seçimi
        scenario_label = QLabel("Select Scenario:")
        layout.addWidget(scenario_label)
        
        scenario_combo = QComboBox()
        scenario_combo.addItems(self.dialog_scenarios.keys())
        layout.addWidget(scenario_combo)
        
        # Diyalog görüntüleme
        dialog_text = QTextEdit()
        dialog_text.setReadOnly(True)
        layout.addWidget(dialog_text)
        
        def update_dialog():
            scenario = self.dialog_scenarios[scenario_combo.currentText()]
            dialog_content = ""
            for role, text in scenario:
                dialog_content += f"{role}: {text}\n\n"
            dialog_text.setText(dialog_content)
        
        scenario_combo.currentTextChanged.connect(update_dialog)
        update_dialog()
        
        # Rol seçimi
        role_label = QLabel("Choose Your Role:")
        layout.addWidget(role_label)
        
        role_combo = QComboBox()
        role_combo.addItems(["Role 1", "Role 2"])
        layout.addWidget(role_combo)
        
        # Kayıt kontrolleri
        control_layout = QHBoxLayout()
        
        record_button = QPushButton("Record Response")
        record_button.clicked.connect(self.start_recording)
        control_layout.addWidget(record_button)
        
        play_button = QPushButton("Play Example")
        play_button.clicked.connect(lambda: self.play_dialog_example(scenario_combo.currentText()))
        control_layout.addWidget(play_button)
        
        layout.addLayout(control_layout)
        
        # Sonuç görüntüleme
        result_label = QLabel("Your Response:")
        layout.addWidget(result_label)
        
        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_text.setMaximumHeight(100)
        layout.addWidget(result_text)
        
        dialog.exec_()
        
    def start_role_play(self):
        """Rol yapma senaryosunu başlat"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Role Play")
        dialog.setMinimumSize(600, 500)
        layout = QVBoxLayout(dialog)
        
        # Senaryo seçimi
        scenario_label = QLabel("Select Scenario:")
        layout.addWidget(scenario_label)
        
        scenario_combo = QComboBox()
        scenario_combo.addItems(self.role_play_scenarios.keys())
        layout.addWidget(scenario_combo)
        
        # Senaryo detayları
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        layout.addWidget(details_text)
        
        def update_details():
            scenario = self.role_play_scenarios[scenario_combo.currentText()]
            details = f"""
            Setting: {scenario['setting']}
            
            Roles:
            - {scenario['roles'][0]}
            - {scenario['roles'][1]}
            
            Objectives:
            """
            for obj in scenario['objectives']:
                details += f"- {obj}\n"
            details_text.setText(details)
        
        scenario_combo.currentTextChanged.connect(update_details)
        update_details()
        
        # Rol seçimi
        role_label = QLabel("Choose Your Role:")
        layout.addWidget(role_label)
        
        role_combo = QComboBox()
        def update_roles():
            role_combo.clear()
            scenario = self.role_play_scenarios[scenario_combo.currentText()]
            role_combo.addItems(scenario['roles'])
        
        scenario_combo.currentTextChanged.connect(update_roles)
        update_roles()
        layout.addWidget(role_combo)
        
        # Kontrol butonları
        control_layout = QHBoxLayout()
        
        start_button = QPushButton("Start Role Play")
        start_button.clicked.connect(lambda: self.begin_role_play(scenario_combo.currentText(), role_combo.currentText()))
        control_layout.addWidget(start_button)
        
        record_button = QPushButton("Record Response")
        record_button.clicked.connect(self.start_recording)
        control_layout.addWidget(record_button)
        
        layout.addLayout(control_layout)
        
        # İlerleme göstergesi
        progress_label = QLabel("Progress:")
        layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        layout.addWidget(progress_bar)
        
        dialog.exec_()
        
    def play_dialog_example(self, scenario_name):
        """Diyalog örneğini oynat"""
        scenario = self.dialog_scenarios[scenario_name]
        text = " ".join([line[1] for line in scenario])
        
        try:
            self.cleanup_temp_file()
            tts = gTTS(text=text, lang='en', slow=(self.speech_rate < 0.8))
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            self.temp_audio_file = temp_file.name
            
            tts.save(self.temp_audio_file)
            time.sleep(0.5)
            
            pygame.mixer.music.load(self.temp_audio_file)
            pygame.mixer.music.play()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error playing dialog: {str(e)}")
            
    def begin_role_play(self, scenario_name, selected_role):
        """Rol yapma oturumunu başlat"""
        scenario = self.role_play_scenarios[scenario_name]
        QMessageBox.information(self, "Role Play Started", 
            f"You are now playing the role of {selected_role}\n\n"
            f"Setting: {scenario['setting']}\n\n"
            f"Your objectives:\n" + "\n".join([f"- {obj}" for obj in scenario['objectives']]))
        
    def show_example_video(self):
        """Örnek video göster"""
        try:
            video = self.video_library[list(self.video_library.keys())[0]]
            
            # YouTube videosunu tarayıcıda aç
            webbrowser.open(video['url'])
            
            QMessageBox.information(self, "Video Playing",
                f"Video açılıyor: {video['title']}\n\n"
                f"Video tarayıcınızda açılacaktır.")
            
        except Exception as e:
            QMessageBox.warning(self, "Error",
                f"Video açılırken hata oluştu: {str(e)}\n\n"
                "Lütfen internet bağlantınızı kontrol edin.")

    def show_video_library(self):
        """Video kütüphanesini göster"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Video Library")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)
        
        # Video seçimi
        video_combo = QComboBox()
        video_combo.addItems(self.video_library.keys())
        layout.addWidget(video_combo)
        
        # Video bilgileri
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        layout.addWidget(info_text)
        
        def update_info():
            video = self.video_library[video_combo.currentText()]
            info_text.setText(f"""
            Title: {video['title']}
            Description: {video['description']}
            Type: {video['type']}
            URL: {video['url']}
            """)
        
        video_combo.currentTextChanged.connect(update_info)
        update_info()
        
        # Oynat butonu
        play_button = QPushButton("Open in Browser")
        play_button.clicked.connect(lambda: webbrowser.open(
            self.video_library[video_combo.currentText()]['url']
        ))
        layout.addWidget(play_button)
        
        dialog.exec_()
        
    def open_audio_library(self):
        """Ses kütüphanesini aç"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Audio Library")
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)
        
        # Kategori seçimi
        category_combo = QComboBox()
        category_combo.addItems(self.audio_library.keys())
        layout.addWidget(category_combo)
        
        # Ses dosyaları listesi
        files_list = QListWidget()
        layout.addWidget(files_list)
        
        def update_files():
            files_list.clear()
            category = self.audio_library[category_combo.currentText()]
            for file, desc in category['files'].items():
                files_list.addItem(f"{desc}")  # Dosya adı yerine açıklamayı göster
        
        category_combo.currentTextChanged.connect(update_files)
        update_files()
        
        def play_selected_audio():
            if files_list.currentItem():
                description = files_list.currentItem().text()
                # Açıklamaya göre örnek metin oluştur
                sample_texts = {
                    "Practice 'th' sound": "Think about three things.",
                    "Practice 'r' sound": "Red roses are really romantic.",
                    "Practice '-ed' endings": "I walked and talked yesterday.",
                    "Question intonation": "Would you like some coffee?",
                    "Statement intonation": "This is a simple statement.",
                    "Word emphasis": "I REALLY want to learn English.",
                    "Word stress patterns": "Photography is my favorite hobby.",
                    "Sentence rhythm": "I love to study English every day.",
                    "Connected speech": "What are you going to do today?"
                }
                
                text = sample_texts.get(description, description)
                
                try:
                    self.cleanup_temp_file()
                    tts = gTTS(text=text, lang='en', slow=(self.speech_rate < 0.8))
                    
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    temp_file.close()
                    self.temp_audio_file = temp_file.name
                    
                    tts.save(self.temp_audio_file)
                    time.sleep(0.5)
                    
                    pygame.mixer.music.load(self.temp_audio_file)
                    pygame.mixer.music.play()
                    
                except Exception as e:
                    QMessageBox.warning(dialog, "Error", f"Error playing audio: {str(e)}")
        
        # Kontrol butonları
        control_layout = QHBoxLayout()
        
        play_button = QPushButton("Play Selected")
        play_button.clicked.connect(play_selected_audio)
        control_layout.addWidget(play_button)
        
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(pygame.mixer.music.stop)
        control_layout.addWidget(stop_button)
        
        layout.addLayout(control_layout)
        
        dialog.exec_()
        
    def start_interactive_exercise(self):
        """İnteraktif alıştırma başlat"""
        # İnteraktif alıştırma penceresi
        pass

    def load_progress(self):
        """İlerleme verilerini yükle"""
        try:
            if os.path.exists('speech_progress.json'):
                with open('speech_progress.json', 'r') as f:
                    data = json.load(f)
                    self.current_score = data.get('total_score', 0)
                    self.total_attempts = data.get('total_attempts', 0)
                    self.favorite_sentences = data.get('favorites', [])
                    self.daily_stats = data.get('daily_stats', {})
                    self.category_stats = data.get('category_stats', {})
            else:
                # Dosya yoksa varsayılan değerleri ayarla
                self.current_score = 0
                self.total_attempts = 0
                self.favorite_sentences = []
                self.daily_stats = {}
                self.category_stats = {}
        except Exception as e:
            print(f"İlerleme verileri yüklenirken hata: {str(e)}")
            # Hata durumunda varsayılan değerleri ayarla
            self.current_score = 0
            self.total_attempts = 0
            self.favorite_sentences = []
            self.daily_stats = {}
            self.category_stats = {}

    def save_progress(self):
        """İlerleme verilerini kaydet"""
        try:
            current_date = time.strftime('%Y-%m-%d')
            
            # Günlük istatistikleri güncelle
            if current_date not in self.daily_stats:
                self.daily_stats[current_date] = {'total_score': 0, 'attempts': 0}
            self.daily_stats[current_date]['total_score'] += self.current_score
            self.daily_stats[current_date]['attempts'] += 1
            
            data = {
                'total_score': self.current_score,
                'total_attempts': self.total_attempts,
                'last_practice': time.strftime('%Y-%m-%d %H:%M:%S'),
                'daily_stats': self.daily_stats,
                'category_stats': self.category_stats,
                'favorites': self.favorite_sentences
            }
            
            with open('speech_progress.json', 'w') as f:
                json.dump(data, f)
                
        except Exception as e:
            print(f"İlerleme kaydedilirken hata: {str(e)}")

    def init_practice_tab(self):
        """Konuşma pratiği sekmesi"""
        layout = QVBoxLayout(self.practice_tab)
        
        # Üst kontrol paneli
        control_panel = QHBoxLayout()
        
        # Kategori seçimi
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Tüm Kategoriler",
            "Temel Günlük Konuşmalar (B1)",
            "İş ve Profesyonel Hayat (B1-B2)",
            "Akademik ve Eğitim (B2)",
            "Sosyal Konular ve Güncel Olaylar (B2)",
            "Kültür ve Sanat (B2)",
            "Seyahat ve Deneyimler (B1-B2)",
            "Duygular ve Kişisel Gelişim (B2)",
            "Bilim ve Teknoloji (B2)",
            "Çevre ve Sürdürülebilirlik (B2)",
            "İş İletişimi (B2)",
            "Sağlık ve Wellness (B1-B2)"
        ])
        self.category_combo.currentTextChanged.connect(self.change_category)
        control_panel.addWidget(QLabel("Kategori:"))
        control_panel.addWidget(self.category_combo)
        
        # Hız kontrolü
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 150)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.update_speech_rate)
        control_panel.addWidget(QLabel("Hız:"))
        control_panel.addWidget(self.speed_slider)
        
        layout.addLayout(control_panel)
        
        # İlerleme bilgisi
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("İlerleme: 0%")
        progress_layout.addWidget(self.progress_label)
        self.practice_time_label = QLabel("Pratik Süresi: 0 dk")
        progress_layout.addWidget(self.practice_time_label)
        layout.addLayout(progress_layout)
        
        # Örnek metin
        self.example_text = QTextEdit()
        self.example_text.setReadOnly(True)
        self.example_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Örnek Cümle:"))
        layout.addWidget(self.example_text)
        
        # Telaffuz ipuçları
        self.pronunciation_tips = QTextEdit()
        self.pronunciation_tips.setReadOnly(True)
        self.pronunciation_tips.setMaximumHeight(80)
        layout.addWidget(QLabel("Telaffuz İpuçları:"))
        layout.addWidget(self.pronunciation_tips)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Örneği Dinle")
        self.play_button.clicked.connect(self.play_text)
        button_layout.addWidget(self.play_button)
        
        self.record_button = QPushButton("Konuşmaya Başla")
        self.record_button.clicked.connect(self.start_recording)
        button_layout.addWidget(self.record_button)
        
        self.next_button = QPushButton("Sonraki Cümle")
        self.next_button.clicked.connect(self.next_sentence)
        self.next_button.setEnabled(False)  # Başlangıçta devre dışı
        button_layout.addWidget(self.next_button)
        
        self.translate_button = QPushButton("Çeviri")
        self.translate_button.clicked.connect(self.translate_text)
        button_layout.addWidget(self.translate_button)
        
        self.favorite_button = QPushButton("❤️ Favorilere Ekle")
        self.favorite_button.clicked.connect(self.toggle_favorite)
        button_layout.addWidget(self.favorite_button)
        
        layout.addLayout(button_layout)
        
        # Sonuç alanı
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(80)
        layout.addWidget(QLabel("Sonuç:"))
        layout.addWidget(self.result_text)
        
        # Doğruluk çubuğu
        self.accuracy_bar = QProgressBar()
        self.accuracy_bar.setRange(0, 100)
        layout.addWidget(QLabel("Doğruluk:"))
        layout.addWidget(self.accuracy_bar)
        
        # Geri bildirim
        self.feedback_label = QLabel()
        layout.addWidget(self.feedback_label)
        
        # Çeviri alanı
        self.translation_text = QTextEdit()
        self.translation_text.setReadOnly(True)
        self.translation_text.setMaximumHeight(80)
        layout.addWidget(QLabel("Türkçe Çeviri:"))
        layout.addWidget(self.translation_text)
        
        # İlk cümleyi yükle
        self.next_sentence()

    def start_practice(self):
        """Konuşma pratiğini başlat"""
        self.start_button.setEnabled(False)
        self.next_button.setEnabled(True)
        self.next_sentence()

    def next_sentence(self):
        """Sonraki cümleye geç"""
        category = self.category_combo.currentText()
        
        if category == "Tüm Kategoriler":
            # Rastgele bir cümle seç
            self.current_sentence_index = random.randint(0, len(self.example_sentences) - 1)
        else:
            # Kategori indekslerini bul
            category_indices = {
                "Temel Günlük Konuşmalar (B1)": (0, 10),
                "İş ve Profesyonel Hayat (B1-B2)": (10, 20),
                "Akademik ve Eğitim (B2)": (20, 30),
                "Sosyal Konular ve Güncel Olaylar (B2)": (30, 40),
                "Kültür ve Sanat (B2)": (40, 50),
                "Seyahat ve Deneyimler (B1-B2)": (50, 60),
                "Duygular ve Kişisel Gelişim (B2)": (60, 70),
                "Bilim ve Teknoloji (B2)": (70, 80),
                "Çevre ve Sürdürülebilirlik (B2)": (80, 90),
                "İş İletişimi (B2)": (90, 100),
                "Sağlık ve Wellness (B1-B2)": (100, 110)
            }
            
            # Seçilen kategoriden rastgele bir cümle seç
            start_idx, end_idx = category_indices[category]
            self.current_sentence_index = random.randint(start_idx, end_idx - 1)
        
        self.example_text.setText(self.example_sentences[self.current_sentence_index])
        self.result_text.clear()
        self.accuracy_bar.setValue(0)
        self.feedback_label.clear()
        self.translation_text.clear()
        self.update_pronunciation_tips()

    def on_recording_finished(self, text):
        """Ses tanıma tamamlandığında çağrılır"""
        self.record_button.setEnabled(True)
        
        # Benzerlik oranını hesapla
        similarity = self.calculate_similarity(text.lower(), self.example_text.toPlainText().lower())
        
        # Sonuçları göster
        self.result_text.setText(f"Söylediğiniz: {text}")
        self.accuracy_bar.setValue(int(similarity))
        
        # Geri bildirim ver ve butonları ayarla
        if similarity >= 90:
            feedback = "Mükemmel! 🌟 Sonraki cümleye geçebilirsiniz."
            self.record_button.setText("Tekrar Dene")
            # Sonraki cümleye geçişe izin ver
            self.next_button.setEnabled(True)
        elif similarity >= 75:
            feedback = "Çok iyi! ⭐ Biraz daha pratik yapabilirsiniz."
            self.record_button.setText("Tekrar Dene")
            # Sonraki cümleye geçişe izin ver
            self.next_button.setEnabled(True)
        elif similarity >= 60:
            feedback = "İyi 👍 Biraz daha pratik yapın. Tekrar deneyin."
            self.record_button.setText("Tekrar Dene")
            # Aynı cümlede kal
            self.next_button.setEnabled(False)
        else:
            feedback = "Tekrar denemelisiniz 🔄"
            self.record_button.setText("Tekrar Dene")
            # Aynı cümlede kal
            self.next_button.setEnabled(False)
        
        self.feedback_label.setText(feedback)
        
        # İstatistikleri güncelle
        self.update_statistics(similarity)

    def on_recording_error(self, error):
        """Ses tanıma hatası olduğunda çağrılır"""
        self.record_button.setEnabled(True)
        self.record_button.setText("Konuşmaya Başla")
        self.result_text.setText(f"Hata: {error}")

    def calculate_similarity(self, text1, text2):
        """İki metin arasındaki benzerliği hesapla"""
        # Basit bir benzerlik hesaplama
        words1 = set(text1.split())
        words2 = set(text2.split())
        common_words = words1.intersection(words2)
        
        if not words2:
            return 0
            
        return (len(common_words) / len(words2)) * 100

    def update_statistics(self, similarity):
        """İstatistikleri güncelle"""
        if not hasattr(self, 'total_attempts'):
            self.total_attempts = 0
        if not hasattr(self, 'current_score'):
            self.current_score = 0
            
        self.current_score += similarity
        self.total_attempts += 1
        self.update_progress_label()
        # Otomatik geçiş kaldırıldı

    def init_games_tab(self):
        """Oyunlar sekmesi"""
        layout = QVBoxLayout(self.games_tab)
        
        # Oyun seçim listesi
        games_list = QListWidget()
        games_list.addItems([
            "Kelime Eşleştirme",
            "Cümle Tamamlama",
            "Telaffuz Yarışması",
            "Kelime Hafıza Oyunu",
            "Diyalog Tamamlama"
        ])
        layout.addWidget(QLabel("Oyunlar:"))
        layout.addWidget(games_list)
        
        # Oyun bilgi paneli
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Oyun Bilgisi:"))
        layout.addWidget(info_text)
        
        def update_game_info(current_item):
            game_info = {
                "Kelime Eşleştirme": "İngilizce kelimeleri Türkçe karşılıklarıyla eşleştirin.",
                "Cümle Tamamlama": "Eksik kelimeleri doğru şekilde yerleştirerek cümleleri tamamlayın.",
                "Telaffuz Yarışması": "Kelimeleri doğru telaffuz ederek puan kazanın.",
                "Kelime Hafıza Oyunu": "Eşleşen kelime kartlarını bulun.",
                "Diyalog Tamamlama": "Diyalogdaki boşlukları uygun ifadelerle doldurun."
            }
            if current_item:
                info_text.setText(game_info.get(current_item.text(), ""))
        
        games_list.currentItemChanged.connect(update_game_info)
        
        # Başlat butonu
        start_button = QPushButton("Oyunu Başlat")
        start_button.clicked.connect(lambda: self.start_game(games_list.currentItem().text() if games_list.currentItem() else None))
        layout.addWidget(start_button)
        
    def start_game(self, game_name):
        """Seçilen oyunu başlat"""
        if not game_name:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir oyun seçin!")
            return
            
        QMessageBox.information(self, "Oyun", f"{game_name} yakında eklenecek!")

    def init_analysis_tab(self):
        """Analiz sekmesi"""
        layout = QVBoxLayout(self.analysis_tab)
        
        # Analiz türü seçimi
        analysis_combo = QComboBox()
        analysis_combo.addItems([
            "İlerleme Grafikleri",
            "Telaffuz Analizi",
            "Kelime Kullanım Sıklığı",
            "Performans Raporu",
            "Öğrenme Analizi"
        ])
        layout.addWidget(QLabel("Analiz Türü:"))
        layout.addWidget(analysis_combo)
        
        # Grafik görüntüleme alanı
        graph_area = QWidget()
        graph_area.setMinimumHeight(300)
        layout.addWidget(graph_area)
        
        # Analiz detayları
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        layout.addWidget(QLabel("Detaylar:"))
        layout.addWidget(details_text)
        
        def update_analysis_details(analysis_type):
            """Seçilen analiz türüne göre detayları güncelle"""
            details = {
                "İlerleme Grafikleri": self.get_progress_details(),
                "Telaffuz Analizi": self.get_pronunciation_details(),
                "Kelime Kullanım Sıklığı": self.get_word_usage_details(),
                "Performans Raporu": self.get_performance_details(),
                "Öğrenme Analizi": self.get_learning_details()
            }
            details_text.setText(details.get(analysis_type, ""))
            
        analysis_combo.currentTextChanged.connect(update_analysis_details)
        
        # İstatistik özeti
        stats_layout = QHBoxLayout()
        
        total_practice_label = QLabel(f"Toplam Pratik: {self.total_attempts}")
        stats_layout.addWidget(total_practice_label)
        
        avg_score_label = QLabel(f"Ortalama Puan: {self.get_average_score():.1f}%")
        stats_layout.addWidget(avg_score_label)
        
        layout.addLayout(stats_layout)
        
    def get_progress_details(self):
        """İlerleme detaylarını getir"""
        if not self.daily_stats:
            return "Henüz ilerleme verisi bulunmuyor."
            
        details = "Son 7 Günlük İlerleme:\n\n"
        for date, stats in list(sorted(self.daily_stats.items()))[-7:]:
            if stats['attempts'] > 0:
                avg = stats['total_score'] / stats['attempts']
                details += f"{date}: {avg:.1f}% ({stats['attempts']} pratik)\n"
        return details
        
    def get_pronunciation_details(self):
        """Telaffuz analizi detaylarını getir"""
        return "Telaffuz analizi yakında eklenecek."
        
    def get_word_usage_details(self):
        """Kelime kullanım detaylarını getir"""
        return "Kelime kullanım analizi yakında eklenecek."
        
    def get_performance_details(self):
        """Performans detaylarını getir"""
        if self.total_attempts == 0:
            return "Henüz performans verisi bulunmuyor."
            
        details = f"""Genel Performans:
        
Toplam Pratik: {self.total_attempts}
Ortalama Puan: {self.get_average_score():.1f}%
Pratik Süresi: {self.get_total_practice_time()} dakika
Öğrenilen Kelimeler: {len(self.learned_words)}
"""
        return details
        
    def get_learning_details(self):
        """Öğrenme analizi detaylarını getir"""
        return "Öğrenme analizi yakında eklenecek."
        
    def get_average_score(self):
        """Ortalama puanı hesapla"""
        if self.total_attempts == 0:
            return 0
        return (self.current_score / self.total_attempts)
        
    def get_total_practice_time(self):
        """Toplam pratik süresini dakika cinsinden hesapla"""
        if not hasattr(self, 'practice_start_time'):
            return 0
        return int((time.time() - self.practice_start_time) / 60)

    def init_social_tab(self):
        """Sosyal öğrenme sekmesi"""
        layout = QVBoxLayout(self.social_tab)
        
        # Özellik seçimi
        features_tabs = QTabWidget()
        
        # Grup pratik odası
        group_practice_tab = QWidget()
        group_layout = QVBoxLayout(group_practice_tab)
        group_layout.addWidget(QPushButton("Yeni Oda Oluştur"))
        group_layout.addWidget(QPushButton("Odaya Katıl"))
        features_tabs.addTab(group_practice_tab, "Grup Pratik")
        
        # Partner eşleştirme
        partner_tab = QWidget()
        partner_layout = QVBoxLayout(partner_tab)
        partner_layout.addWidget(QPushButton("Partner Bul"))
        partner_layout.addWidget(QPushButton("Profilim"))
        features_tabs.addTab(partner_tab, "Partner Bul")
        
        # Topluluk
        community_tab = QWidget()
        community_layout = QVBoxLayout(community_tab)
        community_layout.addWidget(QPushButton("Soru Sor"))
        community_layout.addWidget(QPushButton("Cevaplar"))
        features_tabs.addTab(community_tab, "Topluluk")
        
        layout.addWidget(features_tabs)
        
        # Aktif kullanıcılar
        active_users_label = QLabel("Aktif Kullanıcılar: 0")
        layout.addWidget(active_users_label)
        
        # Pratik odaları listesi
        rooms_list = QListWidget()
        layout.addWidget(QLabel("Aktif Pratik Odaları:"))
        layout.addWidget(rooms_list)
        
        # Sohbet alanı
        chat_area = QTextEdit()
        chat_area.setReadOnly(True)
        layout.addWidget(QLabel("Sohbet:"))
        layout.addWidget(chat_area)
        
        # Mesaj gönderme
        message_layout = QHBoxLayout()
        message_input = QLineEdit()
        send_button = QPushButton("Gönder")
        message_layout.addWidget(message_input)
        message_layout.addWidget(send_button)
        layout.addLayout(message_layout) 

    def init_learning_plan_tab(self):
        """Öğrenme planı sekmesi"""
        layout = QVBoxLayout(self.learning_plan_tab)
        
        # Seviye belirleme
        level_button = QPushButton("Seviye Tespit Sınavı")
        level_button.clicked.connect(self.start_level_test)
        layout.addWidget(level_button)
        
        # Hedef belirleme
        goals_group = QGroupBox("Hedefler")
        goals_layout = QVBoxLayout()
        goals_layout.addWidget(QCheckBox("TOEFL Hazırlık"))
        goals_layout.addWidget(QCheckBox("İş İngilizcesi"))
        goals_layout.addWidget(QCheckBox("Günlük Konuşma"))
        goals_group.setLayout(goals_layout)
        layout.addWidget(goals_group)
        
        # Program oluşturma
        create_plan_button = QPushButton("Program Oluştur")
        create_plan_button.clicked.connect(self.create_learning_plan)
        layout.addWidget(create_plan_button)
        
        # Program görüntüleme
        self.schedule_view = QTextEdit()
        self.schedule_view.setReadOnly(True)
        layout.addWidget(QLabel("Haftalık Program:"))
        layout.addWidget(self.schedule_view)
        
    def start_level_test(self):
        """Seviye tespit sınavını başlat"""
        QMessageBox.information(self, "Seviye Testi", "Seviye tespit sınavı yakında eklenecek!")
        
    def create_learning_plan(self):
        """Öğrenme planı oluştur"""
        plan = """Haftalık Çalışma Programı:
        
Pazartesi:
- Kelime Çalışması (30 dk)
- Konuşma Pratiği (30 dk)
- Dinleme Egzersizi (30 dk)

Salı:
- Gramer Tekrarı (30 dk)
- Okuma Anlama (30 dk)
- Telaffuz Çalışması (30 dk)

Çarşamba:
- Diyalog Pratiği (45 dk)
- Yazma Alıştırması (45 dk)

Perşembe:
- Video İzleme ve Not Alma (45 dk)
- Konuşma Pratiği (45 dk)

Cuma:
- Kelime Tekrarı (30 dk)
- Serbest Konuşma (30 dk)
- Haftalık Değerlendirme (30 dk)

Cumartesi-Pazar:
- Film/Dizi İzleme
- İngilizce Kitap Okuma
- Online Language Exchange
"""
        self.schedule_view.setText(plan)
        QMessageBox.information(self, "Program Hazır", "Öğrenme planınız oluşturuldu!")

    def init_multimedia_tab(self):
        """Multimedya sekmesi"""
        layout = QVBoxLayout(self.multimedia_tab)
        
        # Medya türü seçimi
        media_tabs = QTabWidget()
        
        # Video dersler
        video_tab = QWidget()
        video_layout = QVBoxLayout(video_tab)
        video_layout.addWidget(QLabel("Video Dersler"))
        video_list = QListWidget()
        for video in self.video_library.values():
            video_list.addItem(video['title'])
        video_layout.addWidget(video_list)
        media_tabs.addTab(video_tab, "Videolar")
        
        # Diyalog simülasyonları
        dialog_tab = QWidget()
        dialog_layout = QVBoxLayout(dialog_tab)
        dialog_layout.addWidget(QLabel("Diyalog Simülasyonları"))
        dialog_list = QListWidget()
        dialog_list.addItems(self.dialog_scenarios.keys())
        dialog_layout.addWidget(dialog_list)
        media_tabs.addTab(dialog_tab, "Diyaloglar")
        
        # Ses analizi
        audio_tab = QWidget()
        audio_layout = QVBoxLayout(audio_tab)
        audio_layout.addWidget(QLabel("Ses Analizi"))
        
        # Ses kütüphanesi
        audio_list = QListWidget()
        for category in self.audio_library.values():
            for file_desc in category['files'].values():
                audio_list.addItem(file_desc)
        audio_layout.addWidget(audio_list)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        play_button = QPushButton("Oynat")
        play_button.clicked.connect(lambda: self.play_selected_media(
            video_list.currentItem().text() if video_list.currentItem() else None,
            dialog_list.currentItem().text() if dialog_list.currentItem() else None,
            audio_list.currentItem().text() if audio_list.currentItem() else None
        ))
        button_layout.addWidget(play_button)
        
        stop_button = QPushButton("Durdur")
        stop_button.clicked.connect(pygame.mixer.music.stop)
        button_layout.addWidget(stop_button)
        
        audio_layout.addLayout(button_layout)
        media_tabs.addTab(audio_tab, "Ses Analizi")
        
        layout.addWidget(media_tabs)
        
        # Medya bilgi paneli
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Medya Bilgisi:"))
        layout.addWidget(info_text)
        
        def update_media_info(index):
            tab_name = media_tabs.tabText(index)
            if tab_name == "Videolar" and video_list.currentItem():
                title = video_list.currentItem().text()
                video = next((v for v in self.video_library.values() if v['title'] == title), None)
                if video:
                    info_text.setText(f"Başlık: {video['title']}\nAçıklama: {video['description']}")
            elif tab_name == "Diyaloglar" and dialog_list.currentItem():
                scenario = dialog_list.currentItem().text()
                if scenario in self.dialog_scenarios:
                    dialog = self.dialog_scenarios[scenario]
                    info = "Diyalog:\n"
                    for role, text in dialog:
                        info += f"{role}: {text}\n"
                    info_text.setText(info)
            elif tab_name == "Ses Analizi" and audio_list.currentItem():
                info_text.setText(f"Ses Çalışması: {audio_list.currentItem().text()}")
                
        media_tabs.currentChanged.connect(update_media_info)
        video_list.currentItemChanged.connect(lambda: update_media_info(media_tabs.currentIndex()))
        dialog_list.currentItemChanged.connect(lambda: update_media_info(media_tabs.currentIndex()))
        audio_list.currentItemChanged.connect(lambda: update_media_info(media_tabs.currentIndex()))
        
    def play_selected_media(self, video_title=None, dialog_name=None, audio_desc=None):
        """Seçili medyayı oynat"""
        try:
            if video_title:
                video = next((v for v in self.video_library.values() if v['title'] == video_title), None)
                if video:
                    webbrowser.open(video['url'])
            elif dialog_name:
                self.play_dialog_example(dialog_name)
            elif audio_desc:
                # Ses örneğini oynat
                sample_texts = {
                    "Practice 'th' sound": "Think about three things.",
                    "Practice 'r' sound": "Red roses are really romantic.",
                    "Practice '-ed' endings": "I walked and talked yesterday.",
                    "Question intonation": "Would you like some coffee?",
                    "Statement intonation": "This is a simple statement.",
                    "Word emphasis": "I REALLY want to learn English.",
                    "Word stress patterns": "Photography is my favorite hobby.",
                    "Sentence rhythm": "I love to study English every day.",
                    "Connected speech": "What are you going to do today?"
                }
                
                text = sample_texts.get(audio_desc, audio_desc)
                self.cleanup_temp_file()
                tts = gTTS(text=text, lang='en', slow=(self.speech_rate < 0.8))
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_file.close()
                self.temp_audio_file = temp_file.name
                
                tts.save(self.temp_audio_file)
                time.sleep(0.5)
                
                pygame.mixer.music.load(self.temp_audio_file)
                pygame.mixer.music.play()
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Medya oynatılırken hata oluştu: {str(e)}") 

    def init_tools_tab(self):
        """Pratik araçlar sekmesi"""
        layout = QVBoxLayout(self.tools_tab)
        
        # Araç seçimi
        tools_tabs = QTabWidget()
        
        # Sözlük
        dictionary_tab = QWidget()
        dict_layout = QVBoxLayout(dictionary_tab)
        dict_layout.addWidget(QLabel("Sözlük"))
        dict_search = QLineEdit()
        dict_search.setPlaceholderText("Kelime ara...")
        dict_layout.addWidget(dict_search)
        dict_result = QTextEdit()
        dict_result.setReadOnly(True)
        dict_layout.addWidget(dict_result)
        search_button = QPushButton("Ara")
        dict_layout.addWidget(search_button)
        tools_tabs.addTab(dictionary_tab, "Sözlük")
        
        # Gramer kontrol
        grammar_tab = QWidget()
        grammar_layout = QVBoxLayout(grammar_tab)
        grammar_layout.addWidget(QLabel("Gramer Kontrol"))
        grammar_input = QTextEdit()
        grammar_input.setPlaceholderText("Kontrol edilecek metni girin...")
        grammar_layout.addWidget(grammar_input)
        check_button = QPushButton("Kontrol Et")
        grammar_layout.addWidget(check_button)
        grammar_result = QTextEdit()
        grammar_result.setReadOnly(True)
        grammar_layout.addWidget(grammar_result)
        tools_tabs.addTab(grammar_tab, "Gramer")
        
        # Telaffuz kılavuzu
        pronunciation_tab = QWidget()
        pron_layout = QVBoxLayout(pronunciation_tab)
        pron_layout.addWidget(QLabel("Telaffuz Kılavuzu"))
        pron_input = QLineEdit()
        pron_input.setPlaceholderText("Kelime girin...")
        pron_layout.addWidget(pron_input)
        pron_result = QTextEdit()
        pron_result.setReadOnly(True)
        pron_layout.addWidget(pron_result)
        listen_button = QPushButton("Dinle")
        pron_layout.addWidget(listen_button)
        tools_tabs.addTab(pronunciation_tab, "Telaffuz")
        
        # Kelime listesi
        wordlist_tab = QWidget()
        wordlist_layout = QVBoxLayout(wordlist_tab)
        wordlist_layout.addWidget(QLabel("Kelime Listeleri"))
        wordlist_combo = QComboBox()
        wordlist_combo.addItems([
            "Temel Kelimeler",
            "İş İngilizcesi",
            "Akademik Kelimeler",
            "TOEFL Kelimeleri",
            "Deyimler"
        ])
        wordlist_layout.addWidget(wordlist_combo)
        wordlist = QListWidget()
        wordlist_layout.addWidget(wordlist)
        tools_tabs.addTab(wordlist_tab, "Kelime Listesi")
        
        layout.addWidget(tools_tabs)
        
        # Araç açıklamaları
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Araç Bilgisi:"))
        layout.addWidget(info_text)
        
        def update_tool_info(index):
            tool_info = {
                0: "İngilizce-Türkçe ve Türkçe-İngilizce sözlük. Kelime anlamları, örnekler ve telaffuz.",
                1: "Gramer hatalarını kontrol edin ve düzeltme önerileri alın.",
                2: "Kelimelerin doğru telaffuzunu öğrenin ve pratik yapın.",
                3: "Seviyenize uygun kelime listeleri ve çalışma kartları."
            }
            info_text.setText(tool_info.get(index, ""))
            
        tools_tabs.currentChanged.connect(update_tool_info)
        update_tool_info(0)  # İlk sekme için bilgiyi göster

    def init_exam_prep_tab(self):
        """Sınav hazırlık sekmesini başlat"""
        layout = QVBoxLayout(self.exam_prep_tab)
        
        # Sınav seçimi
        exam_selection = QGroupBox("Sınav Seçimi")
        exam_layout = QVBoxLayout()
        
        self.exam_combo = QComboBox()
        self.exam_combo.addItems(["YDS", "YÖKDİL"])
        exam_layout.addWidget(QLabel("Sınav Türü:"))
        exam_layout.addWidget(self.exam_combo)
        
        # Konular listesi
        self.topic_list = QListWidget()
        self.topic_list.addItems([
            "Kelime Bilgisi",
            "Dilbilgisi",
            "Çeviri Teknikleri",
            "Okuma Anlama"
        ])
        exam_layout.addWidget(QLabel("Konular:"))
        exam_layout.addWidget(self.topic_list)
        
        exam_selection.setLayout(exam_layout)
        layout.addWidget(exam_selection)
        
        # Başlatma butonu
        start_button = QPushButton("Seçili Konuyu Başlat")
        start_button.clicked.connect(self.start_selected_topic)
        layout.addWidget(start_button)
        
        # Tam sınav butonu
        full_exam_button = QPushButton("Tam Sınav Başlat")
        full_exam_button.clicked.connect(self.start_full_exam)
        layout.addWidget(full_exam_button)

    def start_selected_topic(self):
        """Seçili konuyu başlat"""
        if not self.topic_list.currentItem():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir konu seçin!")
            return
            
        topic = self.topic_list.currentItem().text()
        exam_type = self.exam_combo.currentText()
        
        if exam_type == "YDS":
            self.start_yds_practice(topic)
        else:  # YÖKDİL
            self.start_yokdil_practice(topic)

    def start_full_exam(self):
        """Tam sınavı başlat"""
        exam_type = self.exam_combo.currentText()
        self.start_exam_practice(exam_type)

    def start_yds_practice(self, topic):
        """YDS pratik sınavını başlat"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"YDS Practice - {topic}")
        dialog.setMinimumSize(800, 600)
        layout = QVBoxLayout(dialog)
        
        # Soruları yükle
        questions = self.load_yds_questions()[topic]
        if not questions:
            QMessageBox.warning(self, "Uyarı", "Bu bölüm için henüz soru bulunmamaktadır.")
            return
            
        # Soru indeksini sıfırla
        self.current_question_index = 0
        self.current_questions = questions  # Soruları sınıf değişkeni olarak sakla
        
        # Soru görüntüleme alanı
        self.question_group = QGroupBox("Soru")
        question_layout = QVBoxLayout()
        
        # Soru sayacı
        self.question_counter = QLabel(f"Soru: 1/{len(questions)}")
        question_layout.addWidget(self.question_counter)
        
        # Soru metni
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        question_layout.addWidget(self.question_label)
        
        # Seçenekler için radio butonlar
        self.radio_buttons = []
        for _ in range(4):
            radio = QRadioButton()
            self.radio_buttons.append(radio)
            question_layout.addWidget(radio)
        
        self.question_group.setLayout(question_layout)
        layout.addWidget(self.question_group)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("Kontrol Et")
        self.check_button.clicked.connect(self.check_current_question)
        button_layout.addWidget(self.check_button)
        
        self.next_button = QPushButton("Sonraki Soru")
        self.next_button.clicked.connect(self.next_question)
        self.next_button.setEnabled(False)  # Başlangıçta devre dışı
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
        
        # İlk soruyu göster
        self.show_current_question()
        
        dialog.exec_()

    def show_current_question(self):
        """Mevcut soruyu göster"""
        if not hasattr(self, 'current_questions') or not hasattr(self, 'current_question_index'):
            return
            
        if 0 <= self.current_question_index < len(self.current_questions):
            question = self.current_questions[self.current_question_index]
            
            # Soru metnini göster
            if "text" in question:
                # Okuma sorusu ise
                self.question_label.setText(f"{question['text']}\n\n{question['question']}")
            else:
                # Normal soru ise
                self.question_label.setText(question["question"])
            
            # Seçenekleri göster
            for i, option in enumerate(question["options"]):
                self.radio_buttons[i].setText(option)
                self.radio_buttons[i].setChecked(False)
            
            # Soru sayacını güncelle
            self.question_counter.setText(f"Soru: {self.current_question_index + 1}/{len(self.current_questions)}")
            
            # Butonları ayarla
            self.check_button.setEnabled(True)
            self.next_button.setEnabled(False)

    def check_current_question(self):
        """Mevcut sorunun cevabını kontrol et"""
        if not hasattr(self, 'current_questions') or not hasattr(self, 'current_question_index'):
            return
            
        if 0 <= self.current_question_index < len(self.current_questions):
            question = self.current_questions[self.current_question_index]
            
            # Seçili cevabı bul
            selected = None
            for i, radio in enumerate(self.radio_buttons):
                if radio.isChecked():
                    selected = i
                    break
            
            if selected is None:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir seçenek seçin!")
                return
                
            # Cevabı kontrol et
            if selected == question["correct"]:
                QMessageBox.information(self, "Doğru!", "Tebrikler! Doğru cevap!")
            else:
                QMessageBox.warning(self, "Yanlış!", 
                    f"Yanlış cevap. Doğru cevap: {question['options'][question['correct']]}")
            
            # Sonraki soru butonunu aktif et
            self.next_button.setEnabled(True)
            self.check_button.setEnabled(False)

    def next_question(self):
        """Sonraki soruya geç"""
        if not hasattr(self, 'current_questions') or not hasattr(self, 'current_question_index'):
            return
            
        self.current_question_index += 1
        
        if self.current_question_index < len(self.current_questions):
            self.show_current_question()
        else:
            QMessageBox.information(self, "Tamamlandı", "Tüm sorular tamamlandı!")
            self.current_question_index = len(self.current_questions) - 1

    def load_yds_questions(self):
        """YDS soruları yükle"""
        return {
            "Kelime Bilgisi": self.generate_yds_vocabulary_questions(),
            "Dilbilgisi": self.generate_yds_grammar_questions(),
            "Çeviri Teknikleri": self.generate_yds_translation_questions(),
            "Okuma Anlama": self.generate_yds_reading_questions()
        }

    def generate_yds_vocabulary_questions(self):
        """YDS kelime bilgisi soruları"""
        return [
            {
                "type": "kelime",
                "question": "The study ______ that regular exercise can improve mental health.",
                "options": ["suggests", "implements", "conducts", "performs"],
                "correct": 0,
                "explanation": "'Suggests' is correct as it means to indicate or imply based on evidence."
            },
            {
                "type": "kelime",
                "question": "The research findings ______ a strong correlation between diet and health.",
                "options": ["indicate", "perform", "conduct", "implement"],
                "correct": 0,
                "explanation": "'Indicate' is correct as it means to show or suggest."
            },
            {
                "type": "kelime",
                "question": "The new technology has ______ improved productivity in the workplace.",
                "options": ["significantly", "marginally", "partially", "slightly"],
                "correct": 0,
                "explanation": "'Significantly' is correct as it means substantially or notably."
            },
            {
                "type": "kelime",
                "question": "Scientists have ______ several potential solutions to the problem.",
                "options": ["proposed", "suggested", "recommended", "advised"],
                "correct": 0,
                "explanation": "'Proposed' is most formal and appropriate in scientific context."
            },
            {
                "type": "kelime",
                "question": "The company's decision to expand has ______ affected local businesses.",
                "options": ["adversely", "negatively", "badly", "poorly"],
                "correct": 0,
                "explanation": "'Adversely' is most formal and precise in this context."
            },
            # ... 15 more vocabulary questions
        ]

    def generate_yds_grammar_questions(self):
        """YDS dilbilgisi soruları"""
        return [
            {
                "type": "dilbilgisi",
                "question": "If I ______ more time yesterday, I would have helped you.",
                "options": ["had had", "have had", "had", "would have"],
                "correct": 0,
                "explanation": "Past unreal conditional requires 'had had' in the if-clause."
            },
            {
                "type": "dilbilgisi",
                "question": "By next month, she ______ at the company for 10 years.",
                "options": ["will have been working", "will work", "has been working", "works"],
                "correct": 0,
                "explanation": "Future Perfect Continuous for ongoing action until future point."
            },
            {
                "type": "dilbilgisi",
                "question": "The project ______ by the end of next week.",
                "options": ["will have been completed", "will complete", "will be completing", "completes"],
                "correct": 0,
                "explanation": "Future Perfect Passive for completed action in future."
            },
            {
                "type": "dilbilgisi",
                "question": "She ______ in London for five years before moving to Paris.",
                "options": ["had been living", "has been living", "was living", "lived"],
                "correct": 0,
                "explanation": "Past Perfect Continuous for duration before past action."
            },
            {
                "type": "dilbilgisi",
                "question": "The report ______ to all department heads by tomorrow morning.",
                "options": ["will have been sent", "will be sent", "will send", "is sent"],
                "correct": 0,
                "explanation": "Future Perfect Passive for completed action by future time."
            },
            # ... 15 more grammar questions
        ]

    def generate_yds_translation_questions(self):
        """YDS çeviri soruları"""
        return [
            {
                "type": "ceviri",
                "question": "Select the best translation: 'Teknolojinin hızlı gelişimi günlük hayatımızı önemli ölçüde etkilemektedir.'",
                "options": [
                    "The rapid development of technology significantly affects our daily life.",
                    "Technology's fast improvement is affecting our daily life.",
                    "The quick advancement of technology is important for daily life.",
                    "Technology develops rapidly to affect our daily life."
                ],
                "correct": 0,
                "explanation": "The first option maintains both meaning and formal tone."
            },
            {
                "type": "ceviri",
                "question": "Choose the best translation: 'Bilimsel araştırmalar, küresel ısınmanın beklenenden daha hızlı ilerlediğini göstermektedir.'",
                "options": [
                    "Scientific research indicates that global warming is progressing faster than expected.",
                    "Scientific studies show global warming is moving fast.",
                    "Research shows that global warming moves quicker than we thought.",
                    "Studies indicate global warming's quick progress."
                ],
                "correct": 0,
                "explanation": "The first option best preserves the formal tone and complete meaning."
            },
            {
                "type": "ceviri",
                "question": "Select the best translation: 'Sürdürülebilir kalkınma, gelecek nesillerin ihtiyaçlarını göz önünde bulundurmalıdır.'",
                "options": [
                    "Sustainable development must take into account the needs of future generations.",
                    "Development should be sustainable for future generations.",
                    "Future generations' needs are important for sustainable development.",
                    "Sustainability in development considers future needs."
                ],
                "correct": 0,
                "explanation": "The first option best captures the formal structure and complete meaning."
            },
            # ... 17 more translation questions
        ]

    def generate_yds_reading_questions(self):
        """YDS okuma soruları"""
        return [
            {
                "type": "okuma",
                "text": """Climate change is one of the most pressing challenges facing our world today. Rising global temperatures have led to more frequent extreme weather events, melting polar ice caps, and rising sea levels. Scientists warn that without immediate action, these changes could have devastating consequences for both human societies and natural ecosystems.""",
                "question": "What is the main concern expressed in the passage about climate change?",
                "options": [
                    "The potential devastating impact on both society and nature",
                    "The rising global temperatures only",
                    "The melting of polar ice caps",
                    "The frequency of extreme weather"
                ],
                "correct": 0,
                "explanation": "The passage emphasizes comprehensive impact on both human societies and ecosystems."
            },
            {
                "type": "okuma",
                "text": """Artificial Intelligence (AI) has revolutionized various sectors of the economy. From healthcare to finance, AI applications are transforming how we work and live. However, this rapid advancement also raises important ethical questions about privacy, job displacement, and the future of human-machine interaction.""",
                "question": "What is the main theme of the passage?",
                "options": [
                    "The impact and implications of AI advancement",
                    "The technical aspects of AI",
                    "The economic benefits of AI",
                    "The future of work"
                ],
                "correct": 0,
                "explanation": "The passage discusses both positive impacts and ethical concerns of AI."
            },
            # ... 18 more reading questions
        ]

    def start_exam_practice(self, exam_type):
        """Sınav pratiği başlat"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{exam_type} Practice")
        dialog.setMinimumSize(1000, 800)
        layout = QVBoxLayout(dialog)
        
        # Soru alanı
        self.question_area = QGroupBox("Soru")
        question_layout = QVBoxLayout()
        
        # Soru metni
        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)
        question_layout.addWidget(self.question_text)
        
        # Cevap seçenekleri
        self.answer_group = QGroupBox("Cevaplar")
        self.answer_layout = QVBoxLayout()
        self.answer_buttons = []
        for _ in range(4):
            radio = QRadioButton()
            self.answer_buttons.append(radio)
            self.answer_layout.addWidget(radio)
        self.answer_group.setLayout(self.answer_layout)
        
        question_layout.addWidget(self.answer_group)
        self.question_area.setLayout(question_layout)
        layout.addWidget(self.question_area)
        
        # Sınav bilgileri
        info_group = QGroupBox("Sınav Bilgileri")
        info_layout = QVBoxLayout()
        
        # Soru sayacı
        self.question_counter = QLabel("Soru: 0/0")
        info_layout.addWidget(self.question_counter)
        
        # Süre
        self.time_label = QLabel("Kalan Süre: 00:00")
        info_layout.addWidget(self.time_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("Kontrol Et")
        self.check_button.clicked.connect(self.check_exam_answer)
        self.check_button.setEnabled(False)
        button_layout.addWidget(self.check_button)
        
        self.next_button = QPushButton("Sonraki Soru")
        self.next_button.clicked.connect(self.next_exam_question)
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button)
        
        self.finish_button = QPushButton("Sınavı Bitir")
        self.finish_button.clicked.connect(self.finish_exam)
        self.finish_button.setEnabled(False)
        button_layout.addWidget(self.finish_button)
        
        layout.addLayout(button_layout)
        
        # Sınav başlatma
        start_button = QPushButton("Sınavı Başlat")
        start_button.clicked.connect(lambda: self.start_selected_exam(exam_type))
        layout.addWidget(start_button)
        
        dialog.exec_()

    def start_selected_exam(self, exam_type):
        """Seçilen sınavı başlat"""
        # Soruları yükle
        questions = []
        if exam_type == "YDS":
            # Her kategoriden 20 soru al
            for category in ["Kelime Bilgisi", "Dilbilgisi", "Çeviri Teknikleri", "Okuma Anlama"]:
                category_questions = self.load_yds_questions()[category]
                if category_questions:
                    # Her kategoriden rastgele 20 soru seç
                    selected = random.sample(category_questions, min(20, len(category_questions)))
                    questions.extend(selected)
        
        if not questions:
            QMessageBox.warning(self, "Uyarı", "Sınav için yeterli soru bulunamadı!")
            return
            
        # Soruları karıştır
        random.shuffle(questions)
        
        # Sınav verilerini ayarla
        self.current_exam = {
            "questions": questions,
            "time": 180  # 3 saat
        }
        self.current_question_index = 0
        self.answers = {}
        
        # Zamanı başlat
        self.remaining_time = self.current_exam["time"] * 60  # saniye cinsinden
        self.update_time_label()
        
        # İlk soruyu göster
        self.show_current_exam_question()
        
        # Butonları aktifleştir
        self.check_button.setEnabled(True)
        self.finish_button.setEnabled(True)
        
        # Zamanlayıcıyı başlat
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_exam_time)
        self.timer.start(1000)  # her saniye güncelle

    def update_exam_time(self):
        """Sınav süresini güncelle"""
        self.remaining_time -= 1
        self.update_time_label()
        
        if self.remaining_time <= 0:
            self.timer.stop()
            self.finish_exam()

    def update_time_label(self):
        """Zaman etiketini güncelle"""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.time_label.setText(f"Kalan Süre: {minutes:02d}:{seconds:02d}")

    def show_current_exam_question(self):
        """Mevcut sınav sorusunu göster"""
        if "sections" in self.current_exam:
            # TOEFL/IELTS formatı
            section = self.current_exam["sections"][self.current_section]
            if self.current_section == "Reading":
                # Okuma sorusu göster
                pass
            elif self.current_section == "Listening":
                # Dinleme sorusu göster
                pass
            # ... diğer bölümler
        else:
            # YDS/YÖKDİL formatı
            question = self.current_exam["questions"][self.current_question_index]
            self.question_text.setText(question["question"])
            
            # Seçenekleri göster
            for i, option in enumerate(question["options"]):
                self.answer_buttons[i].setText(option)
                self.answer_buttons[i].setChecked(False)
            
        # Soru sayacını güncelle
        total_questions = len(self.current_exam["questions"])
        self.question_counter.setText(f"Soru: {self.current_question_index + 1}/{total_questions}")

    def check_exam_answer(self):
        """Sınav cevabını kontrol et"""
        if "sections" in self.current_exam:
            # TOEFL/IELTS formatı
            pass
        else:
            # YDS/YÖKDİL formatı
            question = self.current_exam["questions"][self.current_question_index]
            
            # Seçili cevabı bul
            selected = None
            for i, radio in enumerate(self.answer_buttons):
                if radio.isChecked():
                    selected = i
                    break
            
            if selected is None:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir seçenek seçin!")
                return
            
            # Cevabı kaydet
            self.answers[self.current_question_index] = selected
            
            # Doğru/yanlış kontrolü
            if selected == question["correct"]:
                QMessageBox.information(self, "Doğru!", f"Tebrikler!\n\n{question.get('explanation', '')}")
            else:
                QMessageBox.warning(self, "Yanlış!", 
                    f"Doğru cevap: {question['options'][question['correct']]}\n\n{question.get('explanation', '')}")

    def next_exam_question(self):
        """Sonraki sınav sorusuna geç"""
        if "sections" in self.current_exam:
            # TOEFL/IELTS formatı
            # Bölüm içinde ilerle veya sonraki bölüme geç
            pass
        else:
            # YDS/YÖKDİL formatı
            self.current_question_index += 1
            if self.current_question_index < len(self.current_exam["questions"]):
                self.show_current_exam_question()
            else:
                self.finish_exam()

    def finish_exam(self):
        """Sınavı bitir ve sonuçları göster"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # Sonuçları hesapla
        total_questions = len(self.current_exam["questions"])
        answered_questions = len(self.answers)
        correct_answers = sum(1 for q_idx, answer in self.answers.items() 
                            if answer == self.current_exam["questions"][q_idx]["correct"])
        
        # Sonuç mesajı
        score = (correct_answers / total_questions) * 100
        result_message = f"""
        Sınav tamamlandı!
        
        Toplam Soru: {total_questions}
        Cevaplanan Soru: {answered_questions}
        Doğru Cevap: {correct_answers}
        Yanlış Cevap: {answered_questions - correct_answers}
        Boş Soru: {total_questions - answered_questions}
        
        Başarı Oranı: {score:.2f}%
        """
        
        QMessageBox.information(self, "Sınav Sonucu", result_message)

    def update_analysis(self):
        """Analiz verilerini güncelle"""
        try:
            # Günlük istatistikleri kontrol et
            if not hasattr(self, 'daily_stats'):
                return
                
            if not self.daily_stats:
                self.analysis_text.setText("Henüz veri bulunmamaktadır.")
                return
                
            # Son 7 günün istatistiklerini hesapla
            recent_stats = self.daily_stats[-7:]
            total_practice = sum(day.get('practice_count', 0) for day in recent_stats)
            total_score = sum(day.get('average_score', 0) * day.get('practice_count', 0) 
                            for day in recent_stats)
            
            if total_practice == 0:
                average_score = 0
            else:
                average_score = total_score / total_practice
                
            daily_average = total_practice / len(recent_stats) if recent_stats else 0
            
            # Kategori bazlı istatistikler
            category_stats = {}
            for day in recent_stats:
                for category, stats in day.get('categories', {}).items():
                    if category not in category_stats:
                        category_stats[category] = {'total_score': 0, 'count': 0}
                    category_stats[category]['total_score'] += stats.get('score', 0)
                    category_stats[category]['count'] += stats.get('count', 0)
            
            # Analiz metnini oluştur
            analysis_text = f"""Son 7 Gün Analizi:
            
            Genel İstatistikler:
            - Ortalama Puan: {average_score:.1f}
            - Toplam Pratik: {total_practice}
            - Günlük Ortalama: {daily_average:.1f}
            
            Kategori Bazlı Performans:"""
            
            for category, stats in category_stats.items():
                if stats['count'] > 0:
                    cat_average = stats['total_score'] / stats['count']
                    analysis_text += f"\n{category}:"
                    analysis_text += f"\n  - Ortalama Puan: {cat_average:.1f}"
                    analysis_text += f"\n  - Toplam Pratik: {stats['count']}"
            
            # Günlük ilerleme
            analysis_text += "\n\nGünlük İlerleme:"
            for day in recent_stats:
                date = day.get('date', 'Bilinmeyen Tarih')
                score = day.get('average_score', 0)
                count = day.get('practice_count', 0)
                analysis_text += f"\n{date}: Puan: {score:.1f}, Pratik: {count}"
            
            # Analiz metnini göster
            if hasattr(self, 'analysis_text'):
                self.analysis_text.setText(analysis_text)
                
        except Exception as e:
            print(f"Analiz güncellenirken hata oluştu: {str(e)}")
            if hasattr(self, 'analysis_text'):
                self.analysis_text.setText("Analiz verilerini güncellerken bir hata oluştu.")

    def start_business_practice(self):
        """İş İngilizcesi pratiğini başlat"""
        category = self.business_category.currentText()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"İş İngilizcesi - {category}")
        dialog.setMinimumSize(800, 600)
        layout = QVBoxLayout(dialog)
        
        # Pratik içeriği
        content_group = QGroupBox("Pratik İçeriği")
        content_layout = QVBoxLayout()
        
        # Senaryo veya örnek metin
        scenario_text = QTextEdit()
        scenario_text.setReadOnly(True)
        scenario_text.setText(self.get_business_scenario(category))
        content_layout.addWidget(scenario_text)
        
        # Cevap/pratik alanı
        response_group = QGroupBox("Cevabınız")
        response_layout = QVBoxLayout()
        
        response_text = QTextEdit()
        response_layout.addWidget(response_text)
        
        response_group.setLayout(response_layout)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        layout.addWidget(response_group)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        
        check_button = QPushButton("Kontrol Et")
        check_button.clicked.connect(lambda: self.check_business_response(response_text.toPlainText(), category))
        button_layout.addWidget(check_button)
        
        next_button = QPushButton("Sonraki")
        next_button.clicked.connect(lambda: self.load_next_business_scenario(scenario_text, category))
        button_layout.addWidget(next_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def get_business_scenario(self, category):
        """Kategori için iş senaryosu getir"""
        scenarios = {
            "E-posta Yazma": """Senaryo: Bir iş toplantısını ertelemeniz gerekiyor.
            
            Görev: Aşağıdaki bilgileri içeren profesyonel bir e-posta yazın:
            - Toplantının erteleme sebebi
            - Önerilen yeni tarih ve saat
            - Özür dileme
            - Alternatif tarihler için esneklik""",
            
            "Toplantı İfadeleri": """Senaryo: Proje ilerleme toplantısı yönetiyorsunuz.
            
            Görev: Aşağıdaki durumlar için uygun ifadeleri kullanın:
            - Toplantıyı açma
            - Gündem maddelerini sunma
            - Katılımcılardan görüş alma
            - Toplantıyı özetleme ve kapatma""",
            
            "Sunum Teknikleri": """Senaryo: Yeni bir ürünü tanıtacaksınız.
            
            Görev: Aşağıdaki bölümleri içeren bir sunum hazırlayın:
            - Açılış ve kendinizi tanıtma
            - Ürün özellikleri
            - Pazar analizi
            - Satış hedefleri
            - Soru-cevap yönetimi""",
            
            "Müzakere Becerileri": """Senaryo: Tedarikçi ile fiyat görüşmesi yapıyorsunuz.
            
            Görev: Aşağıdaki durumlar için uygun ifadeleri kullanın:
            - İlk teklifi sunma
            - Karşı teklife cevap verme
            - Koşulları müzakere etme
            - Anlaşmaya varma""",
            
            "Telefon Görüşmeleri": """Senaryo: Uluslararası bir müşteri şikayetini telefonda çözmeniz gerekiyor.
            
            Görev: Aşağıdaki adımları içeren bir görüşme yapın:
            - Karşılama ve kendinizi tanıtma
            - Şikayeti dinleme ve not alma
            - Çözüm önerme
            - Görüşmeyi uygun şekilde sonlandırma"""
        }
        
        return scenarios.get(category, "Senaryo bulunamadı.")

    def check_business_response(self, response, category):
        """İş senaryosu cevabını kontrol et"""
        if not response.strip():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir cevap girin!")
            return
            
        # Basit bir değerlendirme yap
        QMessageBox.information(self, "Değerlendirme", 
            "Cevabınız kaydedildi. Gerçek bir iş ortamında kullanılabilecek iyi bir yanıt!")

    def load_next_business_scenario(self, text_widget, category):
        """Sonraki iş senaryosunu yükle"""
        text_widget.setText(self.get_business_scenario(category))

    def load_business_data(self):
        """İş İngilizcesi verilerini yükle"""
        pass  # Gerekirse burada verileri yükle

    # Diğer sınıf metodları buraya eklenecek