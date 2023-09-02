# GEF Scraper 2.0
# Scrapes the GEF website based on CSV input (prev. version used JSON)
#
# SPDX-License-Identifier: MIT
#
# Copyright (C) Thomas Makin 2023
# Copyright (C) Sky Park 2022
#

from bs4 import BeautifulSoup
import csv, requests, sys, os
import xlsxwriter

PREFIX = "https://www.thegef.org/projects-operations/projects/"
TIMELINE_FIELDS = [
    'Received by GEF',
    'Preparation Grant Approved',
    'Concept Approved',
    'Project Approved for Implementation',
    'Project Closed',
    'Project Cancelled'
]
FINANCE_FIELDS = [
    "Co-financing Total",
    "GEF Project Grant",
    "GEF Agency Fees"
]
INVALIDS = 'invalid.txt'

def writeResults(timeline_results, financials_results):
    print("Writing results...")

    workbook = xlsxwriter.Workbook('gef-scraped.xlsx', {'strings_to_numbers': True})
    money_format = workbook.add_format({'num_format': '$#,##0'})

    # Write timeline data to sheet 1
    timeline_sheet = workbook.add_worksheet()
    
    row = 0
    col = 0

    timeline_sheet.write_row(row, col, tuple(["ID", "Project Name", "Project URL"]
                                         + TIMELINE_FIELDS))
    for result in timeline_results:
        row += 1
        timeline_sheet.write_row(row, col, tuple(result))

    timeline_sheet.set_column(1, 2, 30)

    # Write finance data to sheet 2
    finance_sheet = workbook.add_worksheet()
    
    row = 0
    col = 0

    finance_sheet.write_row(row, col, tuple(["ID", "Project Name", "Project URL"]
                                         + FINANCE_FIELDS))
    for result in financials_results:
        row += 1
        finance_sheet.write_row(row, col, tuple(result))

    finance_sheet.set_column(1, 2, 30)
    finance_sheet.set_column(3, 5, 12, money_format)

    workbook.close()

try:
    projects = []

    # Open CSV file for reading
    with open('gef.csv', 'r', encoding="utf8") as file:
        invalid = open(INVALIDS, 'w')
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            # Ignore header
            if row[0] == "Title":
                continue

            title = row[0]
            _id = row[1]

            projects.append((_id, title))
        invalid.close()

    print("Retrieving data...")
    # ID, Name, 
    #Received by GEF, concept approved date, project approved for implementation date, project closed date
    timeline_results = []
    financials_results = []
    count = 0
    for _id, name in projects:
        if count % 100 == 0:
            print(count)
        count += 1

        soup = BeautifulSoup(requests.get(PREFIX + _id).text, 'html.parser')

        # Find timeline element and parse relevant children
        timeline = soup.find("div", class_="project-timeline")
        if timeline is not None:
            timeline_items = timeline.findChildren("div", class_="views-field", recursive=True)

            dates = []
            for field in TIMELINE_FIELDS:
                for ti in timeline_items:
                    if ti.span.contents[0] == field:
                        date = ti.find_all("div", {"class":"field-content"})
                        if len(date) > 0:
                            dates.append(date[0].contents[0])
                        else:
                            dates.append('pm') # Label present, date missing
                        break
                else:
                    dates.append('na') # Label not present
            
            # NOTE: URL = PREFIX + proj id
            timeline_results.append([_id, name, PREFIX + _id] + dates)
        else:
            print("Timeline not found (id %s)", _id)

        # Find financials element and parse relevant children
        financials = soup.find("div", class_="project-financials")
        if financials is not None:
            financials_items = financials.findChildren("div", class_="views-field", recursive=True)

            financial_data = []
            for field in FINANCE_FIELDS:
                for fi in financials_items:
                    if len(fi.span.contents) > 0 and fi.span.contents[0] == field:
                        figure = fi.find_all("div", {"class":"field-content"})
                        if len(figure) > 0:
                            financial_data.append(figure[0].contents[0].replace(",", ""))
                        else:
                            financial_data.append('pm') # Label present, figure missing
                        break
                else:
                    financial_data.append('na') # Label not present
            
            # NOTE: URL = PREFIX + proj id
            financials_results.append([_id, name, PREFIX + _id] + financial_data)
        else:
            print("Financial data not found (id %s)", _id)

    writeResults(timeline_results, financials_results)

except KeyboardInterrupt:
    print('Interrupted')
    try:
        writeResults(timeline_results, financials_results)

        sys.exit(1)
    except SystemExit:
        os._exit(2)
