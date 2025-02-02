from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt
from transformers import pipeline

class ChatTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Sohbet geçmişini başlat
        self.chat_history = []
        # Sohbet modelini başlat
        self.conversation = pipeline(
            "text-generation",
            model="gpt2"  # Daha küçük bir model kullanıyoruz
        )
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Başlık
        title = QLabel("Sohbet Botu")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Sohbet geçmişi alanı
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setMinimumHeight(300)
        layout.addWidget(self.chat_area)
        
        # Mesaj giriş alanı
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Mesajınızı yazın...")
        layout.addWidget(self.message_input)
        
        # Gönder butonu
        self.send_button = QPushButton("Gönder")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)
        
        # Başlangıç mesajını göster
        self.add_bot_message("Merhaba! Benimle İngilizce pratik yapabilirsin. Nasıl yardımcı olabilirim?")
        
    def add_user_message(self, message):
        """Kullanıcı mesajını sohbet alanına ekle"""
        self.chat_area.append(f"<p style='color: blue;'><b>Sen:</b> {message}</p>")
        self.chat_history.append({"role": "user", "content": message})
        
    def add_bot_message(self, message):
        """Bot mesajını sohbet alanına ekle"""
        self.chat_area.append(f"<p style='color: green;'><b>Bot:</b> {message}</p>")
        self.chat_history.append({"role": "assistant", "content": message})
        
    def send_message(self):
        """Mesajı gönder ve yanıt al"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
            
        # Kullanıcı mesajını göster
        self.add_user_message(message)
        self.message_input.clear()
        
        try:
            # Bot yanıtını al
            context = " ".join([msg["content"] for msg in self.chat_history[-3:]])  # Son 3 mesajı kullan
            response = self.conversation(context + "\nBot:", max_length=100, num_return_sequences=1)
            bot_response = response[0]['generated_text'].split("\nBot:")[-1].strip()
            
            # Bot yanıtını göster
            self.add_bot_message(bot_response)
            
        except Exception as e:
            self.add_bot_message(f"Üzgünüm, bir hata oluştu: {str(e)}")
            
        # Sohbet alanını en alta kaydır
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )