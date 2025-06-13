QUANTITY_OF_CLASSES_THAT_MUST_BE_TESTED = 1

class Commit:
    def __init__(self, web_url: str, merge_author: str, project_id: str, sha: str = '', commit_author: str = '', has_tests: bool = False):
        self.sha = self.get_sha_from(web_url) if sha == '' else sha
        self.commit_author = commit_author
        self.web_url = web_url
        self.merge_author = merge_author
        self.has_tests = has_tests
        self.should_have_tests = False
        self.project_id = project_id

    def set_commit_author(self, commit_author: str):
        self.commit_author = commit_author

    def get_sha_from(self, web_url: str) -> str:
        return web_url.split("/commit/")[1]

    def __repr__(self):
        return f"\nweb_url: {self.web_url}\nmerge_author: {self.merge_author}\ncommit_author: {self.commit_author}\nshould_have_tests: {self.should_have_tests}\nhas_tests: {self.has_tests}\n"

    def to_json(self):
        return {
            "commit_author": self.commit_author,
            "merge_author": self.merge_author,
            "sha": self.sha,
            "web_url": self.web_url,
            "project_id": self.project_id,
        }

    def set_has_tests(self, diffs: list):
        quantity_of_modified_classes = 0
        quantity_of_tested_classes = 0
        for diff in diffs:
            new_path: str = str(diff["new_path"]).lower()
            if "src" in new_path or ("classes" in new_path and "tests/unit/classes" not in new_path):
                quantity_of_modified_classes += 1

            if "tests/unit" in new_path:
                quantity_of_tested_classes += 1

        self.should_have_tests = quantity_of_modified_classes != 0
        self.has_tests = quantity_of_tested_classes >= QUANTITY_OF_CLASSES_THAT_MUST_BE_TESTED