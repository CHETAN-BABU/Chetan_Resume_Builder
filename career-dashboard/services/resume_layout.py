"""Rank registered resume content and measure real two-page content usage."""
from __future__ import annotations
import re
from pathlib import Path
from PIL import Image
from pypdf import PdfReader
from career import tex_escape
from validate_resume import extract_zero_argument_macros, strip_latex_comments

# Related terms aid ordering only; they never create candidate claims.
SIGNALS = {
    'ai': ('agentic', 'genai', 'langgraph', 'generative', 'rag', 'retrieval', 'ai'),
    'analysis': ('python', 'statistics', 'data science', 'machine learning', 'classification', 'modelling', 'modeling'),
    'reporting': ('power bi', 'tableau', 'dashboard', 'reporting', 'visualisation', 'visualization', 'bi'),
    'data': ('sql', 'etl', 'warehouse', 'warehousing', 'snowflake', 'redshift', 'data quality', 'reconciliation'),
    'consulting': ('client', 'stakeholder', 'requirements', 'consulting', 'communication', 'business', 'brd'),
}

def terms(text):
    text = text.casefold()
    return {word for word in re.findall(r'[a-z][a-z0-9+#.-]*', text) if len(word) > 2} - {'and', 'the', 'with', 'for', 'from', 'that', 'this', 'through', 'within', 'across', 'into', 'using', 'data'}


def score(text, job):
    target = job['title'] + ' ' + job['description']
    points = 2 * len(terms(text) & terms(target))
    for values in SIGNALS.values():
        if any(re.search(r'\b' + re.escape(t) + r'\b', target, re.I) for t in values):
            points += sum(3 for t in values if re.search(r'\b' + re.escape(t) + r'\b', text, re.I))
    return points


def ranked_source(source, job, evidence, active):
    """Preserve user wording; expand only recognized template slots with approved facts."""
    registered = {i['id'] for i in active if not i.get('deleted') and i['review_state'] == 'registered'}
    registry = {i['id']: i for i in evidence['claims'] + evidence['projects']}
    changes = []
    def facts(id):
        entry = registry.get(id, {})
        if id not in registered or entry.get('status') in {'hold', 'missing'}:
            return []
        return entry.get('approved_facts', [])
    def bullet(id, text):
        return '  % EVIDENCE: ' + id + '\n  \\item ' + tex_escape(text) + '\n'
    # Only replace the original compressed education paragraph. User-written text stays intact.
    ds_role = bool(re.search(r'\b(ai|genai|data scientist|data science|machine learning)\b', job['title'], re.I))
    pid = extract_zero_argument_macros(source).get('SelectedProjectID')
    capstone = facts('PROJ-MSC-FRAUD')
    match = re.search(r'  % EVIDENCE: PROJ-MSC-FRAUD\n  \\item Capstone work compares[^\n]+\n', source)
    if ds_role and pid != 'PROJ-MSC-FRAUD' and capstone and match:
        # All detail stays inside MSc education and retains limitations alongside methods/results.
        expanded = [
            'MSc capstone: ' + capstone[0] + ' ' + capstone[1],
            capstone[2] + ' ' + capstone[4],
            capstone[3],
        ]
        source = source[:match.start()] + ''.join(bullet('PROJ-MSC-FRAUD', f) for f in expanded) + source[match.end():]
        changes.append('Expanded MSc methods, evaluation and limitations from registered capstone evidence.')
    multivariate = facts('PROJ-FAANG-PCA')
    academic = re.search(r'  % EVIDENCE: PROJ-SECOM-FAULT-DETECTION PROJ-FAANG-PCA PROJ-CLUSTERING-DBSCAN\n  \\item Additional academic work covers[^\n]+\n', source)
    if ds_role and pid != 'PROJ-FAANG-PCA' and len(multivariate) >= 5 and academic:
        detail = 'MSc multivariate analysis: ' + multivariate[0] + ' ' + multivariate[1] + ' ' + multivariate[4]
        source = source[:academic.start()] + bullet('PROJ-FAANG-PCA', detail) + source[academic.end():]
        changes.append('Expanded registered multivariate coursework data-preparation and leakage checks, retaining interpretation limits.')
    training = facts('TRAINING-001')
    if len(training) > 1 and training[1] not in source:
        pattern = r'(  % EVIDENCE: TRAINING-002\n  \\item Progressed to Associate Analyst[^\n]+\n)'
        source, count = re.subn(pattern, lambda m: bullet('TRAINING-001', training[1]) + m[0], source, count=1)
        if count:
            changes.append('Added registered BI lifecycle training detail.')
    # A useful omitted professional baseline; no invented savings or ownership claim.
    recon = facts('PROJ-AZ-RECON')
    if recon and pid != 'PROJ-AZ-RECON':
        baseline = next((f for f in recon if 'six people' in f), None)
        if baseline and tex_escape(baseline) not in source:
            pattern = r'(  % EVIDENCE: PROJ-AZ-RECON\n  \\item Co-developed a five-source[^\n]+\n)'
            source, count = re.subn(pattern, lambda m: m[0] + bullet('PROJ-AZ-RECON', baseline), source, count=1)
            if count:
                changes.append('Added the reported reconciliation-process baseline under AstraZeneca.')
    # Add only the skill claim explicitly tied to the selected registered candidate project.
    conditional_skills = {'PROJ-BLOGBOARD': 'SKILL-AGENTIC-001', 'PROJ-EU-COMPLIANCE-RAG': 'SKILL-GENAI-LOCAL-001', 'PROJ-RAG-CHATBOT': 'SKILL-GENAI-001'}
    skill_id = conditional_skills.get(pid) if ds_role else None
    skill_facts = facts(skill_id) if skill_id else []
    source = re.sub(r'% STUDIO_PROJECT_SKILLS\n% EVIDENCE:[^\n]+\n[^\n]+\n', '', source)
    if skill_facts:
        label = registry[pid]['resume_content']['title']
        text = '; '.join(skill_facts)
        line = '% STUDIO_PROJECT_SKILLS\n% EVIDENCE: ' + pid + ' ' + skill_id + '\n\\textbf{Candidate project (' + tex_escape(label) + '):} ' + tex_escape(text) + '\\\\[2pt]\n'
        source = re.sub(r'\\section\{Technical Skills\}\s*', lambda m: r'\section{Technical Skills}' + '\n' + line + '\n', source, count=1)
        changes.append('Added skills evidenced by the selected candidate project, labelled separately from professional skills.')
    # Rank existing skill phrases without adding JD-only terms.
    macros = extract_zero_argument_macros(source)
    if 'CoreSkills' in macros:
        skills = macros['CoreSkills'].split('; ')
        ordered = sorted(skills, key=lambda s: -score(s, job))
        old = r'\newcommand{\CoreSkills}{' + macros['CoreSkills'] + '}'
        source = source.replace(old, r'\newcommand{\CoreSkills}{' + '; '.join(ordered) + '}', 1)
    # Rank bullet constructs together with their evidence IDs, preserving each professional group.
    def rank_items(match):
        body = match[1]
        chunks = list(re.finditer(r'(?m)^\s*% EVIDENCE: [^\n]+\n\s*\\item [^\n]+\n', body))
        if not chunks or 'SelectedProjectBullet' in body:
            return match[0]
        # Only sort complete standard one-line template constructs; no arbitrary custom LaTeX parsing.
        if re.sub(r'\s+', '', ''.join(c[0] for c in chunks)) != re.sub(r'\s+', '', body):
            return match[0]
        return '\\begin{resumeitems}\n' + ''.join(c[0].lstrip('\n') for c in sorted(chunks, key=lambda c: -score(c[0], job))) + '\\end{resumeitems}'
    exp = re.search(r'\\section\{Professional Experience\}[\s\S]*?(?=\\section\{)', source)
    if exp:
        ordered_exp = re.sub(r'\\begin\{resumeitems\}([\s\S]*?)\\end\{resumeitems\}', rank_items, exp[0])
        source = source[:exp.start()] + ordered_exp + source[exp.end():]
    # Client blocks stay inside the same job and employment dates remain chronological.
    client_pattern = r'(?m)^% EVIDENCE: [^\n]+\n\\clientheading\{[^\n]+\}\n\\begin\{resumeitems\}[\s\S]*?\\end\{resumeitems\}\n'
    clients = list(re.finditer(client_pattern, source))
    if len(clients) == 3 and not source[clients[0].end():clients[1].start()].strip() and not source[clients[1].end():clients[2].start()].strip():
        source = source[:clients[0].start()] + '\n'.join(c[0] for c in sorted(clients, key=lambda c: -score(c[0], job))) + source[clients[-1].end():]
    # The old fixed break is the cause of the unfilled page; let content flow naturally.
    source = source.replace(r'\newpage', '').replace(r'\clearpage', '')
    sections = re.split(r'(?=\\section\{)', source)
    names = [re.match(r'\\section\{([^}]+)\}', s) for s in sections]
    mapping = {m[1]: part for m, part in zip(names, sections) if m}
    required = ['Professional Summary', 'Core Skills', 'Professional Experience', 'Selected Project', 'Education', 'Certifications', 'Technical Skills']
    if set(mapping) != set(required) or source.count(r'\end{document}') != 1:
        raise ValueError('Fill two pages needs the standard seven-section template. Your custom source is saved unchanged; restore a template version first.')
    for name in mapping:
        mapping[name] = mapping[name].replace(r'\end{document}', '').strip() + '\n\n'
    priority = ['Selected Project', 'Professional Experience'] if ds_role and pid in conditional_skills else ['Professional Experience', 'Selected Project']
    order = ['Professional Summary', 'Core Skills', *priority, 'Education', 'Technical Skills', 'Certifications']
    source = sections[0] + ''.join(mapping[name] for name in order) + '\\end{document}\n'
    changes.append('Ranked skills, professional examples and section order against the saved JD; employment chronology is preserved.')
    return source, {'section_order': order, 'changes': changes, 'method': 'Deterministic JD relevance ordering of registered evidence; not an ATS score.'}


def set_density(source, body_pt=11.0, item_sep=5.0):
    # Standard margins, fixed readable font. No stretch-to-fill spacers or fake content.
    source = re.sub(r'% STUDIO_DENSITY_START[\s\S]*?% STUDIO_DENSITY_END\n?', '', source)
    source = re.sub(r'\\documentclass\[[^\]]*\]\{article\}', r'\\documentclass[a4paper,11pt]{article}', source, count=1)
    source = re.sub(r'\\renewcommand\{\\baselinestretch\}\{[^}]+\}', r'\\renewcommand{\\baselinestretch}{1.02}', source, count=1)
    source = re.sub(r'itemsep=[\d.]+pt', 'itemsep=' + str(item_sep) + 'pt', source)
    source = source.replace('\\usepackage{needspace}\n', '')
    source = source.replace('\\Needspace', '\\StudioNeedspace')
    source = source.replace('\\newcommand{\\roleheading}[4]{%', '\\newcommand{\\roleheading}[4]{%\n  \\StudioNeedspace{6\\baselineskip}') if '\\StudioNeedspace{6\\baselineskip}' not in source else source
    source = source.replace('\\newcommand{\\clientheading}[1]{\\textbf', '\\newcommand{\\clientheading}[1]{\\StudioNeedspace{5\\baselineskip}\\textbf')
    config = '% STUDIO_DENSITY_START\n\\DeclareFontShape{T1}{lmr}{m}{n}{<->ec-lmr10}{}\n\\DeclareFontFamily{TS1}{lmr}{}\n\\DeclareFontShape{TS1}{lmr}{m}{n}{<->ts1-lmr10}{}\n\\DeclareFontShape{T1}{lmr}{m}{it}{<->ec-lmri10}{}\n\\newcommand{\\StudioNeedspace}[1]{\\par\\begingroup\\dimen0=#1\\relax\\dimen2=\\pagegoal\\advance\\dimen2 by -\\pagetotal\\ifdim\\dimen0>\\dimen2\\penalty-10000\\fi\\endgroup}\n\\clubpenalty=10000\n\\widowpenalty=10000\n\\interlinepenalty=10000\n\\renewcommand{\\normalsize}{\\fontsize{' + str(body_pt) + 'pt}{' + str(round(body_pt * 1.20, 2)) + 'pt}\\selectfont}\n% STUDIO_DENSITY_END\n'
    return source.replace(r'\begin{document}', config + '\\begin{document}\n\\normalsize', 1).replace('\\normalsize\n\\normalsize', '\\normalsize')


def validate_density(source):
    """Allow exactly the generated readable font block; reject extra overrides."""
    blocks = re.findall(r'% STUDIO_DENSITY_START[\s\S]*?% STUDIO_DENSITY_END\n?', source)
    errors = []
    point = re.search(r'\\fontsize\{([\d.]+)pt\}', blocks[0]) if len(blocks) == 1 else None
    if not point or not 10 <= float(point[1]) <= 12:
        errors.append('Studio requires one generated density block with 10–12pt body text')
    else:
        expected = re.search(r'% STUDIO_DENSITY_START[\s\S]*?% STUDIO_DENSITY_END\n?', set_density(r'\begin{document}', float(point[1])))[0]
        if blocks[0] != expected:
            errors.append('Studio density block differs from the supported readable layout')
    # The approved block alone may define fontsize. Everything else retains legacy prohibitions.
    remaining = source.replace(blocks[0], '') if len(blocks) == 1 else source
    return errors, strip_latex_comments(remaining)


def measure_pages(pdf, pages_dir):
    """Measure ink extent and internal whitespace in the actual rendered pages."""
    reader = PdfReader(str(pdf))
    pages = []
    for index, page in enumerate(reader.pages, 1):
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        with Image.open(Path(pages_dir) / f'page-{index:02d}.png') as image:
            image = image.convert('L')
            # Ignore antialias noise; text/rules are dark. Margins are fixed to the base template.
            dark = image.point(lambda p: 255 if p < 190 else 0)
            box = dark.getbbox()
            scale = height / image.height
            if box:
                top, bottom = box[1] * scale, box[3] * scale
                rows = [y for y in range(box[1], box[3]) if dark.crop((box[0], y, box[2], y + 1)).getbbox()]
                max_gap = max((b - a - 1 for a, b in zip(rows, rows[1:])), default=0) * scale
            else:
                top, bottom, max_gap = height, 0, height
        margin = 0.52 * 72
        fill = max(0, min(1, (bottom - top) / (height - 2 * margin)))
        pages.append({'page': index, 'fill_percent': round(fill * 100, 1), 'bottom_blank_mm': round((height - margin - bottom) * 25.4 / 72, 1), 'largest_internal_gap_mm': round(max_gap * 25.4 / 72, 1), 'a4': abs(width - 595.28) < 2 and abs(height - 841.89) < 2, 'words': len((page.extract_text() or '').split()), 'within_margins': top >= margin - 5 and bottom <= height - margin + 5})
    full = len(pages) == 2 and all(p['fill_percent'] >= 92 and p['bottom_blank_mm'] <= 16 and p['largest_internal_gap_mm'] <= 12 and p['a4'] and p['within_margins'] for p in pages)
    return {'full_two_pages': full, 'pages': pages, 'target_fill_percent': 92, 'normal_margins_mm': 13.2}
