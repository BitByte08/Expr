import requests
from bs4 import BeautifulSoup
from collections import Counter

def crawl_fow(champion: str):
    url = f"https://www.fow.lol/stats/{champion}"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")

    primary_runes = []
    secondary_runes = []
    shard_runes = []
    item_build = []

    for div in soup.find_all("div"):
        style = div.get("style", "")

        # -----------------------
        # 주 룬: width 116px
        # -----------------------
        if "width: 116px" in style:
            if len(primary_runes) < 4:
                imgs = div.select("img.antiBorder")
                for img in imgs:
                    tipsy_html = img.get("tipsy", "")
                    # BeautifulSoup로 HTML 파싱 후 <span> 안 텍스트 추출
                    tipsy_soup = BeautifulSoup(tipsy_html, "html.parser")
                    span = tipsy_soup.find("span")
                    if span:
                        rune_name = span.get_text(strip=True).strip("<> ")  # "집중 공격" 등
                        primary_runes.append(rune_name)
        # -----------------------
        # 부 룬: width 100px
        # -----------------------
        elif "width: 100px" in style:
            if len(secondary_runes) < 3:
                imgs = div.select("img.antiBorder")
                for img in imgs:
                    tipsy_html = img.get("tipsy", "")
                    # BeautifulSoup로 HTML 파싱 후 <span> 안 텍스트 추출
                    tipsy_soup = BeautifulSoup(tipsy_html, "html.parser")
                    span = tipsy_soup.find("span")
                    if span:
                        rune_name = span.get_text(strip=True).strip("<> ")  # "집중 공격" 등
                        secondary_runes.append(rune_name)

        # -----------------------
        # 파편: width 68px
        # -----------------------
        elif "width: 68px" in style:
            if len(shard_runes) < 2:
                imgs = div.select("img.antiBorder")
                for img in imgs:
                    tipsy_html = img.get("tipsy", "")
                    # BeautifulSoup로 HTML 파싱 후 <span> 안 텍스트 추출
                    tipsy_soup = BeautifulSoup(tipsy_html, "html.parser")
                    span = tipsy_soup.find("span")
                    if span:
                        rune_name = span.get_text(strip=True).strip("<> ")  # "집중 공격" 등
                        shard_runes.append(rune_name)


        elif "width:128px" in style:
            title_span = div.find("span", class_="summary_title")
            if title_span and "아이템 빌드" in title_span.get_text():
                imgs = div.select("div.content_full img.tipsy_live.item_icon")
                for img in imgs:
                    item_name = img.get("alt", "").strip()
                    if item_name and len(item_build) < 3:
                        item_build.append(item_name)
    skill_order = []

    # 테이블 찾기
    for table in soup.find_all("table", style=lambda s: s and "width:250px" in s):
        if len(skill_order) <= 0:
            for tr in table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 2:
                    continue
                # 두 번째 td.rskill_build_c가 실제 스킬명
                skill_name = tds[1].get_text(strip=True)
                # 레벨별 우선순위 컬럼만 선택
                priority_cells = [td for td in tds[2:] if 'rskill_build' in td.get('class', [])]
                for _ in range(len(priority_cells)):
                    skill_order.append(skill_name)
    filtered_skills = [s for s in skill_order if s != 'R']

    # 빈도 계산
    count = Counter(filtered_skills)

    # 빈도 순으로 정렬 (높은 순서부터)
    sorted_skills = [skill for skill, _ in count.most_common()]

    # 만약 Q, W, E 중 누락된 게 있으면 추가
    for s in ['Q', 'W', 'E']:
        if s not in sorted_skills:
            sorted_skills.append(s)
    skill_order = sorted_skills

    return {
        "runes": {
            "primary": primary_runes,
            "secondary": secondary_runes,
            "shard": shard_runes
        },
        "build": item_build,
        "skill_order": skill_order
    }
