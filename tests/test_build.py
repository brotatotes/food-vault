import importlib.util
import json
import tempfile
import unittest
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
        self.assertEqual(len(self.recipes), 27)
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
        ]:
            self.assertEqual(urls.count(url), 1)

    def test_takeout_names(self):
        self.assertEqual({item['name'] for item in self.takeouts}, {
            'Happy + Hale', 'Alpaca', 'CAVA', 'Chipotle', 'Guasaca',
            'Mediterranean Grill & Grocery', 'Namu'
        })

    def test_uncertainty_and_ingredient_warning(self):
        self.assertEqual(len(self.links), 2)
        self.assertTrue(all(link['status'] == 'Recipe details pending' for link in self.links))
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
            (root / 'data/recipe-links.json').write_text(json.dumps(self.links))
            with patch.object(build, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'duplicate saved source'):
                    build.build_recipe_links({self.links[0]['sourceUrl'].rstrip('/')})


if __name__ == '__main__':
    unittest.main()
