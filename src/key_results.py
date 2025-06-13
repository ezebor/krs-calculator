from collections import defaultdict
from datetime import datetime
from typing import Callable, Any

import pandas
import pandas as pd

from src.clients import *
from src.models import *

FORMAT = os.environ.get("DATETIME_FORMAT")
JIRA_DATETIME_FORMAT = os.environ.get("JIRA_DATETIME_FORMAT")

TYPE_BAU = "bau"

class KRHandler:
    def __init__(self, client: Client):
        self.client = client
        self.metric_rows: dict = {}

    def calculate(self) -> Any:
        pass

    def process_periods(self, a_function: Callable[[int, int], Any], year_start: int, month_start: int, year_end: int, month_end):
        current_month = month_start
        current_year = year_start
        while current_year <= year_end and current_month < month_end:
            a_function(current_year, current_month)
            current_year, current_month = self.increment_period(current_year, current_month)

    def increment_period(self, year: int, month: int) -> (int, int):
        current_month = month
        current_year = year
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1
        return current_year, current_month

class KRVelocityAndOperativeExcellence(KRHandler):
    def __init__(self, client: Client, year: int):
        super().__init__(client)
        self.delivered_date = None
        self.summary = defaultdict(lambda: defaultdict(lambda: {
            "total": 0,
            "delivered": 0,
            "bau_total": 0,
            "bau_delivered": 0,
            "qa_fail_issues": set()
        }))
        self.sprint_date_ranges = {}
        self.year = year

    def calculate(self):
        self.download_statistics()
        self.build_metric()

    def download_statistics(self):
        filename = f"./inputs/velocity_{self.year}.csv"
        if not os.path.exists(filename):
            sprint_field_id = self.client.get_sprint_id()

            issues = self.client.get_issues(sprint_id=sprint_field_id)

            for issue in issues:
                sprint_data = issue["fields"].get(sprint_field_id)
                sprint_list = sprint_data if isinstance(sprint_data, list) else [sprint_data] if sprint_data else []
                assignee = issue["fields"].get("assignee", {}).get("displayName", "Sin asignar")
                epic_name = issue.get('fields', {}).get('parent', {}).get('fields', {}).get('summary', "")

                for sprint in sprint_list:
                    name = sprint.get("name", "")
                    if f"{self.year}" in name and sprint.get("startDate") and sprint.get("endDate"):
                        self.sprint_date_ranges[name] = (
                            datetime.strptime(sprint["startDate"], JIRA_DATETIME_FORMAT),
                            datetime.strptime(sprint["endDate"], JIRA_DATETIME_FORMAT)
                        )
                # QA Failed tracking (único por issue por sprint)
                self.record_qa_fails(issue, assignee)

                delivered_date_obj = datetime.strptime(self.delivered_date, JIRA_DATETIME_FORMAT) if self.delivered_date else None
                for sprint_name, (start, end) in self.sprint_date_ranges.items():
                    self.summary[assignee][sprint_name]["total"] += 1
                    is_bau_issue = TYPE_BAU in epic_name.lower() and str(self.year) in epic_name
                    if is_bau_issue:
                        self.summary[assignee][sprint_name]["bau_total"] += 1
                    if delivered_date_obj and delivered_date_obj <= end:
                        self.summary[assignee][sprint_name]["delivered"] += 1
                        if is_bau_issue:
                            self.summary[assignee][sprint_name]["bau_delivered"] += 1

                self.sprint_date_ranges = {}
                self.delivered_date = None

            # Paso 4: salida
            records = [
                self.build_summary_record(values, sprint, user)
                for user, sprints_data in self.summary.items()
                for sprint, values in sprints_data.items()
            ]

            pd.DataFrame.from_records(records).to_csv(filename, index=False)

    def build_summary_record(self, values: dict, sprint_name: str, user: str):
        total = values["total"]
        delivered = values["delivered"]
        bau_total = values["bau_total"]
        bau_delivered = values["bau_delivered"]
        qa_fails = len(values["qa_fail_issues"])
        pct_total = round((delivered / total) * 100, 2) if total > 0 else 0
        pct_bau = round((bau_delivered / bau_total) * 100, 2) if bau_total > 0 else 0
        return {
            "developer": user,
            "sprint": sprint_name,
            "% delivered (total)": pct_total,
            "% BAU delivered": pct_bau,
            "Total issues": total,
            "Total bau": bau_total,
            "Total QA Failed": qa_fails
        }

    def record_qa_fails(self, issue: dict, assignee: str):
        delivery_statuses = {"to deploy in prod", "done", "in qa", "to qa"}
        qa_fail_status = "qa failed"

        for history in issue.get("changelog", {}).get("histories", []):
            change_time = datetime.strptime(history["created"], JIRA_DATETIME_FORMAT)
            for item in history.get("items", []):
                if item["field"] == "status":
                    new_status = item.get("toString", "").lower()
                    if new_status in delivery_statuses and not self.delivered_date:
                        self.delivered_date = history["created"]
                    if new_status == qa_fail_status:
                        for sprint_name, (start, end) in self.sprint_date_ranges.items():
                            if start <= change_time <= end:
                                self.summary[assignee][sprint_name]["qa_fail_issues"].add(issue["key"])

    def build_metric(self):
        filename = f"./outputs/velocity_and_operative_excellence_for_{self.year}.csv"
        if not os.path.exists(filename):
            input_rows = pd.read_csv(f"./inputs/velocity_{self.year}.csv").to_dict(orient="records")
            accumulators = defaultdict(lambda: {
                "total_delivered_percentage": 0,
                "total_bau_delivered_percentage": 0,
                "total_issues": 0,
                "total_bau": 0,
                "total_qa_fails": 0,
            })
            for row in input_rows:
                developer = row["developer"]
                accumulators[developer]["total_delivered_percentage"] += row["% delivered (total)"] * row["Total issues"]
                accumulators[developer]["total_bau_delivered_percentage"] += row["% BAU delivered"] * row["Total bau"]
                accumulators[developer]["total_issues"] += row["Total issues"]
                accumulators[developer]["total_bau"] += row["Total bau"]
                accumulators[developer]["total_qa_fails"] += row["Total QA Failed"]

            output_records = [
                {
                    "developer": developer,
                    "total_delivered_weighted_average": accumulators[developer]["total_delivered_percentage"] / max(accumulators[developer]["total_issues"], 1),
                    "total_bau_delivered_weighted_average": accumulators[developer]["total_bau_delivered_percentage"] / max(accumulators[developer]["total_bau"], 1),
                    "total_qa_fails": accumulators[developer]["total_qa_fails"]
                }
                for developer in accumulators.keys()
            ]

            pd.DataFrame.from_records(output_records).to_csv(filename, index=False)


class KRQualityStandardsHandler(KRHandler):
    def __init__(self, client: Client, year_start: int, month_start: int, year_end: int, month_end: int):
        super().__init__(client)
        self.year_start = year_start
        self.month_start = month_start
        self.year_end = year_end
        self.month_end = month_end

    def calculate(self) -> None:
        params = [self.year_start, self.month_start, self.year_end, self.month_end]
        self.download_commits(*params)
        self.download_testing_data(*params)
        self.build_metric(*params)

    def download_commits(self, year_start: int, month_start: int, year_end: int, month_end) -> None:
        if year_start > year_end or (year_start <= year_end and month_start > month_end):
            raise Exception("End date must not be earlier than start date")

        self.process_periods(self.process_commits_of_period, year_start, month_start, year_end, month_end)

    def process_commits_of_period(self, year: int, month: int):
        filename = f"./inputs/commits_{year}_{month}.csv"
        if not os.path.exists(filename):
            with(open(filename, "w")) as file:
                commits = [
                    commit.to_json() for commit in self.get_commits(year, month)
                ]
                json.dump(commits, file, indent=3)

    def get_commits(self, year: int, month: int) -> list[Commit]:
        result = []
        for user in json.loads(os.environ.get("USERS")):
            print(f"Getting commits of {user}")

            commits = [
                Commit(commit["web_url"], commit["author_name"], commit["project_id"])
                for commit in self.client.get_commits(user=user, year=year, month=month)
            ]

            for commit in commits:
                merge_request = self.client.get_merge_requests(commit.sha, commit.project_id)
                commit.set_commit_author(
                    merge_request[0]["author"]["name"] if len(merge_request) > 0 else commit.merge_author)

            print(f"Appending {len(commits)} commits from {user}")
            result += commits

        return result

    def download_testing_data(self, year_start: int, month_start: int, year_end: int, month_end):
        self.process_periods(self.process_tests_of_period, year_start, month_start, year_end, month_end)

    def process_tests_of_period(self, year: int, month: int):
        if not os.path.exists(f"./inputs/unit_tests_{year}_{month}.csv"):
            filename = f"./inputs/commits_{year}_{month}.csv"
            if not os.path.exists(filename):
                raise FileNotFoundError(f"File {filename} not found")

            with(open(filename, "r")) as file:
                commits_json = json.load(file)
                commits = []
                for commit_json in commits_json:
                    commit = Commit(commit_json["web_url"],
                                    commit_json["merge_author"],
                                    commit_json["project_id"],
                                    commit_json["sha"],
                                    commit_json["commit_author"])
                    diffs = self.client.get_merge_requests_diff(commit.sha, commit.project_id)
                    commit.set_has_tests(diffs)
                    commits.append(commit)
                    print(f"Processed commit: {commit}")
                self.create_csv_with_tests_metric(commits, month, year)

    def create_csv_with_tests_metric(self, commits: list[Commit], month: int, year: int):
        sha_list: list[str] = []
        merge_requests_list: list[str] = []
        authors_list: list[str] = []
        has_tests_list: list[bool] = []
        should_have_tests_list: list[bool] = []

        for commit in commits:
            if commit.should_have_tests:
                sha_list.append(commit.sha)
                merge_requests_list.append(commit.web_url)
                authors_list.append(commit.commit_author)
                has_tests_list.append(commit.has_tests)
                should_have_tests_list.append(commit.should_have_tests)

        csv_content = {
            "author": authors_list,
            "merge_request": merge_requests_list,
            "sha": sha_list,
            "has_tests": has_tests_list,
            "should_have_tests": should_have_tests_list,
        }

        pandas.DataFrame(csv_content).to_csv(f"./inputs/unit_tests_{year}_{month}.csv", index=False)

    def build_metric(self, year_start: int, month_start: int, year_end: int, month_end: int):
        self.process_periods(self.gather_information_of_period, year_start, month_start, year_end, month_end)
        rows = list(self.metric_rows.values())
        filename = f"./outputs/quality_standards_from_{year_start}_{month_start}_to_{year_end}_{month_end}.csv"
        if not os.path.exists(filename):
            rows = [
                {
                    "developer": row["developer"],
                    "percentage_of_merge_requests_with_tests": row["quantity_of_merge_requests_with_tests"] / row["quantity_of_merge_requests"],
                    "quantity_of_merge_requests": row["quantity_of_merge_requests"]
                }
                for row in rows
            ]
            pandas.DataFrame.from_records(rows).to_csv(filename, index=False)

    def gather_information_of_period(self, year: int, month: int):
        filename = f"./inputs/unit_tests_{year}_{month}.csv"
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {filename} not found")

        data = pandas.read_csv(filename).to_dict("records")
        for row in data:
            author_name = row["author"]
            if author_name not in self.metric_rows:
                self.metric_rows[author_name] = {
                    "developer": author_name,
                    "quantity_of_merge_requests": 0,
                    "quantity_of_merge_requests_with_tests": 0
                }

            if row["should_have_tests"]:
                self.metric_rows[author_name]["quantity_of_merge_requests"] += 1

            if row["has_tests"]:
                self.metric_rows[author_name]["quantity_of_merge_requests_with_tests"] += 1

                if not row["should_have_tests"]:
                    self.metric_rows[author_name]["quantity_of_merge_requests"] += 1

