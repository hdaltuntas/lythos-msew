"""
Text of the interface shell.

Nothing is written into the page: the browser fetches this dictionary from
`/api/meta`, so changing the language is handled in one place and the wording
sits beside the rest of the program's translations. Whatever `i18n` already
says is reused; only what the web shell adds of its own is spelled out here.
"""

from __future__ import annotations

from ..i18n import TRANSLATIONS

#: Text the web shell needs and the rest of the program does not.
#: key -> (English, Turkish)
SHELL = {
    "tagline": ("mechanically stabilised earth walls",
                "donatılı zemin (MSE) istinat duvarları"),
    "language": ("Language", "Dil"),
    "open": ("Open…", "Aç…"),
    "save": ("Save", "Kaydet"),
    "theme": ("Theme", "Tema"),
    "ready": ("Ready.", "Hazır."),
    "tab_inputs": ("1 · Wall", "1 · Duvar"),
    "tab_heights": ("2 · Height study", "2 · Yükseklik çalışması"),
    "add_row": ("+ Add row", "+ Satır ekle"),
    "del_row": ("− Remove row", "− Satır sil"),
    "types_group": ("Reinforcement types (steel and polymer strips, geogrids, geotextiles)",
                    "Donatı türleri (çelik ve polimer şerit, geogrid, geotekstil)"),
    "layers_group": ("Reinforcement layers (from the base up)",
                     "Donatı tabakaları (tabandan yukarı)"),
    "generate": ("Generate layers", "Tabakaları üret"),
    "catalog": ("Catalogue", "Katalog"),
    "catalog_add": ("+ Add to types", "+ Türlere ekle"),
    "catalog_added": ("Added from the catalogue", "Katalogdan eklendi"),
    "catalog_note": ("Typical market sizes and strength classes with FHWA's typical factors; "
                     "check them against the datasheet of the product specified.",
                     "Piyasadaki tipik ölçüler ve dayanım sınıfları, FHWA'nın tipik "
                     "katsayılarıyla; kullanılacak ürünün teknik föyüne göre kontrol ediniz."),
    "generated": ("Layers generated.", "Tabakalar üretildi."),
    "external_title": ("External stability", "Dış duraylılık"),
    "internal_title": ("Internal stability, layer by layer", "İç duraylılık, tabaka tabaka"),
    "seismic_title": ("Earthquake, layer by layer", "Deprem, tabaka tabaka"),
    "bearing_title": ("Bearing capacity by method", "Yönteme göre taşıma gücü"),
    "heights_title": ("Results by height", "Yüksekliğe göre sonuçlar"),
    "view_summary": ("Summary", "Özet"),
    "view_layers": ("Layers", "Tabakalar"),
    "view_text": ("Results", "Sonuçlar"),
    "view_figures": ("Figures", "Şekiller"),
    "view_heights": ("Heights", "Yükseklikler"),
    "figure": ("Figure", "Şekil"),
    "report_format": ("Report", "Rapor"),
    "report_pdf": ("PDF report", "PDF rapor"),
    "report_html": ("HTML report", "HTML rapor"),
    "report_docx": ("Word report", "Word rapor"),
    "no_results": ("Run the analysis.", "Analizi çalıştırın."),
    "no_heights": ("Set the height range and the layout rule, then run the height study.",
                   "Yükseklik aralığını ve yerleşim kuralını girip yükseklik çalışmasını "
                   "başlatın."),
    "error": ("Error", "Hata"),
    "saved": ("Saved.", "Kaydedildi."),
    "loaded": ("Project loaded.", "Proje yüklendi."),
    "bad_file": ("That file is not a Lythos MSEW project.",
                 "Bu dosya bir Lythos MSEW projesi değil."),
    "busy": ("An analysis is already running.", "Bir hesap zaten sürüyor."),
    "cancel": ("Stop", "Durdur"),
    "cancelled": ("Cancelled.", "İptal edildi."),
    "stop_hint": ("Press Ctrl+C to stop.", "Durdurmak için Ctrl+C."),
    "stopped": ("stopped", "durduruldu"),
}

#: Keys taken straight from the program's translations, under the same name.
REUSED = [
    "run_analysis_button", "running_analysis", "analysis_complete", "report_action",
    "report_running", "warnings_title", "types_note", "layers_note",
    "hs_run", "hs_export_csv", "hs_export_xlsx", "hs_progress", "hs_done", "hs_no_data",
]


def shell_strings(lang: str = "en") -> dict:
    """Every string the page needs, in one language."""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    strings = {key: (tr if lang == "tr" else en) for key, (en, tr) in SHELL.items()}
    strings.update({key: translations[key] for key in REUSED})
    return strings
