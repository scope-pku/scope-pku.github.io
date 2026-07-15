#!/usr/bin/env python3
"""Rebuild the English Hugo content from the immutable VSB HTML snapshot."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import urllib.request
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/xulm.pku.edu.cn"
SITE = ROOT / "site"
CONTENT = SITE / "content/en"
DATA = SITE / "data"
MEDIA = SITE / "static/media"
BASE_URL = "https://xulm.pku.edu.cn/"
MANIFEST_FILE = DATA / "migration-assets.json"

MEDIA.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

if MANIFEST_FILE.exists():
    ASSETS = json.loads(MANIFEST_FILE.read_text())
else:
    ASSETS = {}


def soup_for(relative_path: str) -> BeautifulSoup:
    return BeautifulSoup((SOURCE / relative_path).read_text(), "html.parser")


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u200b", "")).strip()


def copyedit(value: str) -> str:
    """Correct traceable source defects without changing scientific meaning."""
    replacements = {
        "Our researches include": "Our research includes",
        "Interficial": "Interfacial",
        "non-equilibruim": "non-equilibrium",
        "prior their deformation": "prior to deformation",
        "published on": "published in",
        "published by": "published in",
        "Nature Science Review": "National Science Review",
        " ptransitions": " transitions",
        "thesis:Structures": "thesis: Structures",
        "thesis:Thermodynamic": "thesis: Thermodynamic",
        "thesis:Phase": "thesis: Phase",
    }
    for source, replacement in replacements.items():
        value = value.replace(source, replacement)
    return value


def request_bytes(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "XuGroupMigration/1.0"})
    error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), response.headers.get_content_type()
        except Exception as exc:  # pragma: no cover - network recovery
            error = exc
            time.sleep(attempt + 1)
    raise RuntimeError(f"Failed to download {url}: {error}")


def absolute_url(url: str) -> str:
    return urljoin(BASE_URL, url)


def image_extension(url: str, content_type: str) -> str:
    query_extension = parse_qs(urlparse(url).query).get("e", [""])[0].lower()
    if query_extension in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if query_extension == ".jpeg" else query_extension
    return {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(content_type, ".jpg")


def download_image(url: str, stem: str, *, force_jpeg: bool = False) -> str:
    source_url = absolute_url(url)
    existing = ASSETS.get(source_url)
    if existing and (SITE / "static" / existing["path"].lstrip("/")).exists():
        return existing["path"]
    existing_files = list(MEDIA.glob(f"{stem}.*"))
    if len(existing_files) == 1:
        destination = existing_files[0]
        local_path = f"/media/{destination.name}"
        ASSETS[source_url] = {
            "path": local_path,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        }
        return local_path

    payload, content_type = request_bytes(source_url)
    extension = ".jpg" if force_jpeg else image_extension(source_url, content_type)
    destination = MEDIA / f"{stem}{extension}"
    image = ImageOps.exif_transpose(Image.open(BytesIO(payload)))
    image.thumbnail((1800, 1400), Image.Resampling.LANCZOS)
    if extension == ".jpg":
        if image.mode not in {"RGB", "L"}:
            background = Image.new("RGB", image.size, "white")
            if image.mode == "RGBA":
                background.paste(image, mask=image.getchannel("A"))
            else:
                background.paste(image.convert("RGB"))
            image = background
        image.save(destination, "JPEG", quality=84, optimize=True, progressive=True)
    elif extension == ".png":
        image.save(destination, "PNG", optimize=True)
    else:
        image.save(destination)

    local_path = f"/media/{destination.name}"
    ASSETS[source_url] = {
        "path": local_path,
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }
    return local_path


def download_file(url: str, filename: str) -> str:
    source_url = absolute_url(url)
    destination = MEDIA / filename
    if not destination.exists():
        payload, _ = request_bytes(source_url)
        destination.write_bytes(payload)
    local_path = f"/media/{filename}"
    ASSETS[source_url] = {
        "path": local_path,
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }
    return local_path


def largest_content(soup: BeautifulSoup):
    candidates = soup.find_all(id=re.compile(r"^vsb_content(?:_|$)"))
    if not candidates:
        raise ValueError("No VSB content wrapper found")
    return max(candidates, key=lambda node: len(clean_text(node.get_text(" ", strip=True))))


def prepare_fragment(node, asset_prefix: str | None = None):
    fragment = BeautifulSoup(str(node), "html.parser")
    for unwanted in fragment.select("script, style, link"):
        unwanted.decompose()
    for icon in fragment.select('img[src*="fileTypeImages/icon_pdf"]'):
        icon.decompose()
    for paragraph in fragment.find_all("p"):
        if not clean_text(paragraph.get_text(" ")) and not paragraph.find("img"):
            paragraph.decompose()
    for wrapper in fragment.find_all(["div", "span", "font", "big", "small", "sup", "sub", "xie", "xieti"]):
        wrapper.unwrap()

    image_number = 0
    for image in fragment.find_all("img"):
        source_url = image.get("src", "")
        if not source_url:
            image.decompose()
            continue
        if source_url.startswith("/") and asset_prefix:
            image_number += 1
            image["src"] = download_image(source_url, f"{asset_prefix}-{image_number:02d}")
        image["alt"] = image.get("alt") or ""
        image.attrs = {key: value for key, value in image.attrs.items() if key in {"src", "alt"}}

    for anchor in fragment.find_all("a"):
        href = anchor.get("href", "")
        if href.startswith("/"):
            anchor["href"] = absolute_url(href)
        anchor.attrs = {"href": anchor.get("href", "")}
    for tag in fragment.find_all(True):
        if tag.name not in {"a", "img"}:
            tag.attrs = {}
    return fragment


def to_markdown(node, asset_prefix: str | None = None, *, strip_emphasis: bool = False) -> str:
    fragment = prepare_fragment(node, asset_prefix)
    result = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm", "--wrap=none"],
        input=str(fragment),
        text=True,
        check=True,
        capture_output=True,
    ).stdout
    result = re.sub(r"(?m)^-\s+#{1,6}\s*\n\n\s{2}(\S)", r"- \1", result)
    result = re.sub(r"(?m)^[ \t]*(?:-\s+)?#{1,6}[ \t]*$", "", result)
    result = re.sub(r"(?m)\\[ \t]*$", "", result)
    result = re.sub(r"(?m)[ \t]+$", "", result)
    if strip_emphasis:
        result = re.sub(r"(?<!\\)\*+", "", result)
    return re.sub(r"\n{3,}", "\n\n", result).strip()


def front_matter(
    title: str,
    translation_key: str,
    *,
    aliases: list[str] | None = None,
    summary: str | None = None,
    weight: int | None = None,
    layout: str | None = None,
    gallery: str | None = None,
) -> str:
    lines = ["---", f"title: {json.dumps(title, ensure_ascii=False)}", f"translationKey: {translation_key}"]
    if summary:
        lines.append(f"summary: {json.dumps(summary, ensure_ascii=False)}")
    if weight is not None:
        lines.append(f"weight: {weight}")
    if layout:
        lines.append(f"layout: {layout}")
    if gallery:
        lines.append(f"gallery: {gallery}")
    if aliases:
        lines.append("aliases:")
        lines.extend(f"  - {json.dumps(alias)}" for alias in aliases)
    lines.extend(["---", ""])
    return "\n".join(lines)


def write_page(relative_path: str, body: str, **metadata) -> None:
    destination = CONTENT / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text((front_matter(**metadata) + body.strip()).rstrip() + "\n")


def migrate_home() -> None:
    home = soup_for("index.htm")
    hero_source = home.select_one("#flashBoxu_u3_ img")["src"]
    hero = download_image(hero_source, "home-group-photo", force_jpeg=True)
    body = (
        "We are a computational research group in soft condensed matter physics and computational physics. "
        "Our group focuses on investigating the behavior of matter at the nanoscale, utilizing state-of-the-art "
        "computational tools and techniques.\n\n"
        "## Research interests\n\n"
        "- **Water science:** Structure and phase transition of water, water under nano confinement, and water at two-dimensional interfaces.\n"
        "- **Theoretical and computational physics:** Phase transitions and supercritical phenomena.\n"
        "- **Non-equilibrium statistical physics:** Dynamic and thermodynamic processes of glass transition and crystallization.\n"
    )
    write_page(
        "_index.md",
        body,
        title="Xu Research Group",
        translation_key="home",
        aliases=["/index.htm"],
    )
    (DATA / "home.json").write_text(json.dumps({"hero": hero}, indent=2))


def migrate_research_and_contact() -> None:
    research = largest_content(soup_for("Research.htm"))
    headings = {
        "Research Fields": None,
        "Phase transition and critical phenomena in complex substances": "h2",
        "Interficial water structure and dynamics": "h2",
        "Amorphous solids and non-equilibruim phase transitions": "h2",
        "References:": "h3",
    }
    for paragraph in list(research.find_all("p")):
        text = clean_text(paragraph.get_text(" "))
        if text not in headings:
            continue
        replacement = headings[text]
        if replacement is None:
            paragraph.decompose()
        else:
            new_tag = research.new_tag(replacement)
            new_tag.string = text
            paragraph.replace_with(new_tag)
    write_page(
        "research/_index.md",
        copyedit(to_markdown(research, "research")),
        title="Research",
        translation_key="research",
        aliases=["/Research.htm"],
    )

    contact = (
        "Limei Xu\n\n"
        "**Address:** School of Physics, Peking University, No. 209 Chengfu Road, "
        "Haidian District, Beijing, China, 100871\n\n"
        "**Office:** Room 537, West Building, School of Physics, Peking University\n\n"
        "**Telephone:** +86 10-6275-5043\n\n"
        "**Email:** [limei.xu@pku.edu.cn](mailto:limei.xu@pku.edu.cn)\n\n"
        "**Personal page:** [Peking University faculty profile]"
        "(https://faculty.pku.edu.cn/xulm/zh_CN/index.htm) (Chinese)\n\n"
        "---\n\n"
        "Students\n\n"
        "**Student offices:** Rooms 525 and 527, West Building, School of Physics, Peking University\n"
    )
    write_page(
        "contact/_index.md",
        contact,
        title="Contact",
        translation_key="contact",
        aliases=["/Contact_Us.htm"],
    )


def migrate_people() -> None:
    soup = soup_for("People.htm")
    cv_path = download_file("/pdf/LimeiXu_CV.pdf", "limei-xu-cv.pdf")
    categories: list[dict] = []
    category_lookup: dict[str, list] = {}

    leader_image = download_image(soup.select_one(".Leaderp1 img")["src"], "people-limei-xu")
    leader = {
        "name": "Limei Xu 徐莉梅",
        "role": "Boya Distinguished Professor, Peking University",
        "details": ["International Center for Quantum Materials (ICQM), School of Physics, Peking University, Beijing, China"],
        "telephone": "+86 10-6275-5043",
        "email": "limei.xu@pku.edu.cn",
        "profile": "/people/limei-xu/",
        "personal_page": "https://faculty.pku.edu.cn/xulm/zh_CN/index.htm",
        "cv": cv_path,
        "image": leader_image,
        "status": "current",
    }
    categories.append({"name": "Group Leader", "people": [leader]})

    current_category = None
    record_number = 0
    for node in soup.find_all("div"):
        classes = node.get("class", [])
        if "Leader" in classes:
            if "display:none" not in node.get("style", "").replace(" ", ""):
                current_category = clean_text(node.get_text(" "))
                if current_category != "Group Leader" and current_category not in category_lookup:
                    people: list[dict] = []
                    category_lookup[current_category] = people
                    categories.append({"name": current_category, "people": people})
        elif "postdoctor2" in classes and current_category:
            record_number += 1
            name_tag = node.find("peoplespan2")
            if not name_tag:
                continue
            paragraphs = [clean_text(p.get_text(" ")) for p in node.find_all("p", recursive=False)]
            paragraphs = [text for text in paragraphs if text]
            email = ""
            interest = ""
            details = []
            for paragraph in paragraphs:
                if re.match(r"E-?mail:", paragraph, re.I):
                    email = paragraph.split(":", 1)[1].strip()
                elif paragraph.startswith("Research Interest:"):
                    interest = paragraph.split(":", 1)[1].strip()
                else:
                    details.append(paragraph)
            image_node = node.find_previous("div", class_="postdoctor1").find("img")
            person = {
                "name": clean_text(name_tag.get_text(" ")),
                "details": details,
                "email": email,
                "research_interest": interest,
                "image": download_image(image_node["src"], f"people-{record_number:02d}"),
                "status": "alumni" if current_category == "Alumni" else "current",
            }
            category_lookup[current_category].append(person)

    if record_number != 28:
        raise AssertionError(f"Expected 28 non-leader people, found {record_number}")
    (DATA / "people.json").write_text(json.dumps({"categories": categories}, ensure_ascii=False, indent=2))
    write_page(
        "people/_index.md",
        "Current members and alumni of the Xu Research Group.\n",
        title="People",
        translation_key="people",
        aliases=["/People.htm"],
    )
    profile_body = (
        "Boya Distinguished Professor, Peking University\n\n"
        "International Center for Quantum Materials (ICQM), School of Physics, Peking University\n\n"
        "**Address:** School of Physics, Peking University, No. 209 Chengfu Road, Haidian District, Beijing, China, 100871\n\n"
        "**Office:** Room 537, West Building, School of Physics, Peking University\n\n"
        "**Telephone:** +86 10-6275-5043\n\n"
        "**Email:** [limei.xu@pku.edu.cn](mailto:limei.xu@pku.edu.cn)\n\n"
        "**Personal page:** [Peking University faculty profile](https://faculty.pku.edu.cn/xulm/zh_CN/index.htm) (Chinese)\n\n"
        f"**Curriculum vitae:** [Download PDF]({cv_path})\n"
    )
    write_page(
        "people/limei-xu.md",
        profile_body,
        title="Limei Xu 徐莉梅",
        translation_key="limei-xu",
        aliases=["/info/1011/1012.htm"],
    )


def deduplicate_list_items(node) -> None:
    seen = set()
    for item in list(node.find_all("li")):
        text = clean_text(item.get_text(" "))
        if text in seen:
            item.decompose()
        else:
            seen.add(text)


def migrate_news() -> None:
    breaking = largest_content(soup_for("News/Breaking_News.htm"))
    all_news = largest_content(soup_for("News/All_News_and_Events.htm"))
    recent = []
    for item in breaking.find_all("li")[:8]:
        link = item.find("a", href=True)
        text = clean_text(item.get_text(" "))
        match = re.match(r"(\d{4}\.\d{2})\s*(.*)", text)
        recent.append({
            "date": match.group(1) if match else "",
            "text": copyedit(match.group(2) if match else text),
            "url": link["href"] if link else "",
        })
    (DATA / "recent_news.json").write_text(json.dumps(recent, ensure_ascii=False, indent=2))
    write_page(
        "news/_index.md",
        copyedit(to_markdown(breaking, strip_emphasis=True)),
        title="News",
        translation_key="news",
        aliases=["/News/Breaking_News.htm"],
    )
    deduplicate_list_items(all_news)
    write_page(
        "news/all-news.md",
        copyedit(to_markdown(all_news, strip_emphasis=True)),
        title="All News and Events",
        translation_key="all-news",
        aliases=["/News/All_News_and_Events.htm"],
        summary="Complete archive of group publications, events, awards, and member news.",
        weight=10,
    )


def migrate_publications() -> None:
    write_page(
        "publications/_index.md",
        "Research highlights, the complete publication list, and student theses.\n",
        title="Publications",
        translation_key="publications",
    )

    soup = soup_for("Publications/Highlights.htm")
    records = []
    markdown_records = []
    for index, block in enumerate(soup.select("div.jieshaoyou1"), start=1):
        title_tag = block.find("biaoti")
        content_nodes = block.find_all(id="vsb_content")
        if not title_tag or not content_nodes:
            continue
        title = clean_text(title_tag.get_text(" "))
        image_wrapper = block.find_previous_sibling("div", class_="tupianzuo1") or block.find_previous("div", class_="tupianzuo1")
        image = download_image(image_wrapper.find("img")["src"], f"highlight-{index:02d}")
        content = max(content_nodes, key=lambda node: len(clean_text(node.get_text(" "))))
        body = to_markdown(content, strip_emphasis=True)
        links = [anchor["href"] for anchor in content.find_all("a", href=True)]
        external = next((url for url in links if not url.startswith("/system/")), "")
        records.append({
            "title": title,
            "image": image,
            "url": external,
            "summary": clean_text(content.get_text(" "))[:240].rstrip() + "…",
        })
        markdown_records.append(f"## {title}\n\n![{title}]({image})\n\n{body}")
    if len(records) != 15:
        raise AssertionError(f"Expected 15 highlights, found {len(records)}")
    (DATA / "highlights.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
    write_page(
        "publications/highlights.md",
        "\n\n".join(markdown_records),
        title="Research Highlights",
        translation_key="highlights",
        aliases=["/Publications/Highlights.htm"],
        summary="Selected research highlights from the Xu Research Group.",
        weight=10,
    )

    full_list = largest_content(soup_for("Publications/Full_List.htm"))
    write_page(
        "publications/full-list.md",
        to_markdown(full_list, strip_emphasis=True),
        title="Full Publication List",
        translation_key="full-publication-list",
        aliases=["/Publications/Full_List.htm"],
        summary="Complete publication list from 2005 to 2026.",
        weight=20,
    )

    theses = largest_content(soup_for("Publications/Theses.htm"))
    write_page(
        "publications/theses.md",
        copyedit(to_markdown(theses, strip_emphasis=True)),
        title="Theses",
        translation_key="theses",
        aliases=["/Publications/Theses.htm"],
        summary="Doctoral and student theses supervised in the group.",
        weight=30,
    )


def migrate_teaching() -> None:
    pages = {
        "2022": "Teaching/a2022.htm",
        "2021": "Teaching/a2021.htm",
        "2020": "Teaching/a2020.htm",
        "2019": "Teaching/a2019.htm",
    }
    current = largest_content(soup_for("Teaching.htm"))
    for heading in current.find_all("h1"):
        heading.name = "h2"
    write_page(
        "teaching/_index.md",
        to_markdown(current),
        title="Teaching",
        translation_key="teaching",
        aliases=["/Teaching.htm"],
    )
    for weight, (year, source) in enumerate(pages.items(), start=1):
        content = largest_content(soup_for(source))
        for heading in content.find_all("h1"):
            heading.name = "h2"
        write_page(
            f"teaching/{year}.md",
            to_markdown(content),
            title=year,
            translation_key=f"teaching-{year}",
            aliases=[f"/Teaching/a{year}.htm"],
            summary=f"Courses taught in {year}.",
            weight=weight * 10,
        )


def migrate_photos() -> None:
    galleries = [
        ("group-members", "Group Members", "Photos/Group_Members.htm", "/Photos/Group_Members.htm"),
        ("meetings", "Meetings", "Photos/Meetings.htm", "/Photos/Meetings.htm"),
        ("have-fun", "Have Fun", "Photos/Have_Fun.htm", "/Photos/Have_Fun.htm"),
        ("dine-together", "Dine Together", "Photos/Dine_Toghter.htm", "/Photos/Dine_Toghter.htm"),
        ("graduation", "Graduation", "Photos/Graduation.htm", "/Photos/Graduation.htm"),
    ]
    expected = {"group-members": 3, "meetings": 2, "have-fun": 3, "dine-together": 1, "graduation": 4}
    alt_text = {
        "group-members": "Xu Research Group members",
        "meetings": "Xu Research Group meeting",
        "have-fun": "Xu Research Group activity",
        "dine-together": "Xu Research Group dining together",
        "graduation": "Xu Research Group graduation",
    }
    photo_data = {}
    write_page(
        "photos/_index.md",
        "Group portraits, meetings, graduations, and group activities.\n",
        title="Photos",
        translation_key="photos",
    )
    for weight, (key, title, source, alias) in enumerate(galleries, start=1):
        content = largest_content(soup_for(source))
        images = []
        for index, image in enumerate(content.select('img[src^="/virtual_attach_file.vsb"]'), start=1):
            images.append({
                "src": download_image(image["src"], f"photos-{key}-{index:02d}"),
                "alt": f"{alt_text[key]}, photo {index}",
            })
        if len(images) != expected[key]:
            raise AssertionError(f"Expected {expected[key]} images in {key}, found {len(images)}")
        photo_data[key] = {"title": title, "images": images}
        write_page(
            f"photos/{key}.md",
            "",
            title=title,
            translation_key=f"photos-{key}",
            aliases=[alias],
            summary=f"{title} photo gallery.",
            layout="gallery",
            gallery=key,
            weight=weight * 10,
        )
    (DATA / "photos.json").write_text(json.dumps(photo_data, ensure_ascii=False, indent=2))


def verify() -> None:
    people = json.loads((DATA / "people.json").read_text())
    people_count = sum(len(category["people"]) for category in people["categories"])
    if people_count != 29:
        raise AssertionError(f"Expected 29 people including leader, found {people_count}")
    if len(json.loads((DATA / "highlights.json").read_text())) != 15:
        raise AssertionError("Highlight count mismatch")
    if sum(len(gallery["images"]) for gallery in json.loads((DATA / "photos.json").read_text()).values()) != 13:
        raise AssertionError("Photo count mismatch")
    missing = [entry["path"] for entry in ASSETS.values() if not (SITE / "static" / entry["path"].lstrip("/")).exists()]
    if missing:
        raise AssertionError(f"Missing migrated assets: {missing}")


def main() -> None:
    migrate_home()
    migrate_research_and_contact()
    migrate_people()
    migrate_news()
    migrate_publications()
    migrate_teaching()
    migrate_photos()
    MANIFEST_FILE.write_text(json.dumps(ASSETS, ensure_ascii=False, indent=2, sort_keys=True))
    verify()
    print(f"Migrated English content with {len(ASSETS)} local assets")


if __name__ == "__main__":
    main()
