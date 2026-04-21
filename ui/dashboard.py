import sys
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QSystemTrayIcon, QMenu, QSlider)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QAction, QIcon, QColor
from utils.db_manager import SettingsDB

class Dashboard(QMainWindow):
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.db = SettingsDB()
        
        self.setWindowTitle("VisionHands Senior Pro")
        self.setFixedSize(800, 600)
        
        self.camera_active = True

        self._init_ui()
        self._init_tray()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 5, 15, 15)
        self.main_layout.setSpacing(0)

        self.central_widget.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                  stop:0 rgba(10, 15, 35, 255), stop:1 rgba(20, 35, 80, 255));
                color: white; font-family: 'Segoe UI', sans-serif;
            }
        """)

        self.status_label = QLabel("SYSTEM: LOCKED")
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #55aaff; border: none; height: 30px;")
        self.main_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # Видео контейнер 16:9 (640x360)
        self.video_frame = QFrame()
        self.video_frame.setFixedSize(644, 364)
        self.video_frame.setStyleSheet("border: 2px solid #005aff; border-radius: 12px; background: black;")
        v_layout = QVBoxLayout(self.video_frame)
        v_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_container = QLabel()
        self.video_container.setFixedSize(640, 360)
        v_layout.addWidget(self.video_container)
        self.main_layout.addWidget(self.video_frame, alignment=Qt.AlignCenter)

        self.main_layout.addSpacing(15)

        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(50, 0, 50, 0)
        
        sens_vbox = QVBoxLayout()
        sens_vbox.addWidget(QLabel("SENSITIVITY"), alignment=Qt.AlignCenter)
        self.sens_slider = QSlider(Qt.Horizontal)
        self.sens_slider.setRange(5, 30)
        self.sens_slider.setValue(int(self.db.get('mouse_sensitivity') * 10))
        self.sens_slider.valueChanged.connect(self.save_settings)
        sens_vbox.addWidget(self.sens_slider)
        settings_layout.addLayout(sens_vbox)

        smooth_vbox = QVBoxLayout()
        smooth_vbox.addWidget(QLabel("SMOOTHING"), alignment=Qt.AlignCenter)
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setRange(1, 100)
        self.smooth_slider.setValue(int(self.db.get('smoothing_beta') * 1000))
        self.smooth_slider.valueChanged.connect(self.save_settings)
        smooth_vbox.addWidget(self.smooth_slider)
        settings_layout.addLayout(smooth_vbox)
        
        self.main_layout.addLayout(settings_layout)

        self.main_layout.addSpacing(25)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(20) # Больше места между кнопками
        
        self.cam_btn = QPushButton("CAM OFF")
        self.cam_btn.setStyleSheet(self._btn_style("#005aff"))
        self.cam_btn.clicked.connect(self.toggle_camera)
        
        self.tray_btn = QPushButton("TRAY")
        self.tray_btn.setStyleSheet(self._btn_style("#55aaff"))
        self.tray_btn.clicked.connect(self.hide)
        
        self.exit_btn = QPushButton("EXIT")
        self.exit_btn.setStyleSheet(self._btn_style("#ff4444"))
        self.exit_btn.clicked.connect(QApplication.instance().quit)
        
        self.button_layout.addWidget(self.cam_btn)
        self.button_layout.addWidget(self.tray_btn)
        self.button_layout.addWidget(self.exit_btn)
        self.main_layout.addLayout(self.button_layout)

    def _btn_style(self, color):
        return f"""
            QPushButton {{ 
                background: rgba(0,0,0,0.3); 
                border: 1px solid {color}; 
                color: {color}; 
                padding: 14px; 
                border-radius: 10px; 
                font-weight: bold; 
                font-size: 13px;
                min-width: 180px; 
            }} 
            QPushButton:hover {{ 
                background: {color}; 
                color: white; 
            }}
        """

    def save_settings(self):
        new_sens = self.sens_slider.value() / 10.0
        new_smooth = self.smooth_slider.value() / 1000.0
        self.db.set('mouse_sensitivity', new_sens)
        self.db.set('smoothing_beta', new_smooth)
        self.processor.update_settings(new_sens, new_smooth)

    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_pixmap = QPixmap(32, 32)
        icon_pixmap.fill(QColor(0, 90, 255))
        self.tray_icon.setIcon(QIcon(icon_pixmap))
        self.tray_icon.show()

    def toggle_camera(self):
        self.camera_active = not self.camera_active
        self.cam_btn.setText("CAM ON" if not self.camera_active else "CAM OFF")

    def update_frame(self):
        if not self.camera_active: return
        frame, _, _, profile, is_auth = self.processor.get_ui_data()
        if frame is not None:
            self.status_label.setText(f"SYSTEM: {profile.upper()}" if is_auth else "SYSTEM: LOCKED")
            self.status_label.setStyleSheet(f"color: {'#00ffaa' if is_auth else '#55aaff'}; font-size: 18px; font-weight: bold; border: none;")
            
            h, w = frame.shape[:2]
            target_h = int(w * 9 / 16)
            if h > target_h:
                start = (h - target_h) // 2
                frame = frame[start:start+target_h, :]

            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
            self.video_container.setPixmap(QPixmap.fromImage(qt_image).scaled(640, 360, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        self.hide()
        event.ignore()
