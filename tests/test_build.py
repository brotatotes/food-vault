import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('food_build', ROOT / 'tools/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.recipes = json.loads((ROOT / 'data/recipes.json').read_text())
        self.takeouts = json.loads((ROOT / 'data/takeouts.json').read_text())
        self.links = json.loads((ROOT / 'data/recipe-links.json').read_text())

    def test_counts_and_complete_recipes(self):
        self.assertEqual(len(self.recipes), 31)
        for recipe in self.recipes:
            self.assertTrue(recipe['ingredients'])
            self.assertTrue(recipe['steps'])
            self.assertTrue((ROOT / 'docs' / recipe['image']).is_file())

    def test_requested_sources_saved_once(self):
        urls = []
        for recipe in self.recipes:
            if recipe.get('sourceUrl'):
                urls.append(recipe['sourceUrl'].rstrip('/'))
            urls.extend(item['url'].rstrip('/') for item in recipe.get('additionalSources', []))
        urls.extend(item['sourceUrl'].rstrip('/') for item in self.links)
        self.assertEqual(len(urls), len(set(urls)))
        for url in [
            'https://kellyscleankitchen.com/2023/11/27/avgolemono-soup',
            'https://cooked.wiki/saved/bd2e2b66-555e-4079-87e7-fd9af7cc9749',
            'https://eatingalonediaries.substack.com/p/day-1725-pork-rib-and-daikon-soup',
            'https://tiffycooks.com/classic-braised-taiwanese-beef-stew',
            'https://thefoodietakesflight.com/easy-one-pot-pumpkin-mushroom-rice',
            'https://feelgoodfoodie.net/recipe/3-ingredient-chia-pudding',
            'https://feelgoodfoodie.net/recipe/overnight-oats',
        ]:
            self.assertEqual(urls.count(url), 1)

    def test_addition_order_and_original_dates(self):
        for recipe in self.recipes:
            self.assertIsNotNone(datetime.fromisoformat(recipe['addedAt']).utcoffset())
        ordered = sorted(self.recipes, key=lambda recipe: datetime.fromisoformat(recipe['addedAt']), reverse=True)
        self.assertEqual([recipe['slug'] for recipe in ordered[:6]], [
            '3-ingredient-chia-pudding', 'easy-overnight-oats',
            'nepali-style-chicken-chukauni', 'taiwanese-pork-rib-daikon-soup',
            'avgolemono-soup', 'classic-braised-taiwanese-beef-stew'
        ])
        pumpkin = next(recipe for recipe in ordered if recipe['slug'] == 'one-pot-pumpkin-mushroom-rice')
        self.assertTrue(pumpkin['addedAt'].startswith('2026-07-28'))
        self.assertGreater(ordered.index(pumpkin), 3)

    def test_feelgoodfoodie_base_and_optional_flavors(self):
        chia = next(item for item in self.recipes if item['slug'] == '3-ingredient-chia-pudding')
        oats = next(item for item in self.recipes if item['slug'] == 'easy-overnight-oats')
        for recipe in [chia, oats]:
            self.assertEqual(recipe['duration'], '1 serving')
            self.assertIn('Yumna Jawad', recipe['creator'])
            self.assertIn('Feel Good Foodie', recipe['imageCredit'])
        self.assertIn('optional', chia['ingredients'][2])
        self.assertIn('Quantity not specified', chia['ingredients'][3])
        self.assertEqual(oats['ingredients'][:2], ['Base: ½ cup rolled oats', 'Base: ½ cup milk of choice'])
        self.assertEqual(sum(item.startswith('Optional add-in:') for item in oats['ingredients']), 4)
        self.assertEqual(sum(' flavor:' in item for item in oats['ingredients']), 6)
        self.assertIn('alternatives, not one combined ingredient list', ' '.join(oats['steps']))
        self.assertIn('8 hours 5 minutes total', ' '.join(oats['evidence']))
        self.assertIn('2 hours minimum', ' '.join(oats['evidence']))
        self.assertIn('at least 4 hours', ' '.join(oats['evidence']))

    def test_takeout_names(self):
        self.assertEqual({item['name'] for item in self.takeouts}, {
            'Happy + Hale', 'Alpaca', 'CAVA', 'Chipotle', 'Guasaca',
            'Mediterranean Grill & Grocery', 'Namu'
        })

    def test_uncertainty_and_ingredient_warning(self):
        self.assertEqual(self.links, [])
        chukauni = next(item for item in self.recipes if item['slug'] == 'nepali-style-chicken-chukauni')
        self.assertIn('No split or additional quantity has been invented', ' '.join(chukauni['evidence']))
        self.assertIn('165°F', ' '.join(chukauni['steps']))
        self.assertEqual(chukauni['duration'], 'Yield not stated')
        soup = next(item for item in self.recipes if item['slug'] == 'taiwanese-pork-rib-daikon-soup')
        self.assertEqual(soup['duration'], '3–4 servings')
        self.assertIn('45–60 minutes', ' '.join(soup['steps']))
        stew = next(item for item in self.recipes if item['slug'] == 'classic-braised-taiwanese-beef-stew')
        self.assertIn('not bean-free', ' '.join(stew['evidence']))
        pumpkin = next(item for item in self.recipes if item['slug'] == 'one-pot-pumpkin-mushroom-rice')
        self.assertEqual(pumpkin['additionalSources'][0]['url'], 'https://www.instagram.com/reel/DQE60voCTC5/')

    def test_no_private_chat_in_new_collections(self):
        text = json.dumps(self.takeouts + self.links)
        for private in ['Emily Hao', 'Lulu Sun', 'Korean beef msg', 'no ingredients were used']:
            self.assertNotIn(private, text)

    def test_built_data_matches_source(self):
        for filename in ['recipes.json', 'takeouts.json', 'recipe-links.json']:
            self.assertEqual((ROOT / 'data' / filename).read_bytes(), (ROOT / 'docs/data' / filename).read_bytes())

    def test_takeout_validation_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            (root / 'data/takeouts.json').write_text(json.dumps([self.takeouts[0], self.takeouts[0]]))
            with patch.object(build, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Duplicate takeout slug'):
                    build.build_takeouts()

    def test_saved_links_reject_existing_recipe_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            link = {'slug': 'duplicate', 'title': 'Duplicate', 'sourceUrl': self.recipes[0]['sourceUrl'], 'status': 'Pending', 'note': 'Test fixture'}
            (root / 'data/recipe-links.json').write_text(json.dumps([link]))
            with patch.object(build, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'duplicate saved source'):
                    build.build_recipe_links({link['sourceUrl'].rstrip('/')})


if __name__ == '__main__':
    unittest.main()
