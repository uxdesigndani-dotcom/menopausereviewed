#!/usr/bin/env python3
"""
Optimization pass for menopausereviewed.com articles:
1. Inject "Related reading" cross-link section before </article>
2. Add FAQ schema to high-intent articles for Google rich results
"""
import re
import os
import json

ARTICLES_DIR = "articles"

# Map of article slug -> list of related articles to link to
# Each related is (slug, title, dek)
RELATED = {
    "hot-flashes-explained": [
        ("sleep-menopause-insomnia", "Why insomnia hits hardest at 3 AM", "Cortisol, GABA, and the evidence on CBT-I and MHT for menopausal sleep."),
        ("hrt-vs-bioidentical-hormones", "HRT vs. bioidentical hormones", "What the WHI got wrong and what NAMS 2022 changed."),
        ("menopause-supplements-evidence", "The menopause supplement guide", "Black cohosh, soy, evening primrose — graded against the literature."),
    ],
    "sleep-menopause-insomnia": [
        ("hot-flashes-explained", "Hot flashes, decoded", "The neuroscience behind vasomotor symptoms and what fezolinetant changed."),
        ("perimenopause-brain-fog", "The brain fog survival guide", "Why cognitive symptoms compound when sleep is fragmented."),
        ("hrt-vs-bioidentical-hormones", "HRT vs. bioidentical hormones", "MHT's effects on sleep architecture and progesterone's role."),
    ],
    "perimenopause-brain-fog": [
        ("sleep-menopause-insomnia", "Why insomnia hits hardest at 3 AM", "Sleep fragmentation is one of the biggest drivers of cognitive symptoms."),
        ("34-symptoms-perimenopause", "The 34 symptoms most doctors miss", "Brain fog in the context of the full perimenopause picture."),
        ("menopause-supplements-evidence", "The menopause supplement guide", "Magnesium, omega-3, B12 — what the evidence actually supports."),
    ],
    "genitourinary-syndrome-menopause": [
        ("hrt-vs-bioidentical-hormones", "HRT vs. bioidentical hormones", "Why vaginal estrogen is the safest hormonal therapy on the market."),
        ("34-symptoms-perimenopause", "The 34 symptoms most doctors miss", "GSM in the context of the full perimenopause symptom map."),
        ("hot-flashes-explained", "Hot flashes, decoded", "The other vasomotor symptom that gets more clinical attention than GSM."),
    ],
    "bone-density-menopause": [
        ("menopause-supplements-evidence", "The menopause supplement guide", "Why supplemental calcium may not do what you think — and what does."),
        ("hrt-vs-bioidentical-hormones", "HRT vs. bioidentical hormones", "MHT remains first-line for bone protection in symptomatic women."),
        ("peptides-for-menopause", "Peptides for menopause", "Where BPC-157 research stands — and the gap between preclinical and human."),
    ],
    "menopause-supplements-evidence": [
        ("hot-flashes-explained", "Hot flashes, decoded", "What actually reduces vasomotor symptoms when supplements fall short."),
        ("bone-density-menopause", "Bone density after menopause", "Why calcium supplementation is more complicated than the bottle suggests."),
        ("peptides-for-menopause", "Peptides for menopause", "When women look past supplements — what the peptide evidence shows."),
    ],
    "34-symptoms-perimenopause": [
        ("hot-flashes-explained", "Hot flashes, decoded", "The neuroscience behind the most-discussed symptom."),
        ("sleep-menopause-insomnia", "Why insomnia hits hardest at 3 AM", "Sleep disruption is the symptom most under-treated."),
        ("genitourinary-syndrome-menopause", "GSM: vaginal and urinary health after 40", "The 50–70% of women whose symptoms go unaddressed."),
    ],
    "hrt-vs-bioidentical-hormones": [
        ("hot-flashes-explained", "Hot flashes, decoded", "How HRT compares to the new NK3R antagonist fezolinetant."),
        ("bone-density-menopause", "Bone density after menopause", "Where MHT fits in fracture prevention."),
        ("genitourinary-syndrome-menopause", "GSM: vaginal and urinary health after 40", "Why vaginal estrogen sits in its own safety category."),
    ],
    "peptides-for-menopause": [
        ("menopause-supplements-evidence", "The menopause supplement guide", "What evidence-based supplementation looks like before considering peptides."),
        ("bone-density-menopause", "Bone density after menopause", "Where BPC-157 sits in the bone-tendon research."),
        ("hrt-vs-bioidentical-hormones", "HRT vs. bioidentical hormones", "The first-line evidence base most women haven't fully explored yet."),
    ],
}

# FAQ schema for high-intent articles (questions Google rewards with rich results)
FAQ_SCHEMA = {
    "hot-flashes-explained": [
        {"q": "What causes hot flashes during menopause?",
         "a": "Hot flashes are driven by KNDy neurons in the hypothalamus. As estrogen declines, these neurons become hyperactive and signal through the neurokinin-3 receptor pathway, narrowing the thermoneutral zone and triggering vasodilation and sweating. Fezolinetant, approved by the FDA in 2023, works by blocking this receptor."},
        {"q": "How long do hot flashes typically last?",
         "a": "The SWAN study (JAMA Internal Medicine, 2015) found a median duration of 7.4 years, with 25% of women experiencing hot flashes for 10 years or more. Roughly 40% of women in their 60s remain symptomatic."},
        {"q": "What is the most effective treatment for hot flashes?",
         "a": "Menopausal hormone therapy (MHT) remains the most effective treatment, reducing frequency by 75–90%. For women who cannot take hormones, fezolinetant (Veozah) and SSRIs/SNRIs like paroxetine (Brisdelle) are FDA-approved non-hormonal alternatives with moderate efficacy."},
        {"q": "Does black cohosh work for hot flashes?",
         "a": "The 2012 Cochrane review found insufficient evidence that black cohosh outperforms placebo (P=0.79). The NIH LiverTox database has logged over 50 cases of liver injury associated with its use."},
    ],
    "menopause-supplements-evidence": [
        {"q": "Which menopause supplements actually have evidence behind them?",
         "a": "Vitamin D (when deficient), magnesium glycinate (for sleep latency), omega-3 EPA/DHA (cardiovascular and mood), and probiotics with L. crispatus (for vaginal/UTI prevention) have the strongest evidence. Black cohosh, evening primrose oil, and maca have minimal to no evidence above placebo."},
        {"q": "Are menopause supplements regulated?",
         "a": "No. The FDA does not pre-approve supplements for safety or efficacy. A 2015 New York Attorney General investigation found that many major retailers' herbal supplements did not contain the ingredients listed. Look for third-party certifications like USP or NSF."},
        {"q": "Does soy help with hot flashes?",
         "a": "Evidence is population-dependent. Soy isoflavones show modest benefit in Asian populations and in women who are 'equol producers' — about 30% of Westerners and 50% of East Asians. For the rest, evidence is weak."},
        {"q": "Should I take calcium for bone health during menopause?",
         "a": "Meta-analyses by Bolland et al. (BMJ 2015) found that calcium supplementation alone does not reduce fracture risk and may carry cardiovascular concerns. Dietary calcium plus resistance training and vitamin D when deficient have stronger evidence than calcium pills."},
    ],
    "sleep-menopause-insomnia": [
        {"q": "Why do menopausal women wake up at 3 AM?",
         "a": "3 AM corresponds to the body's circadian cortisol nadir followed by a steep rise. In menopause, declining estradiol disrupts GABA signaling and increases HPA-axis reactivity, while progesterone's neurosteroid metabolite allopregnanolone — which has natural anxiolytic effects — also drops. Together this leaves women uniquely vulnerable to early-morning awakening."},
        {"q": "What is the most effective treatment for menopausal insomnia?",
         "a": "Cognitive behavioral therapy for insomnia (CBT-I) is the gold standard, with RCTs (McCurry et al., JAMA Internal Medicine; Kalmbach et al., Sleep) showing it outperforms medication long-term. For women with vasomotor-driven awakening, MHT addresses the underlying mechanism."},
        {"q": "Does melatonin help with menopausal insomnia?",
         "a": "A 2026 Frontiers in Nutrition meta-analysis found melatonin's effect on menopausal sleep is inconclusive. It may help with sleep onset latency at low doses (0.3–1mg) but does not reliably address middle-of-night awakening, which is the dominant pattern in menopause."},
    ],
    "perimenopause-brain-fog": [
        {"q": "Is perimenopause brain fog permanent?",
         "a": "No. The Greendale et al. SWAN study (Neurology 2009, n=2,362) found that cognitive performance — particularly verbal memory and processing speed — dips transiently during the menopause transition but returns to baseline after final menstrual period. Approximately 11–13% of women show clinically significant impairment."},
        {"q": "Does HRT prevent menopause brain fog?",
         "a": "The KEEPS-Cog (2019) and ELITE-Cog (2016) trials found no cognitive benefit from MHT in healthy menopausal women. MHT is not currently indicated for cognitive symptoms alone, though it may help indirectly by improving sleep and reducing hot flashes."},
        {"q": "What helps with menopause brain fog?",
         "a": "The strongest evidence is for sleep optimization (CBT-I), regular aerobic and resistance exercise, screening and correcting iron and B12 deficiencies, and omega-3 EPA/DHA. Cognitive symptoms also improve as vasomotor symptoms resolve."},
    ],
    "bone-density-menopause": [
        {"q": "Does taking calcium prevent osteoporosis?",
         "a": "Meta-analyses by Bolland et al. (BMJ 2015) found supplemental calcium alone does not reduce fracture risk and may increase cardiovascular event risk. Dietary calcium, vitamin D when deficient, and especially resistance training (LIFTMOR trial 2018) have stronger evidence."},
        {"q": "How fast does bone loss happen during menopause?",
         "a": "The SWAN bone substudy (Greendale et al. 2012) showed bone loss accelerates 1–2 years before the final menstrual period and peaks at approximately 2% per year for roughly 3 years post-FMP."},
        {"q": "When should I get a bone density scan?",
         "a": "USPSTF 2025 guidance recommends DEXA screening for all women age 65+, and earlier with risk factors (low body weight, family history of fracture, smoking, glucocorticoid use, certain medical conditions). The FRAX tool can estimate 10-year fracture probability."},
    ],
}


def build_related_section(slug):
    related = RELATED.get(slug, [])
    if not related:
        return ""
    cards = ""
    for r_slug, r_title, r_dek in related:
        cards += f'''
          <a class="related-card" href="/articles/{r_slug}">
            <h3 class="related-card__title">{r_title}</h3>
            <p class="related-card__dek">{r_dek}</p>
          </a>'''
    return f'''
      <section class="related-reading">
        <div class="container">
          <p class="related-reading__eyebrow">Related reading</p>
          <h2 class="related-reading__title">Continue exploring.</h2>
          <div class="related-reading__grid">{cards}
          </div>
        </div>
      </section>'''


def build_faq_schema(slug):
    faqs = FAQ_SCHEMA.get(slug)
    if not faqs:
        return ""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["q"],
                "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}
            } for faq in faqs
        ]
    }
    return f'    <script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n    </script>\n'


def optimize_article(filepath):
    slug = os.path.basename(filepath).replace(".html", "")
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Strip existing related section if rerun
    html = re.sub(r'\n\s*<section class="related-reading">.*?</section>\n', '\n', html, flags=re.DOTALL)
    # Strip existing FAQ schema if rerun
    html = re.sub(r'\s*<script type="application/ld\+json">\s*\{\s*"@context"[^<]*?"@type":\s*"FAQPage".*?</script>\n?', '', html, flags=re.DOTALL)

    # 1. Inject related reading section AFTER </article>, BEFORE </main>
    related = build_related_section(slug)
    if related and "</article>\n    </main>" in html:
        html = html.replace("</article>\n    </main>", f"</article>{related}\n    </main>")

    # 2. Inject FAQ schema BEFORE </head>
    faq = build_faq_schema(slug)
    if faq and "</head>" in html:
        html = html.replace("</head>", f"{faq}  </head>")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return bool(related), bool(faq)


if __name__ == "__main__":
    results = []
    for f in sorted(os.listdir(ARTICLES_DIR)):
        if f.endswith(".html"):
            path = os.path.join(ARTICLES_DIR, f)
            related_added, faq_added = optimize_article(path)
            results.append((f, related_added, faq_added))
    print(f"{'Article':<45} {'Related':<10} {'FAQ':<5}")
    print("-" * 60)
    for f, r, faq in results:
        print(f"{f:<45} {'✓' if r else '-':<10} {'✓' if faq else '-':<5}")
