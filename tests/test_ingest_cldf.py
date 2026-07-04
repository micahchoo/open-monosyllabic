"""_ipa gates: CLTS grapheme/BIPA slash resolution (the bug that silently lost
100% of castrosui), plus honesty gates — polymorphemic joins, bound morphemes,
reconstructions, and multi-word phrases must NOT mint fake monosyllable shapes."""

from oms.canon import canonicalize
from oms.ingest_cldf import _ipa, _is_proto


def test_clts_grapheme_bipa_token_resolves_to_bipa_side():
    assert _ipa({"Segments": "tʃ/tɕ a"}) == "tɕa"


def test_castrosui_tone_token_resolves_and_canon_siphons_tone():
    ipa = _ipa({"Segments": "z ə t ₇/⁵⁵"})
    assert ipa == "zət⁵⁵"
    c = canonicalize(ipa)
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
