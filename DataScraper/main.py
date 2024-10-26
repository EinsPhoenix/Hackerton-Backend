from Grabber import GetLinksFromCategory, GetPageContent

def main():
    with open("createdTexts.txt", "r") as file:
        createdTexts = file.read().split("\n")
    with open("categories.txt", "r") as file:
        categories = file.read().split("\n")
    with open("createdTexts.txt", "a") as file:
        for category in categories:
            links = GetLinksFromCategory(category)
            count = 0
            for link in links:
                if link not in createdTexts:
                    titel, content = GetPageContent(f"https://de.wikipedia.org{link}")
                    # TODO: Summary und Tags getten
                        # Text in die Datenbank adden
                    createdTexts.append(link)
                    file.write(f"{link}\n")


if __name__ == "__main__":
    main()