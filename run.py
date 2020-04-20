from aggregator import app
from aggregator.scrape_content import scrape


if __name__ == '__main__':
    scrape()
    app.run(host='127.0.0.1', port=8080, threaded=True, debug=True)
