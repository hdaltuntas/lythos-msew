"""
Every text of Lythos MSEW, in English and Turkish.

Each entry is written once as ``key: (English, Turkish)`` so the two languages
cannot drift apart: a key without its translation is a syntax error, not a
blank on the screen. `TRANSLATIONS[lang][key]` is how the rest of the program
reads them.
"""

from __future__ import annotations

ENTRIES = {
    # ------------------------------------------------------------------ input errors
    "err_height": ("The wall height must be greater than zero.",
                   "Duvar yüksekliği sıfırdan büyük olmalıdır."),
    "err_embedment": ("The embedment must be positive and smaller than the wall height.",
                      "Gömülme derinliği pozitif ve duvar yüksekliğinden küçük olmalıdır."),
    "err_batter": ("The batter of the face must be between 0 and 30°.",
                   "Yüz eğimi 0 ile 30° arasında olmalıdır."),
    "err_backslope": ("The backslope must be positive and flatter than the friction angle of "
                      "the retained fill ({phi:.1f}°).",
                      "Arka şev açısı pozitif ve arka dolgunun içsel sürtünme açısından "
                      "({phi:.1f}°) küçük olmalıdır."),
    "err_toe_slope": ("The slope in front of the wall must be between 0 and 45°.",
                      "Duvar önündeki şev açısı 0 ile 45° arasında olmalıdır."),
    "err_gamma": ("{soil}: the unit weight must be greater than zero.",
                  "{soil}: birim hacim ağırlık sıfırdan büyük olmalıdır."),
    "err_phi": ("{soil}: the friction angle must be between 0 and 60°.",
                "{soil}: içsel sürtünme açısı 0 ile 60° arasında olmalıdır."),
    "err_fill_phi": ("The reinforced and the retained fill need a friction angle.",
                     "Donatılı dolgu ile arka dolgunun içsel sürtünme açısı olmalıdır."),
    "err_foundation_strength": ("The foundation soil has no strength: enter c' and φ', or cu "
                                "with φ = 0.",
                                "Temel zemininin dayanımı yok: c' ve φ' ya da φ = 0 ile cu "
                                "giriniz."),
    "err_gamma_sat": ("The saturated unit weight of the foundation soil must exceed γw.",
                      "Temel zemininin doygun birim hacim ağırlığı γw'den büyük olmalıdır."),
    "err_no_layers": ("The wall has no reinforcement layer.",
                      "Duvarda donatı tabakası yok."),
    "err_kind": ("Reinforcement '{name}': unknown kind.",
                 "'{name}' donatısı: bilinmeyen tür."),
    "err_geosynthetic": ("Reinforcement '{name}': a geosynthetic needs Tult > 0, reduction "
                         "factors of at least 1 and a coverage ratio above 0.",
                         "'{name}' donatısı: geosentetik için Tult > 0, en az 1 olan azaltma "
                         "katsayıları ve sıfırdan büyük kaplama oranı gerekir."),
    "err_polymer_strip": ("Reinforcement '{name}': a polymer strip needs Tult per strip, "
                          "reduction factors of at least 1, its width and its horizontal "
                          "spacing.",
                          "'{name}' donatısı: polimer şerit için şerit başına Tult, en az 1 "
                          "olan azaltma katsayıları, genişlik ve yatay aralık gerekir."),
    "err_strip": ("Reinforcement '{name}': a steel strip needs its width, thickness, yield "
                  "strength and horizontal spacing.",
                  "'{name}' donatısı: çelik şerit için genişlik, kalınlık, akma dayanımı ve "
                  "yatay aralık gerekir."),
    "err_pullout_params": ("Reinforcement '{name}': α and the connection ratio must be "
                           "greater than zero.",
                           "'{name}' donatısı: α ve bağlantı oranı sıfırdan büyük olmalıdır."),
    "err_unknown_type": ("A layer refers to the reinforcement '{name}', which is not in the "
                         "type table.",
                         "Bir tabaka, tür tablosunda olmayan '{name}' donatısını kullanıyor."),
    "err_layer_height": ("The layer at z = {z:.3f} m must lie between the base and the top of "
                         "the wall (0 < z < {H:.2f} m).",
                         "z = {z:.3f} m'deki tabaka duvar tabanı ile tepesi arasında olmalıdır "
                         "(0 < z < {H:.2f} m)."),
    "err_layer_length": ("The layer at z = {z:.3f} m needs a length.",
                         "z = {z:.3f} m'deki tabakanın boyu girilmemiş."),
    "err_strip_load": ("The strip load needs a width, and its centre must be at least half "
                       "its width behind the face.",
                       "Şerit yükün genişliği olmalı ve merkezi yüzden en az yarı genişliği "
                       "kadar geride olmalıdır."),
    "err_seismic": ("The peak ground acceleration coefficient A must be between 0 and 1.",
                    "En büyük yer ivmesi katsayısı A, 0 ile 1 arasında olmalıdır."),
    "err_mononobe": ("The seismic coefficient and the backslope together exceed the friction "
                     "angle: Mononobe–Okabe has no active state.",
                     "Deprem katsayısı ile arka şev birlikte içsel sürtünme açısını aşıyor: "
                     "Mononobe–Okabe aktif durumu yok."),
    "err_layout": ("The layout needs a spacing, and a first layer between the base and the "
                   "top of the wall.",
                   "Yerleşim için aralık ve taban ile duvar tepesi arasında bir ilk tabaka "
                   "gerekir."),
    "err_heights": ("The height range needs 0 < H min ≤ H max and a positive step.",
                    "Yükseklik aralığı için 0 < H min ≤ H maks ve pozitif adım gerekir."),

    # ------------------------------------------------------------------ warnings
    "warn_lengths_vary": ("The layers are not all the same length; the external checks use "
                          "the length of the lowest layer, L = {L:.2f} m.",
                          "Tabakaların boyları eşit değil; dış duraylılık kontrolleri en alt "
                          "tabakanın boyunu kullanır, L = {L:.2f} m."),
    "warn_min_length": ("The shortest layer ({L:.2f} m) is shorter than FHWA's minimum, "
                        "the larger of 0.7·H and 2.4 m ({rule:.2f} m).",
                        "En kısa tabaka ({L:.2f} m), FHWA'nın en küçük boyundan (0.7·H ile "
                        "2.4 m'nin büyüğü, {rule:.2f} m) kısa."),
    "warn_spacing": ("The largest vertical spacing, {s:.2f} m, exceeds the {limit:.2f} m "
                     "FHWA recommends.",
                     "En büyük düşey aralık, {s:.2f} m, FHWA'nın önerdiği {limit:.2f} m'yi "
                     "aşıyor."),
    "warn_short_le": ("{n} layer(s) reach less than {Le:.2f} m beyond the active zone; "
                      "their pullout check fails on that account.",
                      "{n} tabaka aktif bölgenin ötesine {Le:.2f} m'den az uzanıyor; bu "
                      "nedenle sıyrılma kontrolleri sağlanmıyor."),
    "warn_strip_behind": ("The strip load lies behind the reinforced zone; it is counted in "
                          "the internal checks only.",
                          "Şerit yük donatılı bölgenin gerisinde; yalnızca iç duraylılık "
                          "kontrollerinde hesaba katıldı."),
    "warn_water": ("The water table is {dw:.2f} m below the base, within the foundation's "
                   "failure zone; the self-weight term uses a reduced unit weight.",
                   "Su tablası tabanın {dw:.2f} m altında, temelin göçme bölgesi içinde; zati "
                   "ağırlık terimi azaltılmış birim hacim ağırlıkla hesaplandı."),
    "warn_undrained": ("The foundation soil is analysed undrained (φ = 0): sliding and "
                       "bearing rest on cu alone.",
                       "Temel zemini drenajsız (φ = 0) çözüldü: kayma ve taşıma gücü yalnızca "
                       "cu'ya dayanıyor."),
    "warn_mixed_kinds": ("The wall mixes extensible and inextensible reinforcement; each "
                         "layer is checked with its own failure surface and Kr.",
                         "Duvarda uzayabilir ve uzamaz donatılar birlikte kullanılmış; her "
                         "tabaka kendi göçme yüzeyi ve Kr değeriyle kontrol edildi."),
    "warn_live_on_slope": ("A live surcharge is applied on a sloping backfill; check that "
                           "traffic can in fact reach it.",
                           "Eğimli arka dolguya hareketli sürşarj uygulandı; trafiğin gerçekten "
                           "oraya erişip erişmediğini kontrol ediniz."),

    # ------------------------------------------------------------------ choice labels
    "kind_strip": ("Steel strip", "Çelik şerit"),
    "kind_polymer_strip": ("Polymer strip", "Polimer şerit"),
    "family_steel_ha": ("Ribbed steel strips (HA, galvanised)",
                        "Nervürlü çelik şeritler (HA, galvanizli)"),
    "family_polymer": ("Polymer strips (PET core, PE sheath)",
                       "Polimer şeritler (PET çekirdek, PE kılıf)"),
    "family_geogrid_hdpe": ("Uniaxial HDPE geogrids", "Tek eksenli HDPE geogridler"),
    "family_geogrid_pet": ("PET geogrids", "PET geogridler"),
    "family_geotextile": ("Woven geotextiles", "Dokuma geotekstiller"),
    "kind_geogrid": ("Geogrid", "Geogrid"),
    "kind_geotextile": ("Geotextile", "Geotekstil"),
    "design_asd": ("ASD — factors of safety (FHWA-NHI-00-043)",
                   "ASD — güvenlik sayıları (FHWA-NHI-00-043)"),
    "design_lrfd": ("LRFD — load and resistance factors (AASHTO)",
                    "LRFD — yük ve direnç katsayıları (AASHTO)"),
    "design_short_asd": ("ASD", "ASD"),
    "design_short_lrfd": ("LRFD", "LRFD"),
    "method_terzaghi": ("Terzaghi (1943)", "Terzaghi (1943)"),
    "method_meyerhof": ("Meyerhof (1963)", "Meyerhof (1963)"),
    "method_hansen": ("Brinch Hansen (1970)", "Brinch Hansen (1970)"),
    "method_vesic": ("Vesić (1973)", "Vesić (1973)"),
    "method_ec7": ("EN 1997-1 Annex D", "EN 1997-1 Ek D"),
    "rule_ratio": ("L = ratio · H", "L = oran · H"),
    "rule_fixed": ("Fixed length", "Sabit boy"),
    "soil_reinforced": ("Reinforced fill", "Donatılı dolgu"),
    "soil_retained": ("Retained fill", "Arka dolgu"),
    "soil_foundation": ("Foundation soil", "Temel zemini"),
    "plane_reinforced": ("through the reinforced fill", "donatılı dolgu içinden"),
    "plane_foundation": ("on the foundation soil", "temel zemini üzerinde"),
    "plane_interface": ("along the lowest geosynthetic", "en alttaki geosentetik boyunca"),

    # ------------------------------------------------------------------ input groups
    "group_project": ("Project", "Proje"),
    "title_label": ("Title", "Başlık"),
    "analyst_label": ("Analyst", "Hazırlayan"),
    "group_geometry": ("Wall geometry", "Duvar geometrisi"),
    "H_label": ("Design height H", "Tasarım yüksekliği H"),
    "embedment_label": ("Embedment d", "Gömülme derinliği d"),
    "batter_label": ("Face batter ω", "Yüz eğimi ω"),
    "backslope_label": ("Backslope β", "Arka şev β"),
    "toe_slope_label": ("Slope in front of the toe", "Topuk önündeki şev"),
    "facing_label": ("Facing thickness", "Kaplama kalınlığı"),
    "geometry_note": ("H from the levelling pad to the top of the wall. A batter of 10° or "
                      "more is treated with Coulomb's Ka.",
                      "H, tesviye tabanından duvar tepesine ölçülür. 10° ve üzeri yüz eğimi "
                      "Coulomb Ka ile hesaplanır."),
    "group_loads": ("Surcharges", "Sürşarjlar"),
    "q_dead_label": ("Permanent surcharge", "Kalıcı sürşarj"),
    "q_live_label": ("Live (traffic) surcharge", "Hareketli (trafik) sürşarjı"),
    "strip_enabled_label": ("Strip load on the wall", "Duvar üzerinde şerit yük"),
    "strip_P_label": ("Strip load P", "Şerit yük P"),
    "strip_width_label": ("Width of the strip load", "Şerit yük genişliği"),
    "strip_offset_label": ("Face to its centre", "Yüzden merkezine"),
    "strip_live_label": ("The strip load is a live load", "Şerit yük hareketli yüktür"),
    "loads_note": ("The live load drives but never resists: it is left out of sliding, "
                   "overturning and pullout, and kept in bearing and in the tension of the "
                   "layers.",
                   "Hareketli yük iter ama direnmez: kayma, devrilme ve sıyrılmada dikkate "
                   "alınmaz; taşıma gücü ve donatı çekme kuvvetinde alınır."),
    "group_reinforced": ("Reinforced fill", "Donatılı dolgu"),
    "group_retained": ("Retained fill", "Arka dolgu"),
    "group_foundation": ("Foundation soil", "Temel zemini"),
    "gamma_label": ("Unit weight γ", "Birim hacim ağırlık γ"),
    "phi_label": ("Friction angle φ'", "İçsel sürtünme açısı φ'"),
    "gamma_sat_label": ("Saturated unit weight γsat", "Doygun birim hacim ağırlık γdoy"),
    "c_label": ("Cohesion c' (cu if φ = 0)", "Kohezyon c' (φ = 0 ise cu)"),
    "water_depth_label": ("Water table below the base", "Su tablasının tabandan derinliği"),
    "gamma_water_label": ("Unit weight of water γw", "Suyun birim hacim ağırlığı γw"),
    "foundation_note": ("Enter φ = 0 and cu as the cohesion for an undrained foundation.",
                        "Drenajsız temel için φ = 0 ve kohezyon olarak cu giriniz."),
    "group_options": ("Design method and bearing capacity",
                      "Tasarım yöntemi ve taşıma gücü"),
    "design_label": ("Design method", "Tasarım yöntemi"),
    "bearing_method_label": ("Bearing capacity factors", "Taşıma gücü katsayıları"),
    "bearing_embedment_label": ("Count the embedment as a surcharge (q = γ·d)",
                                "Gömülmeyi sürşarj olarak say (q = γ·d)"),
    "bearing_inclination_label": ("Load inclination factors", "Yük eğim katsayıları"),
    "Cds_label": ("Direct sliding coefficient Cds", "Doğrudan kayma katsayısı Cds"),
    "options_note": ("FHWA leaves out the embedment and the load inclination in the bearing "
                     "capacity of an MSE wall; switch them on to follow the general equation. "
                     "Cds applies to sliding along a geosynthetic layer.",
                     "FHWA, MSE duvarın taşıma gücünde gömülmeyi ve yük eğimini dikkate "
                     "almaz; genel denklemi uygulamak için açınız. Cds, geosentetik tabaka "
                     "boyunca kaymada kullanılır."),
    "group_corrosion": ("Steel corrosion", "Çelik korozyonu"),
    "design_life_label": ("Design life", "Tasarım ömrü"),
    "zinc_label": ("Galvanising thickness", "Galvaniz kalınlığı"),
    "steel_rate_label": ("Carbon steel loss per face", "Yüz başına karbon çeliği kaybı"),
    "corrosion_note": ("Zinc is lost at 15 µm/yr for 2 years, then 4 µm/yr; after it is gone "
                       "the steel is lost on both faces.",
                       "Çinko ilk 2 yıl 15 µm/yıl, sonra 4 µm/yıl kaybolur; bittikten sonra "
                       "çelik her iki yüzden kaybolur."),
    "group_seismic": ("Earthquake", "Deprem"),
    "seismic_enabled_label": ("Pseudo-static seismic check", "Psödo-statik deprem kontrolü"),
    "A_label": ("Peak ground acceleration coefficient A", "En büyük yer ivmesi katsayısı A"),
    "pullout_factor_label": ("Reduction of F* under seismic loading",
                             "Depremde F* azaltma katsayısı"),
    "seismic_note": ("Am = (1.45 − A)·A. Externally half the dynamic thrust PAE is added to "
                     "the inertia PIR of a block 0.5·H wide; internally the inertia of the "
                     "active zone is shared out by the resisting lengths.",
                     "Am = (1.45 − A)·A. Dış duraylılıkta dinamik itkinin yarısı, 0.5·H "
                     "genişliğindeki bloğun ataletine (PIR) eklenir; iç duraylılıkta aktif "
                     "bölgenin ataleti direnç boylarına göre paylaştırılır."),
    "group_criteria": ("Required factors of safety (ASD)",
                       "Gerekli güvenlik sayıları (ASD)"),
    "group_criteria_lrfd": ("Resistance factors (LRFD)", "Direnç katsayıları (LRFD)"),
    "FS_sliding_label": ("Sliding", "Kayma"),
    "FS_overturning_label": ("Overturning", "Devrilme"),
    "ecc_asd_label": ("Eccentricity e ≤ L / …", "Dışmerkezlik e ≤ L / …"),
    "FS_bearing_label": ("Bearing capacity", "Taşıma gücü"),
    "FS_tensile_label": ("Tensile, geosynthetics", "Çekme, geosentetik"),
    "steel_ratio_label": ("Steel: Ta = … · Fy · Ac", "Çelik: Ta = … · Fy · Ac"),
    "FS_pullout_label": ("Pullout", "Sıyrılma"),
    "FS_connection_label": ("Connection, geosynthetics", "Bağlantı, geosentetik"),
    "seismic_ratio_label": ("Seismic FS as a share of static", "Deprem GS / statik GS oranı"),
    "phi_sliding_label": ("φ sliding", "φ kayma"),
    "phi_bearing_label": ("φ bearing", "φ taşıma gücü"),
    "ecc_lrfd_label": ("Eccentricity e ≤ L / …", "Dışmerkezlik e ≤ L / …"),
    "phi_steel_label": ("φ tensile, steel strips", "φ çekme, çelik şerit"),
    "phi_geo_label": ("φ tensile, geosynthetics", "φ çekme, geosentetik"),
    "phi_pullout_label": ("φ pullout", "φ sıyrılma"),
    "min_Le_label": ("Minimum length beyond the active zone Le",
                     "Aktif bölge ötesinde en küçük boy Le"),
    "criteria_note": ("Seismic checks ask for the static factors of safety times the share "
                      "given, and e ≤ L/4.",
                      "Deprem kontrolleri statik güvenlik sayılarının verilen oranını ve "
                      "e ≤ L/4 koşulunu arar."),
    "criteria_lrfd_note": ("Loads are factored by AASHTO LRFD Table 3.4.1-2 (EV 1.00/1.35, "
                           "EH 1.50, ES 0.75/1.50, LS 1.75); the seismic case uses the "
                           "extreme-event factors.",
                           "Yükler AASHTO LRFD Tablo 3.4.1-2'ye göre çarpanlanır (EV 1.00/1.35, "
                           "EH 1.50, ES 0.75/1.50, LS 1.75); deprem durumunda aşırı olay "
                           "katsayıları kullanılır."),
    "group_layout": ("Layout generator", "Yerleşim üreteci"),
    "z1_label": ("Height of the first layer", "İlk tabakanın yüksekliği"),
    "Sv_label": ("Vertical spacing Sv", "Düşey aralık Sv"),
    "rule_label": ("Reinforcement length", "Donatı boyu"),
    "ratio_label": ("L / H", "L / H"),
    "L_fixed_label": ("Fixed length L", "Sabit boy L"),
    "L_min_label": ("Shortest length", "En kısa boy"),
    "layout_type_label": ("Reinforcement type", "Donatı türü"),
    "layout_note": ("Generate fills the layer table for the height above; the height study "
                    "uses the same rule.",
                    "Üret, tabaka tablosunu yukarıdaki yükseklik için doldurur; yükseklik "
                    "çalışması aynı kuralı kullanır."),
    "group_heights": ("Height range", "Yükseklik aralığı"),
    "H_min_label": ("Lowest height", "En küçük yükseklik"),
    "H_max_label": ("Greatest height", "En büyük yükseklik"),
    "step_label": ("Step", "Adım"),
    "heights_note": ("Each height is laid out by the generator's rule and analysed on its "
                     "own; the embedment is kept at no more than half the height.",
                     "Her yükseklik üretecin kuralıyla yerleştirilip ayrı ayrı çözülür; "
                     "gömülme derinliği yüksekliğin yarısını aşmaz."),

    # ------------------------------------------------------------------ table columns
    "col_name": ("Name", "Ad"),
    "col_kind": ("Kind", "Tür"),
    "col_Tult": ("Tult kN/m", "Tult kN/m"),
    "col_RFID": ("RFID", "RFID"),
    "col_RFCR": ("RFCR", "RFCR"),
    "col_RFD": ("RFD", "RFD"),
    "col_Rc": ("Rc", "Rc"),
    "col_b": ("b mm", "b mm"),
    "col_t": ("t mm", "t mm"),
    "col_Fy": ("Fy MPa", "Fy MPa"),
    "col_Sh": ("Sh m", "Sh m"),
    "col_Ci": ("Ci", "Ci"),
    "col_F0": ("F*₀", "F*₀"),
    "col_alpha": ("α", "α"),
    "col_CR": ("CR", "CR"),
    "col_z": ("z m", "z m"),
    "col_L": ("L m", "L m"),
    "col_type": ("Type", "Tür"),
    "types_note": ("Geogrids and geotextiles: Tult [kN/m], the reduction factors, Rc and Ci. "
                   "Steel strips: b, t, Fy, the horizontal spacing Sh and F*₀ at the top. "
                   "Polymer strips: Tult per strip [kN], the reduction factors, b, Sh and Ci. "
                   "CR is the connection strength as a share of the long-term strength.",
                   "Geogrid ve geotekstil: Tult [kN/m], azaltma katsayıları, Rc ve Ci. Çelik "
                   "şerit: b, t, Fy, yatay aralık Sh ve tepedeki F*₀. Polimer şerit: şerit "
                   "başına Tult [kN], azaltma katsayıları, b, Sh ve Ci. CR, bağlantı "
                   "dayanımının uzun süreli dayanıma oranıdır."),
    "layers_note": ("z is the height above the levelling pad, L the length from the face.",
                    "z, tesviye tabanından yükseklik; L, yüzden ölçülen boydur."),

    # ------------------------------------------------------------------ status
    "ok_short": ("OK", "UYGUN"),
    "notok_short": ("NOT OK", "UYGUN DEĞİL"),
    "na_short": ("n/a", "—"),

    # ------------------------------------------------------------------ cards
    "card_sliding": ("Sliding", "Kayma"),
    "card_overturning": ("Overturning", "Devrilme"),
    "card_eccentricity": ("Eccentricity", "Dışmerkezlik"),
    "card_bearing": ("Bearing capacity", "Taşıma gücü"),
    "card_tensile": ("Tensile strength", "Çekme dayanımı"),
    "card_pullout": ("Pullout", "Sıyrılma"),
    "card_connection": ("Connection", "Bağlantı"),
    "card_internal_sliding": ("Sliding along a layer", "Tabaka boyunca kayma"),
    "card_length": ("Required length", "Gerekli boy"),
    "card_seismic": ("Earthquake", "Deprem"),
    "card_at_layer": ("layer z = {z:.3f} m", "tabaka z = {z:.3f} m"),
    "card_none": ("none within 4·H", "4·H içinde yok"),
    "card_length_sub": ("uniform; rule ≥ {rule:.2f} m", "eşit boy; kural ≥ {rule:.2f} m"),
    "card_seismic_sub": ("{n} of {total} checks hold", "{total} kontrolün {n} tanesi sağlanıyor"),

    # ------------------------------------------------------------------ results text
    "res_title": ("MSE WALL RESULTS", "DONATILI ZEMİN DUVAR SONUÇLARI"),
    "res_wall": ("Wall: H = {H:.2f} m, d = {d:.2f} m, batter ω = {omega:.1f}°, backslope "
                 "β = {beta:.1f}°, L = {L:.2f} m ({n} layers)",
                 "Duvar: H = {H:.2f} m, d = {d:.2f} m, yüz eğimi ω = {omega:.1f}°, arka şev "
                 "β = {beta:.1f}°, L = {L:.2f} m ({n} tabaka)"),
    "res_design": ("Design method: {design}", "Tasarım yöntemi: {design}"),
    "res_ka": ("Ka retained = {kb:.4f} (δ = β), Ka reinforced = {kr:.4f}, θ = {theta:.1f}°",
               "Ka arka dolgu = {kb:.4f} (δ = β), Ka donatılı dolgu = {kr:.4f}, "
               "θ = {theta:.1f}°"),
    "res_forces": ("Forces per metre: ΣV = {V:.1f} kN, ΣH = {Hf:.1f} kN, M_R = {MR:.1f} kNm, "
                   "M_O = {MO:.1f} kNm, e = {e:.3f} m",
                   "Metre başına kuvvetler: ΣV = {V:.1f} kN, ΣH = {Hf:.1f} kN, "
                   "M_R = {MR:.1f} kNm, M_O = {MO:.1f} kNm, e = {e:.3f} m"),
    "res_external_title": ("External stability", "Dış duraylılık"),
    "res_check_line": ("{name:<26}{value:>12}{required:>12}   {status}",
                       "{name:<26}{value:>12}{required:>12}   {status}"),
    "res_check_head": ("{name:<26}{value:>12}{required:>12}",
                       "{name:<26}{value:>12}{required:>12}"),
    "res_value": ("value", "değer"),
    "res_required": ("required", "gerekli"),
    "res_sliding_plane": ("  sliding {plane}", "  kayma {plane}"),
    "res_bearing_title": ("Bearing capacity of the foundation",
                          "Temel zemininin taşıma gücü"),
    "res_bearing": ("B' = L − 2e = {B:.3f} m, σv = ΣV / B' = {s:.1f} kPa, q_ult = {q:.1f} kPa "
                    "({method})",
                    "B' = L − 2e = {B:.3f} m, σv = ΣV / B' = {s:.1f} kPa, q_ult = {q:.1f} kPa "
                    "({method})"),
    "res_internal_title": ("Internal stability, layer by layer",
                           "İç duraylılık, tabaka tabaka"),
    "res_seismic_title": ("Earthquake (pseudo-static)", "Deprem (psödo-statik)"),
    "res_seismic": ("A = {A:.3f}, Am = {Am:.3f}, PAE = {PAE:.1f} kN/m, PIR = {PIR:.1f} kN/m, "
                    "active zone inertia Pi = {Pi:.1f} kN/m",
                    "A = {A:.3f}, Am = {Am:.3f}, PAE = {PAE:.1f} kN/m, PIR = {PIR:.1f} kN/m, "
                    "aktif bölge ataleti Pi = {Pi:.1f} kN/m"),
    "res_length": ("Required uniform length: L = {L:.2f} m (FHWA minimum {rule:.2f} m)",
                   "Gerekli eşit boy: L = {L:.2f} m (FHWA en küçüğü {rule:.2f} m)"),
    "res_no_length": ("No uniform length up to 4·H satisfies the checks.",
                      "4·H'ye kadar hiçbir eşit boy kontrolleri sağlamıyor."),
    "res_governing": ("Governing layer: z = {z:.3f} m", "Belirleyici tabaka: z = {z:.3f} m"),

    # ------------------------------------------------------------------ check names
    "chk_sliding": ("Sliding", "Kayma"),
    "chk_overturning": ("Overturning", "Devrilme"),
    "chk_eccentricity": ("Eccentricity e [m]", "Dışmerkezlik e [m]"),
    "chk_bearing": ("Bearing capacity", "Taşıma gücü"),
    "chk_tensile": ("Tensile", "Çekme"),
    "chk_pullout": ("Pullout", "Sıyrılma"),
    "chk_connection": ("Connection", "Bağlantı"),
    "chk_internal_sliding": ("Sliding along a layer", "Tabaka boyunca kayma"),
    "value_FS": ("FS", "GS"),
    "factor_inclination": ("Load inclination i", "Yük eğimi i"),
    "factor_ground": ("Ground slope g", "Arazi eğimi g"),
    "value_CDR": ("CDR", "KTO"),

    # ------------------------------------------------------------------ layer table heads
    "head_z": ("z m", "z m"),
    "head_type": ("type", "tür"),
    "head_Sv": ("Sv m", "Sv m"),
    "head_Kr": ("Kr", "Kr"),
    "head_sigma_v": ("σv kPa", "σv kPa"),
    "head_Tmax": ("Tmax kN/m", "Tmax kN/m"),
    "head_Tlt": ("T_al kN/m", "T_al kN/m"),
    "head_La": ("La m", "La m"),
    "head_Le": ("Le m", "Le m"),
    "head_Fstar": ("F*", "F*"),
    "head_Pr": ("Pr kN/m", "Pr kN/m"),
    "head_tensile": ("tensile", "çekme"),
    "head_pullout": ("pullout", "sıyrılma"),
    "head_connection": ("connect.", "bağlantı"),
    "head_sliding": ("sliding", "kayma"),
    "head_Tmd": ("Tmd kN/m", "Tmd kN/m"),
    "head_Ttotal": ("Ttotal kN/m", "Ttoplam kN/m"),
    "head_method": ("Method", "Yöntem"),
    "head_Nc": ("Nc", "Nc"),
    "head_Nq": ("Nq", "Nq"),
    "head_Ng": ("Nγ", "Nγ"),
    "head_qult": ("q_ult kPa", "q_ult kPa"),
    "head_qallow": ("q_all kPa", "q_em kPa"),
    "head_qr": ("φ·q_ult kPa", "φ·q_ult kPa"),
    "head_margin": ("value", "değer"),

    # ------------------------------------------------------------------ figures
    "fig_section": ("Section: the wall, its reinforcement and the forces on it",
                    "Kesit: duvar, donatısı ve etkiyen kuvvetler"),
    "fig_pressure": ("Lateral stress and the tension in the layers",
                     "Yatay gerilme ve tabakalardaki çekme kuvveti"),
    "fig_internal": ("Internal checks, layer by layer", "İç duraylılık kontrolleri, tabaka tabaka"),
    "fig_pullout": ("Pullout: resistance against tension", "Sıyrılma: direnç ve çekme kuvveti"),
    "fig_external": ("External stability", "Dış duraylılık"),
    "fig_bearing": ("Bearing capacity of the foundation by method",
                    "Yönteme göre temel taşıma gücü"),
    "fig_length": ("External checks against the reinforcement length",
                   "Donatı boyuna göre dış duraylılık kontrolleri"),
    "fig_seismic": ("Earthquake: tension and resistance in the layers",
                    "Deprem: tabakalarda çekme kuvveti ve direnç"),
    "plot_z": ("Height above the base z [m]", "Tabandan yükseklik z [m]"),
    "plot_x": ("Distance from the toe [m]", "Topuktan uzaklık [m]"),
    "plot_y": ("Elevation [m]", "Kot [m]"),
    "plot_force": ("Force per metre [kN/m]", "Metre başına kuvvet [kN/m]"),
    "plot_stress": ("Horizontal stress σH [kPa]", "Yatay gerilme σH [kPa]"),
    "plot_margin": ("Value / required", "Değer / gerekli"),
    "plot_length": ("Reinforcement length L [m]", "Donatı boyu L [m]"),
    "plot_pressure": ("Pressure [kPa]", "Basınç [kPa]"),
    "plot_limit": ("limit", "sınır"),
    "plot_water": ("water table", "su tablası"),
    "plot_failure": ("failure surface", "göçme yüzeyi"),
    "plot_Tmax": ("Tmax", "Tmax"),
    "plot_Tallow": ("allowable T", "izin verilen T"),
    "plot_Pr": ("pullout resistance", "sıyrılma direnci"),
    "plot_sigma_h": ("σH = Kr·σv", "σH = Kr·σv"),
    "plot_Ka": ("Ka·σv", "Ka·σv"),
    "plot_applied": ("applied σv", "uygulanan σv"),
    "plot_ultimate": ("q_ult", "q_ult"),
    "plot_allow": ("q_ult / FS", "q_ult / GS"),
    "plot_resist": ("φ·q_ult", "φ·q_ult"),
    "plot_current": ("current L", "mevcut L"),
    "plot_required": ("required L", "gerekli L"),
    "plot_static": ("static", "statik"),
    "plot_seismic": ("seismic", "deprem"),
    "plot_Ttotal": ("Tmax + Tmd", "Tmax + Tmd"),
    "plot_seismic_weakest": ("seismic, weakest check", "deprem, en zayıf kontrol"),

    # ------------------------------------------------------------------ height study
    "hs_run": ("Run the height study", "Yükseklik çalışmasını başlat"),
    "hs_title": ("HEIGHT STUDY", "YÜKSEKLİK ÇALIŞMASI"),
    "hs_info": ("{n} heights from {lo:.2f} to {hi:.2f} m · {design} · rule: {rule}",
                "{lo:.2f} – {hi:.2f} m arası {n} yükseklik · {design} · kural: {rule}"),
    "hs_ranges": ("Every check holds for H = {spans}; the shaded heights fail.",
                  "Bütün kontroller H = {spans} için sağlanıyor; taralı yüksekliklerde "
                  "sağlanmıyor."),
    "hs_none_ok": ("A check fails at every height of the range.",
                   "Aralığın her yüksekliğinde en az bir kontrol sağlanmıyor."),
    "hs_all_ok": ("Every check holds over the whole range.",
                  "Bütün kontroller tüm aralıkta sağlanıyor."),
    "hs_progress": ("Height {done} of {total}…", "Yükseklik {done} / {total}…"),
    "hs_done": ("Height study finished: {n} heights.", "Yükseklik çalışması bitti: {n} yükseklik."),
    "hs_failed": ("The height study could not start: {e}", "Yükseklik çalışması başlatılamadı: {e}"),
    "hs_no_data": ("Run the height study first.", "Önce yükseklik çalışmasını çalıştırın."),
    "hs_cancelled": ("(stopped early)", "(erken durduruldu)"),
    "hs_export_csv": ("Export CSV", "CSV dışa aktar"),
    "hs_export_xlsx": ("Export XLSX", "XLSX dışa aktar"),
    "hs_col_H": ("H m", "H m"),
    "hs_col_L": ("L m", "L m"),
    "hs_col_n": ("layers", "tabaka"),
    "hs_col_req": ("L req. m", "gerekli L m"),
    "hs_col_status": ("status", "durum"),
    "fig_hs_margins": ("Checks against the wall height", "Duvar yüksekliğine göre kontroller"),
    "fig_hs_length": ("Reinforcement length against the wall height",
                      "Duvar yüksekliğine göre donatı boyu"),
    "plot_H": ("Wall height H [m]", "Duvar yüksekliği H [m]"),
    "plot_rule_L": ("L of the rule", "kuralın L'si"),
    "plot_min_L": ("0.7·H, 2.4 m", "0.7·H, 2.4 m"),

    # ------------------------------------------------------------------ shell texts shared
    "run_analysis_button": ("Analyse the wall", "Duvarı çözümle"),
    "running_analysis": ("Analysing…", "Çözümleniyor…"),
    "analysis_complete": ("Analysis complete.", "Çözümleme tamamlandı."),
    "report_action": ("Export report…", "Raporu dışa aktar…"),
    "report_running": ("Writing the report…", "Rapor yazılıyor…"),
    "warnings_title": ("Warnings", "Uyarılar"),
}

TRANSLATIONS = {
    "en": {key: pair[0] for key, pair in ENTRIES.items()},
    "tr": {key: pair[1] for key, pair in ENTRIES.items()},
}


def t(lang: str, key: str, **params) -> str:
    """One text in one language, formatted; the key itself if it is unknown.

    A parameter that is itself a key of the translations (a soil's name) is
    translated before it is put in.
    """
    table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = table.get(key, key)
    if not params:
        return text
    params = {k: (table.get(v, v) if isinstance(v, str) else v) for k, v in params.items()}
    return text.format(**params)


def warning_text(lang: str, warning) -> str:
    """An engine warning, (key, params), as a sentence."""
    key, params = warning
    return t(lang, key, **params)
