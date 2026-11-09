import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE = "https://api.kie.ai"


def find_dotenv():
    here = Path(__file__).resolve().parent
    for folder in [here, *here.parents]:
        candidate = folder / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_key():
    path = find_dotenv()
    if path is None:
        raise RuntimeError(".env with KIE_API_KEY not found in this folder or any parent")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() == "KIE_API_KEY":
            value = value.strip().strip('"').strip("'")
            if value:
                return value
    raise RuntimeError("KIE_API_KEY missing inside .env")


def session():
    s = requests.Session()
    s.headers.update({
        "Authorization": "Bearer " + load_key(),
        "Content-Type": "application/json",
    })
    return s


def get_credit(s):
    r = s.get(BASE + "/api/v1/chat/credit", timeout=30)
    r.raise_for_status()
    return r.json()


def create_task(s, model, payload):
    body = {"model": model, "input": payload}
    r = s.post(BASE + "/api/v1/jobs/createTask", json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 200:
        raise RuntimeError("createTask failed: " + json.dumps(data))
    return data["data"]["taskId"]


def poll(s, task_id, timeout=300, interval=4):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = s.get(BASE + "/api/v1/jobs/recordInfo", params={"taskId": task_id}, timeout=30)
        r.raise_for_status()
        data = r.json().get("data", {})
        state = data.get("state")
        last = data
        if state == "success":
            return data
        if state == "fail":
            raise RuntimeError("task failed: " + json.dumps(data))
        time.sleep(interval)
    raise TimeoutError("task did not finish: " + json.dumps(last or {}))


def result_urls(data):
    rj = data.get("resultJson")
    if isinstance(rj, str):
        rj = json.loads(rj)
    return (rj or {}).get("resultUrls", [])


def upload_base64(s, path, upload_path="images/refs", file_name=None):
    p = Path(path)
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    body = {
        "base64Data": "data:image/png;base64," + b64,
        "uploadPath": upload_path,
        "fileName": file_name or p.name,
    }
    last_exc = None
    for url in (BASE + "/api/file-base64-upload", BASE + "/api/v1/file-base64-upload"):
        try:
            r = s.post(url, json=body, timeout=120)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            data = r.json()
            dl = (data.get("data") or {}).get("downloadUrl")
            if dl:
                return dl
            last_exc = RuntimeError("no downloadUrl: " + json.dumps(data))
        except requests.HTTPError as exc:
            last_exc = exc
    raise RuntimeError("upload failed: " + repr(last_exc))


def download(s, url, dest):
    r = s.get(url, timeout=120)
    r.raise_for_status()
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    Path(dest).write_bytes(r.content)
    return len(r.content)


if __name__ == "__main__":
    s = session()
    print(json.dumps(get_credit(s), ensure_ascii=False, indent=2))
