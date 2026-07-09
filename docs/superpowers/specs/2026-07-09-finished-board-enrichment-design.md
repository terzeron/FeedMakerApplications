# 완성기 게시판 연동 enrichment 설계

- 날짜: 2026-07-09
- 대상 스크립트: `naver/post_process_group_series.py` (여러 zlpla 피드가 공유하는 collection post_process)
- 관련 피드: `plamodel/zlpla.aero`(항공기), `plamodel/zlpla.afv`(AFV) 등

## 1. 배경 / 목적

`post_process_group_series.py`는 제작기 게시판에서 "같은 작성자가 같은 킷을 여러 편에
걸쳐 만든 제작기 시리즈"를 클러스터링해 출력한다. 그러나 대다수 제작자는 완성 결과물을
**제작기 게시판이 아니라 별도의 완성기 게시판**에 올린다. 제작기 게시판만 보면 시리즈의
"완성"을 알 수 없다.

목적: 제작기 시리즈에 대해, **같은 작성자가 비슷한 시기에 같은 제품으로 올린 완성기
게시물**을 완성기 게시판에서 찾아 시리즈 목록에 추가한다. 그리고 **완성기 글이 매칭될
때만 그 시리즈를 출력**한다(완성기 매칭이 곧 "완성" 근거).

## 2. 게시판 매핑 (조사 결과)

카페 ID `10503958`. 제작기/완성기는 서로 다른 menu:

| 피드                | 제작기 menu | 완성기 menu         |
| ------------------- | ----------- | ------------------- |
| zlpla.aero (항공기) | 145         | **13** (항공기완성) |
| zlpla.afv (AFV)     | 144         | **21** (AFV완성)    |

완성기 boardlist API는 검증됨:
`https://apis.naver.com/cafe-web/cafe-boardlist-api/v1/cafes/10503958/menus/{menuId}/articles?pageSize=50&sortBy=TIME&viewType=L&page={n}`

응답의 각 `result.articleList[].item`에서 사용하는 필드:
`articleId`, `writerInfo.nickName`, `subject`, `writeDateTimestamp`(참고용),
`readCount`, `likeCount`, `commentCount`, `blindArticle`, `openArticle`, `restrictMenu`.
링크 형식은 기존과 동일: `https://m.cafe.naver.com/ca-fe/web/cafes/{cafeId}/articles/{articleId}`.

## 3. 통신 방식 결정 (통신 최소화)

세 후보를 비교했다.

- **A. 회원 게시물 API** (`/members/{memberKey}/articles`): newlist에 memberKey가 없어
  별도 해석 필요 → 비효율/불가.
- **B. 작성자 검색 API** (`ta=WRITER&q=`): 실제 검색 엔드포인트가 SPA 내부 호출이라
  특정 불가(probe 전부 404), 불안정. 매 run마다 자격 작성자 수만큼(≈30~80회) 요청.
- **C. 완성기 boardlist 증분 인덱스 (채택)**: 검증된 boardlist API로 완성기 목록을
  로컬 영속 인덱스에 저장하고, 매 run에는 신규분만 상단 몇 페이지 갱신. 매칭은 전부 로컬.
  정상 상태에서 **run당 1~2 페이지**, 최초 backlog는 여러 호출에 걸쳐 점진 수집.

**결정: C.** 근거: 검증된 API만 사용, 통신량이 작성자 수와 무관하게 낮게 유지됨,
매칭이 로컬 정확 일치라 검색 API의 fuzzy/불안정성 회피.

완성기 boardlist는 글당 articleId 간격이 ~12로 촘촘. 10페이지 ≈ 6000 articleId(≈28일).
90일 매칭 창(≈18000) ≈ 30페이지, 현재 accum 전체 span(361773~407330) ≈ 76페이지.
영속 인덱스이므로 최초 1회 backlog 비용 뒤 steady-state는 run당 1~2페이지.

## 4. 설정 관리 (`finished_url_list`)

제작기가 conf.json의 `list_url_list`로 관리되듯, 완성기는 **동일 블록에 대칭 키
`finished_url_list`** 로 관리한다.

```jsonc
"configuration": {
  "collection": {
    "list_url_list": [ ".../menus/145/.../page=1", "...page=2", ... ],
    "finished_url_list": [
      "https://apis.naver.com/cafe-web/cafe-boardlist-api/v1/cafes/10503958/menus/13/articles?pageSize=50&sortBy=TIME&viewType=L&page=1"
    ],
    "post_process_script_list": [ "../../naver/post_process_group_series.py" ]
  }
}
```

- 값은 완성기 boardlist **base URL** 리스트. 스크립트가 base만 취하고 `page` 파라미터는
  스스로 덮어써 페이지네이션. 제작기처럼 50개를 나열할 필요 없이 **1줄로 충분**.
- 프레임워크(`feed_maker_util.Config.get_collection_configs`)는 화이트리스트된 키만
  읽으므로 `finished_url_list`는 **조용히 무시**(스키마 거부 없음). 스크립트가
  `feed_dir/conf.json`을 직접 `json.load` 하여 이 키를 읽는다.
- **하위 호환**: `finished_url_list`가 없으면 완성기 enrichment를 끄고 기존 동작
  (제목 기반 `REQUIRE_COMPLETION` 게이트) 유지 → 피드별 opt-in.

대안(하드코딩 매핑 `{145:13}`, 숫자만 `finished_menu_id`)은 각각 "공유 스크립트에
하드코딩", "cafeId/host 파생 필요로 불투명"이라 기각.

## 5. 상태 파일

feed_dir 아래:

- `.series_accum.tsv` — **기존 그대로.** 제작기 항목 누적. `page=1`(새 수집 시작)에 초기화.
- `.finished_index.tsv` — **신규, 영속(page=1에도 초기화하지 않음).** 완성기 인덱스.
  라인 형식: `articleId\tlink\tnickName\tsubject\tread\tlike\tcomment`.
  articleId 내림차순 유지. 공개(`openArticle && !blindArticle && !restrictMenu`) 글만 저장.

## 6. 매칭(매핑) 알고리즘

제작기 시리즈는 기존 `_cluster()` 결과 클러스터. 각 클러스터 C:

- `author`: nickName (모든 파트 공통 — 클러스터는 작성자별로 만들어짐)
- kit signature: 파트들의 `model_codes` 합집합, `nouns` 합집합
- articleId 범위: 파트 링크에서 뽑은 `[C.min, C.max]`

완성기 인덱스 항목 E가 C에 **매칭**되려면 세 조건 모두 만족:

1. **작성자**: `E.nickName == C.author` (정확히 일치)
2. **제품** (기존 클러스터링의 "코드 우선" 규칙 재사용):
   - `E.subject`의 model_code ∩ C.model_codes ≠ ∅ → 매칭, **또는**
   - C에 코드가 전혀 없을 때만: `E.subject`의 명사 ∩ C.nouns ≠ ∅ → 매칭.
   - (C에 코드가 있으면 코드로만 판정 → 오병합 차단)
3. **시기**: `C.min ≤ E.articleId ≤ C.max + FINISHED_MATCH_MARGIN`
   (`FINISHED_MATCH_MARGIN = 18000` ≈ 90일)

**충돌 처리:**

- 한 완성기 항목 E가 여러 클러스터에 매칭되면 **가장 근접한 하나**에만 귀속
  (우선순위: model_code 매칭 > 명사 매칭, 동급이면 `|E.articleId - C.max|` 최소).
  같은 완성기 글이 두 시리즈에 중복 출력되는 것을 방지.
- 한 클러스터에 완성기 항목이 여러 개 매칭되면 전부 첨부(보통 1개).

## 7. 출력 / 게이트 변경

`finished_url_list`가 설정된 경우:

- 게이트: 기존 `REQUIRE_COMPLETION`(제목에 `[완完]`)을 **"매칭 완성기 항목 ≥ 1"** 로 대체.
- 다편 시리즈(`len(c) >= MIN_SERIES_SIZE`) 중 **완성기 매칭이 있는 클러스터만** 출력.
- 출력 시 클러스터의 제작기 라인들 뒤에 매칭된 완성기 라인
  (`link\ttitle\tread\tlike\tcomment`, title은 `{nickName}: {subject}`)을 이어 붙인다.
- 그룹 구분(빈 줄) 규칙은 기존과 동일.

`finished_url_list`가 없으면: 기존 동작 그대로.

## 8. 완성기 인덱스 갱신 로직

각 post_process 호출마다:

1. `finished_url_list` 없으면 skip(기존 동작).
2. 인덱스 로드(`.finished_index.tsv`).
3. **상단 refresh**: base URL로 page=1,2,... 요청, 각 페이지 항목 중 `articleId >
index_max`인 신규만 인덱스에 추가. 신규가 0인 페이지를 만나면 중단.
4. **하단 확장**: accum의 최소 articleId(`need_min`)를 인덱스가 아직 못 덮으면
   (`index_min > need_min`) 더 오래된 페이지를 요청해 확장.
5. **run당 페이지 상한** `MAX_FETCH_PAGES_PER_CALL`(기본 3)으로 통신 폭주 방지.
   최초 backlog는 50개 제작기 페이지 처리(=50회 호출)에 걸쳐 점진적으로 채워진다.
6. 갱신된 인덱스 저장.

## 9. 에러 처리 / 엣지 케이스

- **네트워크 실패/타임아웃/JSON 오류**: 해당 페이지 fetch만 중단하고 예외를 삼킨다.
  기존 인덱스가 있으면 그것으로 매칭, 없으면 이번 호출은 매칭 0(=출력 0). **스크립트는
  절대 실패시키지 않는다.**
- **stderr 오염 금지**: 프레임워크는 서브프로세스 stderr에 "error" 문자열이 있으면
  출력 전체를 폐기한다. 네트워크 예외 메시지가 stderr로 새지 않도록 `_suppress_stderr`
  및 예외 삼킴을 적용한다. 로깅은 하지 않거나 stdout 오염 없이 조용히 처리.
- **비공개/blind 완성기 글**: 인덱스에서 제외.
- **nickName 변경/동명이인**: nickName 정확 일치로 처리(현 데이터 관례상 충분).
  오매칭 위험은 제품(코드/명사) + 시기 창으로 완화.
- HTTP: `requests.get(url, cookies=read_cookies(feed_dir), headers={UA, Referer}, timeout)`.
  `post_process_navercafe.py`의 `read_cookies` 관례를 그대로 따른다(crawler.py 서브프로세스
  미사용 — PATH/경로 취약성 회피).

## 10. 검증 계획

- **단위 테스트**(스크립트 내 `TEST` 환경변수 블록, `capture_item_navercafe.py` 패턴):
  - 완성기 API 응답 파싱(공개/blind 필터).
  - 매칭 알고리즘: 코드 매칭, 명사 매칭(코드 없을 때만), 시기 창 경계, 작성자 불일치,
    다중 클러스터 충돌 귀속.
  - 인덱스 상단 refresh / 하단 확장 / 페이지 상한(네트워크는 mock).
  - 게이트: `finished_url_list` 유무에 따른 동작 분기(하위 호환).
- **수동 통합 검증**: `zlpla.aero`에서 `page=1` 1회 실행 →
  `./post_process_group_series.py -f . '...&page=1' < newlist/YYYYMMDD.txt`
  로 완성기 라인이 붙는지, 통신 페이지 수가 상한 이내인지 확인.
- 실제 알려진 사례(예: "티벳여우벼리 아카데미과학 1/48 F4F-4 완성")로 매칭 스팟체크.

## 11. 상수 요약

- `MIN_SERIES_SIZE = 2` (기존)
- `FINISHED_MATCH_MARGIN = 18000` (≈90일, 완성기 상한 여유)
- `MAX_FETCH_PAGES_PER_CALL = 3` (호출당 완성기 페이지 상한)
- `FINISHED_INDEX_FILENAME = ".finished_index.tsv"`

## 12. 범위 밖 (YAGNI)

- 작성자 memberKey 기반 매칭(newlist에 없음, nickName으로 충분).
- 완성기 검색 API(엔드포인트 불특정·불안정).
- 인덱스의 오래된 항목 자동 trim(영속 유지, 필요 시 후속 과제).
- 다른 카페/사이트 일반화(현재 zlpla 전용 스크립트).
