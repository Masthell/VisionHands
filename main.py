import sys
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

from PySide6.QtWidgets import QApplication
from core.processor import VisionProcessor
from ui.dashboard import Dashboard

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    model_path = 'models/hand_landmarker.task'
    if not os.path.exists(model_path):
        return

    try:
        processor = VisionProcessor()
        window = Dashboard(processor)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
    finally:
        if 'processor' in locals():
            processor.stop()

if __name__ == "__main__":
    main()
