import csv

from anthropic import Anthropic
from dotenv import load_dotenv
from packaging.version import Version

load_dotenv()                      # STEP 0: 
client = Anthropic()
MODEL = "claude-sonnet-5-5"


# STEP 1: CSV padho
def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


# STEP 2: 
def find_latest_version(name, url):
    question = f"What is the latest stable version of '{name}'?"
    if url:
        question += f" Check this source first: {url}"
    question += " Reply with ONLY the version number, like 1.2.3. If not found, reply NOT_FOUND."

    messages = [{"role": "user", "content": question}]
    for _ in range(3):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=messages,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        )
        if resp.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": resp.content})

    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return text.split()[-1] if text else "NOT_FOUND"


# STEP 3: 
def compare(current, latest):
    if latest == "NOT_FOUND":
        return "UNKNOWN"
    if not current:
        return "NO_CURRENT_VERSION"
    try:
        return "UP_TO_DATE" if Version(current) >= Version(latest.lstrip("v")) else "OUTDATED"
    except Exception:
        return "CHECK_MANUALLY"


# STEP 4: 
def main():
    rows = read_csv("requiredsoftwares.csv")
    for row in rows:
        row["latest_version"] = find_latest_version(row["name"], row.get("url", ""))
        row["status"] = compare(row.get("version", ""), row["latest_version"])
        print(f'{row["sno"]}. {row["name"]}: {row.get("version") or "-"} -> {row["latest_version"]}  [{row["status"]}]')

    with open("latest_versions.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print("Done! Result: latest_versions.csv")


if __name__ == "__main__":
    main()