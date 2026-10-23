"""유튜브 영상을 Gemini로 분석해 노션 데이터베이스에 학습 노트를 만든다.

GitHub Actions에서 실행되며 입력은 환경변수로 받는다.
"""

import json
import os
import re
import sys

import requests
from google import genai
from google.genai import types

import schemas

NOTION_VERSION = "2022-06-28"
TEXT_LIMIT = 2000  # 노션 rich_text 한 덩어리 최대 길이
BLOCK_BATCH = 100  # 노션 요청 한 번에 넣을 수 있는 블록 수


def env(name, default=None):
    value = os.environ.get(name, "").strip()
    if not value and default is None:
        sys.exit(f"환경변수 {name}가 비어 있습니다.")
    return value or default


def normalize_url(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|live/|embed/)([\w-]{11})", url)
    if not m:
        sys.exit(f"유튜브 영상 주소가 아닙니다: {url}")
    return f"https://www.youtube.com/watch?v={m.group(1)}"


def fetch_meta(url):
    try:
        r = requests.get("https://www.youtube.com/oembed", params={"url": url, "format": "json"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("title", ""), data.get("author_name", "")
    except requests.RequestException:
        return "", ""


def analyze(url, tags, memo):
    schema, guides = schemas.build(tags)
    prompt = schemas.PROMPT.format(
        tags=", ".join(tags),
        guides=guides,
        memo=f"\n사용자 메모(특히 신경 써서 볼 부분): {memo}" if memo else "",
    )
    client = genai.Client(api_key=env("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=env("GEMINI_MODEL", "gemini-flash-latest"),
        contents=types.Content(parts=[
            # 영상 토큰은 대부분 오디오(초당 32)라, 프레임은 5초에 한 장만 본다
            types.Part(
                file_data=types.FileData(file_uri=url),
                video_metadata=types.VideoMetadata(fps=float(env("FRAME_FPS", "0.2"))),
            ),
            types.Part(text=prompt),
        ]),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema,
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
        ),
    )
    u = response.usage_metadata
    usage = f"입력 {u.prompt_token_count:,} · 출력 {u.candidates_token_count or 0:,} · 생각 {u.thoughts_token_count or 0:,} 토큰"
    print(f"토큰 사용량: {usage}")
    return json.loads(response.text), usage


# ---------- 노션 블록 ----------

def seconds(ts):
    parts = [int(p) for p in re.findall(r"\d+", ts or "")]
    if not 2 <= len(parts) <= 3:
        return None
    total = 0
    for p in parts:
        total = total * 60 + p
    return total


def text(content, link=None, bold=False, code=False):
    content = str(content or "")
    chunks = [content[i:i + TEXT_LIMIT] for i in range(0, len(content), TEXT_LIMIT)]
    return [{
        "type": "text",
        "text": {"content": c, "link": {"url": link} if link else None},
        "annotations": {"bold": bold, "code": code},
    } for c in chunks]


def ts_link(url, ts):
    sec = seconds(ts)
    if sec is None:
        return text(ts or "")
    return text(ts, link=f"{url}&t={sec}s")


def block(kind, rich, **extra):
    return {"object": "block", "type": kind, kind: {"rich_text": rich, **extra}}


def heading(content, level=2):
    return block(f"heading_{level}", text(content))


def para(rich):
    return block("paragraph", rich if isinstance(rich, list) else text(rich))


def bullet(rich):
    return block("bulleted_list_item", rich if isinstance(rich, list) else text(rich))


def table(headers, rows):
    def row(cells):
        return {"type": "table_row", "table_row": {"cells": [c if isinstance(c, list) else text(c) for c in cells]}}
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": [row(headers)] + [row(r) for r in rows],
        },
    }


def terms(items):
    return [bullet(text(f"{i['term']}: ", bold=True) + text(i["explanation"])) for i in items]


def render_harmony(d, url):
    out = []
    for p in d["progressions"]:
        title = p["name"] + (f" ({p['key']})" if p["key"] else "")
        out.append(heading(title, 3))
        out.append(para(text(" → ".join(c["symbol"] for c in p["chords"]), code=True)))
        out.append(table(
            ["코드", "로마숫자", "기능", "보이싱", "뉘앙스", "근거", "시간"],
            [[c["symbol"], c["roman"], c["function"], c["voicing"], c["nuance"], c["source"],
              ts_link(url, c["timestamp"])] for c in p["chords"]],
        ))
    if d["concepts"]:
        out.append(heading("개념 정리", 3))
        out += terms(d["concepts"])
    return out


def render_sound(d, url):
    out = []
    for p in d["patches"]:
        out.append(heading(f"{p['target']} · {p['instrument']}", 3))
        out.append(table(
            ["단계", "설정", "효과", "근거", "시간"],
            [[s["stage"], s["setting"], s["why"], s["source"], ts_link(url, s["timestamp"])] for s in p["steps"]],
        ))
    return out


def render_daw(d, url):
    out = [para(f"DAW: {d['daw']}")] if d["daw"] else []
    if d["steps"]:
        out.append(table(
            ["작업", "방법", "단축키", "시간"],
            [[s["action"], s["detail"], text(s["shortcut"], code=bool(s["shortcut"])), ts_link(url, s["timestamp"])]
             for s in d["steps"]],
        ))
    out += [bullet(t) for t in d["tips"]]
    return out


def render_rhythm(d, url):
    out = []
    for p in d["patterns"]:
        out.append(heading(f"{p['name']} ({p['time_signature']})", 3))
        if p["grid"]:
            out.append({"object": "block", "type": "code",
                        "code": {"rich_text": text(p["grid"]), "language": "plain text"}})
        out.append(para(text(p["feel"])))
        out.append(para(text(f"근거: {p['source']} · ") + ts_link(url, p["timestamp"])))
    if d["concepts"]:
        out.append(heading("개념 정리", 3))
        out += terms(d["concepts"])
    return out


def render_arrangement(d, url):
    out = []
    if d["sections"]:
        out.append(table(
            ["구간", "마디", "악기", "기법·의도", "시간"],
            [[s["section"], s["bars"], s["instruments"], s["technique"], ts_link(url, s["timestamp"])]
             for s in d["sections"]],
        ))
    if d["techniques"]:
        out.append(heading("편곡 기법", 3))
        out += terms(d["techniques"])
    return out


def render_mixing(d, url):
    out = []
    if d["chain"]:
        out.append(table(
            ["트랙", "프로세서", "설정", "목적", "근거", "시간"],
            [[c["track"], c["processor"], c["settings"], c["purpose"], c["source"], ts_link(url, c["timestamp"])]
             for c in d["chain"]],
        ))
    out += [bullet(t) for t in d["tips"]]
    return out


RENDERERS = {
    "harmony": render_harmony,
    "sound_design": render_sound,
    "daw": render_daw,
    "rhythm": render_rhythm,
    "arrangement": render_arrangement,
    "mixing": render_mixing,
}


def build_blocks(url, tags, data):
    blocks = [
        {"object": "block", "type": "video", "video": {"type": "external", "external": {"url": url}}},
        {"object": "block", "type": "callout", "callout": {
            "rich_text": text("\n".join(data["summary"])), "icon": {"type": "emoji", "emoji": "📝"}}},
    ]
    for tag in tags:
        field = schemas.SECTIONS[tag][0]
        if data.get(field):
            blocks.append(heading(tag))
            blocks += RENDERERS[field](data[field], url)
    if data["moments"]:
        blocks.append(heading("주요 구간"))
        blocks += [bullet(ts_link(url, m["timestamp"]) + text(f"  {m['point']}")) for m in data["moments"]]
    if data["practice"]:
        blocks.append(heading("연습 과제"))
        blocks += [block("to_do", text(p), checked=False) for p in data["practice"]]
    blocks.append(para(text("근거 표시: 말함 = 강사 설명 · 화면 = 영상에 보임 · 추정 = 소리로 짐작 (확인 필요)")))
    return blocks


# ---------- 노션 API ----------

def notion(method, path, body):
    r = requests.request(
        method, f"https://api.notion.com/v1/{path}", json=body, timeout=30,
        headers={
            "Authorization": f"Bearer {env('NOTION_TOKEN')}",
            "Notion-Version": NOTION_VERSION,
        },
    )
    if not r.ok:
        sys.exit(f"노션 API 오류 {r.status_code}: {r.text}")
    return r.json()


def create_page(url, tags, memo, title, channel, data):
    keywords = [k.replace(",", " ")[:100] for k in data["key_concepts"] if k.strip()]
    props = {
        "제목": {"title": text(title or url)},
        "URL": {"url": url},
        "태그": {"multi_select": [{"name": t} for t in tags]},
        "채널": {"rich_text": text(channel)},
        "요약": {"rich_text": text(" ".join(data["summary"]))},
        "키워드": {"multi_select": [{"name": k} for k in dict.fromkeys(keywords)]},
        "키": {"rich_text": text(data["key"])},
        "BPM": {"number": data["bpm"] or None},
        "난이도": {"select": {"name": data["difficulty"]}},
        "메모": {"rich_text": text(memo)},
    }
    blocks = build_blocks(url, tags, data)
    page = notion("POST", "pages", {
        "parent": {"database_id": env("NOTION_DATABASE_ID")},
        "properties": props,
        "children": blocks[:BLOCK_BATCH],
    })
    for i in range(BLOCK_BATCH, len(blocks), BLOCK_BATCH):
        notion("PATCH", f"blocks/{page['id']}/children", {"children": blocks[i:i + BLOCK_BATCH]})
    return page["url"]


def main():
    url = normalize_url(env("INPUT_URL"))
    tags = [t.strip() for t in env("INPUT_TAGS").split(",") if t.strip()]
    unknown = [t for t in tags if t not in schemas.TAGS]
    if not tags or unknown:
        sys.exit(f"알 수 없는 태그: {unknown or '없음'} (사용 가능: {', '.join(schemas.TAGS)})")
    memo = env("INPUT_MEMO", "")

    title, channel = fetch_meta(url)
    print(f"분석 시작: {title or url} [{', '.join(tags)}]")
    data, usage = analyze(url, tags, memo)
    page_url = create_page(url, tags, memo, title, channel, data)
    print(f"노션 페이지 생성: {page_url}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### [{title or url}]({page_url})\n\n태그: {', '.join(tags)}\n\n토큰: {usage}\n")


if __name__ == "__main__":
    main()
