from ServerInteractions import InitServer, Login, GetSummaryAndTags, AddNewText
from Grabber import GetPageContent, GetLinksFromCategory

def main():
    gateway = "http://127.0.0.1:8000/"
    # TODO: Hier muss ich noch den Pfad für den server angeben
    # serverProcess = InitServer(path)
    with open("createdTexts.txt", "r") as file:
        createdTexts = file.read().split("\n")
    with open("categories.txt", "r") as file:
        categories = file.read().split("\n")
    with open("createdTexts.txt", "a") as file:
        token = Login(gateway)
        for category in categories:
            links = GetLinksFromCategory(category)
            count = 0
            for link in links:
                if link not in createdTexts:
                    titel, content = GetPageContent(f"https://de.wikipedia.org{link}")
                    summary, mainTag, subTags = GetSummaryAndTags(gateway, titel, content, token)
                    response = AddNewText(titel, content, summary, mainTag, subTags, token)
                    if response.status_code == 201:
                        createdTexts.append(link)
                        file.write(f"{link}\n")
                        print(f"{link} / Words: {len(content.split(" "))}")
                    else:
                        raise Exception(response.status_code, response.text)
                    count += 1
                    if count == 1:
                        break
    # serverProcess.join()

# Run command:
    # py .\main.py -p "C:\Users\Jan\Documents\Projects\GitRepos\QuizGen\manage.py" -cp "categories.txt"
if __name__ == "__main__":
    main()