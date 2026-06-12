#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import Callable, List, NamedTuple, Optional

from bin.feed_maker_util import IO
from bin.crawler import Crawler


class Feed(NamedTuple):
    link: str
    title: str
    body: str


# article 상세 페이지의 태그 링크: <a href="/blog/@user/?tag=4942" ...>태그명</a>
# href/class/텍스트가 여러 줄에 걸쳐 있을 수 있어 DOTALL로 처리한다.
TAG_LINK_RE = re.compile(r'<a\s+href="[^"]*\?tag=\d+"[^>]*>(.*?)</a>', re.DOTALL)


def parse_args(argv: List[str]) -> tuple[int, List[str]]:
    num_of_recent_feeds = 20
    exclude_keywords: List[str] = []

    optlist, _ = getopt.getopt(argv, "f:n:x:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-x":
            exclude_keywords = [kw.strip() for kw in a.split(",") if kw.strip()]

    return num_of_recent_feeds, exclude_keywords


def strip_tags(line: str) -> str:
    return re.sub(r"<[^>]+>", "", line).strip()


def extract_tags(html: str) -> List[str]:
    """article 상세 페이지 HTML에서 태그 텍스트 목록을 추출한다.

    list 페이지에는 태그가 없으므로, 태그 기반 제외를 위해서는 각 글의
    상세 페이지를 들여다봐야 한다.
    """
    tags: List[str] = []
    for raw in TAG_LINK_RE.findall(html):
        text = strip_tags(raw)
        if text:
            tags.append(text)
    return tags


def parse_feed_list(line_list: List[str]) -> List[Feed]:
    feeds: List[Feed] = []
    seen_links: set[str] = set()

    link = None
    title = None
    body_parts: List[str] = []
    in_h2 = False
    in_body = False

    def finalize() -> None:
        nonlocal link, title, body_parts, in_h2, in_body
        if link and title and link not in seen_links:
            seen_links.add(link)
            feeds.append(Feed(link, title, " ".join(body_parts).strip()))
        link = None
        title = None
        body_parts = []
        in_h2 = False
        in_body = False

    for line in line_list:
        # <a href="/blog/@username/9698/" class="block">
        m = re.search(r'<a\s+href="(/blog/@[^"]+/\d+/)"[^>]*class="block"', line)
        if m:
            finalize()
            link = "https://wikidocs.net" + m.group(1)
            continue

        if not link:
            continue

        if title is None:
            # <h2 class="text-xl font-bold ...">
            if not in_h2:
                if re.search(r'<h2[^>]*class="text-xl font-bold', line):
                    in_h2 = True
                    # 제목이 같은 줄에 함께 있을 수도 있다
                    text = strip_tags(line)
                    if text:
                        title = text
                        in_h2 = False
                continue
            text = strip_tags(line)
            if text:
                title = text
                in_h2 = False
            continue

        # <p class="... break-words"> ... 본문 excerpt ... </p>
        if not in_body:
            if re.search(r"<p[^>]*break-words", line):
                in_body = True
                text = strip_tags(line)
                if text:
                    body_parts.append(text)
                if "</p>" in line:
                    finalize()
            continue

        if "</p>" in line:
            text = strip_tags(line)
            if text:
                body_parts.append(text)
            finalize()
            continue
        text = strip_tags(line)
        if text:
            body_parts.append(text)

    finalize()
    return feeds


def filter_excluded(
    feeds: List[Feed],
    exclude_keywords: List[str],
    get_extra_text: Optional[Callable[[Feed], str]] = None,
    limit: Optional[int] = None,
) -> List[Feed]:
    """제외 키워드에 걸리는 feed를 걸러낸다.

    매칭 대상은 기본적으로 list 페이지에서 얻은 제목+본문이다.
    get_extra_text가 주어지면 각 feed의 추가 텍스트(예: 상세 페이지 태그)를
    매칭 대상에 포함시켜, list 페이지에 없는 태그 기반 제외도 가능하게 한다.
    limit이 주어지면 통과한 feed가 limit개에 도달하는 즉시 멈춰
    불필요한 추가 fetch를 피한다.
    """
    if not exclude_keywords:
        return feeds

    result: List[Feed] = []
    for feed in feeds:
        if limit is not None and len(result) >= limit:
            break
        haystack = f"{feed.title} {feed.body}"
        if get_extra_text is not None:
            extra = get_extra_text(feed)
            if extra:
                haystack = f"{haystack} {extra}"
        if any(keyword in haystack for keyword in exclude_keywords):
            continue
        result.append(feed)
    return result


def print_feeds(feeds: List[Feed], limit: int) -> None:
    for feed in feeds[:limit]:
        print(f"{feed.link}\t{feed.title}")


def main() -> int:
    num_of_recent_feeds, exclude_keywords = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()
    feeds = parse_feed_list(line_list)

    if exclude_keywords:
        # 태그는 list 페이지에 없고 각 글의 상세 페이지에만 있으므로,
        # 제외 판정을 위해 상세 페이지를 추가로 받아 태그를 들여다본다.
        # 태그는 JS 렌더링 없이 노출되므로 render_js=False로 충분하다.
        crawler = Crawler(render_js=False, timeout=60)

        def get_tags_text(feed: Feed) -> str:
            html, error, _ = crawler.run(feed.link)
            if not html or error:
                return ""
            return " ".join(extract_tags(html))

        feeds = filter_excluded(
            feeds, exclude_keywords, get_tags_text, num_of_recent_feeds
        )
    else:
        feeds = filter_excluded(feeds, exclude_keywords)

    print_feeds(feeds, num_of_recent_feeds)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import io
        import contextlib
        import unittest

        def card(link: str, title_lines: List[str], body_lines: List[str]) -> List[str]:
            """리스트 페이지의 카드 하나에 해당하는 HTML 라인 목록을 만든다."""
            lines = [f'<a href="{link}" class="block">']
            lines.append(
                '<h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">'
            )
            lines.extend(title_lines)
            lines.append("</h2>")
            if body_lines is not None:
                lines.append(
                    '<p class="text-gray-600 dark:text-gray-400 mt-2 break-words">'
                )
                lines.extend(body_lines)
                lines.append("</p>")
            return lines

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_defaults(self):
                self.assertEqual(parse_args([]), (20, []))

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), (5, []))

            def test_parse_args_exclude_single(self):
                self.assertEqual(parse_args(["-x", "AD"]), (20, ["AD"]))

            def test_parse_args_exclude_multiple(self):
                self.assertEqual(
                    parse_args(["-x", "AD,PR,Sponsored"]),
                    (20, ["AD", "PR", "Sponsored"]),
                )

            def test_parse_args_exclude_trims_whitespace(self):
                self.assertEqual(parse_args(["-x", " AD , PR "]), (20, ["AD", "PR"]))

            def test_parse_args_exclude_drops_empty(self):
                self.assertEqual(parse_args(["-x", "AD,, ,PR,"]), (20, ["AD", "PR"]))

            def test_parse_args_exclude_empty_string(self):
                self.assertEqual(parse_args(["-x", ""]), (20, []))

            def test_parse_args_f_ignored(self):
                # -f는 인자를 받지만 동작에 영향 없음(기본값 유지)
                self.assertEqual(parse_args(["-f", "."]), (20, []))

            def test_parse_args_combined(self):
                self.assertEqual(
                    parse_args(["-f", ".", "-n", "3", "-x", "AD, PR"]),
                    (3, ["AD", "PR"]),
                )

            # --- strip_tags ---

            def test_strip_tags_removes_tags(self):
                self.assertEqual(strip_tags("<h2 class='x'>Hello</h2>"), "Hello")

            def test_strip_tags_strips_whitespace(self):
                self.assertEqual(strip_tags("   <b>Hi</b>   "), "Hi")

            def test_strip_tags_plain_text(self):
                self.assertEqual(strip_tags("  plain  "), "plain")

            def test_strip_tags_empty_after_strip(self):
                self.assertEqual(strip_tags("   <br/>   "), "")

            # --- parse_feed_list ---

            def test_parse_feed_list_basic(self):
                lines = card("/blog/@u/1/", ["Title One"], ["Body text"])
                self.assertEqual(
                    parse_feed_list(lines),
                    [Feed("https://wikidocs.net/blog/@u/1/", "Title One", "Body text")],
                )

            def test_parse_feed_list_skips_whitespace_before_title(self):
                lines = card("/blog/@u/1/", ["   ", "", "Real Title"], ["Body"])
                self.assertEqual(parse_feed_list(lines)[0].title, "Real Title")

            def test_parse_feed_list_joins_multiline_body(self):
                lines = card("/blog/@u/1/", ["Title"], ["   ", "line A", "", "line B"])
                self.assertEqual(parse_feed_list(lines)[0].body, "line A line B")

            def test_parse_feed_list_multiple_cards(self):
                lines = card("/blog/@u/1/", ["T1"], ["B1"]) + card(
                    "/blog/@u/2/", ["T2"], ["B2"]
                )
                feeds = parse_feed_list(lines)
                self.assertEqual(
                    [(f.title, f.body) for f in feeds], [("T1", "B1"), ("T2", "B2")]
                )

            def test_parse_feed_list_dedup_by_link(self):
                lines = card("/blog/@u/1/", ["First"], ["B1"]) + card(
                    "/blog/@u/1/", ["Dup"], ["B2"]
                )
                feeds = parse_feed_list(lines)
                self.assertEqual(len(feeds), 1)
                self.assertEqual(feeds[0].title, "First")

            def test_parse_feed_list_card_without_body(self):
                # break-words 단락이 없는 카드도 다음 카드/끝에서 finalize되어야 한다
                lines = ['<a href="/blog/@u/1/" class="block">']
                lines.append(
                    '<h2 class="text-xl font-bold text-gray-800">No Body Title</h2>'
                )
                lines += card("/blog/@u/2/", ["Has Body"], ["B2"])
                feeds = parse_feed_list(lines)
                self.assertEqual(
                    [(f.title, f.body) for f in feeds],
                    [("No Body Title", ""), ("Has Body", "B2")],
                )

            def test_parse_feed_list_same_line_body(self):
                lines = [
                    '<a href="/blog/@u/1/" class="block">',
                    '<h2 class="text-xl font-bold">Title</h2>',
                    '<p class="break-words">Inline body</p>',
                ]
                self.assertEqual(parse_feed_list(lines)[0].body, "Inline body")

            def test_parse_feed_list_ignores_content_before_anchor(self):
                lines = ["<div>garbage</div>", "<span>noise</span>"] + card(
                    "/blog/@u/1/", ["Title"], ["Body"]
                )
                feeds = parse_feed_list(lines)
                self.assertEqual(len(feeds), 1)
                self.assertEqual(feeds[0].title, "Title")

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), [])

            # --- filter_excluded ---

            def _feeds(self):
                return [
                    Feed("l1", "증시 브리핑", "시장 상태 양호"),
                    Feed("l2", "주택담보대출 금리", "은행 비교"),
                    Feed("l3", "일반 글", "서킷브레이커 발동"),
                ]

            def test_filter_excluded_empty_keywords_returns_all(self):
                feeds = self._feeds()
                self.assertEqual(filter_excluded(feeds, []), feeds)

            def test_filter_excluded_by_title(self):
                result = filter_excluded(self._feeds(), ["증시"])
                self.assertEqual([f.link for f in result], ["l2", "l3"])

            def test_filter_excluded_by_body(self):
                # 제목에는 없고 본문에만 있는 키워드도 제거 대상
                result = filter_excluded(self._feeds(), ["서킷브레이커"])
                self.assertEqual([f.link for f in result], ["l1", "l2"])

            def test_filter_excluded_multiple_keywords(self):
                result = filter_excluded(self._feeds(), ["증시", "주택담보대출"])
                self.assertEqual([f.link for f in result], ["l3"])

            def test_filter_excluded_no_match_keeps_all(self):
                feeds = self._feeds()
                self.assertEqual(filter_excluded(feeds, ["없는키워드"]), feeds)

            def test_filter_excluded_substring(self):
                result = filter_excluded(self._feeds(), ["담보"])
                self.assertEqual([f.link for f in result], ["l1", "l3"])

            # --- extract_tags ---

            def test_extract_tags_single(self):
                html = '<a href="/blog/@u/?tag=42" class="x">유용한정보</a>'
                self.assertEqual(extract_tags(html), ["유용한정보"])

            def test_extract_tags_multiline(self):
                # 실제 article 페이지에서 href/class/텍스트가 여러 줄에 걸쳐 있다
                html = (
                    '<a href="/blog/@infoplant/?tag=4942"\n'
                    '   class="text-blue-500 dark:text-blue-400">\n'
                    "    유용한정보\n"
                    "</a>"
                )
                self.assertEqual(extract_tags(html), ["유용한정보"])

            def test_extract_tags_multiple(self):
                html = (
                    '<a href="/blog/@u/?tag=1">재테크</a>'
                    '<a href="/blog/@u/?tag=2">보험연금</a>'
                )
                self.assertEqual(extract_tags(html), ["재테크", "보험연금"])

            def test_extract_tags_ignores_non_tag_links(self):
                # 본문/제목 링크(?tag= 없는 링크)는 태그가 아니다
                html = '<a href="/blog/@u/19075/">백링크 구축 전략</a>'
                self.assertEqual(extract_tags(html), [])

            def test_extract_tags_empty(self):
                self.assertEqual(extract_tags(""), [])

            # --- filter_excluded with extra text (article tags) ---

            def test_filter_excluded_by_extra_text(self):
                # 제목/본문에 없고 article 태그에만 있는 키워드도 제거 대상
                feeds = [Feed("l1", "제목", "본문"), Feed("l2", "다른글", "내용")]
                tags = {"l1": "유용한정보", "l2": "기술"}
                result = filter_excluded(feeds, ["유용한정보"], lambda f: tags[f.link])
                self.assertEqual([f.link for f in result], ["l2"])

            def test_filter_excluded_extra_text_still_matches_body(self):
                # extra가 비어도 기존 title/body 매칭은 그대로 동작
                feeds = [Feed("l1", "증시 브리핑", "")]
                self.assertEqual(filter_excluded(feeds, ["증시"], lambda f: ""), [])

            def test_filter_excluded_limit_stops_early(self):
                # limit만큼 채워지면 이후 feed는 fetch조차 하지 않는다
                calls: List[str] = []

                def extra(f: "Feed") -> str:
                    calls.append(f.link)
                    return ""

                feeds = [Feed(f"l{i}", f"T{i}", "") for i in range(5)]
                result = filter_excluded(feeds, ["없는키워드"], extra, 2)
                self.assertEqual([f.link for f in result], ["l0", "l1"])
                self.assertEqual(calls, ["l0", "l1"])

            # --- print_feeds ---

            def _capture_print(self, feeds, limit):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    print_feeds(feeds, limit)
                return buf.getvalue()

            def test_print_feeds_format(self):
                output = self._capture_print([Feed("l1", "T1", "B1")], 20)
                self.assertEqual(output, "l1\tT1\n")

            def test_print_feeds_respects_limit(self):
                feeds = [Feed(f"l{i}", f"T{i}", "") for i in range(5)]
                output = self._capture_print(feeds, 2)
                self.assertEqual(output, "l0\tT0\nl1\tT1\n")

            def test_print_feeds_empty(self):
                self.assertEqual(self._capture_print([], 20), "")

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py(--render-js=true)로 https://wikidocs.net/blog/main/ 을 받아온
            #       실제 HTML 중 파서가 act하는 영역(블록 anchor + h2 제목 + p excerpt) 3장만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_link_title.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '                        <a href="/blog/@history/18804/" class="block">',
                '                                    <h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">',
                "                                        불교는 어떻게 발상지 인도에서 사라지고 동아시아를 지배하게 되었는가",
                "                                    </h2>",
                '                                    <p class="text-gray-600 dark:text-gray-400 mt-2 break-words">',
                "세계 4대 종교의 하나인 불교가, 정작 그것이 탄생한 발상지 인도에서는 거의 자취를 감추다시피 사라졌다는 사실, 알고 계셨습니까? 많은 분들이 불교의 본고장이라고 하면 당연히…",
                "                                    </p>",
                '                        <a href="/blog/@history/18803/" class="block">',
                '                                    <h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">',
                "                                        마그나카르타는 민주주의 문서가 아니라 귀족의 이익 합의서였다: 800년간의 의미 변천",
                "                                    </h2>",
                '                                    <p class="text-gray-600 dark:text-gray-400 mt-2 break-words">',
                "흔히 민주주의와 자유의 출발점으로 떠받들어지는 마그나카르타가, 사실은 평범한 백성의 권리와는 거의 무관한, 반란을 일으킨 귀족들이 자신들의 특권을 지키기 위해 왕에게 들이민 …",
                "                                    </p>",
                '                        <a href="/blog/@history/18802/" class="block">',
                '                                    <h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">',
                "                                        콘스탄티노플 함락을 결정지은 것은 거대한 대포가 아니라 잠그지 않은 성문 하나였다",
                "                                    </h2>",
                '                                    <p class="text-gray-600 dark:text-gray-400 mt-2 break-words">',
                "1453년 천년의 도시 콘스탄티노플을 무너뜨린 결정적 한 방이, 사실은 역사상 가장 거대했던 그 대포가 아니라 누군가 깜빡하고 잠그지 않은 작은 쪽문 하나였다는 사실, 알고 …",
                "                                    </p>",
            ]

            def test_real_sample_end_to_end(self):
                feeds = parse_feed_list(self.REAL_SAMPLE_LINES)
                feeds = filter_excluded(feeds, [])
                output = self._capture_print(feeds, 5)
                self.assertEqual(
                    output,
                    "https://wikidocs.net/blog/@history/18804/\t불교는 어떻게 발상지 인도에서 사라지고 동아시아를 지배하게 되었는가\n"
                    "https://wikidocs.net/blog/@history/18803/\t마그나카르타는 민주주의 문서가 아니라 귀족의 이익 합의서였다: 800년간의 의미 변천\n"
                    "https://wikidocs.net/blog/@history/18802/\t콘스탄티노플 함락을 결정지은 것은 거대한 대포가 아니라 잠그지 않은 성문 하나였다\n",
                )

            # --- regression: 태그 기반 제외 (신고된 버그) ---
            # list 페이지(제목+본문)에는 '유용한정보'가 없고 상세 페이지의 태그에만 있다.
            # main이 하는 배선(list 카드 파싱 → 상세 페이지 태그 추출 → 제외)을
            # 네트워크 없이 그대로 재현한다. 태그 블록은 실제 article HTML
            # (html/2392daf.html: href/class/텍스트가 여러 줄에 걸친 구조)을 본떴다.
            def test_tag_based_exclusion_end_to_end(self):
                lines = card(
                    "/blog/@infoplant/19075/",
                    ["백링크 구축 전략 2026, 구글 SEO 상위 노출 위한 5가지 핵심"],
                    [
                        "2026년 현재, 검색 엔진 최적화(SEO)의 풍경은 끊임없이 진화하고 있으며…"
                    ],
                ) + card("/blog/@history/18804/", ["불교 이야기"], ["불교가 인도에서…"])
                feeds = parse_feed_list(lines)

                # 상세 페이지 HTML(태그 블록만 발췌). 제목/본문에는 '유용한정보'가 없다.
                article_html = {
                    "https://wikidocs.net/blog/@infoplant/19075/": (
                        '<div class="flex flex-wrap gap-2 my-4">\n'
                        '  <span class="px-3 py-1 rounded-full">\n'
                        '    <a href="/blog/@infoplant/?tag=4942"\n'
                        '       class="text-blue-500 dark:text-blue-400">\n'
                        "        유용한정보\n"
                        "    </a>\n"
                        "  </span>\n"
                        "</div>"
                    ),
                    "https://wikidocs.net/blog/@history/18804/": (
                        '<a href="/blog/@history/?tag=11">역사</a>'
                    ),
                }

                def get_tags_text(feed):
                    return " ".join(extract_tags(article_html[feed.link]))

                result = filter_excluded(feeds, ["유용한정보"], get_tags_text, 20)
                # 유용한정보 태그가 달린 19075만 제외되고 18804는 남는다
                self.assertEqual(
                    [f.link for f in result],
                    ["https://wikidocs.net/blog/@history/18804/"],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
