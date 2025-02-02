from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                               QProgressBar, QGridLayout)
from PyQt5.QtCore import Qt
import json
import os
from datetime import datetime

class ProgressTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_progress()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Başlık
        title = QLabel("İlerleme Takibi")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grid layout için container
        grid = QGridLayout()
        
        # Konuşma pratiği ilerleme
        self.speaking_label = QLabel("Konuşma Pratiği:")
        self.speaking_progress = QProgressBar()
        self.speaking_progress.setRange(0, 100)
        grid.addWidget(self.speaking_label, 0, 0)
        grid.addWidget(self.speaking_progress, 0, 1)
        
        # Dilbilgisi ilerleme
        self.grammar_label = QLabel("Dilbilgisi:")
        self.grammar_progress = QProgressBar()
        self.grammar_progress.setRange(0, 100)
        grid.addWidget(self.grammar_label, 1, 0)
        grid.addWidget(self.grammar_progress, 1, 1)
        
        # Kelime bilgisi ilerleme
        self.vocabulary_label = QLabel("Kelime Bilgisi:")
        self.vocabulary_progress = QProgressBar()
        self.vocabulary_progress.setRange(0, 100)
        grid.addWidget(self.vocabulary_label, 2, 0)
        grid.addWidget(self.vocabulary_progress, 2, 1)
        
        # Genel ilerleme
        self.overall_label = QLabel("Genel İlerleme:")
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        grid.addWidget(self.overall_label, 3, 0)
        grid.addWidget(self.overall_progress, 3, 1)
        
        layout.addLayout(grid)
        
        # İstatistikler
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)
        
    def load_progress(self):
        """İlerleme verilerini yükle"""
        try:
            if os.path.exists('progress.json'):
                with open('progress.json', 'r') as f:
                    data = json.load(f)
                    
                self.speaking_progress.setValue(data.get('speaking', 0))
                self.grammar_progress.setValue(data.get('grammar', 0))
                self.vocabulary_progress.setValue(data.get('vocabulary', 0))
                
                # Genel ilerlemeyi hesapla
                overall = (data.get('speaking', 0) + 
                         data.get('grammar', 0) + 
                         data.get('vocabulary', 0)) / 3
                self.overall_progress.setValue(int(overall))
                
                # İstatistikleri göster
                last_practice = data.get('last_practice', 'Henüz pratik yapılmadı')
                total_sessions = data.get('total_sessions', 0)
                stats_text = f"""
                Son Pratik: {last_practice}
                Toplam Oturum: {total_sessions}
                """
                self.stats_label.setText(stats_text)
            else:
                self.reset_progress()
                
        except Exception as e:
            print(f"İlerleme yüklenirken hata: {str(e)}")
            self.reset_progress()
            
    def save_progress(self):
        """İlerleme verilerini kaydet"""
        data = {
            'speaking': self.speaking_progress.value(),
            'grammar': self.grammar_progress.value(),
            'vocabulary': self.vocabulary_progress.value(),
            'last_practice': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'total_sessions': self.get_total_sessions() + 1
        }
        
        try:
            with open('progress.json', 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"İlerleme kaydedilirken hata: {str(e)}")
            
    def reset_progress(self):
        """İlerleme verilerini sıfırla"""
        self.speaking_progress.setValue(0)
        self.grammar_progress.setValue(0)
        self.vocabulary_progress.setValue(0)
        self.overall_progress.setValue(0)
        self.stats_label.setText("Henüz veri yok")
        
    def get_total_sessions(self):
        """Toplam oturum sayısını döndür"""
        try:
            if os.path.exists('progress.json'):
                with open('progress.json', 'r') as f:
                    data = json.load(f)
                    return data.get('total_sessions', 0)
        except:
            pass
        return 0
        
    def update_progress(self, category, value):
        """Belirli bir kategorideki ilerlemeyi güncelle"""
        if category == 'speaking':
            self.speaking_progress.setValue(value)
        elif category == 'grammar':
            self.grammar_progress.setValue(value)
        elif category == 'vocabulary':
            self.vocabulary_progress.setValue(value)
            
        # Genel ilerlemeyi güncelle
        overall = (self.speaking_progress.value() + 
                  self.grammar_progress.value() + 
                  self.vocabulary_progress.value()) / 3
        self.overall_progress.setValue(int(overall))
        
        # İlerlemeyi kaydet
        self.save_progress() 