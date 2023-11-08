# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from html.parser import HTMLParser

import requests

BASE_URL = "http://worldtimeapi.org/api/timezone/"

class ActionShowTimeZone(Action):
    def name(self) -> Text:
        return "action_find_timezone"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # we can get values from slots by `tracker` object
        target_timezone = tracker.get_slot('target_timezone')
        try:
            overview = False
            if(target_timezone == "World/Timestamps"):
                res = requests.get(BASE_URL)  
                overview = True
            else: 
                res = requests.get(BASE_URL+target_timezone)
            res = res.json()
            if(overview):
                string = ", ".join(res)
                output = f"Here is an overview: {string}"
            else:
                if 'error' in res:
                    output = f"Sorry, we could not find the place you are looking for. Please check the spelling/ please type in this structure: Area/Region. You can also use 'world/timestamps' to get an overview of all supported cities and their timezones."
                elif res['utc_offset']:
                    output = f"Time zone is {res['utc_offset']}"
        except:
            output = 'Ops! There are too many requests on the time zone API. Please try a few moments later...'
        dispatcher.utter_message(text=output)       
        return []

class ActionGetActivities(Action):
    def name(self):
        return "action_get_activities"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        location = tracker.get_slot("location_act")

        if location:
            # Define the API endpoint for Wikivoyage
            api_url = f"https://en.wikivoyage.org/w/api.php"
            
            # Set up the parameters for the API request
            params = {
                "action": "query",
                "titles": location,
                "prop": "extracts",
                "exintro": True,
                "format": "json",
            }
            response = requests.get(api_url, params=params)
            data = response.json()
            # Extract information from the API response
            page_data = data.get("query", {}).get("pages", {})
            if page_data:
                # Retrieve the first page (usually the location page)
                page = next(iter(page_data.values()))
                # Extract the extract (introduction) from the page
                extract = page.get("extract")
                if extract:
                    parser = MyHTMLParser()
                    parser.feed(extract)
                    response_text = f"Here are some popular activities in {location}: {parser.data}"
                else:
                    response_text = f"I couldn't find information about activities in {location}."
            else:
                response_text = f"I couldn't find information about activities in {location}."

        else:
            response_text = "Please provide a valid location."
        dispatcher.utter_message(response_text)
        return []

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = ""
    
    def handle_data(self, data):
        self.data += data