"""
Python script to fetch a randomised comic cover from the Metron Comic API.

This script displays comic book covers on an Inky Impression e-ink display.
You will need to sign up for an Account at https://metron.cloud/ to use this script.
Change the search query to the comic series you want to display!

usage comic.py ["search string"]
"""

import sys
import random
from io import BytesIO
from typing import Optional, List

import mokkari
import requests
from PIL import Image
from inky.auto import auto

# Your own config file to keep your credentials secret
from config import username, password


class ComicCoverFetcher:
    """Handles fetching and displaying comic book covers."""

    COVER_ATTRIBUTES = ['image', 'cover', 'cover_image', 'cover_url', 'image_url']

    def __init__(self, username: str, password: str):
        """
        Initialize the comic cover fetcher.

        Args:
            username: Metron API username
            password: Metron API password
        """
        self.api = mokkari.api(username, password)
        self.inky_display = auto()

    def search_comics(self, series_name: str) -> List:
        """
        Search for comics by series name.

        Args:
            series_name: The name of the comic series to search for

        Returns:
            List of comic issues matching the search term
        """
        print(f"Searching for comics matching: {series_name}")
        results = self.api.issues_list({"series_name": series_name})
        print(f"\nFound {len(results)} results:")

        for idx, issue in enumerate(results, 1):
            print(f"{idx}. {issue.issue_name} (ID: {issue.id})")

        return results

    def get_random_issue(self, results: List):
        """
        Select a random issue from search results.

        Args:
            results: List of comic issues

        Returns:
            A randomly selected issue or None if results is empty
        """
        if not results:
            return None
        return random.choice(results)

    def get_cover_url(self, issue_detail) -> Optional[str]:
        """
        Extract the cover URL from an issue detail object.

        Args:
            issue_detail: The detailed issue object from the API

        Returns:
            Cover URL string or None if not found
        """
        for attr in self.COVER_ATTRIBUTES:
            if hasattr(issue_detail, attr):
                cover_url = getattr(issue_detail, attr)
                if cover_url:
                    print(f"Found cover URL in '{attr}' attribute: {cover_url}")
                    return cover_url
        return None

    def download_image(self, url: str) -> Optional[Image.Image]:
        """
        Download an image from a URL.

        Args:
            url: The URL of the image to download

        Returns:
            PIL Image object or None if download fails
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            response.close()
            return image
        except requests.RequestException as e:
            print(f"Error downloading image: {e}")
            return None

    def process_image(self, image: Image.Image) -> Image.Image:
        """
        Process image for display on Inky screen.

        Rotates portrait images to landscape and resizes to fit display.

        Args:
            image: The PIL Image to process

        Returns:
            Processed PIL Image
        """
        # Rotate the image if it is taller than it is wide
        if image.height > image.width:
            image = image.rotate(90, expand=True)

        # Resize to match display resolution
        image = image.resize(self.inky_display.resolution)
        return image

    def display_on_inky(self, image: Image.Image) -> bool:
        """
        Display an image on the Inky display.

        Args:
            image: The PIL Image to display

        Returns:
            True if successful, False otherwise
        """
        try:
            self.inky_display.set_image(image)
            print("Updating Inky Impression!")
            self.inky_display.show()
            return True
        except Exception as e:
            print(f"Error updating display: {e}")
            return False

    def print_debug_attributes(self, issue_detail):
        """
        Print available attributes for debugging.

        Args:
            issue_detail: The issue detail object to inspect
        """
        print("\nNo cover image URL found. Available attributes:")
        for attr in dir(issue_detail):
            if not attr.startswith('_'):
                print(f"  - {attr}: {getattr(issue_detail, attr, 'N/A')}")

    def fetch_and_display(self, series_name: str) -> bool:
        """
        Main workflow: search, fetch, and display a comic cover.

        Args:
            series_name: The comic series to search for

        Returns:
            True if successful, False otherwise
        """
        # Search for comics
        results = self.search_comics(series_name)

        if not results:
            print(f"\nNo results found for '{series_name}'")
            return False

        # Select random issue
        random_issue = self.get_random_issue(results)
        print(f"\nFetching details for: {random_issue.issue_name}")

        # Get full issue details
        issue_detail = self.api.issue(random_issue.id)

        # Get cover URL
        cover_url = self.get_cover_url(issue_detail)

        if not cover_url:
            self.print_debug_attributes(issue_detail)
            return False

        # Download image
        image = self.download_image(cover_url)
        if not image:
            return False

        # Process and display
        processed_image = self.process_image(image)
        success = self.display_on_inky(processed_image)

        if success:
            print("\nCover image downloaded and set successfully")

        return success


def main():
    """Main entry point for the script."""
    # Get search term from command line or use default
    search_term = sys.argv[1] if len(sys.argv) > 1 else "batman"

    # Initialize fetcher and run
    fetcher = ComicCoverFetcher(username, password)

    try:
        fetcher.fetch_and_display(search_term)
    except Exception as e:
        print(f"\nError setting cover: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

