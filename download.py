#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 22:11:09 2024

@author: anirudhkulkarni
"""

#imports
import requests
import json
from pathlib import Path
import time
from urllib.parse import urljoin
import re

## make an api call, download data, and process it

class TravelDataset:
    def __init__(self, downloadPath, rate_limit_seconds):
        self.downloadPath = Path(downloadPath)
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.visited_pages = set()
        self.data = None
        
    def respect_rate_limit(self):
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
        
        
    def getPage(self, title):
        
        #skip if we've already got this page
        if title in self.visited_pages:
            print(f"Already visited {title}, skipping...")
            return None
        
        self.respect_rate_limit()
        
        url = "https://en.wikivoyage.org/w/api.php"
        # title = "Chicago"
        
        params = {
            "action":"query",
            "format":"json",
            "prop":"extracts|coordinates|links",
            "titles":title,
            "explaintext":True,
            "exsectionformat": "plain",
            "plnamespace": 0,  # Only get links to main namespace
            "pllimit": 500  # Get up to 500 links
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pages = data["query"]["pages"]
            page_content = next(iter(pages.values()))
            
            #visited
            self.visited_pages.add(title)

            #save the data
            save_path = self.downloadPath / f"{title.replace(' ', '_')}.json"
            save_path.parent.mkdir(parents=True,exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(page_content, f, indent=2)
                
            linked_pages=[]
            
            if "links" in page_content:
                linked_pages = [link["title"] for link in page_content["links"]]
                
            return page_content, linked_pages
                
        
        except requests.RequestException as e:
            print(f"Error downloading {title}: {e}")
            return None, []
    
    def crawlFromSeed(self,seed_page, max_pages):
        pages_to_visit = [seed_page]
        pages_scraped = 0
        
        print(f"Started crawl from {seed_page}")
        
        while pages_to_visit and pages_scraped < max_pages:
            current_page = pages_to_visit.pop(0)
            print(f"Scraping page {pages_scraped + 1}/{max_pages}: {current_page}")
            
            content, linked_pages = self.getPage(current_page)
            
            if content:
                pages_scraped += 1
            
                for link in linked_pages:
                    if (link not in self.visited_pages and 
                        link not in pages_to_visit and
                        self._is_valid_travel_page(link)):
                        pages_to_visit.append(link)
                
                print(f"Found {len(linked_pages)} links. Queue size: {len(pages_to_visit)}")
                
                self.save_progress()
                
    def _is_valid_travel_page(self, title):
        """Filter out non-travel related pages"""
        # Skip meta pages, user pages, etc.
        if any(prefix in title for prefix in ["User:", "Talk:", "Template:", "Category:"]):
            return False
            
        # Could add more filters here
        return True
        
    def save_progress(self):
        """Save list of visited pages in case we need to resume later"""
        progress_path = self.downloadPath / "crawl_progress.json"
        with open(progress_path, 'w') as f:
            json.dump(list(self.visited_pages), f)
            
            
if __name__ == "__main__":
    dataset = TravelDataset(
        downloadPath="data",
        rate_limit_seconds=1  # Wait 1 second between requests
    )
    
    # Start crawling from Paris page, limit to 50 pages
    dataset.crawlFromSeed("Paris", max_pages=1000)
        
        
        
        
        
        
        
        
        
        
        
        
        
        