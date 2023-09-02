# GCF Scraper
# Scrapes the Global Climate Fund website based on CSV input (based on gefscrape)
#
# SPDX-License-Identifier: MIT
#
# Copyright (C) Thomas Makin 2023
# Copyright (C) Sky Park 2022
#

from bs4 import BeautifulSoup
import csv, requests, sys, os
import xlsxwriter

PREFIX = "https://www.greenclimate.fund/project/"
META_FIELDS = [
    'Status',
    'Date approved',
    'Est. completion',
    'ESS Category'
]
TIMELINE_FIELDS = [
    'Concept note received',
    'Funding proposal received',
    'Approved by GCF Board',
    'Under implementation',
    'Completed'
]
FINANCE_FIELDS = [
    'Total GCF Financing',
    'Total Co-Financing'
]
INVALIDS = 'invalid.txt'

def writeResults(timeline_results, financials_results, meta_results):
    print("Writing results...")

    workbook = xlsxwriter.Workbook('gcf-scraped.xlsx', {'strings_to_numbers': True})
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

    # Write metadata to sheet 3
    meta_sheet = workbook.add_worksheet()
    
    row = 0
    col = 0

    meta_sheet.write_row(row, col, tuple(["ID", "Project Name", "Project URL"]
                                         + META_FIELDS))
    for result in meta_results:
        row += 1
        meta_sheet.write_row(row, col, tuple(result))

    meta_sheet.set_column(1, 2, 30)

    workbook.close()

try:
    projects = []

    # Open CSV file for reading
    with open('gcf.csv', 'r', encoding="utf8") as file:
        invalid = open(INVALIDS, 'w')
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            # Ignore badly formatted header
            if 'Ref #' in row[0]:
                continue

            title = row[1]
            _id = row[0]

            projects.append((_id, title))
        invalid.close()

    print("Retrieving data...")
    # ID, Name, 
    #Received by GEF, concept approved date, project approved for implementation date, project closed date
    timeline_results = []
    financials_results = []
    meta_results = []
    count = 0
    for _id, name in projects:
        if count % 100 == 0:
            print(count)
        count += 1

        soup = BeautifulSoup(requests.get(PREFIX + _id).text, 'html.parser')

        # Find timeline element and parse relevant children
        # NOTE: dependent on the only vue-based component being the timeline
        # May have to update if they change the layout again
        timeline = soup.find("div", class_="vue-component")
        if timeline is not None:
            timeline_items = timeline.findChildren("h6", recursive=True)
            dates = []

            for field in TIMELINE_FIELDS:
                # We use the done variable to identify if this field has been found
                # NOTE: this is a bad approach but whatever it works
                done = False
                for ti in timeline_items:
                    # Don't keep searching if found
                    if done:
                        break
                    if ti.contents[0] == field:
                        if ti.parent.p is None:
                            dates.append('pm') # Label present, date missing
                            done = True
                            continue
                        if ti.parent.p.strong is not None:
                            if ti.parent.p.strong.span is not None:
                                # Account for insane edge cases
                                if len(ti.parent.p.strong.span.contents) > 0:
                                    date = ti.parent.p.strong.span.contents[0]
                                else:
                                    dates.append('pm') # Label present, date missing
                                    done = True
                                    continue
                            else:
                                if len(ti.parent.p.strong.contents) > 0:
                                    date = ti.parent.p.strong.contents[0]
                                else:
                                    dates.append('pm') # Label present, date missing
                                    done = True
                                    continue
                        else:
                            date = ti.parent.p.contents[0]
                        if len(date) > 0:
                            dates.append(date)
                        else:
                            dates.append('pm') # Label present, date missing

                        done = True

                # If we haven't found this field, drop in na
                if not done:
                    dates.append('na') # Date missing
            
            # NOTE: URL = PREFIX + proj id
            timeline_results.append([_id, name, PREFIX + _id] + dates)

            # Find financials
            financial_data = []
            for field in FINANCE_FIELDS:
                element = soup.find("td", {"data-header" : field})
                if element is not None:
                    figure = element.contents[0]
                    if len(figure) > 0:
                        financial_data.append(figure.replace(",", "").replace("USD ", ""))
                    else:
                        financial_data.append('pm') # Label present, figure missing
                else:
                    financial_data.append('na') # Label not present
            
            # NOTE: URL = PREFIX + proj id
            financials_results.append([_id, name, PREFIX + _id] + financial_data)

            # Find metadata
            meta_data = []
            meta = soup.find("div", {"class" : "meta-information"})
            for field in META_FIELDS:
                # Here we must start from this base query and check for elements *containing* the
                # field as opposed to *being* the field because for some unknowable reason the
                # Est. completed field includes tons of whitespace and a newline which I couldn't
                # get to match directly. This works fine though!
                query_results = meta.findChildren("span", {"class" : "node-label"}, recursive=True)
                label = None
                if query_results is None:
                    continue
                for result in query_results:
                    if field in result.text:
                        label = result
                if label is None:
                    meta_data.append('na') # Label not present
                    continue

                element = label.parent.findChild("span", {"class" : "node-content text-primary"}, recursive=True)

                # This case should never be hit but is there because it is plausible
                if element is None:
                    meta_data.append('pm') # Label present, figure missing
                    continue
                if element.span is not None:
                    figure = element.span.contents[0]
                else:
                    figure = element.contents[0].text.lstrip()
                if len(figure) > 0:
                    meta_data.append(figure)
                else:
                    meta_data.append('pm') # Label present, figure missing
            
            # NOTE: URL = PREFIX + proj id
            meta_results.append([_id, name, PREFIX + _id] + meta_data)

        else:
            print("Timeline not found, assuming invalid entry (id: ", _id, ")")

    writeResults(timeline_results, financials_results, meta_results)

except KeyboardInterrupt:
    print('Interrupted')
    try:
        writeResults(timeline_results, financials_results, meta_results)

        sys.exit(1)
    except SystemExit:
        os._exit(2)
