# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from html.parser import HTMLParser

from datetime import datetime

import requests

TIME_ZONE_URL = "http://worldtimeapi.org/api/timezone/"
LOC_INF_URL = "https://en.wikivoyage.org/w/api.php"
GEO_INF_URL = "http://api.openweathermap.org/geo/1.0/direct"
#POIS_INF_URL = "https://test.api.amadeus.com/v1/reference-data/locations/pois"
OVER_POI_URL = "https://overpass-api.de/api/interpreter"

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
                res = requests.get(TIME_ZONE_URL)  
                overview = True
            else: 
                res = requests.get(TIME_ZONE_URL+target_timezone)
            res = res.json()
            if(overview):
                string = ", ".join(res)
                output = f"Here is an overview: {string}"
            else:
                if 'error' in res:
                    output = f"Sorry, we could not find the place you are looking for. Please check the spelling/ please type in this structure: Area/Region. You can also use 'world/timestamps' to get an overview of all supported cities and their timezones."
                else:
                    parsed_datetime = datetime.strptime(res['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z")
                    formatted_datetime = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    output = f"The time zone is {res['utc_offset']} and it is now {formatted_datetime}"
        except:
            output = 'Ops! There are too many requests on the time zone API. Please try a few moments later...'
        dispatcher.utter_message(text=output)       
        return []

class ActionGetInformation(Action):
    def name(self):
        return "action_get_information"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        location = tracker.get_slot("location_act")

        if location: 

            params = {
                "action": "query",
                "titles": location,
                "prop": "extracts",
                "exintro": True,
                "format": "json",
            }
            response = requests.get(LOC_INF_URL, params=params)

            data = response.json()
            page_data = data.get("query", {}).get("pages", {})

            if page_data:
                page = next(iter(page_data.values()))
                extract = page.get("extract")
                
                if extract:
                    parser = MyHTMLParser()
                    parser.feed(extract)
                    response_text = f"Here is some information about {location}: {parser.data}"
                else:
                    response_text = f"I couldn't find information of {location}."
            else:
                response_text = f"I couldn't find information of {location}."

        else:
            response_text = "Please provide a valid location."
        dispatcher.utter_message(response_text)
        return []
class ActionGetPointOfInterest(Action):
    def get_geolocation(self, city):
        openweathermap_api_key = "8105293046c7f3f036461a31be0278bd"

        params = {
                    "q": city,
                    "appid": openweathermap_api_key
                }
        response = requests.get(GEO_INF_URL, params=params)

        data = response.json()
        firstResult = data[0]

        if "lat" in firstResult and "lon" in firstResult:
            lat = firstResult["lat"]
            lon = firstResult["lon"]
            return lat, lon
        else:
            return None
    
    def name(self) -> Text:
        return "action_get_pois"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        city = tracker.get_slot("location_act")
        if city:
            lat, lon = self.get_geolocation(city)
            if lat is not None and lon is not None:
                query = f"""
                    [out:json];
                    (
                    node({lat - 0.5}, {lon - 0.5}, {lat + 0.5}, {lon + 0.5})["tourism"];
                    );
                    out body 10;
                    """

                response = requests.post(OVER_POI_URL, data=query)
                data = response.json()


                tourist_pois = [
                    item for item in data['elements'] if 'tourism' in item['tags']
                ]
                if tourist_pois:
                    response_text = ""
                    for poi in tourist_pois:
                        name = poi.get('tags', {}).get('name', 'N/A')
                        category = poi.get('tags', {}).get('tourism', 'N/A')
                        website = poi.get('tags', {}).get('website', 'N/A')
                        info = poi.get('tags', {}).get('information', 'N/A')
                        artworktype = poi.get('tags', {}).get('artwork_type', 'N/A')
                        if name != 'N/A':
                            response_text += f"You have {name}, category: {category}.\n"
                        elif info != 'N/A':
                            response_text += f"You have {info}, category: {category}.\n"
                        elif artworktype != 'N/A':
                            response_text += f"You have {artworktype}, category: {category}.\n" 
                        if website != 'N/A':
                            response_text += f"Website: {website}\n"
                else:
                    response_text = "No points of interest found in the specified city using OpenStreetMap."
            else:
                response_text = "Did not find the given city."
        else:
            response_text = "Please provide a valid city name."

        dispatcher.utter_message(response_text)
        return []
  
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = ""
    
    def handle_data(self, data):
        self.data += data

# Amadeus is very restricted so we stopped using it, the problem was also you need to refresh the api-key very often.
        
# amadeus_api_key = "zyX1eH0WMK2K8PK700uPOpFJg8Zk"

#             geolocation = self.get_geolocation(city)
#             if geolocation:
#                 lat, lon = geolocation
            
#                 headers = {
#                     "Authorization": f"Bearer {amadeus_api_key}"
#                 }
#                 params = {
#                     "latitude":lat,
#                     "longitude": lon,
#                     "radius": 5

#                 }
#                 response = requests.get(POIS_INF_URL, params=params, headers=headers)
#                 points_of_interest = response.json()
#                 print(points_of_interest)
#                 if "data" in points_of_interest:
#                     data = points_of_interest["data"]
#                     response_text = ""
#                     for item in data:
#                         name = item.get("name", "Unknown")
#                         category = item.get("category", "Unknown")
#                         tags = item.get("tags", [])
#                         if tags and name and category:
#                             new_line = '\n'
#                             response_text += f"{new_line}You have {name} this is a {category}. Here are some associated tags: {', '.join(tags)}.{new_line}" 