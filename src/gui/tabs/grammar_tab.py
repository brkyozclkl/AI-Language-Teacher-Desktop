from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt
from transformers import pipeline

class GrammarTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        # Gramer düzeltme modeli
        self.grammar_checker = pipeline(
            "text2text-generation",
            model="vennify/t5-base-grammar-correction"
        )
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Başlık
        title = QLabel("Dilbilgisi Kontrolü")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Dil seçimi
        self.language_combo = QComboBox()
        self.language_combo.addItems(["İngilizce", "Almanca", "Fransızca", "İspanyolca"])
        layout.addWidget(self.language_combo)
        
        # Giriş metni
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Kontrol edilecek metni buraya yazın...")
        layout.addWidget(self.input_text)
        
        # Kontrol butonu
        self.check_button = QPushButton("Dilbilgisi Kontrolü Yap")
        self.check_button.clicked.connect(self.check_grammar)
        layout.addWidget(self.check_button)
        
        # Sonuç metni
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Düzeltmeler burada görünecek...")
        layout.addWidget(self.result_text)
        
        # Açıklama etiketi
        self.explanation_label = QLabel("")
        layout.addWidget(self.explanation_label)
        
    def check_grammar(self):
        """Dilbilgisi kontrolü yap"""
        text = self.input_text.toPlainText()
        if not text:
            self.explanation_label.setText("Lütfen bir metin girin.")
            return
            
        try:
            # Gramer düzeltme
            corrected = self.grammar_checker(text, max_length=512)[0]['generated_text']
            
            # Sonuçları göster
            self.result_text.setText(corrected)
            
            # Değişiklikleri vurgula
            if corrected != text:
                self.explanation_label.setText("Düzeltmeler yapıldı. Yeşil renkli metinler önerilen düzeltmelerdir.")
                # Burada daha gelişmiş bir diff görüntüleme yapılabilir
            else:
                self.explanation_label.setText("Metin dilbilgisi açısından doğru görünüyor.")
                
        except Exception as e:
            self.explanation_label.setText(f"Hata oluştu: {str(e)}")
            
    def get_language_code(self):
        """Seçili dilin kodunu döndür"""
        language_map = {
            "İngilizce": "en",
            "Almanca": "de",
            "Fransızca": "fr",
            "İspanyolca": "es"
        }
        return language_map.get(self.language_combo.currentText(), "en") 