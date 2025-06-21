# krs-calculator

# Overview

This script allows you to measure the velocity and quality standards KRs for each member of the team.

# Configuration

1. Create the folders /inputs and /outputs at the root of the project. The /inputs folder will contain all the intermediate files used to reckon the final metrics. The /outputs folder will contain one file for each KR with the final results.
2. Create a .env at the root of the folder. The file must be filled with some variables described in the next sections (see Environment Variables)
3. Verify whether your repositories contain the folders /src and /tests/unit, as it is shown in /src/models.py

## Environment Variables

PROJECT_IDS=["repository_id_1","repository_id_2"]
USER_ID="user_id"
PERSONAL_ACCESS_TOKEN="my_gitlab_access_token"

GITLAB_URL="https://gitlab.com/api/v4/projects"
COMMITS_URI="/repository/commits"
MERGE_REQUESTS_URI="/merge_requests"

DATETIME_FORMAT="%Y-%m-%dT%H:%M:%SZ"
JIRA_DATETIME_FORMAT="%Y-%m-%dT%H:%M:%S.%f%z"

EMAIL="my_email@aper.com"
JIRA_API_TOKEN="my_jira_api_token"
DOMAIN="aper.atlassian.net"

ASSIGNEES=["jira_user_id_1","jira_user_id_2"]

USERS=["user_name_1","user_name_2"]

# Play your app

Go to app.py, instantiate the KRs objects and pass the periods of time to the constructors according to what you want to measure. Afterwards play it. It will create files in both the /inputs and /outputs folders. The files you need to present the KRs of the entered period dwell in the /outputs folder.

