from playwright.sync_api import sync_playwright
import pandas as pd

all_rows = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for page_num in range(1, 6):  # Adjust page range as needed
        url = f"https://results.raceroster.com/v2/en-CA/results/s9v6cbyg2c3m6kps/results?subEvent=229192&page={page_num}"
        page.goto(url)
        page.wait_for_selector('table')  # wait until the table loads

        rows = page.locator('table tbody tr')
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.locator('td')
            row_data = [cells.nth(j).inner_text().strip() for j in range(cells.count())]
            # Only keep first 10 columns
            row_data = row_data[:10]
            if i == 0:  # Print the first row to see the structure
                print("First row data:", row_data)
                print("Number of columns:", len(row_data))
            all_rows.append(row_data)

    browser.close()

# Use the specified headings
columns = [
    'Race Place',
    'Bib',
    'Full Name',
    'Gender',
    'Age',
    'City',
    'Lap Count',
    'Gun Elapsed Time',
    'Chip Elapsed Time',
    'Overall Pace'
]
df = pd.DataFrame(all_rows, columns=columns)
# Prune out anyone whose Lap Count is 0 (did not finish)
df = df[df['Lap Count'] != '0']
print(df.head())

# Save to CSV
df.to_csv('20k_race_results.csv', index=False)
print("Data has been saved to 20k_race_results.csv") 