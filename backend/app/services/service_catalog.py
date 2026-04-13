"""Central service catalog and discovery keyword utilities."""

import re
from typing import Dict, List


TARGET_SERVICE_PORTFOLIO: List[str] = [
    "Web App Development",
    "Mobile App Development",
    "eCommerce Web Development",
    "eCommerce App Development",
    "Product Development",
    "MVP Development",
    "Microsoft MAUI",
    "Salesforce Development",
    "Business Application Development",
    "Microsoft Power Pages",
    "Microsoft Power Apps",
    "Microsoft Power Automate",
    "Microsoft Power BI",
    "Microsoft Copilot Studio",
    "Microsoft Fabric",
    "Digital Transformation",
    "Power Platform Adoption",
    "Azure Consulting",
    "DevOps Consulting & Engineering",
    "Cloud Migration",
    "InfoPath to Power Apps",
    "Microsoft Dynamics 365",
    "Data Engineering",
    "UI/UX Design",
    "Cybersecurity",
    "AI/ML Development",
]


SERVICE_SYNONYM_MAP: Dict[str, List[str]] = {
    "Web App Development": ["web app", "web application", "web development", "frontend", "full stack"],
    "Mobile App Development": ["mobile app", "ios app", "android app", "react native", "flutter"],
    "eCommerce Web Development": ["ecommerce web", "shopify", "woocommerce", "magento", "online store"],
    "eCommerce App Development": ["ecommerce app", "shopping app", "mcommerce", "shop app"],
    "Product Development": ["product development", "product engineering", "software product"],
    "MVP Development": ["mvp development", "minimum viable product", "prototype build"],
    "Microsoft MAUI": ["maui", "microsoft maui", "dotnet maui", ".net maui"],
    "Salesforce Development": ["salesforce", "sales cloud", "service cloud", "apex"],
    "Business Application Development": ["business app", "business application", "line of business app"],
    "Microsoft Power Pages": ["power pages", "microsoft power pages"],
    "Microsoft Power Apps": ["power apps", "microsoft power apps"],
    "Microsoft Power Automate": ["power automate", "flow automation"],
    "Microsoft Power BI": ["power bi", "business intelligence dashboard"],
    "Microsoft Copilot Studio": ["copilot studio", "microsoft copilot studio", "custom copilot"],
    "Microsoft Fabric": ["microsoft fabric", "fabric lakehouse", "fabric analytics"],
    "Digital Transformation": ["digital transformation", "legacy modernization", "modernization"],
    "Power Platform Adoption": ["power platform adoption", "power platform governance"],
    "Azure Consulting": ["azure consulting", "azure architecture", "azure migration"],
    "DevOps Consulting & Engineering": ["devops", "ci/cd", "platform engineering", "sre"],
    "Cloud Migration": ["cloud migration", "migration to cloud", "workload migration"],
    "InfoPath to Power Apps": ["infopath", "infopath to power apps", "forms modernization"],
    "Microsoft Dynamics 365": ["dynamics 365", "crm", "erp", "microsoft dynamics"],
    "Data Engineering": ["data engineering", "etl", "data pipeline", "data platform"],
    "UI/UX Design": ["ui ux", "product design", "ux research", "interface design"],
    "Cybersecurity": ["cybersecurity", "security assessment", "vulnerability", "soc"],
    "AI/ML Development": ["ai", "ml", "machine learning", "llm", "artificial intelligence"],
}


JOB_BOARD_KEYWORD_MAP: Dict[str, List[str]] = {
    "Web App Development": ["web developer", "full stack developer", "react developer"],
    "Mobile App Development": ["mobile app developer", "android developer", "ios developer"],
    "eCommerce Web Development": ["shopify developer", "woocommerce developer", "magento developer"],
    "eCommerce App Development": ["ecommerce app developer", "mobile ecommerce developer", "shopping app developer"],
    "Product Development": ["product engineer", "software product developer", "application engineer"],
    "MVP Development": ["mvp developer", "startup product engineer", "prototype developer"],
    "Microsoft MAUI": ["maui developer", ".net maui developer", "xamarin maui developer"],
    "Salesforce Development": ["salesforce developer", "apex developer", "salesforce consultant"],
    "Business Application Development": ["business application developer", "enterprise application developer", "line of business app developer"],
    "Microsoft Power Pages": ["power pages developer", "power platform developer", "microsoft power pages"],
    "Microsoft Power Apps": ["power apps developer", "power platform developer", "microsoft power apps"],
    "Microsoft Power Automate": ["power automate developer", "rpa developer", "workflow automation engineer"],
    "Microsoft Power BI": ["power bi developer", "bi developer", "power bi consultant"],
    "Microsoft Copilot Studio": ["copilot studio developer", "copilot engineer", "microsoft copilot developer"],
    "Microsoft Fabric": ["microsoft fabric engineer", "fabric data engineer", "fabric developer"],
    "Digital Transformation": ["digital transformation consultant", "transformation manager", "business transformation lead"],
    "Power Platform Adoption": ["power platform consultant", "power platform architect", "power platform specialist"],
    "Azure Consulting": ["azure consultant", "azure cloud architect", "azure engineer"],
    "DevOps Consulting & Engineering": ["devops engineer", "site reliability engineer", "platform engineer"],
    "Cloud Migration": ["cloud migration engineer", "cloud architect", "cloud consultant"],
    "InfoPath to Power Apps": ["infopath migration consultant", "power apps migration developer", "forms modernization developer"],
    "Microsoft Dynamics 365": ["dynamics 365 developer", "dynamics consultant", "crm developer"],
    "Data Engineering": ["data engineer", "etl developer", "data platform engineer"],
    "UI/UX Design": ["ui ux designer", "product designer", "ux designer"],
    "Cybersecurity": ["cybersecurity engineer", "security analyst", "application security engineer"],
    "AI/ML Development": ["machine learning engineer", "ai engineer", "data scientist"],
}


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def infer_services_from_text(text: str, limit: int = 6) -> List[str]:
    """Infer canonical services from query text using portfolio synonym matching."""
    searchable = _normalize_space(text).lower()
    if not searchable:
        return []

    matches: List[str] = []
    seen = set()
    for service, aliases in SERVICE_SYNONYM_MAP.items():
        tokens = [service.lower(), *[a.lower() for a in aliases]]
        if any(token and token in searchable for token in tokens):
            if service not in seen:
                matches.append(service)
                seen.add(service)
            if len(matches) >= limit:
                return matches
    return matches


def build_job_keywords(service: str, max_keywords: int = 8) -> List[str]:
    """Build role-focused job search keywords for a target service."""
    normalized_service = _normalize_space(service)
    if not normalized_service:
        return []

    mapped = JOB_BOARD_KEYWORD_MAP.get(normalized_service, [])
    candidates: List[str] = list(mapped)

    lower_service = normalized_service.lower()
    if not candidates:
        candidates.extend(
            [
                f"{normalized_service} developer",
                f"{normalized_service} engineer",
                f"{normalized_service} consultant",
            ]
        )

    if "development" in lower_service:
        candidates.append(normalized_service.replace("Development", "Developer").replace("development", "developer"))
    if "consulting" in lower_service:
        candidates.append(normalized_service.replace("Consulting", "Consultant").replace("consulting", "consultant"))
    if "design" in lower_service:
        candidates.append(normalized_service.replace("Design", "Designer").replace("design", "designer"))

    deduped: List[str] = []
    seen = set()
    for keyword in candidates:
        cleaned = _normalize_space(keyword)
        if not cleaned:
            continue
        low = cleaned.lower()
        if low in seen:
            continue
        seen.add(low)
        deduped.append(cleaned)
        if len(deduped) >= max_keywords:
            break

    return deduped
