# comic.py

`comic.py` fetches and displays a random comic book cover from the Comic Vine API.

- [comic.py](#comicpy)
  - [About Comic Vine](#about-comic-vine)
  - [Pre-requisites](#pre-requisites)
  - [Usage](#usage)
  - [Notes](#notes)

You can find a more detailed run down of how to use this script in our Learn Guide:

- [Learn: Displaying Comics on Inky Impression](https://learn.pimoroni.com/article/comics-on-inky-impression)

## About Comic Vine

Comic Vine is an awesome online database of comic book information. It has a free API that can be used to search and retrieve detailed information about comics, including cover images, issue details, and more. Check it out at https://comicvine.gamespot.com/ !

## Pre-requisites

You'll need to have the Inky library installed and your virtual environment activated: `source ~/.virtualenvs/pimoroni/bin/activate`

## Usage

1. Get a Comic Vine API key: [https://comicvine.gamespot.com/api/](https://comicvine.gamespot.com/api/)
2. Edit the script to add your API key (`API_KEY` variable).
3. Run the script: `python comic.py`
4. The script will fetch a random comic cover and display it on your Inky Impression.

## Notes

- You can change which volumes/series are searched by adding or removing strings from the `SEARCH_QUERIES` variable - the default is 'Weird Science', which looks like a great read.
- Set `RANDOM_VOLUME = True` to select a random volume from the top 5 search results instead of choosing the first one. We found this varied things up when there were multiple volumes with the same title.