from bjl.MetaScraper import MetaScraper

scraper = MetaScraper()
url = "http://mashable.com/2013/03/08/6-questions-seth-priebatsch-levelup/"
print scraper.parse(url)