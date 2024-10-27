# Data Scraper

## Funktion

    - Durch angeben von Wikipedia Kategorien können viele Wikipedia Artikel auf ein mal in die Datenbank eingelesen werden

## Handhabung

### Vorbereitung

    - Suchen passender Wikipedia Kategorien
    - Datenbank initialisieren
    - "requirements.txt" installieren

### Setup

    - Kategorien in categories.txt einfügen
        - Eine Kategorie pro Zeile
        - (Hinweis) "precheck.py" kann ausgeführt werden, um die Anzahl der Wikipedia Artikel zu kontrollieren
    - In "main.py"
        - Serveradresse in "gateway" speichern
        - Gewünschte Autornamen in "usernames" speichern