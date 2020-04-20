import sqlite3


DB = 'aggregator/db/news.db'
TABLE_NAME = 'top_stories'


class NewsItem:
    def __init__(self, website, headline, summary, link, publish_time):
        self.website = website
        self.headline = headline
        self.summary = summary
        self.link = link
        self.publish_time = publish_time

    def __repr__(self):
        return f'{self.headline}: {self.summary}\r\n{self.link}\r\n{self.publish_time}\r\n'

    @property
    def article_in_db(self):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute(f"""select 1 from {TABLE_NAME} where (link = '{self.link}') or (headline = '{self.solve_escaping(self.headline)}' and summary = '{self.solve_escaping(self.headline)}')""")
        results = cur.fetchall()
        con.commit()
        con.close()
        return bool(len(results))

    @staticmethod
    def solve_escaping(data):
        return data.replace("'", "''")

    def update_db(self):
        if self.article_in_db:
            return
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute(f"""insert into {TABLE_NAME} values ('{self.website}', '{self.solve_escaping(self.headline)}', '{self.solve_escaping(self.summary)}', '{self.link}', '{self.publish_time}')""")
        con.commit()
        con.close()