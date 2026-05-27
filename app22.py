from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
from sentiment_model import analyze_sentiment
import csv
import os

app = Flask(__name__)
CSV_FILE = 'reviews.csv'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    website_url = request.form['website_url']
    
    try:
        # Use Microsoft Edge User-Agent in the headers
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.5735.199 Safari/537.36 Edg/114.0.1823.67"
            )
        }
        response = requests.get(website_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract reviews
        reviews = [review.text for review in soup.find_all('div', class_='_6K-7Co')]

        if not reviews:
            return render_template('result.html', message="No reviews found on the provided Flipkart product page.")

        # Analyze Sentiment
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        review_sentiments = []
        for review in reviews:
            sentiment = analyze_sentiment(review)
            sentiment_counts[sentiment] += 1
            review_sentiments.append((review, sentiment))

        # Save to CSV
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Review', 'Sentiment'])
            writer.writerows(review_sentiments)

        # Render results
        return render_template(
            'result.html',
            sentiment_counts=sentiment_counts,
            total_reviews=len(reviews),
            csv_file=CSV_FILE
        )
    except Exception as e:
        return render_template('result.html', message=f"An error occurred: {str(e)}")

@app.route('/download')
def download():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    return "CSV file not found!"

if __name__ == '__main__':
    app.run(debug=True)
