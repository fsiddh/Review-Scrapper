from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as bs
import pymongo

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
@cross_origin
def reviews():
    if request.method == 'POST':
        searchString = request.form['content'].replace(' ', '')
        try:
            dbConn = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
            db = dbConn['crawlerDB']
            reviews = db[searchString].find({})
            if reviews.count() > 0:
                return render_template('results.html', reviews=reviews)
            else:
                flipkart_link = "https://www.flipkart.com/search?q=" + searchString
                flipkartpage_uClient = uReq(flipkart_link)
                flipkart_page = flipkartpage_uClient.read()
                flipkartpage_uClient.close()

                flipkart_html = bs(flipkart_page, 'html.parser')

                bigboxes = flipkart_html.findAll(
                    'div', {'class': 'bhgxx2 col-12-12'})
                del bigboxes[:3]

                box = bigboxes[0]

                product_link = 'https://www.flipkart.com/search?q=' + \
                    box.div.div.div.a['href']
                product_uClient = uReq(product_link)
                product_page = product_uClient.read()
                product_uClient.close()

                productPage_html = bs(product_page, 'html.parser')

                review_containers = productPage_html.findAll(
                    'div', {'class': '_3nrCtb'})

                table = db[searchString]
                reviews = []

                for review_container in review_containers:
                    try:
                        name = review_container.div.div.findAll(
                            'p', {'class': '_3LYOAd _3sxSiS'})[0].text
                    except:
                        name = 'No Name'

                    try:
                        rating = review_container.div.div.div.div.text
                    except:
                        rating = 'No Rating'

                    try:
                        review_head = review_container.div.div.p.text
                    except:
                        review_head = "There's no head for the review"

                    try:
                        cust_review = review_container.div.div.findAll(
                            'div', {'class': ''})[0].div.text
                    except:
                        cust_review = 'No customer review'

                    mydict = {'Product': searchString, 'Name': name, 'Rating': rating,
                              'Review Head': review_head, 'Review': cust_review}

                    table.insert_one(mydict)

                    reviews.append(mydict)
                return render_template('results.html', reviews=reviews)
        except:
            return 'Something is wrong'
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
