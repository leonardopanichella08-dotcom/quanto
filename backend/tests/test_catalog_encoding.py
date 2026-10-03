from app.core import catalog_meta


def test_text_served_with_the_wrong_encoding_is_mended():
    good = "Le azioni per estenderne l’utilizzo in tutta Italia, per una città più sicura"
    bad = good.encode("utf-8").decode("cp1252")            # come la servono alcune schede: UTF-8 letto come Windows-1252
    assert bad != good
    page = f'<html><head><meta name="description" content="{bad}"/></head><body><h2>Cos&#039;è</h2><p>x</p></body></html>'
    assert catalog_meta.parse_page(page)["summary"] == good
    assert catalog_meta._mend(good) == good                 # il testo giusto non si tocca
