"""Exercise a standalone HTML export in an offline browser context."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def exercise(page, path, original):
    page.goto(path.resolve().as_uri())
    element = lambda name: page.locator("#" + name)
    expect(element("counts")).to_have_text("4 张问答卡 · 4 道选择题")
    element("scope").select_option("1")
    expect(element("counts")).to_have_text("2 张问答卡 · 2 道选择题")
    element("start").click()
    cards = [c for c in original["cards"] if c["source"]["page"] == 2]
    for index, card in enumerate(cards):
        expect(element("question")).to_have_text(card["question"])
        expect(element("counter")).to_have_text(f"{index + 1} / 4")
        expect(element("evidence")).to_be_hidden()
        if card["kind"] == "qa":
            element("reveal").click()
            expect(element("feedback")).to_contain_text(card["answer"])
            element("missed" if index == 0 else "known").click()
        else:
            correct = card["options"].index(card["answer"])
            choice = (correct + 1) % len(card["options"]) if index == 1 else correct
            buttons = element("choices").get_by_role("button")
            buttons.nth(choice).click()
            expect(buttons.nth(choice)).to_be_disabled()
            expect(element("feedback")).to_have_text("正确答案：" + card["answer"] if index == 1 else "回答正确")
        element("citation").click()
        expect(element("citation")).to_contain_text("第 2 页")
        expect(element("quote")).to_have_text(card["source"]["quote"])
        element("next").click()
    expect(element("summary")).to_contain_text("共 4 题 · 答对或自评掌握 2 题 · 需重练 2 题")
    element("retry").click()
    for index, card in enumerate(cards[:2]):
        expect(element("counter")).to_have_text(f"{index + 1} / 2")
        expect(element("question")).to_have_text(card["question"])
        if card["kind"] == "qa":
            element("reveal").click()
            element("known").click()
        else:
            element("choices").get_by_role("button").nth(card["options"].index(card["answer"])).click()
        element("next").click()
    expect(element("summary")).to_contain_text("需重练 0 题")
    expect(element("retry")).to_be_hidden()
    element("reset").click()
    expect(element("setup")).to_be_visible()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, nargs="+")
    browser_option = parser.add_mutually_exclusive_group(required=True)
    browser_option.add_argument("--channel", choices=["chrome", "msedge"])
    browser_option.add_argument("--executable")
    args = parser.parse_args()
    fixture = Path(__file__).parent / "fixtures" / "v0.1.0-cards.json"
    original = json.loads(fixture.read_text(encoding="utf-8"))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=args.channel, executable_path=args.executable)
        context = browser.new_context(offline=True)
        page = context.new_page()
        external, errors = [], []
        page.on("request", lambda request: external.append(request.url) if request.url.startswith(("http:", "https:")) else None)
        page.on("pageerror", lambda error: errors.append(str(error)))
        for html in args.html:
            exercise(page, html, original)
        assert not errors, errors
        assert not external, external
        browser.close()
