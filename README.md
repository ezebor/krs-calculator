# krs-calculator

# Overview

This script allows you to measure the velocity and quality standards KRs for each member of the team.

# Configuration

1. Create the folders /inputs and /outputs at the root of the project. The /inputs folder will contain all the intermediate files used to reckon the final metrics. The /outputs folder will contain one file for each KR with the final results.
2. Create a .env at the root of the folder. The file must be filled with some variables described in the next sections (see Environment Variables)
3. Verify whether your repositories contain the folders /src and /tests/unit, as it is shown in /src/models.py

## Environment Variables

PROJECT_IDS=["repository_id_1","repository_id_2"]
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

### How to get some values

* ASSIGNEES: see what is printed in a filter in hira when you try to get tickets of a specific person. If you copy that, you should be able to get that id.
* USERS: look at the users that make commits to the repos. Those are the names you must take.
* JIRA_API_TOKEN: see this: https://id.atlassian.com/manage-profile/security/api-tokens
* PROJECT_IDS: each string of the array is a project id that you can get from the project settings. You should include only the repositories that can be tested via unit tests (to prevent your teammates from having a low score)
* PERSONAL_ACCESS_TOKEN: see this: https://gitlab.com/-/user_settings/personal_access_tokens?page=1&state=active&sort=expires_asc

# Play your app

Go to app.py, instantiate the KRs objects and pass the periods of time to the constructors according to what you want to measure. Afterwards play it. It will create files in both the /inputs and /outputs folders. The files you need to present the KRs of the entered period dwell in the /outputs folder.

## Implemented KRs so far

There are 3 KRs calculators implemented so far:

### Quality standards KR

This KR will measure the quantity of merge requests of each specified person with unit tests divided by the total quantity of merge requests of the person.

Some merge requests appear to be from the person who merged the MR, which is not right. Therefore internally it first gets all the commits to master created by the specified person, and then it retrieves the MRs corresponding to those commits.

Important: this KR does not measure coverage. It only makes sure that if there is a /src file that was modified, then there is a proper test file under the path tests/unit.

### Velocity

This KR will measure the weighted average of all the sprints included in the configured window time, taking into account the accomplishment percentage of each sprint. The accomplishment percentage of one sprint is calculated like next:
* It gets all the tickets of the person (this process is repeated for each person specified in the environment variable) included in the sprint
* From the previous tickets we reckon the quantity that reached the status "to deploy in prod" or "done" within the sprint
* The second quantity is divided by the first one to put together the percentage

The above procedure is repeated for each person for each sprint in the window time. The results of each sprint for each person will be written in the /inputs files. The result of the metric for each person will be printed in the /outputs file.

### Operative excellence

Same as the Velocity KR, but in this case we filter the tickets so it includes only the tickets whose parent epic is "BAU" (or a name that includes that keyword, not case-sensitive)