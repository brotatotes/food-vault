#!/usr/bin/env python3
"""Check Food Vault navigation and capture bounded desktop/mobile evidence."""
import argparse
import json
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright


def check_site(base_url, output_dir, slugs):
    output_dir.mkdir(parents=True, exist_ok=True)
    base = base_url.rstrip('/')
    report = {'baseUrl': base, 'devices': [], 'errors': []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for device, viewport in [('desktop', {'width': 1280, 'height': 900}), ('mobile', {'width': 393, 'height': 852})]:
            page = browser.new_page(viewport=viewport, device_scale_factor=1)
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(base, wait_until='networkidle')
            page.locator('#recipe-grid .card').first.wait_for(state='visible')
            assert page.locator('#recipes').is_visible()
            assert page.locator('#healthy-takeouts').is_hidden()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Homepage horizontal overflow'
            assert 'sans-serif' not in page.locator('body').evaluate('(el) => getComputedStyle(el).fontFamily')
            page.screenshot(path=str(output_dir / f'home-{device}.png'))
            all_cards = page.locator('#recipe-grid .card').count()
            page.locator('#search').fill('unlikely-no-match-987654321')
            assert page.locator('#empty').is_visible()
            assert page.locator('#recipe-grid .card').count() == 0
            page.locator('#search').fill('')
            assert page.locator('#recipe-grid .card').count() == all_cards
            expected_links = page.request.get(f'{base}/data/recipe-links.json').json()
            assert page.locator('.saved-link').count() == len(expected_links)
            if expected_links:
                assert page.locator('.saved-links').is_visible()
                page.locator('.saved-links').scroll_into_view_if_needed()
                page.locator('.saved-links').screenshot(path=str(output_dir / f'saved-links-{device}.png'))
            else:
                assert page.locator('.saved-links').is_hidden()
            for link in page.locator('.saved-link a').all():
                assert link.get_attribute('href').startswith('https://')
            page.locator('.section-nav a[data-section="healthy-takeouts"]').click()
            page.locator('#healthy-takeouts').wait_for(state='visible')
            page.locator('.takeout-card').first.wait_for(state='visible')
            assert page.locator('#recipes').is_hidden()
            assert page.locator('.takeout-card').count() == 7
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Takeout horizontal overflow'
            page.locator('#takeout-title').scroll_into_view_if_needed()
            page.screenshot(path=str(output_dir / f'takeouts-{device}.png'))
            for card in page.locator('.takeout-card').all():
                slug = card.get_attribute('data-takeout')
                card.scroll_into_view_if_needed()
                assert card.locator('a').get_attribute('href').startswith('https://')
                card.screenshot(path=str(output_dir / f'takeout-{slug}-{device}.png'))
            page.reload(wait_until='networkidle')
            assert page.locator('#healthy-takeouts').is_visible(), 'Takeout deep link reload'
            page.locator('.section-nav a[data-section="recipes"]').click()
            assert page.locator('#recipes').is_visible()
            page.go_back(wait_until='networkidle')
            assert page.locator('#healthy-takeouts').is_visible(), 'Browser back'
            page.go_forward(wait_until='networkidle')
            assert page.locator('#recipes').is_visible(), 'Browser forward'
            for slug in slugs:
                card = page.locator(f'.card[data-slug="{slug}"]')
                card.scroll_into_view_if_needed()
                page.wait_for_function('(slug) => { const i = document.querySelector(`.card[data-slug="${slug}"] img`); return i.complete && i.naturalWidth > 0; }', arg=slug)
                card.screenshot(path=str(output_dir / f'{slug}-card-{device}.png'))
                card.click()
                assert page.locator('#recipe-dialog').is_visible()
                page.locator('.close').click()
                assert page.locator('#recipe-dialog').is_hidden()
                detail = browser.new_page(viewport=viewport, device_scale_factor=1)
                detail.on('pageerror', lambda error: report['errors'].append(str(error)))
                detail.goto(f'{base}/recipes/{quote(slug)}/', wait_until='networkidle')
                detail.locator('#recipe-dialog[open]').wait_for(state='visible')
                assert detail.locator('#recipe-detail h2').inner_text()
                assert detail.locator('.detail-content li').count() > 0
                assert detail.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert detail.locator('#recipe-dialog').evaluate('(el) => el.scrollWidth <= el.clientWidth'), 'Detail horizontal overflow'
                detail.screenshot(path=str(output_dir / f'{slug}-detail-{device}.png'))
                close_box = detail.locator('.dialog-toolbar').bounding_box()
                body_box = detail.locator('#recipe-detail').bounding_box()
                assert close_box['y'] + close_box['height'] <= body_box['y'] + 1, 'Close toolbar overlaps recipe body'
                detail.locator('.detail-content .source-link').first.scroll_into_view_if_needed()
                detail.screenshot(path=str(output_dir / f'{slug}-detail-source-{device}.png'))
                detail.locator('#recipe-detail').evaluate('(el) => el.scrollTop = el.scrollHeight')
                detail.screenshot(path=str(output_dir / f'{slug}-detail-bottom-{device}.png'))
                detail.keyboard.press('Escape')
                assert detail.locator('#recipe-dialog').is_hidden()
                detail.locator('.section-nav a[data-section="healthy-takeouts"]').click()
                assert detail.locator('#healthy-takeouts').is_visible()
                detail.close()
            report['devices'].append({'device': device, 'recipeCount': all_cards, 'takeoutCount': 7, 'pendingSourceCount': len(expected_links), 'checkedSlugs': slugs})
            page.close()
        browser.close()
    (output_dir / 'checks.json').write_text(json.dumps(report, indent=2))
    assert not report['errors'], report['errors']
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--slug', action='append', default=[])
    args = parser.parse_args()
    check_site(args.base_url, args.output_dir, args.slug)
