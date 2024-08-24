from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from Config import *
import numpy as np
import os, sys, cv2, win32gui

class SplasherGui(QDialog):

    def __init__(self, config:Config):
        super().__init__()
        try:
            self.timers = []
            # Parse config file
            self.config = config
            self.prefabs = dict(config.get('layout'))
            self.target = str(config.get('target_program'))
            self.media = dict(config.get('media'))
            self.h = max(1, int(self.prefabs['height']))
            self.w = max(1, int(self.prefabs['width']))
            self.ms_l = max(1, int(config.get('launch_interval')))
            self.ms_e = max(1, int(config.get('exit_interval')))
            # Initialize
            self.init_ui()
            self.set_centered_geometry()
            self.set_window_style()
            self.start()
        except Exception as e:
            print("Failed to invoke the constructor.")
            self.exit_app()
            raise e
    
    def __scheduled_task(self, interval:int, target:staticmethod):
        '''Scheduled task will execute only once after the interval'''
        timer = QTimer()
        timer.timeout.connect(lambda:[target(), timer.stop()])
        timer.start(max(1, interval))
        self.timers.append(timer)
    
    def __scheduled_service(self, interval:int, target:staticmethod):
        '''Scheduled service will execute in loop'''
        timer = QTimer()
        timer.timeout.connect(lambda:target())
        timer.start(max(1, interval))
        self.timers.append(timer)

    def set_centered_geometry(self):
        '''Sets the position and size of the window'''
        screen = QDesktopWidget().screenGeometry()
        ax = (screen.width() - self.w) / 2 + self.prefabs['offset_x']
        ay = (screen.height() - self.h) / 2 + self.prefabs['offset_y']
        self.setGeometry(int(ax), int(ay), self.w, self.h)
        print("Setup centered geometry succeeded.")

    def set_window_style(self):
        '''Sets the style of the window'''
        title = f"Custom Splasher (PID {os.getpid()})"
        flags = Qt.SplashScreen | Qt.WindowStaysOnTopHint
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | flags)

        def ensureTopmost():
            try:
                this_int = win32gui.FindWindow(None, title)
                if win32gui.GetForegroundWindow() != this_int:
                    win32gui.SetForegroundWindow(this_int)
                    print("  Set as foreground window.")
            except:
                print("  Failed to set as foreground window.")
        if self.prefabs['force_topmost']:
            self.__scheduled_service(100, ensureTopmost)
        print("Setup window style succeeded.")

    def start(self):
        '''Starts the main job'''
        # Mask
        self.mask_ = np.zeros((self.h, self.w, 3), np.uint8)
        self.mask_[:] = list(self.media['addictive_color'])
        # Video Handler
        def open_video():
            self.cap = cv2.VideoCapture(self.media['file'])
            cap_fps = self.cap.get(cv2.CAP_PROP_FPS) * self.media['speed']
            if cap_fps <= 0:
                raise ValueError(f"Bad frame rate ({self.cap.get(cv2.CAP_PROP_FPS)} * {self.media['speed']})")
            def open_frame():
                ret, img = self.cap.read()
                if ret:
                    self.show_pixmap(img, self.media['reverse_color'], self.mask_)
                else:
                    print("The video has completed playing ahead of time.")
                    self.exit_system()
            self.__scheduled_service(round(1000 / cap_fps), open_frame)
            print(f"  Video detected, {round(1000 / cap_fps)} ms per frame ({round(cap_fps, 1)} fps)")
        # Image Handler
        def open_image():
            img = cv2.imread(self.media['file'], cv2.IMREAD_COLOR)
            self.show_pixmap(img, self.media['reverse_color'], self.mask_)
            print(f"  Image detected")
        # Open media file
        if os.path.isfile(self.media['file']):
            try:
                if os.path.splitext(self.media['file'])[1].lower() in ['.mp4', '.flv', '.avi', '.ogv']:
                    open_video()
                elif os.path.splitext(self.media['file'])[1].lower() in ['.png', '.jpg', '.jpeg', '.jfif', 'bmp']:
                    open_image()
                else:
                    print("  Failed to recognize the media file as neither video nor image.")
                    print("  Trying to open the media file forcibly.")
                    try:
                        open_video()
                    except:
                        open_image()
            except:
                raise RuntimeError(f"Failed to read media file {self.media['file']}")
        else:
            raise FileNotFoundError(f"Not found {self.media['file']}")
        # Tasks
        try:
            pre_cmd = self.config.get('cmd_preprocess')
            if type(pre_cmd) == str and len(pre_cmd) > 0:
                os.system(pre_cmd)
                print(f"  Executed cmd: {pre_cmd}")
        except:
            print("  Failed to execute preprocess cmd")
        def handle_launch():
            os.system(f"start /min cmd /c \"{self.target}\"")
            self.__scheduled_task(self.ms_e, self.exit_system)
        self.__scheduled_task(self.ms_l, handle_launch)
        print("Setup media succeeded.")
        
    def exit_app(self):
        '''Exits the app and closes the window'''
        print("Request for finalization.")
        try:
            for i in self.timers:
                i.stop()
        except:
            pass
        try:
            self.cap.release()
        except:
            pass
        self.close()
    
    def exit_system(self):
        '''Exits the app and stops the whole program'''
        self.exit_app()
        sys.exit(0)
    
    def init_ui(self):
        '''Initializes the UI of the app'''
        self.media_label = QLabel()
        self.media_label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.addWidget(self.media_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        print("Setup layout succeeded.")

    def show_pixmap(self, img, reverse, mask):
        '''Shows a pixmap on the QLabel'''
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.w, self.h), cv2.INTER_LINEAR)
        img = 255 - img if reverse else img
        img = cv2.add(img, mask)
        q_img = QImage(img.data, img.shape[1], img.shape[0], 3 * img.shape[1], QImage.Format.Format_RGB888)
        self.media_label.setPixmap(QPixmap(q_img))
        # print("  Pixmap render.")

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = SplasherGui(Config())
        window.show()
        app.exec_()
    except Exception as e:
        print("\nError! Failed to initialize!\nPlease check your configuration file.")
        print(f"\n{type(e)}: {e.args}")
        raise e
    sys.exit(0)
