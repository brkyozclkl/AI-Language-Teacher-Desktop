import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.utils.config import load_config

def main():
    """
    Uygulamanın ana giriş noktası
    """
    # Konfigürasyon yükleme
    config = load_config()
    
    # PyQt5 uygulamasını başlat
    app = QApplication(sys.argv)
    
    # Ana pencereyi oluştur
    window = MainWindow(config)
    window.show()
    
    # Uygulama döngüsünü başlat
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 