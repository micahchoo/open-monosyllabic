"""_ipa gates: CLTS grapheme/BIPA slash resolution (the bug that silently lost
100% of castrosui), plus honesty gates — polymorphemic joins, bound morphemes,
reconstructions, and multi-word phrases must NOT mint fake monosyllable shapes."""

from oms.canon import canonicalize
from oms.ingest_cldf import _ipa, _is_proto, _respell, load


def test_clts_grapheme_bipa_token_resolves_to_bipa_side():
    assert _ipa({"Segments": "tʃ/tɕ a"}) == "tɕ a"


def test_castrosui_tone_token_resolves_and_canon_siphons_tone():
    ipa = _ipa({"Segments": "z ə t ₇/⁵⁵"})
    assert ipa == "z ə t ⁵⁵"
    c = canonicalize(ipa, segmented=True)
    assert c.segmental == "zət"
    assert c.tone == "⁵⁵"


def test_morpheme_boundary_drops_row_instead_of_joining():
    assert _ipa({"Segments": "ˀd a ₁/¹³ + v a n ₁/¹³"}) == ""
    assert _ipa({"Segments": "b a + i"}) == ""      # would mint fake diphthong "bai"
    assert _ipa({"Segments": "k a _ m a"}) == ""    # word boundary


def test_empty_bipa_side_still_drops_row():
    assert _ipa({"Segments": "a x/"}) == ""


def test_alternation_tilde_still_drops_row():
    assert _ipa({"Segments": "b~p a"}) == ""


def test_reconstruction_star_in_form_drops_even_with_clean_segments():
    assert _ipa({"Segments": "r u a", "Form": "*rua"}) == ""


def test_bound_morpheme_edge_hyphen_drops_even_with_clean_segments():
    assert _ipa({"Segments": "t a", "Form": "ta-"}) == ""
    assert _ipa({"Segments": "t a", "Form": "-ta"}) == ""


def test_multiword_form_fallback_drops():
    assert _ipa({"Segments": "", "Form": "wa ei"}) == ""


def test_form_fallback_unchanged_for_single_words():
    assert _ipa({"Segments": "", "Form": "ba"}) == "ba"


def test_is_proto_matches_naming_conventions_only():
    assert _is_proto("Proto-Polynesian")
    assert _is_proto("Proto Malagasy")
    assert _is_proto("proto-Chamic")
    assert not _is_proto("Old Chinese")      # attested doculect, stays
    assert not _is_proto("Protogermanicish")  # no separator — not the convention
    assert not _is_proto("Maori")


def test_segments_keep_their_boundaries():
    # "m ai" (one diphthong segment) and "m a i" (two vowels) must stay distinct
    assert _ipa({"Segments": "m ai"}) == "m ai"
    assert _ipa({"Segments": "m a i"}) == "m a i"


def test_abvd_spelling_is_respelled_before_it_is_read_as_ipa():
    # ABVD ships spellings, never Segments: ' is a glottal stop, y is /j/, ng is /ŋ/
    assert _respell("abvd", "'bayo") == "ʔbajo"
    assert _respell("abvd", "nga") == "ŋa"
    assert _respell("abvd", "ʻai") == "ʔai"
    assert _respell("other", "nga") == "nga", "only a dataset with a known spelling is respelled"


def test_load_reads_the_family_column(tmp_path):
    (tmp_path / "metadata.json").write_text('{"id": "t", "license": "CC-BY-4.0"}')
    (tmp_path / "languages.csv").write_text(
        "ID,Name,Glottocode,Macroarea,Latitude,Longitude,Family\n"
        "m,Maori,maor1246,Papunesia,-40,176,Austronesian\n"
        "x,Isolate,isol1234,Africa,,,\n")
    (tmp_path / "parameters.csv").write_text("ID,Name,Concepticon_ID\n")
    (tmp_path / "forms.csv").write_text("ID,Language_ID,Parameter_ID,Form,Segments\n")
    fams = {l["glottocode"]: l["family"] for l in load(tmp_path)["languages"]}
    assert fams == {"maor1246": "Austronesian", "isol1234": ""}


def _dataset(tmp_path, lang_rows, param_rows="", form_rows=""):
    (tmp_path / "metadata.json").write_text('{"id": "t", "license": "CC-BY-4.0"}')
    (tmp_path / "languages.csv").write_text("ID,Name,Glottocode,Glottolog_Name\n" + lang_rows)
    (tmp_path / "parameters.csv").write_text("ID,Name,Concepticon_ID,Concepticon_Gloss\n" + param_rows)
    (tmp_path / "forms.csv").write_text("ID,Language_ID,Parameter_ID,Form,Segments\n" + form_rows)
    return load(tmp_path)


def test_language_is_named_by_glottolog_and_keeps_the_source_name(tmp_path):
    # Source names are doculect labels: "A151_Nkongho", lowercase "anam".
    langs = {l["glottocode"]: l for l in _dataset(tmp_path,
        "a,A151_Nkongho,nkon1248,Nkongho\nb,Tiriyó,trio1238,Trió\nc,Solo,solo1234,\n")["languages"]}
    assert (langs["nkon1248"]["name"], langs["nkon1248"]["alias"]) == ("Nkongho", "A151_Nkongho")
    assert (langs["trio1238"]["name"], langs["trio1238"]["alias"]) == ("Trió", "Tiriyó")
    assert (langs["solo1234"]["name"], langs["solo1234"]["alias"]) == ("Solo", ""), "no Glottolog name: keep the source's"


def test_entries_carry_the_concepticon_gloss(tmp_path):
    e = _dataset(tmp_path, "m,Maori,maor1246,Maori\n", "w,water,3078,IRRIGATE\n", "1,m,w,wai,w ai\n")["entries"][0]
    assert (e["gloss"], e["concepticon_id"], e["concepticon_gloss"]) == ("water", 3078, "IRRIGATE")


def test_abvd_vowel_quality_marks_are_excluded_with_a_reason(tmp_path):
    # Yabem ê, Vietnamese-based ư ă, caron ǎ: each orthography reads them its own
    # way, and canon would strip ̂ as tone. The row is kept only as an exclusion.
    (tmp_path / "metadata.json").write_text('{"id": "abvd", "license": "CC-BY-4.0"}')
    (tmp_path / "languages.csv").write_text("ID,Name,Glottocode\ny,Yabem,yabe1254\n")
    (tmp_path / "parameters.csv").write_text("ID,Name,Concepticon_ID\nx,x,\n")
    (tmp_path / "forms.csv").write_text("ID,Language_ID,Parameter_ID,Form,Segments\n"
                                        "1,y,x,bê,\n2,y,x,mư,\n3,y,x,tǎ,\n4,y,x,la,\n")
    es = {e["ipa"]: e.get("exclude") for e in load(tmp_path)["entries"]}
    assert es["la"] is None
    assert all(es[k] and "no fixed IPA reading" in es[k] for k in ("bê", "mư", "tǎ"))


def test_abvd_macron_writes_length():
    # Pacific spellings write a long vowel with a macron; canon would strip it as
    # tone and merge /maː/ with /ma/ (4,458 ABVD rows, 521 languages).
    assert _respell("abvd", "māta") == "maːta"
    assert _respell("abvd", "fī") == "fiː"
    assert canonicalize(_respell("abvd", "mā")).segmental == "maː"


def test_an_accent_on_a_one_vowel_abvd_form_has_no_fixed_reading():
    # One syllable cannot carry contrastive stress, so the accent writes vowel
    # quality or tone: Chuukese pe / pé, Puluwatese me / mé would merge.
    from oms.ingest_cldf import _spelling_exclusion
    assert _spelling_exclusion("abvd", "pé")
    assert _spelling_exclusion("abvd", "tò")
    assert _spelling_exclusion("abvd", "ráy"), "ABVD y is /j/: one vowel, counted after respelling"
    # on a longer word it is a stress mark: kept, stripped harmlessly later
    assert _spelling_exclusion("abvd", "síbukuʔ") is None
    assert _spelling_exclusion("abvd", "pe") is None
    assert _spelling_exclusion("other", "pé") is None
