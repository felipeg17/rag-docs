import unittest

from app.infrastructure.vector_db.scoring import cosine_distance_to_similarity


class TestCosineDistanceToSimilarity(unittest.TestCase):
    def test_known_values(self):
        for distance, expected in [
            (0.0, 1.0),
            (0.25, 0.75),
            (1.0, 0.0),
            (1.708, 0.0),
            (2.0, 0.0),
            (-1e-7, 1.0),
        ]:
            with self.subTest(distance=distance):
                self.assertAlmostEqual(cosine_distance_to_similarity(distance), expected)

    def test_monotone_non_increasing_and_bounded(self):
        distances = [i * 0.05 for i in range(41)]

        scores = [cosine_distance_to_similarity(d) for d in distances]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(0.0 <= s <= 1.0 for s in scores))
