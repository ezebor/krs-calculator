from src.clients import GitLabClient, JiraClient
from src.key_results import KRQualityStandardsHandler, KRVelocityAndOperativeExcellence

qualityStandardsHandler = KRQualityStandardsHandler(GitLabClient(), 2025, 1, 2025, 7)
qualityStandardsHandler.calculate()

velocityAndOperativeExcellence = KRVelocityAndOperativeExcellence(JiraClient(), 2025)
velocityAndOperativeExcellence.calculate()