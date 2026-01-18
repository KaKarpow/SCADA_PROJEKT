import sys
import datetime
import math
from collections import deque

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, 
                             QGroupBox, QDoubleSpinBox,
                              QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- KONFIGURACJA ---
REFRESH_RATE = 50     # 50ms = 20 FPS
PIPE_WIDTH = 24       # Grube, solidne rury
MAX_HISTORY = 400
AMBIENT_TEMP = 20.0
COOLING_K = 0.0005    # Współczynnik pasywnego stygnięcia
PUMP_SPEED = 1.0      # Prędkość pomp

# --- MATEMATYKA ---

class ThermalComputer:
    """ Oblicza o ile trzeba przegrzać ciecz (Feed-Forward) """
    @staticmethod
    def calculate_required_temp(target_temp, volume):
        if volume <= 0: return target_temp
        cycles = volume / PUMP_SPEED
        seconds = cycles * (REFRESH_RATE / 1000.0)
        # Model strat ciepła w transporcie
        decay = math.exp(-COOLING_K * 20.0 * seconds)
        if decay == 0: return target_temp
        req_temp = AMBIENT_TEMP + (target_temp - AMBIENT_TEMP) / decay
        return req_temp

class DualPID:
    """ PID sterujący grzaniem (+) i chłodzeniem (-) """
    def __init__(self, kp, ki, kd):
        self.kp = kp; self.ki = ki; self.kd = kd
        self.prev_error = 0; self.integral = 0
        
    def compute(self, target, current, dt):
        error = target - current
        
        P = self.kp * error
        
        # Całkowanie tylko w pobliżu celu (Anti-windup)
        if abs(error) < 5.0: self.integral += error * dt
        self.integral = max(min(self.integral, 50), -50)
        I = self.ki * self.integral
        
        D = self.kd * (error - self.prev_error) / dt
        self.prev_error = error
        
        output = P + I + D
        # Zakres -100 (Max Chłodzenie) do 100 (Max Grzanie)
        return max(min(output, 100.0), -100.0)

# --- GRAFIKA (WIDGETY) ---

class CyberTank(QWidget):
    def __init__(self, name, capacity, color_hex):
        super().__init__()
        self.setFixedSize(120, 200)
        self.name = name; self.capacity = capacity
        self.level = 0.0; self.temp = AMBIENT_TEMP
        self.color = QColor(color_hex)
        self.heater_power = 0.0  # > 0
        self.cooling_power = 0.0 # > 0 (gdy PID ujemny)

    def add_liquid(self, amount, t_in):
        if self.level + amount <= self.capacity:
            m_old = self.level; m_new = m_old + amount
            if m_new > 0.001: 
                self.temp = (m_old * self.temp + amount * t_in) / m_new
            self.level += amount
            return True
        return False

    def remove_liquid(self, amount):
        if self.level >= amount: self.level -= amount; return amount
        else: rem = self.level; self.level = 0; return rem

    def update_physics(self, dt):
        if self.level > 1:
            mass_inertia = self.level * 0.2 + 2.0
            
            # 1. Grzanie
            if self.heater_power > 0:
                energy_h = (self.heater_power / 100.0) * 45.0 * dt
                self.temp += energy_h / mass_inertia
            
            # 2. Aktywne Chłodzenie
            if self.cooling_power > 0:
                energy_c = (self.cooling_power / 100.0) * 60.0 * dt 
                self.temp -= energy_c / mass_inertia

        # 3. Pasywne straty
        delta = self.temp - AMBIENT_TEMP
        loss = COOLING_K * delta * 20.0 * dt 
        self.temp -= loss
        self.temp = max(self.temp, AMBIENT_TEMP)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(5,5,-5,-5)
        
        # Tło
        p.setPen(QPen(QColor("#444"), 2)); p.setBrush(QColor("#1a1a1a"))
        p.drawRoundedRect(r, 10, 10)
        
        # Ciecz
        if self.level > 0:
            pct = self.level / self.capacity
            h = pct * (r.height()-4)
            lr = QRectF(r.x()+2, r.bottom()-2-h, r.width()-4, h)
            g = QLinearGradient(lr.topLeft(), lr.topRight())
            g.setColorAt(0, self.color.darker(150)); g.setColorAt(0.5, self.color)
            g.setColorAt(1, self.color.darker(150))
            p.setBrush(g); p.setPen(Qt.NoPen); p.drawRoundedRect(lr, 4, 4)

        # Wizualizacja stanu termicznego
        y = r.bottom() - 25
        if self.heater_power > 1:
            glow = int((self.heater_power/100)*255)
            p.setPen(QPen(QColor(255, 50, 0, glow), 6))
            p.drawLine(int(r.left())+15, int(y), int(r.right())-15, int(y))
            p.setPen(QColor("#ff5555")); p.setFont(QFont("Arial", 8, QFont.Bold))
            p.drawText(r, Qt.AlignBottom|Qt.AlignHCenter, "GRZANIE")
            
        elif self.cooling_power > 1:
            glow = int((self.cooling_power/100)*255)
            p.setPen(QPen(QColor(0, 100, 255, glow), 6)) # Niebieski dla chłodzenia
            p.drawLine(int(r.left())+15, int(y), int(r.right())-15, int(y))
            p.setPen(QColor("#55aaff")); p.setFont(QFont("Arial", 8, QFont.Bold))
            p.drawText(r, Qt.AlignBottom|Qt.AlignHCenter, "CHŁODZENIE")

        p.setPen(QColor("white")); p.setFont(QFont("Consolas", 8))
        p.drawText(r.x(), r.y()-5, r.width(), 20, Qt.AlignCenter, self.name)
        p.setFont(QFont("Consolas", 10, QFont.Bold))
        p.drawText(r, Qt.AlignCenter, f"{self.level:.0f}L\n{self.temp:.1f}°C")

class CyberPipe(QWidget):
    def __init__(self, orient='V'):
        super().__init__()
        self.active = False; self.orient = orient
        # Expanduje aby wypełnić luki w gridzie
        if orient=='V': 
            self.setFixedWidth(PIPE_WIDTH); self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        else: 
            self.setFixedHeight(PIPE_WIDTH); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
    def set_active(self, s): self.active = s; self.update()
    
    def paintEvent(self, e):
        p = QPainter(self)
        c = QColor("#00ccff") if self.active else QColor("#333")
        
        # Overdraw (+2px) żeby zakleić szczeliny
        dr = self.rect()
        if self.orient == 'V': dr.adjust(0, -2, 0, 2)
        else: dr.adjust(-2, 0, 2, 0)
            
        p.fillRect(dr, c)
        
        p.setPen(QPen(QColor(255,255,255,40), 2))
        if self.orient=='V': p.drawLine(6, 0, 6, self.height())
        else: p.drawLine(0, 6, self.width(), 6)

class TurboPump(QWidget):
    def __init__(self, name, type='V'):
        super().__init__()
        # Pompa narożna jest szeroka, żeby dosięgnąć rury z boku
        w = 120 if 'Corner' in type else 60
        self.setFixedSize(w, 60)
        self.name = name; self.pump_type = type
        self.on = False; self.angle = 0
    
    def set_on(self, s): self.on = s; self.update()
    def rotate(self): 
        if self.on: self.angle = (self.angle+60)%360; self.update()
        
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); r = self.rect()
        c_pipe = QColor("#00ccff") if self.on else QColor("#333")
        
        cx = r.center().x(); cy = r.center().y()
        hw = PIPE_WIDTH / 2
        
        p.setPen(Qt.NoPen); p.setBrush(c_pipe)
        
        # Rysowanie Rur z OVERDRAW (Wychodzenie poza obrys dla styku)
        
        if self.pump_type == 'V':
            # Rura pionowa: Wychodzi w górę (-2) i w dół (+2)
            p.drawRect(QRectF(cx-hw, -2, PIPE_WIDTH, r.height()+4))
            
        elif self.pump_type == 'CornerR':
            # Góra -> Środek (Wychodzi w górę -2)
            p.drawRect(QRectF(cx-hw, -2, PIPE_WIDTH, cy+2))
            # Środek -> Prawa Krawędź (Wychodzi w prawo +2)
            p.drawRect(QRectF(cx-hw, cy-hw, r.width()-(cx-hw)+2, PIPE_WIDTH))
            
        elif self.pump_type == 'CornerL':
            # Góra -> Środek
            p.drawRect(QRectF(cx-hw, -2, PIPE_WIDTH, cy+2))
            # Środek -> Lewa Krawędź (Wychodzi w lewo -2)
            p.drawRect(QRectF(-2, cy-hw, cx+hw+2, PIPE_WIDTH))

        # Korpus wirnika
        p.setBrush(QColor(0,0,0, 150)); p.setPen(QPen(QColor("#666"), 2))
        p.drawEllipse(r.center(), 20, 20)

        # Wirnik animowany
        p.save(); p.translate(cx, cy); p.rotate(self.angle)
        col = QColor("#00ff00") if self.on else QColor("#ff4444")
        p.setBrush(col); p.setPen(Qt.NoPen)
        p.drawRect(QRectF(-4, -14, 8, 28)); p.drawRect(QRectF(-14, -4, 28, 8))
        p.restore()
        
        p.setPen(QColor("#ccc")); p.setFont(QFont("Arial", 7, QFont.Bold))
        p.drawText(r, Qt.AlignBottom|Qt.AlignHCenter, self.name)

# --- APLIKACJA ---

class FutureSCADA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA - PROJEKT PG")
        self.resize(1280, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QWidget { color: #dddddd; font-family: 'Segoe UI', sans-serif; }
            QGroupBox { 
                border: 1px solid #444; border-radius: 4px; margin-top: 20px; 
                background: #1a1a1a; font-weight: bold; color: #00ccff;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton {
                background: #333; border: 1px solid #555; color: white; padding: 10px; font-weight: bold;
            }
            QPushButton:hover { background: #444; border-color: #00ccff; }
            QPushButton:disabled { background: #222; color: #555; border-color: #333; }
            QLabel { color: #bbb; font-size: 12px; }
            QTableWidget { background: #1a1a1a; gridline-color: #333; border: none; }
            QHeaderView::section { background: #222; color: #aaa; padding: 4px; }
        """)
        
        self.timer = QTimer(); self.timer.timeout.connect(self.loop)
        self.state = "IDLE"
        self.is_paused = False # Flaga dla AWARYJNEGO STOPU
        self.pid = DualPID(kp=15.0, ki=0.8, kd=5.0)
        self.history = deque(maxlen=MAX_HISTORY)
        self.sim_time = 0.0
        self.calculated_target = 0.0
        
        self.init_ui()

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QHBoxLayout(central); main_layout.setContentsMargins(15,15,15,15)
        
        # --- PANEL LEWY ---
        left = QVBoxLayout()
        
        # Nagłówek
        head = QFrame(); head.setStyleSheet("background: #1e1e1e; border-bottom: 2px solid #00ccff;")
        hl = QHBoxLayout(head)
        self.lcd = QLabel("00:00:00"); self.lcd.setFont(QFont("Consolas", 18, QFont.Bold))
        self.lbl_stat = QLabel("SYSTEM W GOTOWOŚCI"); self.lbl_stat.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 14px;")
        hl.addWidget(QLabel("CZAS PROCESU:")); hl.addWidget(self.lcd); hl.addStretch(); hl.addWidget(self.lbl_stat)
        left.addWidget(head)
        
        # Synoptyka
        scheme_box = QGroupBox("WIZUALIZACJA PROCESU"); sl = QVBoxLayout(scheme_box)
        grid = QGridLayout(); grid.setSpacing(0); grid.setContentsMargins(20,20,20,20)
        
        self.tA = CyberTank("ZB. A", 100, "#00ccff"); self.tA.level=90
        self.tB = CyberTank("ZB. B", 100, "#ffaa00"); self.tB.level=90; self.tB.temp=90
        self.tMix = CyberTank("MIESZALNIK", 200, "#ff00ff")
        self.tOut = CyberTank("MAGAZYN", 300, "#00ff00")
        
        self.pA = TurboPump("P-A", 'CornerR')
        self.pB = TurboPump("P-B", 'CornerL')
        self.pOut = TurboPump("P-OUT", 'V')
        
        self.pipes = [CyberPipe('V') for _ in range(5)] + [CyberPipe('H') for _ in range(2)]
        
        # Układanie na siatce (Bez przerw!)
        grid.addWidget(self.tA, 0, 0, Qt.AlignBottom|Qt.AlignHCenter)
        grid.addWidget(self.tB, 0, 4, Qt.AlignBottom|Qt.AlignHCenter)
        
        grid.addWidget(self.pipes[0], 1, 0, Qt.AlignHCenter)
        grid.addWidget(self.pipes[1], 1, 4, Qt.AlignHCenter)
        
        grid.addWidget(self.pA, 2, 0, Qt.AlignCenter)        
        grid.addWidget(self.pipes[5], 2, 1)                  
        grid.addWidget(self.tMix, 2, 2, 2, 1, Qt.AlignCenter) 
        grid.addWidget(self.pipes[6], 2, 3)                  
        grid.addWidget(self.pB, 2, 4, Qt.AlignCenter)        
        
        grid.addWidget(self.pOut, 4, 2, Qt.AlignTop|Qt.AlignHCenter) 
        grid.addWidget(self.pipes[2], 5, 2, Qt.AlignHCenter) 
        grid.addWidget(self.tOut, 6, 2, Qt.AlignTop|Qt.AlignHCenter)
        
        grid.setRowStretch(1,1); grid.setRowStretch(5,1)
        grid.setColumnStretch(1,1); grid.setColumnStretch(3,1)
        
        sl.addLayout(grid); left.addWidget(scheme_box, stretch=3)
        
        # Sterowanie
        ctrl = QGroupBox("PANEL OPERATORA"); cl = QVBoxLayout(ctrl)
        
        inputs_layout = QGridLayout()
        self.spA = QDoubleSpinBox(); self.spA.setValue(15); self.spA.setSuffix("°C")
        self.spB = QDoubleSpinBox(); self.spB.setValue(95); self.spB.setSuffix("°C")
        self.spT = QDoubleSpinBox(); self.spT.setValue(60); self.spT.setSuffix("°C"); self.spT.setRange(20,95)
        
        inputs_layout.addWidget(QLabel("TEMP. WSADU A:"),0,0); inputs_layout.addWidget(self.spA,0,1)
        inputs_layout.addWidget(QLabel("TEMP. WSADU B:"),1,0); inputs_layout.addWidget(self.spB,1,1)
        inputs_layout.addWidget(QLabel("TEMP. DOCELOWA:"),2,0); inputs_layout.addWidget(self.spT,2,1)
        cl.addLayout(inputs_layout)

        btns_layout = QGridLayout()
        self.btn_start = QPushButton("START"); self.btn_start.clicked.connect(self.start_process)
        self.btn_start.setStyleSheet("border: 2px solid #00ff00; color: #00ff00;")
        
        self.btn_resume = QPushButton("WZNÓW"); self.btn_resume.clicked.connect(self.resume_process)
        self.btn_resume.setStyleSheet("border: 2px solid #ffff00; color: #ffff00;")
        self.btn_resume.setEnabled(False) 
        
        self.btn_pause = QPushButton("AWARYJNY STOP"); self.btn_pause.clicked.connect(self.pause_process)
        self.btn_pause.setStyleSheet("border: 2px solid #ffaa00; color: #ffaa00;")
        
        self.btn_reset = QPushButton("PEŁNY RESET"); self.btn_reset.clicked.connect(self.reset_system)
        self.btn_reset.setStyleSheet("border: 2px solid #ff0000; color: #ff0000;")
        
        btns_layout.addWidget(self.btn_start, 0, 0)
        btns_layout.addWidget(self.btn_resume, 0, 1)
        btns_layout.addWidget(self.btn_pause, 1, 0)
        btns_layout.addWidget(self.btn_reset, 1, 1)
        cl.addLayout(btns_layout)
        
        left.addWidget(ctrl)
        main_layout.addLayout(left, stretch=2)
        
        # --- PANEL PRAWY ---
        right = QVBoxLayout()
        
        plot_box = QGroupBox("TELEMETRIA (PID)"); pl = QVBoxLayout(plot_box)
        self.fig = Figure(facecolor='#1a1a1a'); self.cnv = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111, facecolor='#111')
        self.ax.grid(color='#333', linestyle='--'); self.ax.tick_params(colors='#888')
        for s in self.ax.spines.values(): s.set_color('#444')
        pl.addWidget(self.cnv)
        
        self.line_pv, = self.ax.plot([],[], '#ff3333', lw=2, label='PV (Temp)')
        self.line_sp, = self.ax.plot([],[], '#00ff00', lw=1.5, ls='--', label='SP (Cel)')
        self.line_cv, = self.ax.plot([],[], '#00aaff', lw=1, alpha=0.6, label='Moc (+/-)')
        self.ax.legend(facecolor='#222', edgecolor='#444', labelcolor='white')
        right.addWidget(plot_box, stretch=2)
        
        log_box = QGroupBox("DZIENNIK ZDARZEŃ"); ll = QVBoxLayout(log_box)
        self.log = QTableWidget(0,3); self.log.setHorizontalHeaderLabels(["CZAS","TYP","TREŚĆ"])
        self.log.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log.verticalHeader().setVisible(False)
        ll.addWidget(self.log)
        right.addWidget(log_box, stretch=1)
        
        main_layout.addLayout(right, stretch=3)

    # --- LOGIKA GŁÓWNA ---

    def loop(self):
        dt = REFRESH_RATE / 1000.0
        self.sim_time += dt
        self.lcd.setText(datetime.timedelta(seconds=int(self.sim_time)).__str__())
        
        # FIZYKA ZAWSZE DZIAŁA (nawet przy E-STOP)
        self.tMix.update_physics(dt)
        self.tOut.update_physics(dt)

        # LOGIKA PROCESU (Tylko gdy nie ma pauzy)
        if not self.is_paused:
            if self.state == "FILLING":
                self.lbl_stat.setText(">> NAPEŁNIANIE ZBIORNIKA")
                self.lbl_stat.setStyleSheet("color: #00ccff")
                
                self.pA.set_on(True); self.pB.set_on(True)
                self.pipes[0].set_active(True); self.pipes[1].set_active(True)
                self.pipes[5].set_active(True); self.pipes[6].set_active(True)
                
                volA = self.tA.remove_liquid(PUMP_SPEED); volB = self.tB.remove_liquid(PUMP_SPEED)
                self.tMix.add_liquid(volA, self.tA.temp); self.tMix.add_liquid(volB, self.tB.temp)
                
                if self.tMix.level >= 150 or (self.tA.level<=0 and self.tB.level<=0):
                    self.to_state("CALCULATING")

            elif self.state == "CALCULATING":
                self.pA.set_on(False); self.pB.set_on(False)
                for p in self.pipes: p.set_active(False)
                
                target = self.spT.value()
                self.calculated_target = ThermalComputer.calculate_required_temp(target, self.tMix.level)
                
                diff = self.calculated_target - target
                self.add_log("OBLICZENIA", f"Korekta strat: +{diff:.2f}°C")
                self.to_state("HEATING")

            elif self.state == "HEATING":
                self.lbl_stat.setText(f">> REGULACJA PID (CEL: {self.calculated_target:.1f}°C)")
                self.lbl_stat.setStyleSheet("color: #ffaa00")
                
                out = self.pid.compute(self.calculated_target, self.tMix.temp, dt)
                
                # Obsługa wyjścia bipolarnego
                if out > 0:
                    self.tMix.heater_power = out; self.tMix.cooling_power = 0
                else:
                    self.tMix.heater_power = 0; self.tMix.cooling_power = abs(out)
                
                if abs(self.tMix.temp - self.calculated_target) < 0.1:
                    self.to_state("EMPTYING"); self.tMix.heater_power=0; self.tMix.cooling_power=0

            elif self.state == "EMPTYING":
                self.lbl_stat.setText(">> OPRÓŻNIANIE DO MAGAZYNU")
                self.lbl_stat.setStyleSheet("color: #00ff00")
                self.pOut.set_on(True); self.pipes[2].set_active(True)
                
                vol = self.tMix.remove_liquid(PUMP_SPEED)
                self.tOut.add_liquid(vol, self.tMix.temp)
                
                if self.tMix.level <= 0: self.to_state("DONE")

            elif self.state == "DONE":
                self.pOut.set_on(False); self.pipes[2].set_active(False)
                self.timer.stop()
                
                delta = self.tOut.temp - self.spT.value()
                res = "IDEALNIE" if abs(delta)<0.5 else "OK"
                self.lbl_stat.setText(f"KONIEC. RÓŻNICA: {delta:+.2f}°C [{res}]")
                self.lbl_stat.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 16px;")
                self.add_log("KONIEC", f"Temp Finalna: {self.tOut.temp:.2f}C")
                self.btn_start.setEnabled(True)
                self.btn_resume.setEnabled(False)
        else:
            # TRYB AWARYJNY (PAUZA Z FIZYKĄ)
            self.lbl_stat.setText("!!! AWARYJNY STOP - STYGNIĘCIE !!!")
            self.lbl_stat.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
            
            # Wymuszone wyłączenie elementów wykonawczych
            self.tMix.heater_power = 0; self.tMix.cooling_power = 0
            self.pA.set_on(False); self.pB.set_on(False); self.pOut.set_on(False)
            
            # Animacje też pauzują (chyba że chcesz by się kręciły)
            # W tym bloku nie aktualizujemy logiki procesu, ale fizyka wyżej działa

        # Animacje (Zawsze odświeżamy GUI, ale rotacja tylko jak on=True)
        self.pA.rotate(); self.pB.rotate(); self.pOut.rotate()
        self.tA.update(); self.tB.update(); self.tMix.update(); self.tOut.update()
        
        # Wykres
        sp = self.calculated_target if self.state=="HEATING" else self.spT.value()
        net_power = self.tMix.heater_power - self.tMix.cooling_power
        self.update_plot(self.tMix.temp, sp, net_power)

    def to_state(self, s):
        self.state = s; self.add_log("ZMIANA STANU", s)

    def update_plot(self, pv, sp, cv):
        self.history.append((pv, sp, cv))
        d = list(self.history); x = range(len(d))
        self.line_pv.set_data(x, [v[0] for v in d])
        self.line_sp.set_data(x, [v[1] for v in d])
        self.line_cv.set_data(x, [v[2] for v in d])
        self.ax.set_xlim(0, MAX_HISTORY); self.ax.set_ylim(-110, 110)
        self.cnv.draw()

    def add_log(self, type, msg):
        r = self.log.rowCount(); self.log.insertRow(r)
        t = datetime.datetime.now().strftime("%H:%M:%S")
        self.log.setItem(r,0,QTableWidgetItem(t)); self.log.setItem(r,1,QTableWidgetItem(type))
        self.log.setItem(r,2,QTableWidgetItem(str(msg)))
        self.log.scrollToBottom()

    # --- BUTTON SLOTS ---

    def start_process(self):
        if self.state != "IDLE" and self.state != "DONE": return
        self.tA.temp = self.spA.value(); self.tB.temp = self.spB.value()
        self.history.clear(); self.pid.integral=0; self.sim_time=0
        self.to_state("FILLING")
        self.is_paused = False
        self.timer.start(REFRESH_RATE)
        self.btn_start.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.log.setRowCount(0); self.add_log("SYSTEM", "START PROCESU")

    def pause_process(self):
        if self.state == "IDLE" or self.state == "DONE": return
        # Nie zatrzymujemy timera, tylko wchodzimy w tryb pauzy logicznej
        self.is_paused = True
        self.add_log("SYSTEM", "AWARYJNE ZATRZYMANIE")
        self.btn_resume.setEnabled(True)

    def resume_process(self):
        if self.state == "IDLE" or self.state == "DONE": return
        self.is_paused = False
        self.lbl_stat.setText("PROCES WZNOWIONY")
        self.add_log("SYSTEM", "WZNOWIONO")
        self.btn_resume.setEnabled(False)

    def reset_system(self):
        self.timer.stop(); self.state="IDLE"; self.is_paused = False
        self.btn_start.setEnabled(True); self.btn_resume.setEnabled(False)
        
        self.tA.level=90; self.tB.level=90; self.tMix.level=0; self.tOut.level=0
        self.tMix.heater_power=0; self.tMix.cooling_power=0; self.tMix.temp=20; self.tOut.temp=20
        
        self.pA.set_on(False); self.pB.set_on(False); self.pOut.set_on(False)
        for p in self.pipes: p.set_active(False)
        self.tA.update(); self.tMix.update(); self.tOut.update()
        
        self.lbl_stat.setText("SYSTEM ZRESETOWANY")
        self.add_log("SYSTEM", "PEŁNY RESET")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FutureSCADA()
    window.show()
    sys.exit(app.exec_())