import pytest


EXPECTED_LABELS = ["tristesse", "joie", "amour", "colere", "peur", "surprise"]


class TestSentimentPreprocess:
    """Tests du preprocessing (sans charger le modèle)"""

    @pytest.fixture
    def analyzer_stub(self):
        from services.sentiment.model import SentimentAnalyzer
        return SentimentAnalyzer.__new__(SentimentAnalyzer)

    def test_supprime_urls(self, analyzer_stub):
        result = analyzer_stub.preprocess("Regarde https://example.com super")
        assert "http" not in result

    def test_supprime_mentions(self, analyzer_stub):
        result = analyzer_stub.preprocess("Hello @elonmusk ça va ?")
        assert "@" not in result
        assert "elonmusk" not in result

    def test_garde_mot_hashtag(self, analyzer_stub):
        result = analyzer_stub.preprocess("J'adore #Python")
        assert "#" not in result
        assert "Python" in result

    def test_tronque_512(self, analyzer_stub):
        long_text = "a" * 1000
        result = analyzer_stub.preprocess(long_text)
        assert len(result) <= 512

    def test_texte_vide(self, analyzer_stub):
        result = analyzer_stub.preprocess("")
        assert result == ""

    def test_normalise_espaces(self, analyzer_stub):
        result = analyzer_stub.preprocess("trop   d'espaces    ici")
        assert "   " not in result


@pytest.mark.slow
class TestSentimentModel:
    """Tests du modèle chargé depuis HuggingFace.
    Marqués @slow car le chargement du modèle prend ~30s.
    Lancer avec: pytest -m slow tests/test_sentiment.py
    """

    @pytest.fixture(scope="class")
    def analyzer(self):
        from services.sentiment.model import get_analyzer
        return get_analyzer()

    def test_modele_charge(self, analyzer):
        """Le modèle doit se charger sans erreur"""
        assert analyzer is not None
        assert analyzer.classifier is not None

    def test_predict_retourne_6_labels(self, analyzer):
        """predict() doit retourner un score pour chaque label"""
        scores = analyzer.predict("Je suis content")
        assert len(scores) == 6
        for label in EXPECTED_LABELS:
            assert label in scores

    def test_scores_entre_0_et_1(self, analyzer):
        """Chaque score doit être entre 0 et 1"""
        scores = analyzer.predict("Ceci est un test")
        for label, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{label} = {score} hors limites"

    def test_somme_scores_environ_1(self, analyzer):
        """La somme des scores doit être proche de 1"""
        scores = analyzer.predict("Un tweet quelconque")
        total = sum(scores.values())
        assert abs(total - 1.0) < 0.05, f"Somme = {total}, attendu ~1.0"

    def test_dominant_sentiment(self, analyzer):
        """get_dominant_sentiment doit retourner un label valide"""
        scores = analyzer.predict("Je suis heureux")
        dominant, confidence = analyzer.get_dominant_sentiment(scores)
        assert dominant in EXPECTED_LABELS
        assert 0.0 <= confidence <= 1.0
        assert confidence == max(scores.values())

    def test_joie_detectee(self, analyzer):
        """Un texte joyeux doit être classé joie"""
        scores = analyzer.predict("Je suis tellement heureux aujourd'hui, c'est magnifique!")
        dominant, _ = analyzer.get_dominant_sentiment(scores)
        assert dominant == "joie", f"Attendu joie, obtenu {dominant} ({scores})"

    def test_colere_detectee(self, analyzer):
        """Un texte en colère doit être classé colere"""
        scores = analyzer.predict("C'est inadmissible, je suis furieux de cette situation!")
        dominant, _ = analyzer.get_dominant_sentiment(scores)
        assert dominant == "colere", f"Attendu colere, obtenu {dominant} ({scores})"

    def test_tristesse_detectee(self, analyzer):
        """Un texte triste doit être classé tristesse"""
        scores = analyzer.predict("Je suis tellement triste, j'ai envie de pleurer")
        dominant, _ = analyzer.get_dominant_sentiment(scores)
        assert dominant == "tristesse", f"Attendu tristesse, obtenu {dominant} ({scores})"

    def test_amour_detecte(self, analyzer):
        """Un texte d'amour doit être classé amour"""
        scores = analyzer.predict("Je t'aime tellement mon amour, tu es tout pour moi")
        dominant, _ = analyzer.get_dominant_sentiment(scores)
        assert dominant == "amour", f"Attendu amour, obtenu {dominant} ({scores})"

    def test_predict_batch(self, analyzer):
        """predict_batch doit retourner une liste de scores"""
        texts = ["Je suis content", "Je suis triste", "Je suis en colère"]
        results = analyzer.predict_batch(texts)
        assert len(results) == 3
        for scores in results:
            assert len(scores) == 6

    def test_texte_vide_retourne_zeros(self, analyzer):
        """Un texte vide doit retourner des scores à 0"""
        scores = analyzer.predict("")
        assert all(v == 0.0 for v in scores.values())

    def test_texte_anglais(self, analyzer):
        """Le modèle doit aussi fonctionner en anglais (multilingue)"""
        scores = analyzer.predict("I am so happy and excited about this!")
        dominant, confidence = analyzer.get_dominant_sentiment(scores)
        assert dominant in EXPECTED_LABELS
        assert confidence > 0.3

    def test_singleton_get_analyzer(self):
        """get_analyzer doit retourner la même instance (singleton)"""
        from services.sentiment.model import get_analyzer
        a1 = get_analyzer()
        a2 = get_analyzer()
        assert a1 is a2
