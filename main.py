import requests
from bs4 import BeautifulSoup
import pandas as pd
# User-Agent and Accept-Language headers
headers = {
    'User-Agent': 'Use your own user agent',
    'Accept-Language': 'en-us,en;q=0.5'
}
customer_names = []
review_title = []
ratings = []
comments = []

for i in range(1, 44):
    # Construct the URL for the current page
    url = "https://www.flipkart.com/motorola-g84-5g-viva-magneta-256-gb/product-reviews/itmed938e33ffdf5?pid=MOBGQFX672GDDQAQ&lid=LSTMOBGQFX672GDDQAQSSIAM2&marketplace=FLIPKART&page"+str(i)

    # Send a GET request to the page
    page = requests.get(url, headers=headers)

    # Parse the HTML content
    soup = BeautifulSoup(page.content, 'html.parser')

    # Extract customer names
    names = soup.find_all('p', class_='_2sc7ZR _2V5EHH')
    for name in names:
        customer_names.append(name.get_text())

    # Extract review titles
    title = soup.find_all('p', class_='_2-N8zT')
    for t in title:
        review_title.append(t.get_text())

    # Extract ratings
    rat = soup.find_all('div', class_='_3LWZlK _1BLPMq')
    for r in rat:
        rating = r.get_text()
        if rating:
            ratings.append(rating)
        else:
            ratings.append('0')  # Replace null ratings with 0

    # Extract comments
    cmt = soup.find_all('div', class_='t-ZTKy')
    for c in cmt:
        comment_text = c.div.div.get_text(strip=True)
        comments.append(comment_text)

# Ensure all lists have the same length
min_length = min(len(customer_names), len(review_title), len(ratings), len(comments))
customer_names = customer_names[:min_length]
review_title = review_title[:min_length]
ratings = ratings[:min_length]
comments = comments[:min_length]

# Create a DataFrame from the collected data
data = {
    'Customer Name': customer_names,
    'Review Title': review_title,
    'Rating': ratings,
    'Comment': comments
}

df = pd.DataFrame(data)

print(len(customer_names))
print(len(review_title))
print(len(ratings))
print(len(comments))
customer_names
## comments
import pandas as pd
data = {
    'Customer Name': customer_names,
    'Review Title': review_title,
    'Rating': ratings,
    'Comment': comments
}


df = pd.DataFrame(data)
# df['Rating'].fillna(0, inplace=True)


# Save the DataFrame to a CSV file
df.to_csv('MOTOROLA g84 5G (Viva Magneta, 256 GB).csv', index=False) 