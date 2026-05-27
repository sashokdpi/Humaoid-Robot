from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import csv
from datetime import date

app = Flask(__name__)

def fetch_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup

def scrape_reviews(soup, review_block_class, rating_class, review_class, name_tag, name_class, date_tag, date_class, location_class):
    reviews = []
    review_blocks = soup.find_all('div', {'class': review_block_class})
    for block in review_blocks:
        rating_elem = block.find('div', {'class': rating_class})
        review_elem = block.find('div', {'class': review_class})
        name_elem = block.find(name_tag, {'class': name_class})
        date_elem = block.find(date_tag, {'class': date_class})
        location_elem = block.find('p', {'class': location_class})

        review = {
            'Rating': rating_elem.text.strip() if rating_elem else 'N/A',
            'Review': review_elem.text.strip() if review_elem else 'N/A',
            'Name': name_elem.text.strip() if name_elem else 'N/A',
            'Date': date_elem.text.strip() if date_elem else 'N/A',
            'Location': location_elem.text.strip() if location_elem else 'N/A'
        }
        reviews.append(review)
    return reviews

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    review_block_class = request.form['review_block_class']
    rating_class = request.form['rating_class']
    review_class = request.form['review_class']
    name_tag = request.form['name_tag']
    name_class = request.form['name_class']
    date_tag = request.form['date_tag']
    date_class = request.form['date_class']
    location_class = request.form['location_class']

    try:
        soup = fetch_html(url)
        reviews = scrape_reviews(soup, review_block_class, rating_class, review_class, name_tag, name_class, date_tag, date_class, location_class)

        today = date.today()
        file_name = today.strftime("reviews_%d-%m-%Y.csv")
        header_row = ['Rating', 'Review', 'Name', 'Date', 'Location']

        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=header_row)
            writer.writeheader()
            writer.writerows(reviews)

        return jsonify({'message': f"Scraped {len(reviews)} reviews. Saved to {file_name}.", 'data': reviews})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
