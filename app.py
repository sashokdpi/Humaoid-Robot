import requests
from bs4 import BeautifulSoup
import csv
from datetime import date

def html_code(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup

def cus_rev(soup):
    reviews = []
    review_blocks = soup.find_all('div', {'class': 'col EPCmJX Ma1fCG'})  # Updated class name based on inspection
    for block in review_blocks:
        rating_elem = block.find('div', {'class': 'XQDdHH Ga3i8K'})
        review_elem = block.find('div', {'class': 'ZmyHeo'})
        
        # Differentiate Name and Date
        meta_elements = block.find_all('p', {'class': '_2NsDsF'})
        name_elem = meta_elements[0] if len(meta_elements) > 0 else None
        date_elem = meta_elements[1] if len(meta_elements) > 1 else None

        location_elem = block.find('p', {'class': 'MztJPv'})

        review = {
            'Rating': rating_elem.text.strip() if rating_elem else 'N/A',
            'Review': review_elem.text.strip() if review_elem else 'N/A',
            'Name': name_elem.text.strip() if name_elem else 'N/A',
            'Date': date_elem.text.strip() if date_elem else 'N/A',
            'Location': location_elem.text.strip() if location_elem else 'N/A'  # Location might not be present
        }
        reviews.append(review)
    return reviews

# URL of the page to scrape
url = "https://www.flipkart.com/sony-zv-e10l-mirrorless-camera-body-1650-mm-power-zoom-lens-vlog/product-reviews/itmed07cbb694444?pid=DLLG6G8U8P2NGEHG&lid=LSTDLLG6G8U8P2NGEHGGVZNLB&marketplace=FLIPKART"

reviews = []
page = 1

while True:
    page_url = url + "&page=" + str(page)
    print(f"Scraping page {page}...")
    soup = html_code(page_url)
    page_reviews = cus_rev(soup)
    if not page_reviews:
        print("No more reviews found.")
        break
    reviews.extend(page_reviews)
    page += 1

# Save reviews to a CSV file
today = date.today()
file_name = today.strftime("reviews_%d-%m-%Y.csv")

header_row = ['Rating', 'Review', 'Name', 'Date', 'Location']

with open(file_name, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=header_row)
    writer.writeheader()
    writer.writerows(reviews)

print(f"Scraped {len(reviews)} reviews. Saved to {file_name}.")
