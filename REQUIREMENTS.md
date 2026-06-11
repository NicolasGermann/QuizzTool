# QUIZZ Tool
Dieses Dokument beinhaltet die umsetzungsanleitung für die gleichnahmige Web-App.
Umgesetzte Punkte sollen hier mit einem X markiert werden. 
Zu verwendende Technologien:
Frontend: htmx
Backend: Python + FastAPI

## Frontend 
Das Frontend stellt einer vordefinierten Reihenfolge nach jeweils eine der beiden folgenden möglichkeiten dar:
- [x] Infopage:
  Eine Infopage beinhaltet eine Textbox, und ein Bild, welches die rechte Hälfte des Bildschirms einnimmt, wärend 
  der Text die linke Hälfte ausfüllt.
  Außerdem beinhaltet die Seite einen Kleinen Knopf, um auf die nächste Seite fortzufahren.
  
- [x] Quizzpage:
  Die Quizzpage präsentiert in der oberen Bildschirmhälfte jeweils zwei Bilder.
  Die untere Bildschirmhälfte besteht aus zwei möglichen Antwortmöglichkeiten, die der Nutzer auswählen kann.
  Das Auswählen einer Antwort führt zu der nächsten Seite.
  
## Backend
Das Backend beinhaltet folgende Funktionen:
- [x] Die Ausgewählten Antworten sollen, pro Durchlauf mit einer UUID versehen, in einer CSV abgelegt werden

- [x] Die Reihenfolge sowie der Inhalt der seiten sollen einer YAML datei eintnommen werden.

Bitte füge für jeden Typen eine Beispielseite ein, an der man die Funktionsweise des Systems testen kann.
- [x] Beispielseiten für Infopage und Quizpage erstellt

