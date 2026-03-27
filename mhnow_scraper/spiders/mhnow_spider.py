"""
Monster Hunter Now — Scrapy Spider
===================================
Scrapes all four main categories on monsterhunternow.com:
  • Monsters  https://monsterhunternow.com/en/monsters
  • Weapons   https://monsterhunternow.com/en/weapons
  • Armor     https://monsterhunternow.com/en/armor
  • Skills    https://monsterhunternow.com/en/skills

How it works
------------
The site embeds all item data as HTML-encoded JSON inside a
``<root-island component="..." props="...">`` element on each listing
page.  This data is present in the **raw HTML** (server-side rendered)
— no JavaScript execution or headless browser is required.

Each listing page embeds one root-island component:
  • SortableMonsterList  (monsters)
  • SortableWeaponList   (weapons)
  • SortableArmorList    (armor)
  • SortableSkillList    (skills)

The ``guideTranslations`` dict inside the props maps internal
translation keys (e.g. ``MONSTER_NAME_GREATJAGRAS``) to display
strings (e.g. ``"Great Jagras"``), allowing the spider to resolve
all human-readable names without visiting detail pages.

Adding new categories
---------------------
1.  Add the listing URL to LISTING_PAGES (url → category, component, data_key).
2.  Add a ``_parse_<category>`` method below.
3.  Re-run: scrapy crawl mhnow
"""

import json
import re
from html import unescape

import scrapy

from mhnow_scraper.items import MhnowItem


# ---------------------------------------------------------------------------
# Listing page configuration
# url → (category_label, root-island component name, props data key)
# ---------------------------------------------------------------------------
LISTING_PAGES: dict[str, tuple[str, str, str]] = {
    "https://monsterhunternow.com/en/monsters": (
      "monsters",
      "SortableMonsterList",
      "monsters"
    ),
    "https://monsterhunternow.com/en/weapons": (
      "weapons",
      "SortableWeaponList",
      "weapons"
    ),
    "https://monsterhunternow.com/en/armor": (
      "armor",
      "SortableArmorList",
      "armor"
    ),
    "https://monsterhunternow.com/en/skills": (
      "skills",
      "SortableSkillList",
      "skills"
    ),
}

# Pre-compiled regex to extract the props attribute from a root-island element.
# The props value is HTML-entity-encoded JSON (e.g. &quot; → ").
_ISLAND_RE = re.compile(
    r'<root-island\b[^>]*component="([^"]+)"[^>]*props="([^"]+)"',
    re.DOTALL,
)


class MhnowSpider(scrapy.Spider):
    name = "mhnow"
    allowed_domains = ["monsterhunternow.com"]
    start_urls = list(LISTING_PAGES.keys())

    # ------------------------------------------------------------------ #
    #  Entry point                                                         #
    # ------------------------------------------------------------------ #
    def parse(self, response):
        """
        Route each listing page to the correct category parser.

        Extracts the root-island ``props`` JSON from the raw HTML and
        resolves human-readable names via the embedded ``guideTranslations``
        dictionary.
        """
        config = LISTING_PAGES.get(response.url)
        if not config:
            self.logger.warning("Unrecognised URL: %s", response.url)
            return

        category, component_name, data_key = config
        self.logger.info("Parsing %s listing (%s)", category, response.url)

        # Locate the root-island element for this component.
        props = self._extract_island_props(response.text, component_name)
        if props is None:
            self.logger.error(
                "Could not find root-island[component=%s] on %s",
                component_name,
                response.url,
            )
            return

        guide: dict = props.get("guideTranslations", {})
        data = props.get(data_key, [] if category == "monsters" else {})

        if category == "monsters":
            # data is a list of monster dicts
            for monster in data:
                yield self._parse_monster(monster, guide)

        elif category == "weapons":
            # data is a dict keyed by weapon ID
            for weapon in data.values():
                yield self._parse_weapon(weapon, guide)

        elif category == "armor":
            # data is a dict keyed by armor ID
            for armor in data.values():
                yield self._parse_armor(armor, guide)

        elif category == "skills":
            # data is a dict keyed by skill kind
            for skill in data.values():
                yield self._parse_skill(skill, guide)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_island_props(html: str, component_name: str) -> dict | None:
        """
        Find the first
        ``<root-island component="<component_name>" props="...">``
        element and return its decoded props as a dict, or None if not found.
        """
        for comp, props_raw in _ISLAND_RE.findall(html):
            if comp == component_name:
                try:
                    return json.loads(unescape(props_raw))
                except json.JSONDecodeError:
                    return None
        return None

    def _t(self, guide: dict, key: str, fallback: str | None = None) -> str:
        """
        Resolve a translation key to its display string.

        Falls back to ``fallback`` if given, otherwise to ``key`` itself,
        so the raw key always surfaces in the output rather than being lost.
        """
        return guide.get(key, fallback if fallback is not None else key)

    def _translate_list(self, guide: dict, keys: list) -> list[str]:
        return [self._t(guide, k) for k in keys]

    # ------------------------------------------------------------------ #
    #  Per-category item builders                                          #
    # ------------------------------------------------------------------ #
    def _parse_monster(self, data: dict, guide: dict) -> MhnowItem:
        """
        Build a MhnowItem from a single monster entry in SortableMonsterList.
        """
        mid = data.get("id", "")
        name_key = "MONSTER_NAME_" + mid.upper()

        item = MhnowItem()
        item["category"] = "monsters"
        item["name"] = self._t(guide, name_key, mid)
        # Monster descriptions are available on detail pages but not on the
        # listing page. Set to empty string; follow-up visits could fill it.
        item["description"] = ""
        item["weaknesses"] = self._translate_list(
            guide,
            data.get("weakness", [])
        )
        item["stats"] = [
            {
                "label": "species",
                "value": data.get("species", "")
            },
            {
                "label": "element",
                "value": ", ".join(data.get("element", []) or ["None"])
            },
            {
                "label": "min_grade",
                "value": str(data.get("minGrade", ""))
            },
        ]
        # Material images double as item imagery
        item["image_urls"] = [
            m["imageUrl"]
            for m in data.get("itemData", [])
            if m.get("imageUrl")
        ]
        item["extra_fields"] = {
            "id": mid,
            "habitat": self._translate_list(guide, data.get("habitat", [])),
            "breakable_parts": [p["name"] for p in data.get(
                                                    "breakableParts", []
                                                )],
            "drift_parts": data.get("driftParts", []),
            "materials": [
                {
                    "name": self._t(
                        guide, d.get("name", ""),
                        d.get("name", "")
                    ),
                    "rarity": d.get("itemRarity", 0),
                    "min_grade": d.get("minGrade", 0),
                    "imageUrl": d.get("imageUrl", ""),
                }
                for d in data.get("itemData", [])
            ],
        }
        item["source_url"] = f"https://monsterhunternow.com/en/monsters/{mid}"
        return item

    def _parse_weapon(self, data: dict, guide: dict) -> MhnowItem:
        """
        Build a MhnowItem from a single weapon entry in SortableWeaponList.

        Each weapon has multiple ``grades`` (upgrade tiers), each with
        ``levels`` (max-level breakdowns of attack/element/affinity stats).
        The highest-grade name is used as the item display name.
        """
        grades = data.get("grades", [])
        last_grade = grades[-1] if grades else {}
        name_key = last_grade.get("name", data.get("id", ""))

        item = MhnowItem()
        item["category"] = "weapons"
        item["name"] = self._t(guide, name_key, name_key)
        item["description"] = ""
        item["weaknesses"] = []
        item["stats"] = [
            {
                "label": "weapon_type",
                "value": self._t(
                    guide,
                    data.get("category", ""),
                    data.get("category", "")
                )
            },
            {
                "label": "element",
                "value": self._t(
                    guide,
                    data.get("element", "None"),
                    data.get("element", "None")
                )
            },
            {
                "label": "series",
                "value": self._t(
                    guide,
                    data.get("series", ""),
                    data.get("series", "")
                )
            },
        ]
        item["image_urls"] = list({
            g["imageUrl"] for g in grades if g.get("imageUrl")
        })
        item["extra_fields"] = {
            "id": data.get("id", ""),
            "grades": [
                {
                    "grade":        g.get("grade"),
                    "name":         self._t(
                                        guide,
                                        g.get("name", ""),
                                        g.get("name", "")
                                    ),
                    "skills":       g.get("skills", []),
                    "special_skill": g.get("specialSkill", {}),
                    "levels":       g.get("levels", []),
                }
                for g in grades
            ],
        }
        wid = data.get("id", "").lower()
        item["source_url"] = f"https://monsterhunternow.com/en/weapons/{wid}"
        return item

    def _parse_armor(self, data: dict, guide: dict) -> MhnowItem:
        """
        Build a MhnowItem from a single armor-piece entry in SortableArmorList.

        Each armor piece has multiple ``grades``, each with a ``defense``
        array (one value per upgrade level within the grade) and associated
        ``skills``.
        """
        grades = data.get("grades", [])
        first_grade = grades[0] if grades else {}
        name_key = first_grade.get("name", data.get("id", ""))

        item = MhnowItem()
        item["category"] = "armor"
        item["name"] = self._t(guide, name_key, name_key)
        item["description"] = ""
        item["weaknesses"] = []
        item["stats"] = [
            {"label": "part",   "value": data.get("category", "")},
            {"label": "series", "value": self._t(
                guide,
                data.get("series", ""),
                data.get("series", "")
            )},
        ]
        item["image_urls"] = []
        item["extra_fields"] = {
            "id": data.get("id", ""),
            "grades": [
                {
                    "grade": g.get("grade"),
                    "name": self._t(
                        guide,
                        g.get("name", ""),
                        g.get("name", "")
                    ),
                    "defense_levels":  g.get("defense", []),
                    "driftsmelt_slots": g.get("driftsmeltSlots", 0),
                    "skills": [
                        {"kind": s["kind"], "level": s["level"]}
                        for s in g.get("skills", [])
                    ],
                }
                for g in grades
            ],
        }
        aid = data.get("id", "").lower()
        item["source_url"] = f"https://monsterhunternow.com/en/armor/{aid}"
        return item

    def _parse_skill(self, data: dict, guide: dict) -> MhnowItem:
        """
        Build a MhnowItem from a single skill entry in SortableSkillList.

        Each skill has per-level descriptions stored as translation keys
        in ``guideTranslations``, so the full description text is always
        resolvable without visiting the detail page.
        """
        kind = data.get("kind", "")
        name_key = data.get("name", kind)  # e.g. "SKILL_NAME_75" or the kind

        # Resolve the display name: try the name key first, then fall back
        # to the kind key (which is often also a translation key).
        display_name = guide.get(name_key) or guide.get(kind) or name_key

        # Resolve per-level descriptions
        levels_data = []
        for lv in data.get("levels", []):
            desc_key = lv.get("description", "")
            levels_data.append({
                "level":       lv["level"],
                "description": self._t(guide, desc_key, desc_key),
                "effect":      lv.get("effectAmount", []),
                "condition":   lv.get("conditionAmount", []),
            })

        item = MhnowItem()
        item["category"] = "skills"
        item["name"] = display_name
        # Use Level 1 description as the primary description field
        item["description"] = (
            levels_data[0]["description"] if levels_data else ""
        )
        item["weaknesses"] = []
        item["stats"] = [
            {"label": "skill_category", "value": self._t(
                guide, data.get("category", ""), data.get("category", "")
            )},
            {"label": "max_level", "value": str(data.get("maxLevel", ""))},
        ]
        item["image_urls"] = []
        item["extra_fields"] = {
            "id":       kind,
            "skill_id": data.get("skillId", ""),
            "levels":   levels_data,
        }
        sid = kind.lower()
        item["source_url"] = f"https://monsterhunternow.com/en/skills/{sid}"
        return item
