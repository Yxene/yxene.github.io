import os
import requests
from pathlib import Path

API_KEY = os.getenv("ROOT_ME_API_KEY")
USER_ID = 612388

class RootMeAPIClient(object):
  def __init__(self, api_key: str):
    super(RootMeAPIClient, self).__init__()
    self.s = requests.Session()
    self.s.cookies.set("api_key", api_key)
    self.s.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0"})

  def get_stats(self, user_id: str) -> dict:
    resp = self.s.get(f"https://api.www.root-me.org/auteurs/{user_id}")
    assert resp.status_code == 200, f"/auteurs/{user_id} {resp.status_code} {resp.reason}"
    return resp.json()


def generate_embedded_file(stats: dict) -> str:
  file_content = f"- **Rank :fontawesome-solid-ranking-star: :** {int(stats['position']):,} / +350,000\n- **Points :material-star-four-points: :** {int(stats['score']):,} pts\n- **Challenges solved :material-check: :** {len(stats['validations']):,}\n"
  return file_content

def main():
  output_file = Path("snippets/stats.md")
  client = RootMeAPIClient(API_KEY)
  stats = client.get_stats(USER_ID)
  file_content = generate_embedded_file(stats)
  output_file.write_text(file_content, encoding="utf-8")
  print("Snippet updated :", output_file)


if __name__ == '__main__':
  main()
