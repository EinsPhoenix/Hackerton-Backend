from Grabber import GetLinksFromCategory

def main():
    scrapedLinks = []
    duplicates = []
    with open("categories.txt", "r") as file:
        categories = file.read().split("\n")
    with open("createdTexts.txt", "a") as file:
        for category in categories:
            print(category)
            links = GetLinksFromCategory(category)
            for link in links:
                if link not in scrapedLinks:
                    scrapedLinks.append(link)
                else:
                    duplicates.append(link)
        print(f"Total Links: {len(scrapedLinks)}")
        print(f"Total dups: {len(duplicates)}")
   
if __name__ == "__main__":
    main()