"""태그별 Gemini 응답 스키마와 분석 지시문."""

TAGS = ["화성", "사운드 디자인", "DAW/MIDI", "리듬", "편곡", "믹싱"]

SOURCE = {
    "type": "string",
    "enum": ["말함", "화면", "추정"],
    "description": "근거: 강사가 직접 말함 / 화면(자막·피아노롤·악보·건반)에 보임 / 소리만 듣고 추정",
}
TIMESTAMP = {"type": "string", "description": "영상 내 위치, mm:ss 또는 h:mm:ss. 모르면 빈 문자열"}


def _arr(items):
    return {"type": "array", "items": items}


def _obj(props, required=None):
    return {"type": "object", "properties": props, "required": required or list(props)}


S = {"type": "string"}

COMMON = {
    "summary": _arr(S) | {"description": "영상 핵심 요약 3줄"},
    "key_concepts": _arr(S) | {"description": "분류용 핵심 개념 키워드 3~8개, 짧은 명사형 (예: 세컨더리 도미넌트, 사이드체인)"},
    "difficulty": {"type": "string", "enum": ["입문", "중급", "고급"]},
    "key": {"type": "string", "description": "곡/예제의 조성 (예: C major, A minor). 해당 없으면 빈 문자열"},
    "bpm": {"type": "integer", "description": "예제 템포. 모르면 0"},
    "moments": _arr(_obj({"timestamp": TIMESTAMP, "point": S})) | {"description": "다시 볼 만한 주요 구간"},
    "practice": _arr(S) | {"description": "영상 내용으로 해볼 연습 과제 2~4개"},
}

SECTIONS = {
    "화성": (
        "harmony",
        _obj({
            "progressions": _arr(_obj({
                "name": {"type": "string", "description": "진행 이름이나 맥락 (예: 인트로 진행, 2-5-1 변형)"},
                "key": S,
                "chords": _arr(_obj({
                    "symbol": {"type": "string", "description": "코드 심볼 (예: Cmaj7, G7(b9)/B)"},
                    "roman": {"type": "string", "description": "로마숫자 표기 (예: Imaj7, V7/ii)"},
                    "function": {"type": "string", "description": "화성 기능 (T, SD, D, 차용 등)"},
                    "voicing": {"type": "string", "description": "구성음과 보이싱 (예: LH C-G / RH E-B-D, 3·7음 셸, 드롭2)"},
                    "nuance": {"type": "string", "description": "이 코드의 색채·역할·긴장감에 대한 설명"},
                    "source": SOURCE,
                    "timestamp": TIMESTAMP,
                })),
            })),
            "concepts": _arr(_obj({"term": S, "explanation": S})),
        }),
        "코드 진행은 코드 단위로 빠짐없이 적고, 각 코드의 보이싱(구성음, 텐션, 전위, 손 배치)과 뉘앙스를 설명하세요.",
    ),
    "사운드 디자인": (
        "sound_design",
        _obj({
            "patches": _arr(_obj({
                "target": {"type": "string", "description": "만드는 소리 (예: 슈퍼소 리드, 808 베이스)"},
                "instrument": {"type": "string", "description": "사용 신스/플러그인"},
                "steps": _arr(_obj({
                    "stage": {"type": "string", "description": "OSC, 필터, 엔벨로프, LFO, FX 등"},
                    "setting": {"type": "string", "description": "구체적인 설정값"},
                    "why": {"type": "string", "description": "이 설정이 소리에 주는 효과"},
                    "source": SOURCE,
                    "timestamp": TIMESTAMP,
                })),
            })),
        }),
        "패치를 만드는 단계를 순서대로, 화면에 보이는 파라미터 값은 가능한 한 정확히 적으세요.",
    ),
    "DAW/MIDI": (
        "daw",
        _obj({
            "daw": {"type": "string", "description": "사용 DAW와 버전. 모르면 빈 문자열"},
            "steps": _arr(_obj({
                "action": S,
                "detail": S,
                "shortcut": {"type": "string", "description": "단축키. 없으면 빈 문자열"},
                "timestamp": TIMESTAMP,
            })),
            "tips": _arr(S),
        }),
        "작업 흐름을 따라 할 수 있게 순서대로 적고, 화면이나 말로 나온 단축키·메뉴 경로를 포함하세요.",
    ),
    "리듬": (
        "rhythm",
        _obj({
            "patterns": _arr(_obj({
                "name": S,
                "time_signature": {"type": "string", "description": "박자 (예: 4/4)"},
                "grid": {"type": "string", "description": "16분 그리드 표기. 악기별로 줄바꿈 (예: KICK x---x---x---x---)"},
                "feel": {"type": "string", "description": "그루브·스윙·강세 설명"},
                "source": SOURCE,
                "timestamp": TIMESTAMP,
            })),
            "concepts": _arr(_obj({"term": S, "explanation": S})),
        }),
        "리듬 패턴은 16분 그리드(x = 타격, - = 쉼)로 표기하고 스윙·강세·벨로시티 같은 그루브 요소를 설명하세요.",
    ),
    "편곡": (
        "arrangement",
        _obj({
            "sections": _arr(_obj({
                "section": {"type": "string", "description": "인트로, 벌스, 프리코러스 등"},
                "bars": {"type": "string", "description": "마디 수. 모르면 빈 문자열"},
                "instruments": S,
                "technique": {"type": "string", "description": "이 구간에서 쓰인 편곡 기법과 의도"},
                "timestamp": TIMESTAMP,
            })),
            "techniques": _arr(_obj({"term": S, "explanation": S})),
        }),
        "구간별 악기 구성과 에너지 변화, 사용된 편곡 기법(빌드업, 대선율, 레이어링 등)을 정리하세요.",
    ),
    "믹싱": (
        "mixing",
        _obj({
            "chain": _arr(_obj({
                "track": {"type": "string", "description": "대상 트랙/버스"},
                "processor": {"type": "string", "description": "EQ, 컴프레서 등과 플러그인 이름"},
                "settings": {"type": "string", "description": "구체적인 설정값"},
                "purpose": S,
                "source": SOURCE,
                "timestamp": TIMESTAMP,
            })),
            "tips": _arr(S),
        }),
        "처리 체인을 트랙별로 순서대로 적고, 화면에 보이는 설정값(주파수, 게인, 어택/릴리즈, 비율)을 포함하세요.",
    ),
}


def build(tags):
    props = dict(COMMON)
    guides = []
    for tag in tags:
        field, schema, guide = SECTIONS[tag]
        props[field] = schema
        guides.append(f"- [{tag}] {guide}")
    return _obj(props), "\n".join(guides)


PROMPT = """당신은 음악 이론·작곡·프로듀싱 강의를 정리하는 조교입니다.
이 유튜브 영상을 보고 학습 노트용 데이터를 JSON으로 추출하세요.

규칙:
- 모든 설명은 한국어로 쓰고, 코드 심볼·플러그인 이름 같은 고유 표기는 원문 그대로 둡니다.
- 영상의 말, 화면(자막, 피아노롤, 악보, 건반, 플러그인 화면)을 모두 근거로 씁니다.
- source 필드가 있는 항목은 근거를 정직하게 표시합니다. 소리만 듣고 짐작한 것은 반드시 "추정"입니다.
- 영상에 없는 내용을 지어내지 마세요. 해당 내용이 없으면 빈 배열이나 빈 문자열로 둡니다.
- timestamp는 가능한 한 채워서 나중에 그 구간으로 바로 갈 수 있게 합니다.

분류 태그: {tags}
태그별 지시:
{guides}
{memo}"""
