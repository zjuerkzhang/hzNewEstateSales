import web
from indexPage import indexPage

urls = (
    '/', 'indexPage'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()