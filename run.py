from myapp import create_app
from config import Config, ProductionConfig

if __name__ == '__main__':
    app = create_app(Config, ProductionConfig)
    app.run(host="0.0.0.0", port=10001)
