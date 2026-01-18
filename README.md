\# System SCADA - Automatyczna Mieszalnia Przemysłowa



!\[Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python\&logoColor=white)

!\[PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat\&logo=qt\&logoColor=white)

!\[Matplotlib](https://img.shields.io/badge/Plotting-Matplotlib-11557c?style=flat)

!\[Status](https://img.shields.io/badge/Status-Ukończony-brightgreen)

!\[Course](https://img.shields.io/badge/Przedmiot-Informatyka\_II-blue)

!\[License](https://img.shields.io/badge/License-MIT-grey)



\## 📝 Opis Projektu

Zaawansowana aplikacja wizualizująca proces przemysłowy dozowania, ogrzewania i transportu substancji chemicznych. Projekt realizuje wymagania Etapu II (Python) w ramach przedmiotu Informatyka II.



System symuluje działanie sterownika przemysłowego (PLC/DCS) z wykorzystaniem algorytmów sterowania PID oraz predykcji strat ciepła.



\## 🚀 Główne Funkcjonalności

\* \*\*Wizualizacja High-End:\*\* Interfejs "Cyberpunk/Industrial" z animowanymi pompami wirnikowymi i płynnym przepływem w rurach (technika \*seamless rendering\*).

\* \*\*Zaawansowane Sterowanie (DualPID):\*\* Autorski algorytm obsługujący zarówno grzanie, jak i aktywne chłodzenie w celu utrzymania zadanej temperatury.

\* \*\*Predykcja Feed-Forward:\*\* System oblicza straty ciepła podczas transportu do magazynu i automatycznie koryguje temperaturę docelową ("Naddatek Termiczny").

\* \*\*Realistyczna Fizyka:\*\* Symulacja bezwładności termicznej, mieszania cieczy o różnych temperaturach oraz stygnięcia wg prawa Newtona (nawet po awaryjnym zatrzymaniu).

\* \*\*Bezpieczeństwo:\*\* Obsługa przycisku \*\*AWARYJNY STOP\*\* (Pause) oraz \*\*PEŁNY RESET\*\*.

\* \*\*Telemetria:\*\* Wykresy w czasie rzeczywistym (Matplotlib) oraz logowanie zdarzeń.



\## 🛠️ Wymagania i Instalacja



Projekt wymaga zainstalowanego Pythona (wersja 3.8 lub nowsza).



1\.  \*\*Sklonuj repozytorium:\*\*

&nbsp;   ```bash

&nbsp;   git clone \[https://github.com/TWOJ\_NICK/NAZWA\_REPO.git](https://github.com/TWOJ\_NICK/NAZWA\_REPO.git)

&nbsp;   cd NAZWA\_REPO

&nbsp;   ```



2\.  \*\*Zainstaluj zależności:\*\*

&nbsp;   ```bash

&nbsp;   pip install PyQt5 matplotlib

&nbsp;   ```



3\.  \*\*Uruchom aplikację:\*\*

&nbsp;   ```bash

&nbsp;   python main.py

&nbsp;   ```



\## 📸 Zrzuty Ekranu

\*(Tutaj możesz wrzucić zrzuty ekranu z folderu screenshots, jeśli je dodałeś)\*



\## 👨‍💻 Autor

\*\*Kamil Karpowicz\*\*

Projekt wykonany na zaliczenie przedmiotu Informatyka II.

