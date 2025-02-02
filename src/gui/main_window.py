from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QTabWidget, QPushButton, QLabel)
from PyQt5.QtCore import Qt
from .tabs.speech_tab import SpeechTab
from .tabs.grammar_tab import GrammarTab
from .tabs.chat_tab import ChatTab
from .tabs.progress_tab import ProgressTab

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        """
        Kullanıcı arayüzünü başlat
        """
        # Ana pencere ayarları
        self.setWindowTitle('AI Dil Öğretmeni')
        self.setGeometry(100, 100, 1200, 800)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Hoşgeldin mesajı
        welcome_label = QLabel("AI Dil Öğretmenine Hoş Geldiniz!")
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Tab widget oluştur
        tabs = QTabWidget()
        
        # Tabları ekle
        tabs.addTab(SpeechTab(self), "Konuşma Pratiği")
        tabs.addTab(GrammarTab(self), "Dilbilgisi")
        tabs.addTab(ChatTab(self), "Sohbet")
        tabs.addTab(ProgressTab(self), "İlerleme")
        
        layout.addWidget(tabs)
        
        # Durum çubuğu
        self.statusBar().showMessage('Hazır') 