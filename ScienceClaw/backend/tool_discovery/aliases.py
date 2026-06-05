from __future__ import annotations

import re
import unicodedata


TOOL_CATEGORY_OTHER = "其他"

TOOL_CATEGORY_ORDER = [
    "计算材料",
    "化学信息学",
    "化学数据库",
    "计算化学",
    "光谱分析",
    "化学反应与合成",
    "Python包信息",
    "其他通用工具",
    "学术文献与引用",
    "网页与搜索",
    "文件与执行",
    "统计分析",
    "文档处理",
    "数据存储与检索",
    "知识图谱与本体",
    "数据可视化",
    "机器学习",
    "学术文献",
    "生命科学",
    "药物与化合物",
    "临床医学",
    "材料与化学",
    "地球与环境",
    "天文与空间",
    "数据处理",
    "文档处理",
    "网页与外部服务",
    "技能与工具管理",
    TOOL_CATEGORY_OTHER,
]

PRESERVED_TOOL_TERMS = [
    "ScienceClaw",
    "ToolUniverse",
    "MCP",
    "HTTPS MCP",
    "DeepAgents",
    "sandbox",
    "arXiv",
    "OpenAlex",
    "PubMed",
    "Crossref",
    "UniProt",
    "PDB",
    "AlphaFold",
    "ChEMBL",
    "FAERS",
    "ClinicalTrials",
    "COD",
    "USGS",
    "OpenMeteo",
    "SIMBAD",
    "SDSS",
    "NASA",
    "OpenML",
    "PDF",
    "DOCX",
    "PPTX",
    "XLSX",
    "Markdown",
    "SMILES",
    "JSON",
    "JSON Schema",
]

TOOL_CATEGORY_ALIASES: dict[str, list[str]] = {
    "计算材料": ["材料", "计算材料", "材料模拟", "材料机器学习", "materials", "atomistic", "ASE", "DScribe", "SchNetPack"],
    "化学信息学": ["化学信息学", "化合物", "分子", "SMILES", "CID", "PubChem", "ChEMBL", "RDKit", "cheminformatics"],
    "化学数据库": ["化学数据库", "化合物库", "供应商", "Enamine", "Mcule", "database"],
    "计算化学": ["计算化学", "量子化学", "PySCF", "DFT", "quantum chemistry"],
    "光谱分析": ["光谱", "谱图", "可视化", "Altair", "spectroscopy"],
    "化学反应与合成": ["反应", "合成", "MetaCyc", "reaction", "synthesis"],
    "Python包信息": ["Python", "包信息", "库", "package", "PyPI", "scientific computing"],
    "其他通用工具": ["通用", "工具", "ToolUniverse", "workflow", "utility"],
    "学术文献与引用": ["文献", "引用", "DOI", "Crossref", "OpenAlex", "Semantic Scholar", "DataCite", "citation"],
    "网页与搜索": ["网页", "搜索", "Wikipedia", "GitHub", "web", "search"],
    "统计分析": ["统计", "检验", "log-rank", "statistics"],
    "数据存储与检索": ["数据集", "数据存储", "Dataverse", "OpenML", "HuggingFace", "dataset"],
    "知识图谱与本体": ["知识图谱", "本体", "Wikidata", "SPARQL", "ontology"],
    "数据可视化": ["可视化", "图谱", "visualization", "graph"],
    "机器学习": ["机器学习", "模型", "ModelDB", "machine learning"],
    "学术文献": ["论文", "医学论文", "文献", "预印本", "引用", "摘要", "全文", "paper", "article", "literature", "arXiv", "OpenAlex", "PubMed", "Crossref"],
    "生命科学": ["蛋白", "基因", "通路", "组学", "生物", "protein", "gene", "pathway", "omics", "UniProt", "PDB", "AlphaFold"],
    "药物与化合物": ["药物", "化合物", "靶点", "ADMET", "毒性", "药物毒性", "药物安全", "compound", "drug", "toxicity", "ChEMBL", "FAERS"],
    "临床医学": ["临床", "临床试验", "疾病", "指南", "患者", "clinical", "trial", "disease", "ClinicalTrials"],
    "材料与化学": ["材料", "化学", "晶体", "分子", "反应", "谱图", "materials", "chemistry", "crystal", "molecule", "reaction", "COD", "SMILES"],
    "地球与环境": ["地震", "水文", "气候", "空气质量", "土壤", "海洋", "earth", "environment", "climate", "USGS", "OpenMeteo"],
    "天文与空间": ["天文", "空间", "天体", "星历", "空间天气", "巡天", "astronomy", "space", "SIMBAD", "SDSS", "NASA"],
    "数据处理": ["数据", "表格", "统计", "转换", "可视化", "机器学习", "data", "table", "statistics", "visualization", "machine learning", "OpenML"],
    "文档处理": ["文档", "PDF", "PDF 转换", "DOCX", "PPTX", "XLSX", "Markdown", "转换", "提取", "document"],
    "网页与外部服务": ["网页", "搜索", "抓取", "第三方", "API", "MCP", "web", "search", "crawl", "service"],
    "文件与执行": ["文件", "命令", "执行", "sandbox", "file", "command", "execute"],
    "技能与工具管理": ["技能", "工具", "创建", "保存", "评估", "屏蔽", "skill", "tool", "creator", "evaluation"],
    TOOL_CATEGORY_OTHER: ["其他", "自定义", "未归类", "other", "custom"],
}

SOURCE_CATEGORY_ALIASES: dict[str, str] = {
    "literature": "学术文献",
    "literature_search": "学术文献",
    "publication": "学术文献",
    "pubmed": "学术文献",
    "europepmc": "学术文献",
    "arxiv": "学术文献",
    "openalex": "学术文献",
    "crossref": "学术文献",
    "biology": "生命科学",
    "bioinformatics": "生命科学",
    "protein": "生命科学",
    "gene": "生命科学",
    "uniprot": "生命科学",
    "alphafold": "生命科学",
    "pdb": "生命科学",
    "drug": "药物与化合物",
    "compound": "药物与化合物",
    "pubchem": "药物与化合物",
    "chembl": "药物与化合物",
    "faers": "药物与化合物",
    "admetai": "药物与化合物",
    "clinical": "临床医学",
    "clinical_trials": "临床医学",
    "clinicaltrials": "临床医学",
    "medicine": "临床医学",
    "materials": "材料与化学",
    "chemistry": "材料与化学",
    "crystal": "材料与化学",
    "cod_crystal": "材料与化学",
    "earth": "地球与环境",
    "environment": "地球与环境",
    "climate": "地球与环境",
    "open_meteo": "地球与环境",
    "usgs_earthquake": "地球与环境",
    "astronomy": "天文与空间",
    "space": "天文与空间",
    "nasa_exoplanet": "天文与空间",
    "simbad": "天文与空间",
    "sdss": "天文与空间",
    "data": "数据处理",
    "dataset": "数据处理",
    "statistics": "数据处理",
    "openml": "数据处理",
    "document": "文档处理",
    "pdf": "文档处理",
    "docx": "文档处理",
    "pptx": "文档处理",
    "xlsx": "文档处理",
    "markitdown": "文档处理",
    "web": "网页与外部服务",
    "search": "网页与外部服务",
    "mcp": "网页与外部服务",
    "github": "网页与外部服务",
    "file": "文件与执行",
    "file_download": "文件与执行",
    "execution": "文件与执行",
    "python_executor": "文件与执行",
    "sandbox": "文件与执行",
    "skill": "技能与工具管理",
    "tool": "技能与工具管理",
    "tool_finder": "技能与工具管理",
    "other": TOOL_CATEGORY_OTHER,
}

SOURCE_CATEGORY_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(literature|pubmed|pmc|preprint|citation|scholar|openalex|crossref|datacite|dblp|doaj)"), "学术文献"),
    (re.compile(r"(gene|genome|protein|pathway|uniprot|pdb|ensembl|ncbi|omics|bio|alphafold)"), "生命科学"),
    (re.compile(r"(drug|compound|chembl|pubchem|admet|tox|faers|fda|pharm|binding|target)"), "药物与化合物"),
    (re.compile(r"(clinical|trial|medicine|guideline|disease|patient|mesh|icd|health)"), "临床医学"),
    (re.compile(r"(chem|material|crystal|molecule|reaction|spect|cod_|smiles)"), "材料与化学"),
    (re.compile(r"(earth|climate|meteo|weather|flood|soil|usgs|water|environment|gbif|waqi)"), "地球与环境"),
    (re.compile(r"(astronomy|space|nasa|simbad|sdss|jpl|exoplanet|horizons)"), "天文与空间"),
    (re.compile(r"(data|dataset|dataverse|zenodo|openml|visualization|machine_learning|statistics|software)"), "数据处理"),
    (re.compile(r"(document|pdf|docx|pptx|xlsx|markdown|markitdown|xml)"), "文档处理"),
    (re.compile(r"(web|search|github|url|wiki|api|service|mcp)"), "网页与外部服务"),
    (re.compile(r"(file|download|executor|python_executor|sandbox|execute|command)"), "文件与执行"),
    (re.compile(r"(skill|tool|package_discovery|composition|finder|creator|evaluation|agent)"), "技能与工具管理"),
]


def normalize_text(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").strip().lower()


def normalize_category_key(value: str | None) -> str:
    return re.sub(r"[\s-]+", "_", normalize_text(value))


def is_tool_category_zh(value: str | None) -> bool:
    return bool(value and value in TOOL_CATEGORY_ORDER)


def map_tool_category_to_zh(category: str | None = None, category_zh: str | None = None) -> str:
    if is_tool_category_zh(category_zh):
        return str(category_zh)
    if is_tool_category_zh(category):
        return str(category)
    normalized = normalize_category_key(category)
    if normalized in SOURCE_CATEGORY_ALIASES:
        return SOURCE_CATEGORY_ALIASES[normalized]
    for pattern, category_name in SOURCE_CATEGORY_RULES:
        if pattern.search(normalized):
            return category_name
    return TOOL_CATEGORY_OTHER


def classify_tool_text(*parts: str | None, default: str = TOOL_CATEGORY_OTHER) -> str:
    text = normalize_category_key(" ".join(part or "" for part in parts))
    if not text:
        return default
    for pattern, category_name in SOURCE_CATEGORY_RULES:
        if pattern.search(text):
            return category_name
    return default


def get_tool_category_aliases(category_zh: str) -> list[str]:
    return TOOL_CATEGORY_ALIASES.get(category_zh, TOOL_CATEGORY_ALIASES[TOOL_CATEGORY_OTHER])


def get_tool_category_sort_index(category_zh: str) -> int:
    try:
        return TOOL_CATEGORY_ORDER.index(category_zh)
    except ValueError:
        return len(TOOL_CATEGORY_ORDER)


def expand_query_terms(query: str) -> list[str]:
    normalized = normalize_text(query)
    terms: list[str] = []
    for term in re.split(r"[\s,，;；]+", normalized):
        if term:
            terms.append(term)
    if normalized and normalized not in terms:
        terms.append(normalized)
    for category_zh, aliases in TOOL_CATEGORY_ALIASES.items():
        haystack = [category_zh, *aliases]
        if any(normalize_text(alias) and normalize_text(alias) in normalized for alias in haystack):
            terms.extend(normalize_text(alias) for alias in aliases)
            terms.append(normalize_text(category_zh))
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if term and term not in seen:
            seen.add(term)
            deduped.append(term)
    return deduped
