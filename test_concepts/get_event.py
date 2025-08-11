#Global stuff
import requests
from bs4 import BeautifulSoup


GOOGLE_MAPS_API_KEY = "AIzaSyChH0Lums3D9vqBp8vvxNYHYI3pyWFsDys"
params = {
    "key": GOOGLE_MAPS_API_KEY
}


#For now its unfinished but this is just for prototype purposes to see if this would work - it does
#I need to make a loop so that it goes through every month and every competition to then find all the events
def football():
    competitions = [
        "premier-league",
        "league-one",
        "league-two"
    ]

    #BBC_base_URL = f"https://www.bbc.co.uk/sport/football/{COMPETITION NAME}/scores-fixtures/{MONTH}?filter=fixtures"

    page = requests.get(url="https://www.bbc.co.uk/sport/football/championship/scores-fixtures/2025-08?filter=fixtures")
    doc = BeautifulSoup(page.text, 'html.parser')
    #print(doc.prettify())

    for tag in doc.find_all(["h2", "span"]):
        if tag.name == "h2" and "GroupHeader" in tag.get("class", [])[0]:
            print(tag.get_text())
        elif tag.name == "span" and "versus" in tag.get_text():
            print(tag.get_text())


#TicketMaster
ticketAPI = "YLSSMmVAyf64hkBHUzgmF52yLA75gyh5"
