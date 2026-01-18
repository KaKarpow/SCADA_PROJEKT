# System SCADA - Automatyczna Mieszalnia Przemysłowa

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat&logo=qt&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Plotting-Matplotlib-11557c?style=flat)
![Status](https://img.shields.io/badge/Status-Ukończony-brightgreen)
![Course](https://img.shields.io/badge/Przedmiot-Informatyka_II-blue)
![License](https://img.shields.io/badge/License-MIT-grey)

## 📝 Opis Projektu
Zaawansowana aplikacja wizualizująca proces przemysłowy dozowania, ogrzewania i transportu substancji chemicznych. Projekt realizuje wymagania Etapu II (Python) w ramach przedmiotu Informatyka II.

System symuluje działanie sterownika przemysłowego z wykorzystaniem algorytmów sterowania PID oraz predykcji strat ciepła.

## 🚀 Główne Funkcjonalności
* **Wizualizacja High-End:** Interfejs z animowanymi pompami wirnikowymi i płynnym przepływem w rurach.
* **Zaawansowane Sterowanie (DualPID):** Autorski algorytm obsługujący zarówno grzanie, jak i aktywne chłodzenie w celu utrzymania zadanej temperatury.
* **Predykcja Feed-Forward:** System oblicza straty ciepła podczas transportu do magazynu i automatycznie koryguje temperaturę docelową ("Naddatek Termiczny").
* **Realistyczna Fizyka:** Symulacja bezwładności termicznej, mieszania cieczy o różnych temperaturach oraz stygnięcia wg prawa Newtona (nawet po awaryjnym zatrzymaniu).
* **Bezpieczeństwo:** Obsługa przycisku **AWARYJNY STOP** (Pause) oraz **PEŁNY RESET**.
* **Telemetria:** Wykresy w czasie rzeczywistym (Matplotlib).

## 🛠️ Wymagania i Instalacja

Projekt wymaga zainstalowanego Pythona (wersja 3.8 lub nowsza).

1.  **Sklonuj repozytorium:**
    ```bash
    git clone [https://github.com/KaKarpow/SCADA_PROJEKT.git](https://github.com/KaKarpow/SCADA_PROJEKT.git)
    cd SCADA_PROJEKT
    ```

2.  **Zainstaluj zależności:**
    ```bash
    pip install requirements.txt
    ```

3.  **Uruchom aplikację:**
    ```bash
    python main.py
    ```

## 📸 Zrzuty Ekranu
<img width="1919" height="985" alt="image" src="https://github.com/user-attachments/assets/d9968ecf-f223-4044-9f74-6ad2615ee3c7" />
<img width="1919" height="986" alt="image" src="https://github.com/user-attachments/assets/6caf5df8-7afe-4434-8342-ed948d8fa36a" />


## 👨‍💻 Autor
**Kamil Karpowicz**

Projekt wykonany na zaliczenie przedmiotu Informatyka II.
