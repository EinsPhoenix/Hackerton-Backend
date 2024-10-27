from ServerInteractions import Login, GetSummaryAndTags, AddNewText
from Grabber import GetPageContent, GetLinksFromCategory
from random import choice
from time import perf_counter
from datetime import timedelta

def main():
    start = perf_counter()
    gateway = "http://10.240.167.215:8000/"
    usernames = ["Noah", "Jan", "David", "Marvin", "Tobias", "Justin", "Halil"]
    tokens = []
    for username in usernames:
        tokens.append(Login(gateway, username))
    with open("createdTexts.txt", "r") as file:
        createdTexts = file.read().split("\n")
    with open("categories.txt", "r") as file:
        categories = file.read().split("\n")
    with open("createdTexts.txt", "a") as file:
        i = 0
        for category in categories:
            links = GetLinksFromCategory(category)
            for link in links:
                token = choice(tokens)
                if link not in createdTexts:
                    titel, content = GetPageContent(f"https://de.wikipedia.org{link}")
                    summary, mainTag, subTags = GetSummaryAndTags(gateway, titel, content, token)
                    if summary:
                        response = AddNewText(gateway, titel, content, summary, mainTag, subTags, token)
                        if response.status_code == 201:
                            createdTexts.append(link)
                            file.write(f"{link}\n")
                            i += 1
                        else:
                            if response.status_code != 404:
                                raise Exception(response.status_code, response.text)
                    if i % 100 == 0:
                        print(f"Links: {i} / Total runtime: {timedelta(seconds=perf_counter() - start)}")

if __name__ == "__main__":
    main()