import pandas as pd
import requests
from lxml import html
import re
import time
from datetime import datetime
from flask import Flask, render_template, request

app = Flask(__name__)

# Define headers for HTTP request
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'DNT': '1',  # Do Not Track request header
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://amazon.com/',
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the URL from the form
        review_url = request.form['review_url']

        # Extract the ASIN or Flipkart Product ID from the URL
        if 'amazon.com' in review_url:
            # Amazon ASIN extraction
            asins = [review_url.split('/')[-1]]
            platform = 'amazon'
        elif 'flipkart.com' in review_url:
            # Flipkart product ID extraction
            asins = [review_url.split('/')[-2]]  # Adjust based on the Flipkart URL format
            platform = 'flipkart'
        else:
            return "Unsupported platform", 400

        comments_data = []  # Data for reviews
        review_count = 0  # To count the number of reviews

        for asin in asins:
            print(f'/// {platform.upper()} Product ID {asin}')
            if platform == 'amazon':
                url = f'https://www.amazon.com/dp/{asin}'
                comments_page_url = f'https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent&pageNumber={page}'
            elif platform == 'flipkart':
                url = f'https://www.flipkart.com/{asin}/product-reviews'
                comments_page_url = f'https://www.flipkart.com/{asin}/product-reviews'

            response = requests.get(url, headers=headers)
            print(f'Load {url}...')

            time.sleep(2)

            # Load comments page with paging
            page = 1
            while True:
                print(f'Page {page} | Load {comments_page_url}...')
                try:
                    response = requests.get(comments_page_url, headers=headers)
                    time.sleep(2)

                    tree = html.fromstring(response.content)
                    reviews = tree.xpath('//div[@data-hook="review"]')

                    print(f'Reviews found on the page: {len(reviews)}')
                    review_count += len(reviews)  # Count reviews

                    for review in reviews:
                        # Extract review data (same process as before)
                        review_id = review.xpath('./@id')[0] if review.xpath('./@id') else None
                        name = review.xpath('.//span[@class="a-profile-name"]/text()')[0] if review.xpath('.//span[@class="a-profile-name"]/text()') else None
                        title = review.xpath('.//a[@data-hook="review-title"]/span/text()')[0] if review.xpath('.//a[@data-hook="review-title"]/span/text()') else None
                        rating_str = review.xpath('.//i[@data-hook="review-star-rating"]/span/text()')[0] if review.xpath('.//i[@data-hook="review-star-rating"]/span/text()') else None
                        rating = float(re.search(r'(\d+(\.\d+)?)', rating_str).group(1)) if rating_str else None
                        date_str = review.xpath('.//span[@data-hook="review-date"]/text()')[0] if review.xpath('.//span[@data-hook="review-date"]/text()') else None
                        review_text = review.xpath('.//span[@data-hook="review-body"]//span/text()')[0] if review.xpath('.//span[@data-hook="review-body"]//span/text()') else None

                        country, date = None, None
                        if date_str:
                            match = re.search(r'Reviewed in ([A-Za-z\s]+) on ([A-Za-z]+\s\d{1,2},\s\d{4})', date_str)
                            if match:
                                country = match.group(1).strip()
                                date = datetime.strptime(match.group(2).strip(), '%B %d, %Y')

                        comments_data.append({
                            'asin': asin,
                            'review_id': review_id,
                            'name': name,
                            'title': title,
                            'rating': rating,
                            'country': country,
                            'date': date,
                            'review_text': review_text
                        })

                    # Check for next page (for Flipkart)
                    next_page = tree.xpath("//ul[@class='a-pagination']/li[@class='a-last']/a[@href]")
                    if next_page:
                        page += 1
                    else:
                        break

                except Exception as e:
                    print(f"Error while processing page {page}: {e}")
                    break

        # Create dataframe and save to CSV
        df = pd.DataFrame(comments_data)
        df.to_csv('reviews.csv', index=False)

        return render_template('result.html', review_count=review_count, data=df.to_html())

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
