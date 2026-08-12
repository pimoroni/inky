"""
Python script to fetch a randomised comic cover from the Comic Vine API and show it on an Inky Impression display.
You will need to sign up for an API key at https://comicvine.gamespot.com/api/ to use this script.
Change the search query to the comic series you want to display!
"""

import random
from io import BytesIO

import requests
from PIL import Image

from inky.auto import auto

# Comic Vine API details
API_KEY = "API_KEY_GOES_HERE"
BASE_URL = "https://comicvine.gamespot.com/api/"
HEADERS = {"User-Agent": "Python Comic Vine Client"}

# List of comic series to display, separated by commas. You can add more series to this list, or change the existing ones.
SEARCH_QUERIES = ["Weird Science"]
# Set to True to pick a random volume from the query results (this is helpful if the series is split into multiple volumes):
RANDOM_VOLUME = False

# Inky Impression display setup
inky_display = auto()


def find_volume_id(api_key, query):
    # Our first API call finds a list of volumes that match the search query, and then picks one
    params = {"api_key": api_key, "format": "json", "query": query, "resources": "volume", "limit": 5}
    response = requests.get(f"{BASE_URL}search/", headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    response.close()
    results = data.get("results", [])
    if results:
        for idx, volume in enumerate(results, 1):
            print(f"{idx}: {volume['name']} (ID: {volume['id']}, Start Year: {volume.get('start_year', 'N/A')})")

        if RANDOM_VOLUME is True:
            # Pick a random volume from the search results
            chosen = random.choice(results)
            print(f"Randomly selected: {chosen['name']} (ID: {chosen['id']})")
        else:
            # Pick the first volume from the search results
            chosen = results[0]
            print("Picked first result!")
        return chosen["id"]
    else:
        raise ValueError("No volumes found for the given query.")


def fetch_random_comic_image(api_key, series_id):
    # Once we know the volume ID we can do a second API call to fetch a list of issues and pick a random cover image
    params = {"api_key": api_key, "format": "json", "filter": f"volume:{series_id}", "limit": 100}
    response = requests.get(f"{BASE_URL}issues/", headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    response.close()
    results = data.get("results", [])
    if results:
        issue = random.choice(results)
        # print a link to the issue page on Comic Vine
        print(f"Random issue selected: ID: {issue['id']}")
        print(f"Find out more: {issue['site_detail_url']}")
        image_link = issue["image"]["original_url"]
        return image_link
    else:
        raise ValueError("No comic issues found for the specified series.")


def display_image_on_inky(image_url):
    # Display image on Inky Impression
    response = requests.get(image_url)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content))
    response.close()

    # Rotate the image if it is taller than it is wide
    if image.height > image.width:
        image = image.rotate(90, expand=True)

    image = image.resize(inky_display.resolution)
    inky_display.set_image(image)
    print("Updating Inky Impression!")
    inky_display.show()


try:
    # Pick a random search term from the list
    search_query = random.choice(SEARCH_QUERIES)
    volume_id = find_volume_id(API_KEY, search_query)
    comic_image_url = fetch_random_comic_image(API_KEY, volume_id)
    display_image_on_inky(comic_image_url)
except Exception as e:
    print(f"Error: {e}")
