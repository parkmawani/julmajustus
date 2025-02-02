
import os
import re
import requests
from github import Github

GITHUB_USERNAME = "julmajustus"


def replace_placeholder(content, placeholder_name, new_value):
    """
    Replaces <!-- PLACEHOLDER -->...<!-- PLACEHOLDER --> in 'content'
    with 'new_value'. The placeholder_name is everything between the tags.
    """
    pattern = fr"(<!--\s*{placeholder_name}\s*-->)(.*?)(<!--\s*{placeholder_name}\s*-->)"
    replacement = '\\1' + str(new_value) + '\\3'
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def get_contributions(username, token):
    query = """
    query ($username:String!) {
      user(login:$username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """
    variables = {"username": username}
    headers = {"Authorization": f"bearer {token}"}
    response = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)
    data = response.json()
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

def get_komarev_view_count(username):
    """
    Fetch the Komarev 'Profile Views' badge SVG and extract only the numeric count.
    """
    url = f"https://komarev.com/ghpvc/?username={username}"
    r = requests.get(url, timeout=10)
    svg_content = r.text

    counts = re.findall(r'<text [^>]*>(\d+)</text>', svg_content)
    if not counts:
        return "0"

    return counts[-1]


def main():
    token = os.environ.get("GITHUB_TOKEN", None)
    if not token:
        print("Warning: GITHUB_TOKEN not found in environment. Some stats won't work.")

    g = Github(token) if token else Github()
    user = g.get_user(GITHUB_USERNAME)

    num_repos = user.public_repos
    num_followers = user.followers
    
    contributions = get_contributions("julmajustus", os.environ["GITHUB_TOKEN"])

    num_stars = 0
    for repo in user.get_repos():
        num_stars += repo.stargazers_count

    pr_query = f"author:{user.login} type:pr is:merged is:open is:closed"
    pulls = g.search_issues(pr_query) if token else None
    num_pulls = pulls.totalCount if pulls else 0

    num_commits = 0


    page_views = get_komarev_view_count(GITHUB_USERNAME)

    with open("README.md", "r", encoding="utf-8") as f:
        readme_contents = f.read()

    readme_contents = replace_placeholder(readme_contents, "REPOS_PLACEHOLDER", str(num_repos))
    readme_contents = replace_placeholder(readme_contents, "COMMITS_PLACEHOLDER", str(num_commits))
    readme_contents = replace_placeholder(readme_contents, "CONTRIBUTIONS_PLACEHOLDER", str(contributions))
    readme_contents = replace_placeholder(readme_contents, "PR_PLACEHOLDER", str(num_pulls))
    readme_contents = replace_placeholder(readme_contents, "STARS_PLACEHOLDER", str(num_stars))
    readme_contents = replace_placeholder(readme_contents, "FOLLOWERS_PLACEHOLDER", str(num_followers))
    readme_contents = replace_placeholder(readme_contents, "PV_PLACEHOLDER", str(page_views))

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_contents)


if __name__ == "__main__":
    main()
