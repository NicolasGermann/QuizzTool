# QUIZZ Tool
Dieses Dokument beinhaltet die umsetzungsanleitung für die gleichnahmige Web-App.
Umgesetzte Punkte sollen hier mit einem X markiert werden. 
Zu verwendende Technologien:
Frontend: htmx
Backend: Python + FastAPI

## Frontend 
Das Frontend stellt einer vordefinierten Reihenfolge nach jeweils eine der folgenden möglichkeiten dar:

- [x] Infopage:
  Eine Infopage beinhaltet eine Textbox, und ein Bild, welches die rechte Hälfte des Bildschirms einnimmt, wärend 
  der Text die linke Hälfte ausfüllt.
  Außerdem beinhaltet die Seite einen Kleinen Knopf, um auf die nächste Seite fortzufahren.
  
- [x] Quizzpage:
  Die Quizzpage präsentiert in der oberen Bildschirmhälfte ein oder zwei Bilder.
  Die untere Bildschirmhälfte besteht aus zwei möglichen Antwortmöglichkeiten, die der Nutzer auswählen kann.
  Das Auswählen einer Antwort führt zu der nächsten Seite.
  - [x] Unterstützt ein einzelnes Bild (zentriert)
  - [x] Unterstützt zwei Bilder (nebeneinander)
  - [x] Optional: `save`-Feld (true/false) steuert, ob die Antwort in der CSV gespeichert wird
  - [x] Optional: `correct_answer`-Feld markiert die richtige Antwort

- [x] Quiz-Feedback-Page:
  Eine Feedback-Seite, die nach einer Quizseite angezeigt wird.
  Informiert den Nutzer, ob die vorherige Antwort richtig oder falsch war.
  - [x] Zeigt unterschiedliche Texte für richtige/falsche Antworten
  - [x] Findet automatisch die vorherige Quizseite (oder über `ref_page` konfigurierbar)
  - [x] Speichert selbst keine Daten in der CSV

- [x] Input-Page:
  Eine Seite mit Text und einem Eingabefeld für Zahlen.
  - [x] Zeigt einen beschreibenden Text und ein optionales Bild
  - [x] Eingabefeld mit konfigurierbarem Label, Min- und Max-Werten
  - [x] Speichert den eingegebenen Zahlenwert direkt in der CSV
  - [x] Beispiel: Altersabfrage vor dem Quiz

- [x] Slider-Page:
  Eine Seite mit Text und beliebig vielen Schiebereglern.
  - [x] Zeigt einen beschreibenden Text und ein optionales Bild
  - [x] Beliebige Anzahl an Schiebereglern konfigurierbar
  - [x] Jeder Regler hat konfigurierbaren Text, Min- und Max-Wert
  - [x] Live-Anzeige des aktuellen Wertes
  - [x] Speichert alle Slider-Werte in separaten CSV-Spalten
  - [x] Beispiel: Selbsteinschätzung mit mehreren Skalen

- [x] Responsive Design:
  Alle Seiten sind für verschiedene Bildschirmgrößen optimiert
  - [x] Mobile-optimiert (Stapelung bei schmalen Bildschirmen)
  - [x] Bilder bleiben immer vollständig sichtbar
  - [x] Scrollbar bei kleinen Bildschirmen

## Backend
Das Backend beinhaltet folgende Funktionen:

- [x] Die Ausgewählten Antworten sollen, pro Durchlauf mit einer UUID versehen, in einer CSV abgelegt werden
  - [x] Quizseiten speichern "richtig" oder "falsch" (nicht den tatsächlichen Antworttext)
  - [x] Input-Seiten speichern den eingegebenen Zahlenwert direkt
  - [x] Slider-Seiten speichern jeden Regler-Wert in einer eigenen Spalte
  - [x] Jede Spalte repräsentiert eine Quiz-, Input- oder Slider-Seite (quiz_0, ..., input_0, ..., slider_0, ...)
  - [x] File-Locking für gleichzeitige Zugriffe mehrerer Nutzer

- [x] Die Reihenfolge sowie der Inhalt der seiten sollen einer YAML datei eintnommen werden.
  - [x] Unterstützung mehrerer YAML-Dateien (pages.yaml, pages2.yaml, etc.)
  - [x] Zufällige Auswahl einer YAML-Datei beim Start jeder Session
  - [x] Jede YAML-Datei hat ihre eigene CSV-Datei (answers_pages.csv, answers_pages2.csv, etc.)
  - [x] YAML-Datei wird pro Session beibehalten (via Cookie)

Bitte füge für jeden Typen eine Beispielseite ein, an der man die Funktionsweise des Systems testen kann.
- [x] Beispielseiten für Infopage und Quizpage erstellt
- [x] Beispielseiten für Quiz-Feedback-Page erstellt
- [x] Beispiel für Quiz mit einem Bild
- [x] Zweite YAML-Datei mit anderem Aufbau (Tier-Quiz)

## Docker
- [x] Dockerfile für einfachen Deployment
- [x] Volume-Mount für persistente CSV-Daten (/app/data)

