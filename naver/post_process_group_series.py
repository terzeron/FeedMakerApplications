#!/usr/bin/env python
"""zlpla.aero 전용 collection post_process 스크립트.

수집된 게시물(작성자: 제목 형식) 중에서 "같은 작성자가 같은 킷을 여러 편에
걸쳐 만든 제작기 시리즈"를 찾아 출력한다. 시리즈로 인정되는 조건:

  1) 같은 작성자의 글이 2편 이상 모이고
  2) 그 묶음 안에 제목이 트리거(`완성`)에 매칭되는 완성편이 1편 이상 존재

collection.post_process_script_list 는 list_url_list 의 URL(페이지)마다 개별
호출되므로, 이 스크립트는 feed_dir 아래 상태파일(.series_accum.tsv)에 페이지별
항목을 누적한다. URL 이 page=1 이면(=새 수집 시작) 상태파일을 초기화한다. 매
호출마다 누적된 전체 항목으로 그룹핑을 다시 계산해 전체 그룹핑을 출력하므로,
마지막 페이지 호출의 출력이 완전한 그룹핑이 되고 프레임워크의 최종 dedup 이
중간 페이지의 부분 출력을 흡수한다(페이지 번호를 하드코딩하지 않는다).

입력(stdin) / 출력(stdout) 라인 형식은 newlist 와 동일하다:
    link<TAB>title<TAB>read<TAB>like<TAB>comment

수동으로 특정 newlist 파일에 대해 실행하려면(page=1 로 한 번만 호출):
    ./post_process_group_series.py -f . 'https://...&page=1' < newlist/YYYYMMDD.txt
"""

import json
import os
import re
import sys
from argparse import ArgumentParser
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests

ACCUM_FILENAME = ".series_accum.tsv"

# 완성기 인덱스 상태 파일(영속). page=1 에도 초기화하지 않는다.
FINISHED_INDEX_FILENAME = ".finished_index.tsv"

# 완성기 게시물 링크 형식(capture_item_navercafe.py 와 동일).
URL_PREFIX_TEMPLATE = "https://m.cafe.naver.com/ca-fe/web/cafes/%d/articles/%d"

# 시리즈 최대 articleId 이후 이 폭 안에 올라온 완성기 글까지 "비슷한 시기"로 본다
# (카페 전역 articleId ≈ 200/일 → 18000 ≈ 90일).
FINISHED_MATCH_MARGIN = 18000

# 최초 backlog fetch 깊이 제한(horizon). anchor - 이 값보다 오래된 페이지는 안 받는다
# (24000 ≈ 120일). trim 은 하지 않으므로 이후 인덱스는 완만히 커진다.
FINISHED_COVERAGE = 24000

# page=1 호출 1회당 완성기 boardlist 페이지 요청 상한(통신 폭주 방지).
MAX_FETCH_PAGES_PER_RUN = 50

# 완성기 boardlist 요청 헤더/타임아웃.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
)
HTTP_HEADERS = {"User-Agent": DEFAULT_USER_AGENT, "Referer": "https://cafe.naver.com/"}
HTTP_TIMEOUT = 10

# 시리즈로 인정할 최소 편수(여러 편 = 2편 이상).
MIN_SERIES_SIZE = 2

# 완성/완료 편을 포함한 시리즈만 출력할지 여부.
# False(기본): 같은 작성자·같은 킷의 여러 편 제작기 시리즈를 완성 여부와 무관하게
#              모두 출력한다. 대부분의 시리즈가 제목에 "완성/완료"를 쓰지 않으므로
#              이 게이트를 켜면 대다수 시리즈가 누락된다.
# True: 아래 TRIGGER_RE 에 매칭되는 완성편이 1편 이상 있는 시리즈만 출력한다.
REQUIRE_COMPLETION = True

# 완성편을 가리키는 트리거. "완/완료/완성" 및 한자 "完"을 모두 포함한다
# (완 substring 이 완료·완성을 함께 커버).
TRIGGER_RE = re.compile(r"[완完]")

# 모델명 코드: 앞에 영문자가 오고 숫자를 포함하는 토큰. (F-14D, KF-16D, HH-60G,
# AH-64D, A-6E, B-1B, SU-33, MH-60R, B777-200ER, A321neo, A-10C 등)
# 스케일 표기(1/48, 1/35)는 숫자로 시작하므로 매칭되지 않는다.
MODEL_CODE_RE = re.compile(r"[A-Za-z]+(?:[-\s]?\d+[A-Za-z]*)+")

# 제조사/브랜드. 킷 식별에는 도움이 되지만 너무 흔해서 클러스터링 키로는 쓰지
# 않는다(같은 작성자의 서로 다른 킷을 잘못 병합할 수 있음).
BRANDS = {
    "아카데미",
    "타미야",
    "하세가와",
    "즈베즈다",
    "트럼피터",
    "트럼페터",
    "드래곤",
    "이탈레리",
    "이탈래리",
    "키네틱",
    "키티호크",
    "조형촌",
    "레벨",
    "미니베이스",
    "academy",
    "tamiya",
    "hasegawa",
    "zvezda",
    "trumpeter",
    "dragon",
    "italeri",
    "kinetic",
    "kittyhawk",
    "minibase",
    "revell",
    "meng",
    "아카",
    "아카데미과학",
    "합동과학",
    "아카데미B737맥스",
}

# 킷 이름으로 보기 어려운(공정/상태/일반) 명사. 클러스터링 신호에서 제외한다.
STOP_NOUNS = {
    "제작",
    "제작기",
    "제작중",
    "제작기입니다",
    "완성",
    "완성기",
    "최종",
    "조립",
    "조립완료",
    "도색",
    "완료",
    "시작",
    "작업",
    "사진",
    "주의",
    "스압",
    "스왑",
    "데칼",
    "디테일",
    "디테일업",
    "개조",
    "변환",
    "편",
    "중",
    "님",
    "공정",
    "공정률",
    "프로",
    "초호화",
    "호화",
    "대물",
    "신제품",
    "출시",
    "박스",
    "개봉",
    "부",
    "일차",
    "이번",
    "다시",
    "제법",
    "난이도",
    "고비",
    "고난",
    "연습",
    "출품",
    "본좌",
    "누락",
    "누락본",
    "본",
    "실내",
    "촬영",
    "인테리어",
    "기본",
    "재제작",
    "재작업",
    "재개",
    "무장",
    "휠베이",
    "배선",
    "추가",
    "스텐실",
    "노즈아트",
    "폴딩",
    "만들기",
    # 일반/서술 명사(킷 식별에 무의미해 오병합을 유발).
    "항공기",
    "항공",
    "오랫만",
    "오랜만",
    "과학",
    "한국",
    "동시",
    "내부",
    "공포",
    "성공",
    "도움",
    "최대",
    "얼마",
    "실수",
    "휴가",
    "넋두리",
    "난관",
    "데이터",
    "에어로",
    "신도장",
    "개수",
    "사장",
    "신금형",
    "선반",
    "다이소",
    "은색",
    "프롭",
    "램프",
    "시공",
    "부대",
    "연합",
    "특수",
    "독일",
    "연대",
    "로터",
    "피규어",
}

# newlist 라인의 첫 필드가 http(s) 링크인지 확인.
LINK_RE = re.compile(r"^https?://")

# 링크에서 articleId 추출(.../articles/{id}).
ARTICLE_ID_RE = re.compile(r"/articles/(\d+)")


def _extract_article_id(link: str) -> int | None:
    m = ARTICLE_ID_RE.search(link)
    return int(m.group(1)) if m else None


@contextmanager
def _suppress_stderr():
    """stderr 를 임시로 /dev/null 로 돌린다.

    kiwipiepy 초기화 시 모델 로드 배너 등이 stderr 로 새어나갈 수 있는데,
    프레임워크(feed_maker_util.Process.exec_cmd)는 서브프로세스 stderr 에
    'error' 문자열이 있으면 출력 전체를 폐기한다. 오작동을 막기 위해 억제한다.
    """
    saved_fd = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull_fd, 2)
        yield
    finally:
        os.dup2(saved_fd, 2)
        os.close(devnull_fd)
        os.close(saved_fd)


with _suppress_stderr():
    from kiwipiepy import Kiwi

    _KIWI = Kiwi()


def _extract_nouns(text: str) -> list[str]:
    """kiwi 로 일반명사(NNG)/고유명사(NNP)를 추출한다(길이 2 이상, 불용어 제외)."""
    nouns: list[str] = []
    with _suppress_stderr():
        tokens = _KIWI.tokenize(text)
    for tok in tokens:
        if tok.tag in ("NNG", "NNP") and len(tok.form) >= 2:
            form = tok.form
            if form in STOP_NOUNS or form.lower() in BRANDS:
                continue
            nouns.append(form)
    return nouns


def _extract_model_codes(text: str) -> set[str]:
    """모델명 코드를 정규화(대문자, 구분자 제거)해 집합으로 반환한다."""
    codes: set[str] = set()
    for m in MODEL_CODE_RE.finditer(text):
        token = m.group(0)
        # 실제로 숫자가 들어있는 것만(순수 영문 약어 배제).
        if not any(ch.isdigit() for ch in token):
            continue
        # 브랜드명 + 스케일 숫자(예: "Minibase 1/48")가 코드로 오인되는 것 방지.
        alpha_prefix = re.match(r"[A-Za-z]+", token)
        if alpha_prefix and alpha_prefix.group(0).lower() in BRANDS:
            continue
        norm = re.sub(r"[-\s]", "", token).upper()
        codes.add(norm)
    return codes


class Item:
    """수집된 게시물 한 건."""

    def __init__(self, raw_line: str) -> None:
        self.raw = raw_line
        fields = raw_line.split("\t")
        self.link = fields[0]
        self.title = fields[1] if len(fields) > 1 else ""
        # "작성자: 제목" 분리(첫 콜론 기준).
        if ": " in self.title:
            author, subject = self.title.split(": ", 1)
        elif ":" in self.title:
            author, subject = self.title.split(":", 1)
        else:
            author, subject = "", self.title
        self.author = author.strip()
        self.subject = subject.strip()
        self.model_codes = _extract_model_codes(self.subject)
        self.nouns = set(_extract_nouns(self.subject))
        self.is_trigger = bool(TRIGGER_RE.search(self.subject))


def _cluster(items: list[Item]) -> list[list[Item]]:
    """같은 작성자끼리 묶은 뒤, 모델 코드를 우선 신호로 union-find 클러스터링한다.

    1단계: 같은 모델 코드(F-14D, KF-16D …)를 공유하는 항목을 먼저 병합한다.
           모델 코드가 킷 정체성의 지배적 신호이므로 이것이 최우선이다.
    2단계: 모델 코드로 식별되지 않는(한글 이름으로만 불리는) 킷을 위해, 공유
           명사로 병합한다. 단 **코드를 가진 클러스터에는 명사로 병합하지 않는다**
           (양쪽 모두 코드가 없을 때만 명사 병합). 코드가 있는 킷은 코드로만
           정의하고, 무코드 항목이 명사(구판/스케일 등 범용어 포함)를 다리 삼아
           F-86D·헤리어·미그23 처럼 다른 킷을 뭉치는 것을 원천 차단한다.
    """
    parent = list(range(len(items)))
    # 각 루트가 대표하는 클러스터에 누적된 모델 코드 집합.
    code_agg: list[set[str]] = [set(it.model_codes) for it in items]

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        parent[ra] = rb
        code_agg[rb] |= code_agg[ra]

    # 작성자별 인덱스 그룹.
    by_author: dict[str, list[int]] = {}
    for idx, item in enumerate(items):
        by_author.setdefault(item.author, []).append(idx)

    for indices in by_author.values():
        # 1단계: 모델 코드 공유로 우선 병합.
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                i, j = indices[a], indices[b]
                if items[i].model_codes & items[j].model_codes:
                    union(i, j)
        # 2단계: 공유 명사로 병합하되, 어느 한쪽 클러스터라도 코드를 가지고 있으면
        #        잇지 않는다(명사 병합은 양쪽 모두 무코드일 때만).
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                i, j = indices[a], indices[b]
                if find(i) == find(j):
                    continue
                if not (items[i].nouns & items[j].nouns):
                    continue
                if code_agg[find(i)] or code_agg[find(j)]:
                    continue
                union(i, j)

    clusters: dict[int, list[Item]] = {}
    for idx in range(len(items)):
        clusters.setdefault(find(idx), []).append(items[idx])
    return list(clusters.values())


class FinishedItem:
    """완성기 게시판의 게시물 한 건(인덱스 항목)."""

    def __init__(
        self,
        article_id: int,
        link: str,
        nick: str,
        subject: str,
        read: int,
        like: int,
        comment: int,
        is_public: bool = True,
    ) -> None:
        self.article_id = article_id
        self.link = link
        self.nick = nick
        self.subject = subject
        self.read = read
        self.like = like
        self.comment = comment
        self.is_public = is_public
        self.model_codes = _extract_model_codes(subject)
        self.nouns = set(_extract_nouns(subject))

    @classmethod
    def from_api(cls, item: dict) -> "FinishedItem | None":
        """boardlist API 의 result.articleList[].item 을 FinishedItem 으로 변환."""
        try:
            article_id = int(item["articleId"])
            cafe_id = int(item["cafeId"])
            nick = re.sub(r"[\t\n]", " ", item["writerInfo"]["nickName"].strip())
            subject = re.sub(r"[\t\n]", " ", item["subject"].strip())
        except (KeyError, TypeError, ValueError):
            return None
        link = URL_PREFIX_TEMPLATE % (cafe_id, article_id)
        is_public = (
            bool(item.get("openArticle", False))
            and not item.get("blindArticle", False)
            and not item.get("restrictMenu", False)
        )
        return cls(
            article_id,
            link,
            nick,
            subject,
            int(item.get("readCount", 0)),
            int(item.get("likeCount", 0)),
            int(item.get("commentCount", 0)),
            is_public,
        )

    def to_index_line(self) -> str:
        return (
            f"{self.article_id}\t{self.link}\t{self.nick}\t{self.subject}\t"
            f"{self.read}\t{self.like}\t{self.comment}"
        )

    def to_output_line(self) -> str:
        return (
            f"{self.link}\t{self.nick}: {self.subject}\t"
            f"{self.read}\t{self.like}\t{self.comment}"
        )


def _get_finished_base_url(feed_dir: Path) -> str | None:
    """feed_dir/conf.json 의 collection.finished_url_list 첫 항목(base URL)을 읽는다.

    프레임워크는 이 키를 화이트리스트하지 않아 무시하므로, 스크립트가 직접 읽는다.
    없거나 파싱 실패 시 None(=완성기 enrichment 비활성).
    """
    conf_path = feed_dir / "conf.json"
    try:
        with conf_path.open("r", encoding="utf-8") as f:
            conf = json.load(f)
    except (OSError, ValueError):
        return None
    url_list = (
        conf.get("configuration", {}).get("collection", {}).get("finished_url_list", [])
    )
    if isinstance(url_list, list) and url_list:
        return url_list[0]
    return None


def read_cookies(feed_dir: Path) -> dict[str, str]:
    """feed_dir/cookies.requestsclient.json 에서 쿠키를 읽는다.

    post_process_navercafe.py 의 관례를 그대로 따른다.
    """
    cookie_file = feed_dir / "cookies.requestsclient.json"
    cookies: dict[str, str] = {}
    if cookie_file.is_file():
        try:
            with cookie_file.open("r", encoding="utf-8") as f:
                for cookie in json.load(f):
                    name = cookie.get("name", "")
                    value = cookie.get("value", "")
                    if name and value:
                        cookies[name] = value
        except (OSError, ValueError):
            return {}
    return cookies


def _with_page(base_url: str, page: int) -> str:
    """base URL 의 page 파라미터를 주어진 값으로 덮어쓴다."""
    parsed = urlparse(base_url)
    query = parse_qs(parsed.query)
    query["page"] = [str(page)]
    new_query = urlencode({k: v[-1] for k, v in query.items()})
    return urlunparse(parsed._replace(query=new_query))


def _fetch_finished_page(
    base_url: str, page: int, cookies: dict[str, str]
) -> list[FinishedItem] | None:
    """완성기 boardlist 한 페이지를 받아 FinishedItem 목록으로 반환.

    반환: 파싱된 항목 목록(공개/비공개 모두, is_public 플래그로 구분).
          네트워크/JSON 오류 시 None(=상위에서 fetch 중단).
    """
    url = _with_page(base_url, page)
    try:
        with _suppress_stderr():
            resp = requests.get(
                url, cookies=cookies, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:  # noqa: BLE001 - 어떤 실패도 스크립트를 죽이지 않는다.
        return None
    articles = data.get("result", {}).get("articleList", [])
    result: list[FinishedItem] = []
    for article in articles:
        item = article.get("item")
        if not item:
            continue
        fi = FinishedItem.from_api(item)
        if fi:
            result.append(fi)
    return result


def _load_finished_index(index_path: Path) -> list[FinishedItem]:
    """완성기 인덱스 파일을 읽어 articleId 내림차순 목록으로 반환."""
    if not index_path.exists():
        return []
    items: list[FinishedItem] = []
    with index_path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 7:
                continue
            try:
                article_id = int(parts[0])
                read, like, comment = int(parts[4]), int(parts[5]), int(parts[6])
            except ValueError:
                continue
            items.append(
                FinishedItem(
                    article_id, parts[1], parts[2], parts[3], read, like, comment
                )
            )
    items.sort(key=lambda x: x.article_id, reverse=True)
    return items


def _save_finished_index(index_path: Path, items: list[FinishedItem]) -> None:
    with index_path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(it.to_index_line() + "\n")


def _refresh_finished_index(
    index_path: Path, base_url: str, accum_max: int | None, cookies: dict[str, str]
) -> list[FinishedItem]:
    """완성기 인덱스를 갱신(page=1 호출에서만 부른다).

    상단 신규분을 받되 overlap(기존 인덱스 상단 도달) 또는 horizon(최초 backlog 깊이
    제한) 또는 페이지 상한에서 멈춘다. 공개 글만 저장하고 trim 은 하지 않는다.
    """
    index = _load_finished_index(index_path)
    by_id: dict[int, FinishedItem] = {it.article_id: it for it in index}
    index_max_before = index[0].article_id if index else None

    floor: int | None = None
    fetched_any = False
    for page in range(1, MAX_FETCH_PAGES_PER_RUN + 1):
        items = _fetch_finished_page(base_url, page, cookies)
        if items is None:  # 네트워크/JSON 오류 → 받은 만큼만 유지.
            break
        if not items:  # 빈 페이지 → 게시판 끝.
            break
        fetched_any = True
        page_ids = [it.article_id for it in items]

        if floor is None:
            candidates = [
                v for v in (accum_max, index_max_before, max(page_ids)) if v is not None
            ]
            anchor = max(candidates)
            floor = anchor - FINISHED_COVERAGE

        reached_overlap = False
        for it in items:
            if index_max_before is not None and it.article_id <= index_max_before:
                reached_overlap = True
            if it.is_public and it.article_id not in by_id:
                by_id[it.article_id] = it

        if reached_overlap:
            break
        if min(page_ids) < floor:
            break

    merged = sorted(by_id.values(), key=lambda x: x.article_id, reverse=True)
    if fetched_any:
        _save_finished_index(index_path, merged)
    return merged


def _match_finished_to_clusters(
    clusters: list[list["Item"]], finished_items: list[FinishedItem]
) -> dict[int, list[FinishedItem]]:
    """각 완성기 항목을 가장 근접한 자격 클러스터 하나에 귀속시킨다.

    조건: 작성자 일치 + articleId 시기 창 + 제품(코드 우선, 무코드일 때만 명사) 매칭.
    반환: {cluster_index: [FinishedItem, ...]}
    """
    infos: list[dict | None] = []
    for cluster in clusters:
        if len(cluster) < MIN_SERIES_SIZE:
            infos.append(None)
            continue
        ids = [
            aid
            for aid in (_extract_article_id(it.link) for it in cluster)
            if aid is not None
        ]
        if not ids:
            infos.append(None)
            continue
        codes: set[str] = set()
        nouns: set[str] = set()
        for it in cluster:
            codes |= it.model_codes
            nouns |= it.nouns
        infos.append(
            {
                "author": cluster[0].author,
                "codes": codes,
                "nouns": nouns,
                "min": min(ids),
                "max": max(ids),
            }
        )

    matches: dict[int, list[FinishedItem]] = {}
    for fi in finished_items:
        best_key: tuple[int, int] | None = None
        best_idx = -1
        for idx, info in enumerate(infos):
            if info is None or fi.nick != info["author"]:
                continue
            if not (
                info["min"] <= fi.article_id <= info["max"] + FINISHED_MATCH_MARGIN
            ):
                continue
            code_match = bool(fi.model_codes & info["codes"])
            noun_match = (not info["codes"]) and bool(fi.nouns & info["nouns"])
            if not (code_match or noun_match):
                continue
            key = (1 if code_match else 0, -abs(fi.article_id - info["max"]))
            if best_key is None or key > best_key:
                best_key = key
                best_idx = idx
        if best_idx >= 0:
            matches.setdefault(best_idx, []).append(fi)
    return matches


def _load_accumulated(accum_path: Path) -> list[str]:
    if not accum_path.exists():
        return []
    with accum_path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def _save_accumulated(accum_path: Path, lines: list[str]) -> None:
    with accum_path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def _read_stdin_lines() -> list[str]:
    lines: list[str] = []
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("#"):
            continue
        if "\t" not in line or not LINK_RE.match(line):
            continue
        lines.append(line)
    return lines


def _is_first_page(url: str) -> bool:
    """URL 의 page 파라미터가 1 이거나 없으면 새 수집 시작으로 본다."""
    query = parse_qs(urlparse(url).query)
    page_values = query.get("page")
    if not page_values:
        return True
    return page_values[0] == "1"


def main() -> int:
    parser = ArgumentParser(
        description="group multi-part build-log series by author/kit"
    )
    parser.add_argument(
        "-f", dest="feed_dir", required=True, help="feed directory path"
    )
    parser.add_argument("url", help="the list URL currently being processed")
    args = parser.parse_args()

    feed_dir = Path(args.feed_dir)
    accum_path = feed_dir / ACCUM_FILENAME

    # page=1 이면 새 수집 시작 → 상태 초기화.
    accumulated = [] if _is_first_page(args.url) else _load_accumulated(accum_path)

    seen_links = set()
    for line in accumulated:
        seen_links.add(line.split("\t", 1)[0])

    for line in _read_stdin_lines():
        link = line.split("\t", 1)[0]
        if link in seen_links:
            continue
        seen_links.add(link)
        accumulated.append(line)

    _save_accumulated(accum_path, accumulated)

    items = [Item(line) for line in accumulated]
    clusters = _cluster(items)

    # 완성기 enrichment: conf.json 에 finished_url_list 가 있으면 활성화한다.
    base_url = _get_finished_base_url(feed_dir)
    matches: dict[int, list[FinishedItem]] = {}
    if base_url:
        index_path = feed_dir / FINISHED_INDEX_FILENAME
        if _is_first_page(args.url):
            # page=1 호출에서만 네트워크로 인덱스를 갱신한다(run당 1회).
            article_ids = [
                aid
                for aid in (_extract_article_id(it.link) for it in items)
                if aid is not None
            ]
            accum_max = max(article_ids) if article_ids else None
            finished_items = _refresh_finished_index(
                index_path, base_url, accum_max, read_cookies(feed_dir)
            )
        else:
            # page≠1 호출은 파일에서 로드만(네트워크 0).
            finished_items = _load_finished_index(index_path)
        matches = _match_finished_to_clusters(clusters, finished_items)

    # 여러 편(기본 2편 이상)인 시리즈를 출력.
    #  - 완성기 enrichment 활성: 매칭되는 완성기 글이 있는 시리즈만 출력하고,
    #    시리즈 뒤에 완성기 글을 이어 붙인다(완성기 매칭이 곧 "완성" 근거).
    #  - 비활성: 기존 동작(REQUIRE_COMPLETION 제목 게이트).
    qualifying: list[tuple[list[Item], list[FinishedItem]]] = []
    for idx, cluster in enumerate(clusters):
        if len(cluster) < MIN_SERIES_SIZE:
            continue
        if base_url:
            matched = matches.get(idx)
            if not matched:
                continue
            matched = sorted(matched, key=lambda x: x.article_id)
            qualifying.append((cluster, matched))
        elif not REQUIRE_COMPLETION or any(item.is_trigger for item in cluster):
            qualifying.append((cluster, []))

    out = sys.stdout
    first = True
    for cluster, matched in qualifying:
        if not first:
            out.write("\n")  # 그룹 구분(빈 줄). 최종 newlist 에서는 제거되지만
            # 수동 실행 시 사람이 보기 좋게 한다.
        first = False
        for item in cluster:
            out.write(item.raw + "\n")
        for fi in matched:
            out.write(fi.to_output_line() + "\n")

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import tempfile
        import unittest
        from unittest.mock import patch

        def _fi(article_id, nick, subject, read=0, like=0, comment=0, is_public=True):
            return FinishedItem(
                article_id,
                URL_PREFIX_TEMPLATE % (10503958, article_id),
                nick,
                subject,
                read,
                like,
                comment,
                is_public,
            )

        def _cluster_of(author, subjects, ids):
            """작성자/제목/articleId 로 Item 리스트(클러스터) 생성."""
            cluster = []
            for subject, aid in zip(subjects, ids):
                link = URL_PREFIX_TEMPLATE % (10503958, aid)
                cluster.append(Item(f"{link}\t{author}: {subject}\t0\t0\t0"))
            return cluster

        class TestFinishedItemParsing(unittest.TestCase):
            def _api_item(self, **kw):
                item = {
                    "articleId": 407387,
                    "cafeId": 10503958,
                    "writerInfo": {"nickName": "티벳여우벼리"},
                    "subject": "아카데미과학 1/48 F4F-4 WildCat 완성!!",
                    "readCount": 108,
                    "likeCount": 7,
                    "commentCount": 8,
                    "blindArticle": False,
                    "openArticle": True,
                    "restrictMenu": False,
                }
                item.update(kw)
                return item

            def test_from_api_basic(self):
                fi = FinishedItem.from_api(self._api_item())
                self.assertEqual(fi.article_id, 407387)
                self.assertEqual(
                    fi.link,
                    "https://m.cafe.naver.com/ca-fe/web/cafes/10503958/articles/407387",
                )
                self.assertEqual(fi.nick, "티벳여우벼리")
                self.assertTrue(fi.is_public)
                self.assertIn("F4F4", fi.model_codes)

            def test_from_api_blind_not_public(self):
                self.assertFalse(
                    FinishedItem.from_api(self._api_item(blindArticle=True)).is_public
                )
                self.assertFalse(
                    FinishedItem.from_api(self._api_item(openArticle=False)).is_public
                )
                self.assertFalse(
                    FinishedItem.from_api(self._api_item(restrictMenu=True)).is_public
                )

            def test_from_api_strips_tabs(self):
                fi = FinishedItem.from_api(self._api_item(subject="a\tb\nc"))
                self.assertNotIn("\t", fi.subject)
                self.assertNotIn("\n", fi.subject)

            def test_from_api_missing_field(self):
                self.assertIsNone(FinishedItem.from_api({"articleId": 1}))

            def test_output_line(self):
                fi = _fi(100, "kim", "F-14D 완성", read=5, like=1, comment=2)
                self.assertEqual(
                    fi.to_output_line(),
                    "https://m.cafe.naver.com/ca-fe/web/cafes/10503958/articles/100\tkim: F-14D 완성\t5\t1\t2",
                )

        class TestWithPage(unittest.TestCase):
            def test_overrides_page(self):
                base = (
                    "https://apis.naver.com/x/articles?pageSize=50&sortBy=TIME&page=1"
                )
                self.assertIn("page=7", _with_page(base, 7))
                self.assertNotIn("page=1", _with_page(base, 7))

            def test_adds_page_when_absent(self):
                self.assertIn("page=3", _with_page("https://apis.naver.com/x?a=b", 3))

        class TestIndexRoundTrip(unittest.TestCase):
            def test_save_load(self):
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "idx.tsv"
                    items = [
                        _fi(200, "kim", "F-14D 완성"),
                        _fi(100, "lee", "코브라 완성"),
                    ]
                    _save_finished_index(p, items)
                    loaded = _load_finished_index(p)
                    self.assertEqual([x.article_id for x in loaded], [200, 100])  # desc
                    self.assertEqual(loaded[1].nick, "lee")

            def test_load_missing(self):
                with tempfile.TemporaryDirectory() as d:
                    self.assertEqual(_load_finished_index(Path(d) / "none.tsv"), [])

        class TestMatching(unittest.TestCase):
            def test_code_match_within_window(self):
                c = _cluster_of("kim", ["F-14D 제작기 1", "F-14D 제작 2"], [100, 110])
                fi = _fi(120, "kim", "F-14D 톰캣 완성")
                matches = _match_finished_to_clusters([c], [fi])
                self.assertEqual(matches.get(0), [fi])

            def test_author_mismatch(self):
                c = _cluster_of("kim", ["F-14D 제작기 1", "F-14D 제작 2"], [100, 110])
                fi = _fi(120, "lee", "F-14D 완성")
                self.assertEqual(_match_finished_to_clusters([c], [fi]), {})

            def test_time_window_before_min(self):
                c = _cluster_of("kim", ["F-14D 제작기 1", "F-14D 제작 2"], [100, 110])
                fi = _fi(90, "kim", "F-14D 완성")  # min 미만
                self.assertEqual(_match_finished_to_clusters([c], [fi]), {})

            def test_time_window_after_margin(self):
                c = _cluster_of("kim", ["F-14D 제작기 1", "F-14D 제작 2"], [100, 110])
                fi = _fi(110 + FINISHED_MATCH_MARGIN + 1, "kim", "F-14D 완성")
                self.assertEqual(_match_finished_to_clusters([c], [fi]), {})

            def test_single_part_not_matched(self):
                c = _cluster_of("kim", ["F-14D 제작기 1"], [100])
                fi = _fi(120, "kim", "F-14D 완성")
                self.assertEqual(_match_finished_to_clusters([c], [fi]), {})

            def test_conflict_assigned_to_closest(self):
                c_far = _cluster_of(
                    "kim", ["F-14D 제작기 1", "F-14D 제작 2"], [100, 110]
                )
                c_near = _cluster_of(
                    "kim", ["F-14D 제작기 A", "F-14D 제작 B"], [200, 210]
                )
                fi = _fi(205, "kim", "F-14D 완성")
                matches = _match_finished_to_clusters([c_far, c_near], [fi])
                self.assertNotIn(0, matches)
                self.assertEqual(matches.get(1), [fi])

        class TestRefresh(unittest.TestCase):
            def test_overlap_stops(self):
                # 기존 인덱스 max=300. page1 에 [305,300] → 305 신규, 300 overlap → 1페이지에서 정지.
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "idx.tsv"
                    _save_finished_index(p, [_fi(300, "kim", "old 완성")])
                    pages = {
                        1: [_fi(305, "kim", "new 완성"), _fi(300, "kim", "old 완성")]
                    }
                    calls = []

                    def fake(base, page, cookies):
                        calls.append(page)
                        return pages.get(page, [])

                    with patch("__main__._fetch_finished_page", side_effect=fake):
                        merged = _refresh_finished_index(p, "http://x", 305, {})
                    self.assertEqual(calls, [1])
                    self.assertEqual({m.article_id for m in merged}, {300, 305})

            def test_horizon_stops(self):
                # 인덱스 없음. accum_max=None. anchor=첫페이지 최신. floor=anchor-COVERAGE.
                # 각 페이지 100 id 씩 내려가다 floor 아래로 가면 정지.
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "idx.tsv"
                    top = 100000

                    def fake(base, page, cookies):
                        hi = top - (page - 1) * 10000
                        return [_fi(hi, "kim", "완성"), _fi(hi - 9999, "kim", "완성")]

                    with patch("__main__._fetch_finished_page", side_effect=fake):
                        merged = _refresh_finished_index(p, "http://x", None, {})
                    # floor = 100000 - 24000 = 76000. page3 최소 = 100000-20000-9999=70001 < 76000 → page3 에서 정지.
                    self.assertTrue(min(m.article_id for m in merged) <= 76000)
                    self.assertTrue(max(m.article_id for m in merged) == 100000)

            def test_page_cap(self):
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "idx.tsv"
                    calls = []

                    def fake(base, page, cookies):
                        calls.append(page)
                        # 계속 새 항목(overlap 없음), floor 도 안 만나게 큰 값 유지.
                        return [_fi(10_000_000 - page, "kim", "완성")]

                    with patch("__main__._fetch_finished_page", side_effect=fake):
                        _refresh_finished_index(p, "http://x", 10_000_000, {})
                    self.assertEqual(len(calls), MAX_FETCH_PAGES_PER_RUN)

            def test_network_error_keeps_existing(self):
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "idx.tsv"
                    _save_finished_index(p, [_fi(300, "kim", "old 완성")])
                    with patch("__main__._fetch_finished_page", return_value=None):
                        merged = _refresh_finished_index(p, "http://x", 300, {})
                    self.assertEqual({m.article_id for m in merged}, {300})

            def test_blind_excluded_from_index(self):
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "idx.tsv"

                    def fake(base, page, cookies):
                        if page == 1:
                            return [
                                _fi(305, "kim", "완성"),
                                _fi(304, "kim", "완성", is_public=False),
                            ]
                        return []

                    with patch("__main__._fetch_finished_page", side_effect=fake):
                        merged = _refresh_finished_index(p, "http://x", 305, {})
                    self.assertEqual({m.article_id for m in merged}, {305})

        class TestConfigReading(unittest.TestCase):
            def _write_conf(self, d, conf):
                (Path(d) / "conf.json").write_text(json.dumps(conf), encoding="utf-8")

            def test_reads_finished_url_list(self):
                with tempfile.TemporaryDirectory() as d:
                    self._write_conf(
                        d,
                        {
                            "configuration": {
                                "collection": {"finished_url_list": ["http://x?page=1"]}
                            }
                        },
                    )
                    self.assertEqual(_get_finished_base_url(Path(d)), "http://x?page=1")

            def test_missing_key_returns_none(self):
                with tempfile.TemporaryDirectory() as d:
                    self._write_conf(
                        d, {"configuration": {"collection": {"list_url_list": ["y"]}}}
                    )
                    self.assertIsNone(_get_finished_base_url(Path(d)))

            def test_no_conf_returns_none(self):
                with tempfile.TemporaryDirectory() as d:
                    self.assertIsNone(_get_finished_base_url(Path(d)))

        sys.exit(unittest.main())
    else:
        sys.exit(main())
