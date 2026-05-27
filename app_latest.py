from flask import Flask, render_template, request, send_file
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import os

app = Flask(__name__)

# Path to store the reviews CSV
CSV_PATH = 'C://Users//sasho//OneDrive//Desktop//AI//reviews.csv'
CSV_FOLDER = os.path.dirname(CSV_PATH)

# Create the folder if it doesn't exist
if not os.path.exists(CSV_FOLDER) and CSV_FOLDER != '':
    os.makedirs(CSV_FOLDER)

def scrape_reviews(url):
    # Start Playwright and open the browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set to False if you want to see the browser
        page = browser.new_page()

        try:
            # Open the given URL
            page.goto(url)

            # Wait for the reviews section to load (customize the selector as needed)
            page.wait_for_selector('._2sc7ZR')

            # Extract the page content
            page_source = page.content()
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract customer names
            customer_names = [name.get_text() for name in soup.find_all('p', class_='elementor-element elementor-element-78506a5 elementor-widget elementor-widget-button animated slideInLeft')]

            # Extract review titles
            review_titles = [title.get_text() for title in soup.find_all('p', class_='z9E0IG')]

            # Extract ratings
            ratings = [rating.get_text() for rating in soup.find_all('div', class_='XQDdHH Ga3i8K')]

            # Extract comments
            comments = [comment.get_text(strip=True) for comment in soup.find_all('div', class_='ZmyHeo')]

            # Ensure lists are of the same length
            min_length = min(len(customer_names), len(review_titles), len(ratings), len(comments))
            customer_names = customer_names[:min_length]
            review_titles = review_titles[:min_length]
            ratings = ratings[:min_length]
            comments = comments[:min_length]

            # Create a DataFrame
            data = {
                'Customer Name': customer_names,
                'Review Title': review_titles,
                'Rating': ratings,
                'Comment': comments
            }
            return pd.DataFrame(data)

        except Exception as e:
            print(f"Error occurred: {e}")
            return pd.DataFrame()

        finally:
            # Close the browser
            browser.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    df = scrape_reviews(url)

    if not df.empty:
        # Save reviews to CSV
        df.to_csv(CSV_PATH, index=False)

        # Sentiment Analysis
        positive_reviews = df[df['Rating'].astype(float) >= 4.0].shape[0]
        neutral_reviews = df[(df['Rating'].astype(float) == 3.0)].shape[0]
        negative_reviews = df[df['Rating'].astype(float) < 3.0].shape[0]

        return render_template(
            'result.html',
            total_reviews=len(df),
            positive_reviews=positive_reviews,
            neutral_reviews=neutral_reviews,
            negative_reviews=negative_reviews,
            reviews=df.to_dict(orient='records')
        )
    else:
        return render_template('result.html', total_reviews=0, positive_reviews=0, neutral_reviews=0, negative_reviews=0)

@app.route('/download')
def download_file():
    if os.path.exists(CSV_PATH):
        return send_file(CSV_PATH, as_attachment=True)
    else:
        return "No file to download!", 404

if __name__ == '__main__':
    app.run(debug=True)
