import scrapy
import json
import os
import hashlib


class NewsSpider(scrapy.Spider):
    name = "news"

    start_urls = [
        "https://news.google.com/search?q={company_name}",
        "https://pressgazette.co.uk/?s={company_name}",
        "https://www.bbc.co.uk/search?q={company_name}",
        "https://economictimes.indiatimes.com/topic/{company_name}-news",
        "https://www.ndtvprofit.com/search?q={company_name}",
        "https://trak.in/stories/search/{company_name}",
    ]

    def __init__(self, company_name=None, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)
        self.company_name = company_name.replace(" ", "+") if company_name else "test"
        self.company_name_lower = company_name.lower() if company_name else "test"
        self.result_data = []
        self.scraped_keys = set()
        self.data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(self.data_folder, exist_ok=True)

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        for url in self.start_urls:
            yield scrapy.Request(
                url=url.format(company_name=self.company_name),
                callback=self.parse,
                headers=headers
            )

    def parse(self, response):
        self.log(f"Scraping URL: {response.url}")
        if "pressgazette.co.uk" in response.url:
            self.parse_press_gazette(response)
        elif "bbc.co.uk" in response.url:
            self.parse_bbc(response)
        elif "economictimes.indiatimes.com" in response.url:
            self.parse_economic_times(response)
        elif "ndtvprofit.com" in response.url:
            self.parse_ndtv_profit(response)
        elif "trak.in" in response.url:
            self.parse_trak_in(response)
        else:
            self.parse_google_news(response)

        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            self.log(f"Following next page: {next_page}")
            yield response.follow(next_page, self.parse)

    def parse_press_gazette(self, response):
        for article in response.css("h3.post-title.c-story__header__headline--catalogue"):
            title = article.css("a::text").get()
            url = article.css("a::attr(href)").get()
            article_para = article.css("p.c-story__header__subtitle::text").get()
            self.extract_and_save(title, url, article_para, "Press Gazette")

    def parse_bbc(self, response):
     for promo in response.css("div.ssrcss-1f3bvyz-Stack.e1y4nx260"):
        title = promo.css("a.ssrcss-its5xf-PromoLink span::text").get()
        url = promo.css("a.ssrcss-its5xf-PromoLink::attr(href)").get()
        article_para = promo.css("p.ssrcss-1q0x1qg-Paragraph.e1jhz7w10::text").get()
        
        if url and not url.startswith("http"):
            url = response.urljoin(url)
        
        if not article_para:
            article_para = "No article text"
        
        self.extract_and_save(title, url, article_para, "BBC News")

    def parse_economic_times(self, response):
     for article in response.css("div.clr.flt.topicstry.story_list"):
        title = article.css("a.wrapLines.l2::attr(title)").get()
        url = article.css("a.wrapLines.l2::attr(href)").get()
        
        article_para = article.css("div.contentD p::text").getall() 
        article_para = " ".join(article_para).strip() 
        
        if url and not url.startswith("http"):
            url = response.urljoin(url)
        
        if not article_para:
            article_para = "No article text"
        
        self.extract_and_save(title, url, article_para, "Economic Times")

    def parse_ndtv_profit(self, response):
     for article in response.css("a.card-with-author-date-time-headline-m__search-single-result__VzvTc"):
        url = article.css("::attr(href)").get()
        if url:
            url = response.urljoin(url)
            
        title = article.css("span.card-with-author-date-time-headline-m__story-details-headline__5nTSC::text").get()
        if title:
            article_para = title 

        self.extract_and_save(title, url, article_para, "NDTV Profit")

    def parse_trak_in(self, response):
     for article in response.css("div.blog-card-simple"):
        title = article.css("h3.blog-title a::text").get()
        url = article.css("h3.blog-title a::attr(href)").get()
        article_para = article.css("div.content p::text").get()

        if not article_para:
            article_para = "No article text"

        self.extract_and_save(title, url, article_para, "Trak.in")

    def parse_google_news(self, response):
        for link in response.css("a"):
            title = link.css("::text").get()
            url = link.css("::attr(href)").get()
            article_para = link.css("::text").get()
            if url and not url.startswith("http"):
                url = response.urljoin(url)
            self.extract_and_save(title, url, article_para, "Google News")

    def extract_and_save(self, title, url, article_para, source):
        if title and url and self.company_name_lower in title.lower():
            unique_key = self.generate_unique_key(title, article_para)
            if unique_key not in self.scraped_keys:
                self.scraped_keys.add(unique_key)
                self.result_data.append({
                    "title": title.strip(),
                    "url": url.strip(),
                    "source": source,
                    "article_para": article_para or "No article text",
                    "unique_key": unique_key,
                })
                self.log(f"Saved article: {title}")
        else:
            self.log(f"Skipped article: {title or 'No title'}")

    def generate_unique_key(self, title, article_para):
        article_para = article_para or "unknown_paragraph"
        hash_input = f"{title.lower()}_{article_para}".encode()
        return hashlib.md5(hash_input).hexdigest()

    def save_to_json(self):
        filename = os.path.join(self.data_folder, f"{self.company_name}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.result_data, f, ensure_ascii=False, indent=4)
        self.log(f"Results saved to {filename} with {len(self.result_data)} articles.")

    def close(self, reason):
        self.save_to_json()
        self.log(f"Spider closed: {reason}, total articles saved: {len(self.result_data)}")
