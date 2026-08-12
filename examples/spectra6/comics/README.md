# comicvine_comic.py

`comicvine_comic.py` fetches and displays a random comic book cover from the Comic Vine API.

- [comicvine_comic.py](#comicpy)
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
3. Run the script: `python comicvine_comic.py`
4. The script will fetch a random comic cover and display it on your Inky Impression.

## Notes

- You can change which volumes/series are searched by adding or removing strings from the `SEARCH_QUERIES` variable - the default is 'Weird Science', which looks like a great read.
- Set `RANDOM_VOLUME = True` to select a random volume from the top 5 search results instead of choosing the first one. We found this varied things up when there were multiple volumes with the same title.


# metron_comic.py

`metron_comic.py` fetches and displays a random "Batman" comic book cover from the Metron API.

- [metron_comic.py](#comicpy)
  - [About Metron](#about-Metron)
  - [Pre-requisites](#pre-requisites)
  - [Usage](#usage)
  - [Notes](#notes)


## About Meton

Metron is an alternative online database of comic book information. It has a free API that can be used to search and retrieve detailed information about comics, including cover images, issue details, and more. Check it out at https://metron.cloud/

## Pre-requisites

You'll need to have the Inky library installed and your virtual environment activated: `source ~/.virtualenvs/pimoroni/bin/activate`

## Usage

```bash
python metron_comic.py [search_term]
```

**Examples:**
```bash
# Display a random Batman comic cover
python metron_comic.py batman

# Display a random Spider-Man comic cover
python metron_comic.py "spider-man"

# Uses default search term (batman) if none provided
python metron_comic.py
```

### Installation

1. Configure your Metron API credentials:
```bash
   cp config.py.example config.py
```

2. Edit `config.py` and add your Metron API credentials:
```python
   username = "your_username"
   password = "your_password"
```

### Getting Metron API Credentials

1. Visit https://metron.cloud/
2. Create a free account
3. Use your username and password in `config.py`

