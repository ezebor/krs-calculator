import datetime as dt
import json
import os

import requests
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

PROJECT_IDS: list[str] = json.loads(os.environ.get("PROJECT_IDS"))
USER_ID = os.environ.get("USER_ID")
PERSONAL_ACCESS_TOKEN = os.environ.get("PERSONAL_ACCESS_TOKEN")

GITLAB_URL = os.environ.get("GITLAB_URL")
COMMITS_URI = os.environ.get("COMMITS_URI")
MERGE_REQUESTS_URI = os.environ.get("MERGE_REQUESTS_URI")

PROJECT_URL = f"{GITLAB_URL}/PROJECT_ID"
COMMITS_URL = f"{PROJECT_URL}{COMMITS_URI}"

FORMAT = os.environ.get("DATETIME_FORMAT")

EMAIL = os.environ.get("EMAIL")
API_TOKEN = os.environ.get("JIRA_API_TOKEN")
DOMAIN = os.environ.get("DOMAIN")

class Client:
    def __init__(self):
        self.gitlab_headers = {
            "Authorization": PERSONAL_ACCESS_TOKEN,
        }
        self.jira_headers = {
            "Accept": "application/json"
        }
        self.jira_auth = HTTPBasicAuth(EMAIL, API_TOKEN)

    def get_commits(self, user: str, year: int, month: int):
        pass

    def get_merge_requests(self, sha: str, project_id: str):
        pass

    def get_merge_requests_diff(self, sha: str, project_id: str):
        pass

    def get_sprint_id(self):
        pass

    def get_issues(self, sprint_id: str):
        pass

class GitLabClient(Client):
    def get_commits(self, user: str, year: int, month: int) -> list:
        since = dt.datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
        until = since + relativedelta(months=1)

        params = {
            "since": since.strftime(FORMAT),
            "until": until.strftime(FORMAT),
            "author": user,
            "with_stats": True
        }

        if params is None:
            params = {}

        result = []
        for project_id in PROJECT_IDS:
            data = requests.get(
                COMMITS_URL.replace("PROJECT_ID", project_id),
                headers=self.gitlab_headers,
                params=params).json()
            new_data = [
                {
                    **row,
                    "project_id": f"{project_id}"
                }
                for row in data
            ]
            result = [*result, *new_data]
        return result

    def get_merge_requests(self, sha: str, project_id: str):
        url = COMMITS_URL.replace("PROJECT_ID", project_id)
        return requests.get(f"{url}/{sha}/merge_requests", headers=self.gitlab_headers).json()

    def get_merge_requests_diff(self, sha: str, project_id: str):
        url = COMMITS_URL.replace("PROJECT_ID", project_id)
        return requests.get(f"{url}/{sha}/diff", headers=self.gitlab_headers).json()

class JiraClient(Client):
    def get_sprint_id(self):
        response = requests.get(
            f"https://{DOMAIN}/rest/api/3/field",
            auth=self.jira_auth,
            headers=self.jira_headers,
        )
        sprint_field_id = next((f["id"] for f in response.json() if "sprint" in f["name"].lower()), None)
        if not sprint_field_id:
            raise Exception("No se encontró el campo Sprint")
        print(f"Sprint name found: {sprint_field_id}")
        return sprint_field_id

    def get_issues(self, sprint_id: str):
        PAGE_SIZE = 100

        assignees: list[str] = json.loads(os.environ.get("ASSIGNEES"))

        status_categories = ['"To Do"', '"In Progress"', '"Done"']

        JQL = f'''
               project = "SITE BACKEND"
               AND assignee in ({",".join(assignees)})
               AND statusCategory in ({",".join(status_categories)})
               '''
        headers = {
            **self.jira_headers,
            "Content-Type": "application/json"
        }

        all_fields = [sprint_id, "key", "summary", "status", "assignee", "issuetype", "created", "parent"]

        def internal_get_issues(issues: list, start_at: int) -> list:
            params = {
                "jql": JQL,
                "startAt": start_at,
                "maxResults": PAGE_SIZE,
                "fields": ",".join(all_fields),
                "expand": "changelog"
            }
            response = requests.get(f"https://{DOMAIN}/rest/api/3/search", params=params, headers=headers, auth=self.jira_auth)
            data = response.json()
            print(f"{len(data['issues'])} issues were received")
            issues.extend(data["issues"])
            if start_at + PAGE_SIZE >= data["total"]:
                return issues
            start_at += PAGE_SIZE
            return internal_get_issues(issues, start_at)

        return internal_get_issues([], 0)