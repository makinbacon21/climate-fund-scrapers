# Climate Fund Scrapers

This is a collection of Python-based scraper scripts produced to procure more than the
extremely limited data provided for download by organizations like the
[GCF](https://www.greenclimate.fund/) and [GEF](https://www.thegef.org/).

## How to Use

1. Ensure `bs4` (BeautifulSoup) and `xlsxwriter` are installed via `pip` (see Python's
instructions for your system).

2. Download the CSV format data (or convert to CSV appropriately) and name the files as
expected by the scraper (`gcfscrape.py` grabs `gcf.csv` and `gefscrape.py` grabs
`gef.csv`). The CSVs are needed to determine the ID of each project to grab its details.

3. Run the scraper with `python3 <path to scraper>`

## Acknowledgements

These scripts were written by Thomas Makin, Swarthmore Class of 2025, based on the
original GEF scraper script by Sky Park, Swarthmore Class of 2024.

The scripts are intended for use by Prof. Ayse Kaya of Swarthmore College's Political
Science department.
