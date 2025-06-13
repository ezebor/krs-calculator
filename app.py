from flask import Flask

from src.clients import GitLabClient, JiraClient
from src.key_results import KRQualityStandardsHandler, KRVelocityAndOperativeExcellence

qualityStandardsHandler = KRQualityStandardsHandler(GitLabClient(), 2025, 1, 2025, 7)
qualityStandardsHandler.calculate()

velocityAndOperativeExcellence = KRVelocityAndOperativeExcellence(JiraClient(), 2025)
velocityAndOperativeExcellence.calculate()


# app = Flask(__name__)
#
# @app.route('/')
# def hello_world():  # put application's code here
#     return 'Hello World!'
#
#
# if __name__ == '__main__':
#     app.run(debug=True)