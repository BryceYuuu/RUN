"""生成 GitHub 风格的富 Markdown 页面与 SVG 图表。

输入：
  data/programmes.json        99 条路线的结构化记录（门槛、家属、永居、官方来源）
  data/letsmigrate_guides.json LetsMigrate 指南索引
  data/changes.json           2025–2026 规则变化
  src/details/<国家>.json      每条路线的细节（概述、关键数字、适合/不适合、流程、材料、注意）
  src/notes/<国家>.md          每个国家的深度解读正文
输出：
  docs/europe/*.md、assets/charts/*.svg，以及 README.md / docs/routes/*.md 中 <!-- AUTO:xxx --> 区块
用法：python3 scripts/build_docs.py
"""
import json, os, re
from urllib.parse import quote

RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES = os.path.join(RUN, 'src', 'notes')
GUIDES = json.load(open(os.path.join(RUN, 'data', 'letsmigrate_guides.json')))
progs = json.load(open(os.path.join(RUN, 'data', 'programmes.json')))
CHANGES = json.load(open(os.path.join(RUN, 'data', 'changes.json')))
DETAILS = {}
for _f in sorted(os.listdir(os.path.join(RUN, 'src', 'details'))):
    if _f.endswith('.json'):
        for _k, _v in json.load(open(os.path.join(RUN, 'src', 'details', _f))).items():
            for _key in ('fit', 'unfit', 'docs', 'tips'):
                if _key in _v:
                    _v[_key] = [x for x in _v[_key] if x.strip()]
                    if not _v[_key]:
                        del _v[_key]
            DETAILS[_k] = _v

META = {  # slug: (中文名, English, flag, 欧盟, 申根, 货币)
    'albania': ('阿尔巴尼亚', 'Albania', '🇦🇱', '否（入盟候选国）', '否', 'ALL 列克'),
    'andorra': ('安道尔', 'Andorra', '🇦🇩', '否', '否', 'EUR'),
    'austria': ('奥地利', 'Austria', '🇦🇹', '是', '是', 'EUR'),
    'belgium': ('比利时', 'Belgium', '🇧🇪', '是', '是', 'EUR'),
    'bulgaria': ('保加利亚', 'Bulgaria', '🇧🇬', '是', '是（2025 起完整加入）', 'EUR（2026 起）'),
    'croatia': ('克罗地亚', 'Croatia', '🇭🇷', '是', '是', 'EUR'),
    'cyprus': ('塞浦路斯', 'Cyprus', '🇨🇾', '是', '部分（内部边检未取消）', 'EUR'),
    'czechia': ('捷克', 'Czechia', '🇨🇿', '是', '是', 'CZK 克朗'),
    'denmark': ('丹麦', 'Denmark', '🇩🇰', '是', '是', 'DKK 克朗'),
    'estonia': ('爱沙尼亚', 'Estonia', '🇪🇪', '是', '是', 'EUR'),
    'finland': ('芬兰', 'Finland', '🇫🇮', '是', '是', 'EUR'),
    'france': ('法国', 'France', '🇫🇷', '是', '是', 'EUR'),
    'germany': ('德国', 'Germany', '🇩🇪', '是', '是', 'EUR'),
    'greece': ('希腊', 'Greece', '🇬🇷', '是', '是', 'EUR'),
    'hungary': ('匈牙利', 'Hungary', '🇭🇺', '是', '是', 'HUF 福林'),
    'iceland': ('冰岛', 'Iceland', '🇮🇸', '否（EEA）', '是', 'ISK 克朗'),
    'ireland': ('爱尔兰', 'Ireland', '🇮🇪', '是', '否', 'EUR'),
    'italy': ('意大利', 'Italy', '🇮🇹', '是', '是', 'EUR'),
    'latvia': ('拉脱维亚', 'Latvia', '🇱🇻', '是', '是', 'EUR'),
    'liechtenstein': ('列支敦士登', 'Liechtenstein', '🇱🇮', '否（EEA）', '是', 'CHF 瑞郎'),
    'lithuania': ('立陶宛', 'Lithuania', '🇱🇹', '是', '是', 'EUR'),
    'luxembourg': ('卢森堡', 'Luxembourg', '🇱🇺', '是', '是', 'EUR'),
    'malta': ('马耳他', 'Malta', '🇲🇹', '是', '是', 'EUR'),
    'montenegro': ('黑山', 'Montenegro', '🇲🇪', '否（入盟候选国）', '否', 'EUR'),
    'netherlands': ('荷兰', 'Netherlands', '🇳🇱', '是', '是', 'EUR'),
    'norway': ('挪威', 'Norway', '🇳🇴', '否（EEA）', '是', 'NOK 克朗'),
    'poland': ('波兰', 'Poland', '🇵🇱', '是', '是', 'PLN 兹罗提'),
    'portugal': ('葡萄牙', 'Portugal', '🇵🇹', '是', '是', 'EUR'),
    'romania': ('罗马尼亚', 'Romania', '🇷🇴', '是', '是（2025 起完整加入）', 'RON 列伊'),
    'slovakia': ('斯洛伐克', 'Slovakia', '🇸🇰', '是', '是', 'EUR'),
    'slovenia': ('斯洛文尼亚', 'Slovenia', '🇸🇮', '是', '是', 'EUR'),
    'spain': ('西班牙', 'Spain', '🇪🇸', '是', '是', 'EUR'),
    'sweden': ('瑞典', 'Sweden', '🇸🇪', '是', '是', 'SEK 克朗'),
    'switzerland': ('瑞士', 'Switzerland', '🇨🇭', '否（EFTA）', '是', 'CHF 瑞郎'),
    'turkiye': ('土耳其', 'Türkiye', '🇹🇷', '否', '否', 'TRY 里拉'),
    'united-kingdom': ('英国', 'United Kingdom', '🇬🇧', '否', '否', 'GBP 英镑'),
}
TAGLINE = {
    'albania': '数字游民许可门槛极低（月入约 EUR 330），适合低预算试住',
    'andorra': '被动居留 2026 起涨到 EUR 100 万投资 + 配额，门槛很高',
    'austria': '红白红卡积分制 / 蓝卡 EUR 55,678，21 个月转 Plus 卡',
    'belgium': '工作许可按大区审批，四个大区门槛各不同',
    'bulgaria': '无数字游民签证；蓝卡 + StartUp Visa 证书，税率 10%',
    'croatia': '数字游民最长 18 个月、境外收入免税，但不能续成长期身份',
    'cyprus': '30 万欧投资永居约 2 个月获批；数字游民名额 500',
    'czechia': '员工卡门槛低；数字游民计划不含中国大陆护照',
    'denmark': '不签蓝卡，走 Pay Limit（DKK 55.2 万/年）等本国路线',
    'estonia': '数字游民是 D 签证非居留；就业许可最长 5 年',
    'finland': '专家许可与蓝卡同为 EUR 3,937/月，快速通道 2 周',
    'france': '人才护照员工类年薪 EUR 39,582 即可，首卡最长 4 年',
    'germany': '蓝卡 EUR 50,700（IT 无学历可办），最快 21 个月永居',
    'greece': '黄金签证 40/80 万欧买房；数字游民 EUR 3,500/月',
    'hungary': '25 万欧基金换 10+10 年居留可工作；白卡不能带家属',
    'iceland': '旧远程工作签证已废止，目前无可用数字游民路线',
    'ireland': '不签蓝卡；Critical Skills EUR 40,904 起，英语国家',
    'italy': '数字游民须高技能；投资者签证 25 万欧起（非房产）',
    'latvia': '2026 新法关闭买房居留；蓝卡门槛 EUR 2,723/月',
    'liechtenstein': '配额 + 抽签，第三国国民几乎不可行',
    'lithuania': '2024 起工作必须本国居留；Startup Visa 免资本要求',
    'luxembourg': '蓝卡 EUR 65,652 但首卡 4 年；自雇许可 3 年',
    'malta': 'MPRP 永居约 11–47 万欧；数字游民最长 4 年',
    'montenegro': '非申根；数字游民 2+2 年最友好；投资入籍已关闭',
    'netherlands': '高技术移民 30 岁以下 EUR 4,357/月，需认可雇主',
    'norway': '技术自雇许可禁止远程工作；3 年可申请永居',
    'poland': '工作许可门槛低；2026-04 起全部 MOS 线上递交',
    'portugal': '数字游民 EUR 3,680/月；黄金签证不能买房；入籍改为 10 年',
    'romania': '数字游民门槛最高之一（约 EUR 5,500/月）；蓝卡门槛低',
    'slovakia': '蓝卡门槛全欧最低之一 EUR 1,944/月，首卡 5 年',
    'slovenia': '数字游民 2025 新开、家属可立即团聚；蓝卡 1 倍平均工资',
    'spain': '数字游民 EUR 2,442/月起；黄金签证 2025 年已关闭',
    'sweden': '2026 起工作许可须达中位工资 90%（SEK 34,470/月）',
    'switzerland': '第三国国民配额 + 优先本地，基本只适合高端人才',
    'turkiye': 'USD 40 万买房可申请入籍（非欧盟护照）',
    'united-kingdom': '投资移民已关闭；永居拟从 5 年改为 10 年',
}
ROUTE = {'digital-nomad': '数字游民', 'work': '技术工作', 'startup': '创业', 'self-employed': '自雇',
         'passive': '被动收入居留', 'residence-by-investment': '投资居留', 'citizenship': '入籍', 'other': '替代路线'}
ROUTE_ICON = {'digital-nomad': '💻', 'work': '🧑‍💻', 'startup': '🚀', 'self-employed': '🧾', 'passive': '🏖️',
              'residence-by-investment': '💰', 'citizenship': '🛂', 'other': '🧩'}
ROUTE_COLOR = {'digital-nomad': '1d4ed8', 'work': '0f766e', 'startup': '6d28d9', 'self-employed': '6d28d9',
               'passive': '0e7490', 'residence-by-investment': 'b45309', 'citizenship': 'b45309', 'other': '667085'}
ORDER = ['digital-nomad', 'work', 'startup', 'self-employed', 'passive', 'residence-by-investment', 'citizenship', 'other']
PROFILES = json.load(open(os.path.join(RUN, 'data', 'country_profiles.json')))

# RUN 补充路线（LetsMigrate 未收录）：合并进 progs / DETAILS，统一参与表格和图表
EXTRA_META = {  # id: (threshold, family, pr)
    'spain-non-lucrative-visa': ('EUR 2,400 monthly', '支持家庭成员', '可能通向永居'),
    'portugal-d7-visa': ('EUR 920 monthly', '支持家庭成员', '可能通向永居'),
    'germany-opportunity-card': ('', '家庭规则需核查', '通常偏临时'),
    'germany-skilled-worker-18a-18b': ('', '支持家庭成员', '可能通向永居'),
    'greece-fip': ('EUR 3,500 monthly', '支持家庭成员', '可能通向永居'),
    'italy-elective-residence': ('EUR 31,160 annual', '支持家庭成员', '可能通向永居'),
    'malta-global-residence-programme': ('275,000+', '支持家庭成员', '通常偏临时'),
    'estonia-startup-visa': ('', '支持家庭成员', '可能通向永居'),
    'uk-skilled-worker': ('GBP 41,700 annual', '支持家庭成员', '可能通向永居'),
    'uk-global-talent': ('', '支持家庭成员', '可能通向永居'),
    'uk-hpi': ('', '支持家庭成员', '通常偏临时'),
}
for _c, _rs in json.load(open(os.path.join(RUN, 'src', 'extra_routes.json'))).items():
    for _r in _rs:
        _t, _f, _p = EXTRA_META[_r['id']]
        progs.append({'country': '', 'country_slug': _c, 'programme': _r['name'], 'slug': _r['id'], 'route_type': _r['type'],
                      'audience': '', 'family': _f, 'pr': _p, 'threshold': _t, 'verified': '2026-10', 'letsmigrate': '',
                      'status': 'open', 'extra': True, 'sources': [{'title': a, 'url': b} for a, b in _r.get('sources', [])]})
        DETAILS[_r['id']] = {k: v for k, v in _r.items() if k in ('summary', 'facts', 'fit', 'unfit', 'steps', 'docs', 'tips')}
CLOSED = {p['slug'] for p in progs if p.get('status') == 'closed'}
FX = {'EUR': 1, 'CZK': 0.04, 'DKK': 0.134, 'HUF': 0.00253, 'ISK': 0.0072, 'NOK': 0.086,
      'PLN': 0.234, 'RON': 0.2, 'SEK': 0.088, 'ALL': 0.0103, 'GBP': 1.17}


# ---------- helpers ----------
def badge(label, msg, color):
    enc = lambda s: quote(str(s).replace('-', '--').replace('_', '__').replace(' ', ' '), safe='')
    return f'![{label}](https://img.shields.io/badge/{enc(label)}-{enc(msg)}-{color})'


def yesno_color(v):
    return '2ea44f' if v.startswith('是') else ('dbab09' if v.startswith('部分') else '8b949e')


def fmt_threshold(t):
    if not t:
        return '—'
    out = []
    for part in t.split(' · '):
        m = re.match(r'([A-Z]{3}) ([\d,.]+) (monthly|annual)$', part)
        if m:
            out.append(f"{m.group(1)} {m.group(2)}/{'月' if m.group(3) == 'monthly' else '年'}")
            continue
        m = re.match(r'([\d,]+)\+$', part)
        out.append(f'投资 ≥ {m.group(1)}' if m else part)
    return '；'.join(out)


def income_eur(t):
    for part in (t or '').split(' · '):
        m = re.match(r'([A-Z]{3}) ([\d,.]+) (monthly|annual)$', part)
        if m:
            v = float(m.group(2).replace(',', '')) * FX.get(m.group(1), 1)
            return v / 12 if m.group(3) == 'annual' else v
    return None


def fam(p):
    return {'支持家庭成员': '✅ 可带', '家庭规则需核查': '⚠️ 需核查'}.get(p['family'], '—')


def pr(p):
    return {'可能通向永居': '✅ 可能', '通常偏临时': '⏳ 偏临时'}.get(p['pr'], '—')


def status(p):
    return '⛔ 已关闭' if p['slug'] in CLOSED else '🟢 开放'


def short_name(p, cname):
    n = p['programme']
    return n[len(cname):].strip() if n.startswith(cname) and len(n) > len(cname) else n


def mermaid_steps(steps):
    def clean(s):
        return re.sub(r'["\[\](){}<>|#;]', ' ', s).strip()
    nodes = [f'  s{i}["{"①②③④⑤⑥⑦⑧⑨⑩"[i]} {clean(t)}"]' for i, (t, _) in enumerate(steps[:10])]
    links = ' --> '.join(f's{i}' for i in range(len(nodes)))
    return '```mermaid\nflowchart LR\n' + '\n'.join(nodes) + '\n  ' + links + '\n```'


def facts_table(facts, cols=3):
    cells = [f'<sub>{k}</sub><br><b>{v}</b>' for k, v in facts]
    rows = []
    for i in range(0, len(cells), cols):
        chunk = cells[i:i + cols] + [''] * (cols - len(cells[i:i + cols]))
        rows.append('<tr>' + ''.join(f'<td width="{100 // cols}%" valign="top">{c}</td>' for c in chunk) + '</tr>')
    return '<table>\n' + '\n'.join(rows) + '\n</table>'


def md_inline(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)


# ---------- country page ----------
def stars(v, lo, hi, reverse=False):
    if v is None:
        return ''
    x = (v - lo) / (hi - lo)
    x = 1 - x if reverse else x
    n = max(1, min(5, round(x * 4) + 1))
    return ' ' + '●' * n + '○' * (5 - n)


def profile_block(slug):
    pf = PROFILES.get(slug)
    if not pf:
        return []
    fmt = lambda v, f='{}': '—' if v is None else f.format(v)
    facts = [
        ['💶 生活成本指数（纽约=100）', fmt(pf['col']) + stars(pf['col'], 35, 110, True) if pf['col'] else '—'],
        ['🏠 房租指数（纽约=100）', fmt(pf['rent']) + stars(pf['rent'], 10, 50, True) if pf['rent'] else '—'],
        ['🛡️ 安全指数', fmt(pf['safety']) + stars(pf['safety'], 40, 85) if pf['safety'] else '—'],
        ['💼 平均年薪（总额）', fmt(pf['salary'], 'EUR {:,}')],
        ['🧾 最高个税税率', fmt(pf['tax'], '{}%')],
        ['🛂 护照免签目的地', fmt(pf['passport'], '{} 个（中国 81）')],
        ['🏠 永居年限', pf['pr']], ['🎖️ 入籍年限', pf['cit']],
        ['🔁 双重国籍', {'✅': '✅ 可保留原国籍', '⚠️': '⚠️ 有条件', '❌': '❌ 一般须放弃'}[pf['dual']]],
        ['🗣️ 语言要求', pf['lang']], ['✈️ 中国护照入境', pf['entry']],
    ]
    return ['## 🏙️ 生活与身份档案', '', facts_table(facts), '',
            '<sub>● 越多越好（成本/房租越低、安全越高）。数据：Numbeo 2026 年中、Eurostat、Tax Foundation 2026、Henley 2026；'
            '永居/入籍为常见规则，以官方为准。中国不承认双重国籍。[数据说明](README.md#profiles)</sub>', '']


def programme_section(p, cname):
    d = DETAILS.get(p['slug'], {})
    icon = ROUTE_ICON.get(p['route_type'], '•')
    L = [f'<a id="{p["slug"]}"></a>', '', f'## {icon} {p["programme"]}', '',
         ' '.join([badge('类型', ROUTE[p['route_type']], ROUTE_COLOR[p['route_type']]),
                   badge('状态', '已关闭' if p['slug'] in CLOSED else '开放', 'cf222e' if p['slug'] in CLOSED else '2ea44f'),
                   badge('家属', {'支持家庭成员': '可带', '家庭规则需核查': '需核查'}.get(p['family'], '—'), '0969da' if p['family'] == '支持家庭成员' else '8b949e'),
                   badge('永居', {'可能通向永居': '可能', '通常偏临时': '偏临时'}.get(p['pr'], '—'), '0969da' if p['pr'] == '可能通向永居' else '8b949e')]
                  + ([badge('来源', 'RUN 补充', 'e36209')] if p.get('extra') else [])),
         '']
    if d.get('summary'):
        L += [f'> **{d["summary"]}**', '']
    facts = d.get('facts') or [['门槛信号', fmt_threshold(p['threshold'])], ['适合', p['audience'] or '—']]
    L += [facts_table(facts), '']
    if d.get('fit') or d.get('unfit'):
        li = lambda xs: ''.join(f'<li>{md_inline(x)}</li>' for x in xs)
        L += ['<table><tr>',
              f'<td width="50%" valign="top">✅ <b>适合</b><ul>{li(d.get("fit", []))}</ul></td>',
              f'<td width="50%" valign="top">❌ <b>不适合</b><ul>{li(d.get("unfit", []))}</ul></td>',
              '</tr></table>', '']
    if d.get('steps'):
        L += ['### 🗺️ 申请流程', '', mermaid_steps(d['steps']), '']
        L += [f'{i}. **{t}**' + (f' — {s}' if s else '') for i, (t, s) in enumerate(d['steps'], 1)]
        L.append('')
    if d.get('docs'):
        L += ['### 📋 材料清单', ''] + [f'- [ ] {x}' for x in d['docs']] + ['']
    if d.get('tips'):
        L += ['> [!WARNING]', '> **注意**'] + [f'> - {x}' for x in d['tips']] + ['']
    if p['sources']:
        L += [f'<details><summary>🔗 {"来源" if p.get("extra") else "官方来源"}（{len(p["sources"])}）</summary>', '']
        L += [f'- [{s["title"] or s["url"]}]({s["url"]})' for s in p['sources']]
        L += ['', '</details>', '']
    src = '本条为 RUN 补充路线（LetsMigrate 未收录），来源见上' if p.get('extra') else f'[LetsMigrate 原始记录]({p["letsmigrate"]})'
    L += [f'<sub>数据核查：{p["verified"] or "—"} · {src} · [↑ 回到顶部](#top)</sub>', '', '---', '']
    return '\n'.join(L)


def country_page(slug, prev_slug, next_slug):
    name, en, flag, eu, sch, cur = META[slug]
    ps = sorted([p for p in progs if p['country_slug'] == slug],
                key=lambda p: (p['slug'] in CLOSED, ORDER.index(p['route_type'])))
    ver = max((p['verified'] for p in ps if p['verified']), default='')
    notes = open(os.path.join(NOTES, slug + '.md')).read().strip()
    m = re.search(r'## 一句话判断\s*\n\s*\n(.+?)\n', notes)
    one = m.group(1).strip() if m else TAGLINE[slug]
    deep = re.sub(r'^## 一句话判断\s*\n\s*\n.+?\n', '', notes, flags=re.S).strip()
    deep = re.sub(r'^## ', '### ', deep, flags=re.M)
    nav = ' · '.join([f'[{ROUTE_ICON[p["route_type"]]} {short_name(p, name)}](#{p["slug"]})' for p in ps]
                     + ['[📖 深度解读](#deep)', '[🔗 延伸阅读](#more)'])
    L = ['<a id="top"></a>', '', '<div align="center">', '', f'# {flag} {name} · {en}', '',
         ' '.join([badge('欧盟', eu, yesno_color(eu)), badge('申根', sch, yesno_color(sch)),
                   badge('货币', cur, '0969da'), badge('收录路线', len(ps), '6e40c9'), badge('数据核查', ver or '—', '57606a')]),
         '', f'**{TAGLINE[slug]}**', '', nav, '', '</div>', '',
         '> [!TIP]', f'> **一句话判断**：{one}', '']
    L += profile_block(slug)
    if ps:
        L += ['## 📊 路线速查', '', '| 路线 | 类型 | 门槛信号 | 家属 | 永居 | 状态 |', '|---|---|---|:-:|:-:|:-:|']
        for p in ps:
            L.append(f"| [{p['programme']}](#{p['slug']}) | {ROUTE_ICON[p['route_type']]} {ROUTE[p['route_type']]} | "
                     f"{fmt_threshold(p['threshold'])} | {fam(p)} | {pr(p)} | {status(p)} |")
        L += ['', '<sub>门槛为主申请人的最低信号值，多与当地工资挂钩、每年调整，递交前以官方为准。</sub>', '', '---', '']
        L += [programme_section(p, name) for p in ps]
    L += ['<a id="deep"></a>', '', '## 📖 深度解读', '', deep, '', '---', '']
    g = [(t, f'https://letsmigrate.org/zh-hans/articles/{s}/') for s, t in sorted(GUIDES.items())
         if s.startswith('uk-' if slug == 'united-kingdom' else slug + '-')]
    L += ['<a id="more"></a>', '', '## 🔗 延伸阅读', '']
    if g:
        L += [f'<details><summary>LetsMigrate 中文指南原文（{len(g)} 篇）</summary>', '']
        L += [f'- [{t}]({u})' for t, u in g] + ['', '</details>', '']
    pn, nn = META[prev_slug], META[next_slug]
    L += ['<div align="center">', '',
          f'[← {pn[2]} {pn[0]}]({prev_slug}.md) ｜ [🇪🇺 全部国家](README.md) ｜ [🏠 首页](../../README.md) ｜ [{nn[2]} {nn[0]} →]({next_slug}.md)',
          '', '</div>', '',
          f'<sub>本页根据 [LetsMigrate.org](https://letsmigrate.org/zh-hans/countries/{slug}-zh/) 公开资料及官方来源整理改写，'
          '仅供信息参考，不构成移民、法律、税务或投资建议。</sub>', '']
    return '\n'.join(L)


# ---------- index & route tables ----------
def country_grid(prefix='', cols=4):
    slugs = sorted(META, key=lambda s: META[s][1])
    cells = []
    for s in slugs:
        name, en, flag, eu, sch, cur = META[s]
        n = sum(1 for p in progs if p['country_slug'] == s and p['slug'] not in CLOSED)
        tags = ' '.join(sorted({ROUTE_ICON[p['route_type']] for p in progs if p['country_slug'] == s and p['slug'] not in CLOSED}))
        cells.append(f'<a href="{prefix}{s}.md"><b>{flag} {name}</b></a><br><sub>{en} · {n} 条路线 {tags}</sub><br><sub>{TAGLINE[s]}</sub>')
    rows = []
    for i in range(0, len(cells), cols):
        chunk = cells[i:i + cols] + [''] * (cols - len(cells[i:i + cols]))
        rows.append('<tr>' + ''.join(f'<td width="{100 // cols}%" valign="top">{c}</td>' for c in chunk) + '</tr>')
    return '<table>\n' + '\n'.join(rows) + '\n</table>'


def europe_index():
    L = ['<div align="center">', '', '# 🇪🇺 欧洲 36 国', '',
         '每个国家一页：路线速查表 · 关键数字 · 申请流程图 · 材料清单 · 注意事项 · 官方来源', '',
         '[🏠 首页](../../README.md) ｜ [📊 全部路线对比](#compare) ｜ 图例：💻 数字游民 🧑‍💻 技术工作 🚀 创业 🧾 自雇 💰 投资 🛂 入籍 🧩 其他', '',
         '</div>', '', country_grid(), '', '<a id="compare"></a>', '', '## 📊 全部路线对比', '',
         '| 国家 | 路线 | 类型 | 门槛信号 | 折合 €/月 | 家属 | 永居 | 状态 |', '|---|---|---|---|--:|:-:|:-:|:-:|']
    for p in sorted(progs, key=lambda p: (p['slug'] in CLOSED, ORDER.index(p['route_type']), income_eur(p['threshold']) or 9e9)):
        n, _, f, *_ = META[p['country_slug']]
        inc = income_eur(p['threshold'])
        L.append(f"| {f} [{n}]({p['country_slug']}.md) | [{p['programme']}]({p['country_slug']}.md#{p['slug']}) | "
                 f"{ROUTE_ICON[p['route_type']]} {ROUTE[p['route_type']]} | {fmt_threshold(p['threshold'])} | "
                 f"{'{:,.0f}'.format(inc) if inc else '—'} | {fam(p)} | {pr(p)} | {status(p)} |")
    L += ['', '<sub>非欧元货币按 2026 年粗略汇率折合，仅供横向比较。机器可读数据：[programmes.csv](../../data/programmes.csv)</sub>', '']
    L += ['<a id="profiles"></a>', '', '## 🏙️ 生活与身份横向对比', '',
          '<p align="center"><img src="../../assets/charts/cost-of-living.svg" width="760"></p>', '',
          '| 国家 | 生活成本 | 房租 | 安全 | 平均年薪 € | 最高个税 | 护照 | 永居 | 入籍 | 双重国籍 | 中国护照入境 |',
          '|---|--:|--:|--:|--:|--:|--:|---|---|:-:|---|']
    for s_ in sorted(META, key=lambda s_: META[s_][1]):
        pf = PROFILES[s_]
        v = lambda x, f='{}': '—' if x is None else f.format(x)
        L.append(f"| {META[s_][2]} [{META[s_][0]}]({s_}.md) | {v(pf['col'])} | {v(pf['rent'])} | {v(pf['safety'])} | "
                 f"{v(pf['salary'], '{:,}')} | {v(pf['tax'], '{}%')} | {v(pf['passport'])} | {pf['pr']} | {pf['cit']} | {pf['dual']} | {pf['entry']} |")
    m = PROFILES['_meta']
    L += ['', '<details><summary>📐 指标说明与数据来源</summary>', '']
    L += [f'- **{k}**：{m[k]}' for k in ('col', 'rent', 'safety', 'salary', 'tax', 'passport', 'pr', 'cit', 'dual', 'entry')]
    L += [''] + [f'- [{t}]({u})' for t, u in m['sources']] + ['', '</details>', '']
    return '\n'.join(L)


def route_table(types, prefix='../europe/'):
    rows = [p for p in progs if p['route_type'] in types]
    L = ['| 国家 | 路线 | 一句话 | 门槛信号 | 家属 | 永居 | 状态 |', '|---|---|---|---|:-:|:-:|:-:|']
    for p in sorted(rows, key=lambda p: (p['slug'] in CLOSED, income_eur(p['threshold']) or 9e9)):
        n, _, f, *_ = META[p['country_slug']]
        s = DETAILS.get(p['slug'], {}).get('summary', '')
        L.append(f"| {f} {n} | [{p['programme']}]({prefix}{p['country_slug']}.md#{p['slug']}) | {s} | "
                 f"{fmt_threshold(p['threshold'])} | {fam(p)} | {pr(p)} | {status(p)} |")
    return '\n'.join(L)


def changes_table():
    kind = {'closed': '⛔ 关闭', 'tighter': '🔺 收紧', 'new': '🆕 新开', 'info': '🔄 变化'}
    L = ['| 时间 | 国家 | 类型 | 变化 |', '|---|---|:-:|---|']
    for c in CHANGES:
        link = f"docs/europe/{c['slug']}.md" if c.get('slug') else f"docs/global/{c['global']}.md"
        L.append(f"| {c['date']} | {c['flag']} [{c['country']}]({link}) | {kind[c['kind']]} | {c['text']} |")
    return '\n'.join(L)


# ---------- SVG charts ----------
def svg_bars(title, subtitle, rows, unit='€', color='#0f766e'):
    rows = [r for r in rows if r[1]]
    w, lh, top, left, right = 760, 30, 74, 150, 110
    h = top + lh * len(rows) + 24
    mx = max(v for _, v in rows)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Microsoft YaHei,Segoe UI,sans-serif">',
           f'<rect width="{w}" height="{h}" rx="14" fill="#ffffff" stroke="#e4e7ec"/>',
           f'<text x="24" y="36" font-size="19" font-weight="700" fill="#1d2433">{title}</text>',
           f'<text x="24" y="58" font-size="13" fill="#667085">{subtitle}</text>']
    for i, (label, v) in enumerate(rows):
        y = top + i * lh
        bw = max(4, (w - left - right) * v / mx)
        out += [f'<text x="{left - 12}" y="{y + 15}" font-size="13.5" text-anchor="end" fill="#1d2433">{label}</text>',
                f'<rect x="{left}" y="{y + 3}" width="{w - left - right}" height="16" rx="8" fill="#f2f4f7"/>',
                f'<rect x="{left}" y="{y + 3}" width="{bw:.1f}" height="16" rx="8" fill="{color}"/>',
                f'<text x="{left + bw + 8:.1f}" y="{y + 15}" font-size="13" fill="#475467">{unit}{v:,.0f}</text>']
    out.append('</svg>')
    return '\n'.join(out)


def build_charts():
    cdir = os.path.join(RUN, 'assets', 'charts')
    os.makedirs(cdir, exist_ok=True)
    open_ = [p for p in progs if p['slug'] not in CLOSED]
    nomad = sorted([(META[p['country_slug']][0], income_eur(p['threshold'])) for p in open_
                    if p['route_type'] == 'digital-nomad' and income_eur(p['threshold'])], key=lambda r: r[1])
    blue = sorted([(META[p['country_slug']][0], income_eur(p['threshold'])) for p in open_
                   if ('蓝卡' in p['programme'] or 'Blue Card' in p['programme']) and income_eur(p['threshold'])], key=lambda r: r[1])
    open(os.path.join(cdir, 'nomad-income.svg'), 'w').write(
        svg_bars('💻 数字游民签证：月收入门槛', '主申请人 · 折合欧元/月 · 2026 · 越短越容易', nomad, color='#1d4ed8'))
    open(os.path.join(cdir, 'blue-card.svg'), 'w').write(
        svg_bars('🧑‍💻 欧盟蓝卡：最低月薪门槛', '折合欧元/月 · 2026 · 非欧元按粗略汇率', blue))
    inv_rows = []
    for p in open_:
        if p['route_type'] in ('residence-by-investment', 'citizenship'):
            m = re.search(r'([\d,]+)\+', p['threshold'])
            if m:
                v = int(m.group(1).replace(',', ''))
                inv_rows.append((META[p['country_slug']][0], v if p['country_slug'] != 'turkiye' else v * 0.86))
    inv_rows.sort(key=lambda r: r[1])
    col = sorted([(META[k][0], v['col']) for k, v in PROFILES.items() if k != '_meta' and v.get('col')], key=lambda r: r[1])
    open(os.path.join(cdir, 'cost-of-living.svg'), 'w').write(
        svg_bars('💶 生活成本指数（不含房租）', 'Numbeo 2026 年中 · 纽约 = 100 · 越短越便宜', col, unit='', color='#0e7490'))
    passive = sorted([(META[p['country_slug']][0] + ' ' + short_name(p, META[p['country_slug']][0])[:12], income_eur(p['threshold']))
                      for p in open_ if p['route_type'] == 'passive' and income_eur(p['threshold'])], key=lambda r: r[1])
    open(os.path.join(cdir, 'passive-income.svg'), 'w').write(
        svg_bars('🏖️ 被动收入居留：月收入门槛', '主申请人 · 折合欧元/月 · 不允许工作', passive, color='#0e7490'))
    open(os.path.join(cdir, 'investment.svg'), 'w').write(
        svg_bars('💰 投资居留/入籍：最低投资额', '折合欧元 · 2026 · 不含税费和中介费', inv_rows, color='#b45309'))


# ---------- global pages ----------
GLOBAL = json.load(open(os.path.join(RUN, 'src', 'global.json')))


def detail_blocks(d):
    L = []
    if d.get('summary'):
        L += [f'> **{d["summary"]}**', '']
    if d.get('facts'):
        L += [facts_table(d['facts']), '']
    fit, unfit = [x for x in d.get('fit', []) if x], [x for x in d.get('unfit', []) if x]
    if fit or unfit:
        li = lambda xs: ''.join(f'<li>{md_inline(x)}</li>' for x in xs)
        L += ['<table><tr>', f'<td width="50%" valign="top">✅ <b>适合</b><ul>{li(fit)}</ul></td>',
              f'<td width="50%" valign="top">❌ <b>不适合</b><ul>{li(unfit)}</ul></td>', '</tr></table>', '']
    if d.get('steps'):
        L += ['### 🗺️ 申请流程', '', mermaid_steps(d['steps']), '']
        L += [f'{i}. **{t}**' + (f' — {x}' if x else '') for i, (t, x) in enumerate(d['steps'], 1)] + ['']
    if d.get('docs'):
        L += ['### 📋 材料清单', ''] + [f'- [ ] {x}' for x in d['docs']] + ['']
    tips = [x for x in d.get('tips', []) if x]
    if tips:
        L += ['> [!WARNING]', '> **注意**'] + [f'> - {x}' for x in tips] + ['']
    return L


GLOBAL_PROFILE = {  # Numbeo 2026 年中：生活成本、房租、安全；Henley 2026：护照免签数
    'usa': (69.7, 37.1, 50.8, 179), 'canada': (61.3, 29.1, 54.4, 181), 'australia': (71.4, 33.1, 52.6, 182),
    'new-zealand': (60.2, 24.6, 51.2, 183), 'japan': (47.6, 13.6, 77.8, 188), 'south-korea': (56.7, 13.6, 70.3, 188),
    'singapore': (90.8, 68.3, 77.7, 192), 'hong-kong': (76.4, 59.1, 78.2, 171), 'philippines': (29.1, 7.2, 56.6, 64),
    'thailand': (36.8, 12.8, 63.6, 79), 'malaysia': (34.0, 8.5, 52.0, 180), 'uae': (55.6, 36.3, 86.4, 184),
    'latin-america': (44.4, 17.1, 47.3, 157),
}


def global_page(g, prev_g, next_g):
    notes = open(os.path.join(RUN, 'src', 'global_notes', g['slug'] + '.md')).read()
    notes = re.sub(r'^# .*\n', '', notes)
    notes = re.sub(r'^> 状态核查.*\n', '', notes, flags=re.M)
    notes = re.sub(r'^## ', '### ', notes.strip(), flags=re.M)
    kv = ' '.join(badge(k, v, '0969da') for k, v in g['kv'])
    nav = ' · '.join(f'[{ROUTE_ICON.get(r["type"], "•")} {r["name"]}](#{r["id"]})' for r in g['routes'])
    L = ['<a id="top"></a>', '', '<div align="center">', '', f'# {g["flag"]} {g["name"]} · {g["en"]}', '', kv, '',
         f'**{g["tagline"]}**', '', nav + ' · [📖 深度解读](#deep)', '', '</div>', '',
         '> [!NOTE]', '> 本篇依据 2026-10 对政府页面和公开资料的检索整理，核查深度低于欧洲篇，递交前请回到官方入口核对。', '',
         ]
    if g['slug'] in GLOBAL_PROFILE:
        col, rent, safe, pp = GLOBAL_PROFILE[g['slug']]
        tag = '（以墨西哥为例）' if g['slug'] == 'latin-america' else ''
        L += [f'## 🏙️ 生活档案{tag}', '', facts_table([
            ['💶 生活成本指数（纽约=100）', f'{col}{stars(col, 30, 110, True)}（中国 30.7）'],
            ['🏠 房租指数（纽约=100）', f'{rent}{stars(rent, 8, 70, True)}（中国 9.5）'],
            ['🛡️ 安全指数', f'{safe}{stars(safe, 40, 90)}（中国 77.0）'],
            ['🛂 护照免签目的地', f'{pp} 个（中国 81）']] + [[k, v] for k, v in g['kv']], cols=4), '',
            '<sub>数据：Numbeo 2026 年中、Henley Passport Index 2026。● 越多越好。</sub>', '']
    L += ['## 📊 路线速查', '', '| 路线 | 类型 | 一句话 | 状态 |', '|---|---|---|:-:|']
    for r in g['routes']:
        L.append(f"| [{r['name']}](#{r['id']}) | {ROUTE_ICON.get(r['type'], '•')} {ROUTE[r['type']]} | {r.get('summary', '')} | "
                 f"{'⛔ 已关闭' if r.get('status') == 'closed' else '🟢 开放'} |")
    L += ['', '---', '']
    for r in g['routes']:
        closed = r.get('status') == 'closed'
        L += [f'<a id="{r["id"]}"></a>', '', f'## {ROUTE_ICON.get(r["type"], "•")} {r["name"]}', '',
              badge('类型', ROUTE[r['type']], ROUTE_COLOR[r['type']]) + ' ' +
              badge('状态', '已关闭' if closed else '开放', 'cf222e' if closed else '2ea44f'), '']
        L += detail_blocks(r) + ['<sub>[↑ 回到顶部](#top)</sub>', '', '---', '']
    L += ['<a id="deep"></a>', '', '## 📖 深度解读', '', notes, '']
    if g.get('links'):
        L += ['## 🔗 官方入口', ''] + [f'- [{t}]({u})' for t, u in g['links']] + ['']
    L += ['<div align="center">', '',
          f'[← {prev_g["flag"]} {prev_g["name"]}]({prev_g["slug"]}.md) ｜ [🌏 主要移民地区](README.md) ｜ [🏠 首页](../../README.md) ｜ [{next_g["flag"]} {next_g["name"]} →]({next_g["slug"]}.md)',
          '', '</div>', '']
    return '\n'.join(L)


def global_index():
    cells = []
    for g in GLOBAL:
        lines = '<br>'.join(f'<sub>{k}：{v}</sub>' for k, v in g['kv'][:3])
        cells.append(f'<a href="{g["slug"]}.md"><b>{g["flag"]} {g["name"]}</b></a><br><sub>{g["tagline"]}</sub><br>{lines}')
    rows = []
    for i in range(0, len(cells), 3):
        chunk = cells[i:i + 3] + [''] * (3 - len(cells[i:i + 3]))
        rows.append('<tr>' + ''.join(f'<td width="33%" valign="top">{c}</td>' for c in chunk) + '</tr>')
    L = ['<div align="center">', '', '# 🌏 主要移民地区', '', '[🏠 首页](../../README.md) ｜ [🇪🇺 欧洲 36 国](../europe/README.md) ｜ 英国见 [欧洲篇](../europe/united-kingdom.md)', '', '</div>', '',
         '> [!NOTE]', '> 欧洲篇基于 LetsMigrate 逐条对照官方来源的数据；本篇依据 2026-10 的公开检索整理，核查深度较低，许多数字各来源说法不一，递交前务必回到官方入口核对。', '',
         '<table>', *rows, '</table>', '', '## 📊 全部路线', '', '| 目的地 | 路线 | 类型 | 一句话 |', '|---|---|---|---|']
    for g in GLOBAL:
        for r in g['routes']:
            L.append(f"| {g['flag']} {g['name']} | [{r['name']}]({g['slug']}.md#{r['id']}) | {ROUTE_ICON.get(r['type'], '•')} {ROUTE[r['type']]} | {r.get('summary', '')} |")
    return '\n'.join(L) + '\n'


def inject(path, key, content):
    t = open(path).read()
    new = re.sub(rf'<!-- AUTO:{key} -->.*?<!-- /AUTO -->', lambda m: f'<!-- AUTO:{key} -->\n{content}\n<!-- /AUTO -->', t, flags=re.S)
    open(path, 'w').write(new)


if __name__ == '__main__':
    edir = os.path.join(RUN, 'docs', 'europe')
    os.makedirs(edir, exist_ok=True)
    order = sorted(META, key=lambda s: META[s][1])
    for i, slug in enumerate(order):
        open(os.path.join(edir, slug + '.md'), 'w').write(country_page(slug, order[i - 1], order[(i + 1) % len(order)]))
    open(os.path.join(edir, 'README.md'), 'w').write(europe_index())
    build_charts()
    gdir = os.path.join(RUN, 'docs', 'global')
    for i, g in enumerate(GLOBAL):
        open(os.path.join(gdir, g['slug'] + '.md'), 'w').write(global_page(g, GLOBAL[i - 1], GLOBAL[(i + 1) % len(GLOBAL)]))
    open(os.path.join(gdir, 'README.md'), 'w').write(global_index())
    readme = os.path.join(RUN, 'README.md')
    inject(readme, 'countries', country_grid('docs/europe/'))
    inject(readme, 'changes', changes_table())
    routes = {'digital-nomad.md': ['digital-nomad'], 'skilled-work.md': ['work'],
              'startup-self-employed.md': ['startup', 'self-employed'], 'investment.md': ['residence-by-investment', 'citizenship'],
              'passive-income.md': ['passive']}
    for f, types in routes.items():
        inject(os.path.join(RUN, 'docs', 'routes', f), 'table', route_table(types))
    import csv
    with open(os.path.join(RUN, 'data', 'programmes.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['country', 'country_slug', 'programme', 'route_type', 'status', 'family', 'pr', 'threshold',
                    'income_eur_month', 'verified', 'source', 'url'])
        for p in sorted(progs, key=lambda p: (p['country_slug'], ORDER.index(p['route_type']))):
            inc = income_eur(p['threshold'])
            w.writerow([META[p['country_slug']][0], p['country_slug'], p['programme'], p['route_type'],
                        'closed' if p['slug'] in CLOSED else 'open', p['family'], p['pr'], p['threshold'],
                        round(inc) if inc else '', p['verified'], 'RUN' if p.get('extra') else 'LetsMigrate',
                        p['letsmigrate'] or (p['sources'][0]['url'] if p['sources'] else '')])
    n = sum(1 for p in progs if p['slug'] in DETAILS)
    print(f'built {len(order)} country pages; {n}/{len(progs)} programmes have details')
