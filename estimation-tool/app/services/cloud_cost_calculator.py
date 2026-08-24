"""Cloud Cost Calculator — estimates monthly Azure infrastructure costs.

Maps classified work items and target systems to Azure resource types,
then applies unit pricing to estimate monthly recurring cloud costs.

Pricing is based on Azure India (Central India) region, Pay-As-You-Go rates.
All costs are in INR (₹) per month.

Design: Deterministic — same inputs produce same outputs. No API calls.
"""

import logging
from typing import Any

from app.models.schemas import CatalogWorkItem

logger = logging.getLogger(__name__)

# Azure resource monthly costs (INR, Central India region, moderate tier)
# These are approximate pay-as-you-go rates for typical enterprise usage
AZURE_RESOURCE_COSTS = {
    # Compute
    "app_service_b2": 5500,        # App Service B2 (2 vCPU, 3.5 GB) per instance
    "app_service_s1": 8500,        # App Service S1 (1 vCPU, 1.75 GB) per instance
    "app_service_p1v3": 18000,     # App Service P1v3 (2 vCPU, 8 GB) per instance
    "function_app": 2000,          # Function App (Consumption plan, moderate usage)
    "aks_node_d2v3": 12000,        # AKS node (D2s_v3, 2 vCPU, 8 GB) per node
    "container_instance": 4000,    # ACI (moderate usage)

    # Database
    "sql_db_s2": 12000,            # Azure SQL S2 (50 DTU)
    "sql_db_s3": 24000,            # Azure SQL S3 (100 DTU)
    "cosmos_db": 8000,             # Cosmos DB (400 RU/s, ~10 GB)
    "redis_cache_c1": 6500,        # Redis Cache C1 (1 GB)
    "mongodb_m10": 10000,          # MongoDB Atlas M10 equivalent

    # Messaging & Integration
    "service_bus_standard": 6500,  # Service Bus Standard tier
    "service_bus_premium": 48000,  # Service Bus Premium (1 MU)
    "event_grid": 1500,            # Event Grid (moderate events)
    "api_management_basic": 12000, # APIM Basic tier
    "api_management_standard": 55000, # APIM Standard tier

    # Storage & CDN
    "storage_account": 2000,       # Storage Account (100 GB, moderate ops)
    "blob_storage_hot": 3500,      # Blob Storage Hot (500 GB)
    "cdn_standard": 4000,          # CDN Standard (moderate traffic)

    # Identity & Security
    "azure_ad_b2c": 2500,          # Azure AD B2C (50K auth/month)
    "key_vault": 500,              # Key Vault (moderate operations)
    "app_insights": 3500,          # Application Insights (5 GB/month)

    # Networking
    "load_balancer": 2000,         # Standard Load Balancer
    "application_gateway_v2": 15000, # App Gateway v2
    "vnet": 0,                     # VNet (no cost, but noting for clarity)

    # IoT / Connected
    "iot_hub_s1": 20000,           # IoT Hub S1 (400K msg/day)
    "notification_hub": 3000,      # Notification Hub Standard
    "signalr_standard": 8000,      # SignalR Standard (1 unit)
}

# Maps catalog work item categories to Azure resources needed
CATEGORY_RESOURCE_MAP = {
    "frontend": [
        ("app_service_b2", 1, "Web frontend hosting"),
        ("cdn_standard", 1, "CDN for static assets"),
        ("storage_account", 1, "Static file storage"),
    ],
    "backendCrud": [
        ("app_service_s1", 1, "API backend"),
        ("sql_db_s2", 1, "Database"),
    ],
    "backendLogic": [
        ("app_service_p1v3", 1, "Compute for business logic"),
        ("sql_db_s3", 1, "Database (higher DTU)"),
        ("redis_cache_c1", 1, "Caching layer"),
    ],
    "integration": [
        ("service_bus_standard", 1, "Message broker"),
        ("function_app", 1, "Integration function"),
    ],
    "sap": [
        ("function_app", 2, "SAP adapter functions"),
        ("service_bus_standard", 1, "SAP event queue"),
        ("storage_account", 1, "SAP file staging"),
    ],
    "qa": [],  # No infra cost for QA
    "devops": [
        ("app_insights", 1, "Monitoring & observability"),
    ],
}

# System-specific Azure resource requirements (overrides/additions)
SYSTEM_RESOURCE_MAP = {
    "TVS Connect": [
        ("iot_hub_s1", 1, "IoT Hub for vehicle connectivity"),
        ("notification_hub", 1, "Push notifications (FCM/APNs)"),
        ("signalr_standard", 1, "Real-time features"),
    ],
    "P360": [
        ("signalr_standard", 1, "WebSocket subscriptions"),
        ("cosmos_db", 1, "Graph/document store"),
    ],
    "CNS": [
        ("notification_hub", 1, "Multi-channel notifications"),
        ("service_bus_premium", 1, "High-throughput messaging"),
    ],
    "MDP": [
        ("sql_db_s3", 1, "Master data store"),
        ("redis_cache_c1", 1, "Data cache"),
    ],
    "UMS": [
        ("azure_ad_b2c", 1, "Identity provider"),
        ("redis_cache_c1", 1, "Session/token cache"),
    ],
    "IDP": [
        ("service_bus_premium", 1, "Message broker (high volume)"),
        ("function_app", 2, "Message routing functions"),
    ],
    "Booking Service": [
        ("sql_db_s3", 1, "Booking data"),
        ("redis_cache_c1", 1, "Inventory cache"),
        ("service_bus_standard", 1, "Order events"),
    ],
    "Catalog Service": [
        ("cosmos_db", 1, "Product catalog (document store)"),
        ("redis_cache_c1", 1, "Catalog cache"),
    ],
    "tvsmotor.com": [
        ("cdn_standard", 1, "Global CDN"),
        ("application_gateway_v2", 1, "WAF + routing"),
        ("app_service_p1v3", 2, "Multi-instance web tier"),
    ],
    "Vehicle Systems": [
        ("iot_hub_s1", 1, "Vehicle telemetry ingestion"),
    ],
    "CPG": [
        ("api_management_basic", 1, "Payment gateway proxy"),
        ("key_vault", 1, "Payment credentials"),
    ],
    "Subscription Platform": [
        ("sql_db_s3", 1, "Subscription state"),
        ("function_app", 1, "Entitlement webhooks"),
    ],
}

# Deployment model multipliers (from system_dependencies.json)
DEPLOYMENT_MULTIPLIERS = {
    "multi_region": 2.0,       # 2 regions
    "ib_countrywise": 3.0,     # Multiple country deployments (IB)
    "ib_regionwise": 2.0,      # Regional IB deployments
    "single": 1.0,             # Single region
}


def estimate_cloud_cost(
    work_items: list[CatalogWorkItem],
    target_systems: list[str],
    dependencies: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Estimate monthly Azure cloud infrastructure costs.

    Uses work items and target systems to determine what Azure resources
    are needed, then applies pricing.

    Args:
        work_items: Classified work items with categories.
        target_systems: Systems involved in the project.
        dependencies: System dependency graph (for deployment model info).
        catalog: Estimation catalog (for effort table categories).

    Returns:
        Dict with monthlyTotal, breakdown (per-resource), and notes.
    """
    effort_table = catalog.get("effortTable", {})
    systems_info = dependencies.get("systems", {})

    # Collect all resources needed (deduplicate by resource type)
    resources: dict[str, dict] = {}  # key: resource_type → {qty, reasons}

    # Step 1: Map work item categories to resources
    categories_seen = set()
    for item in work_items:
        unit_data = effort_table.get(item.unitId, {})
        category = unit_data.get("category", "backendLogic")
        if category not in categories_seen:
            categories_seen.add(category)
            for resource_type, qty, reason in CATEGORY_RESOURCE_MAP.get(category, []):
                _add_resource(resources, resource_type, qty, reason)

    # Step 2: Map target systems to additional resources
    for system in target_systems:
        system_resources = SYSTEM_RESOURCE_MAP.get(system, [])
        for resource_type, qty, reason in system_resources:
            _add_resource(resources, resource_type, qty, f"{system}: {reason}")

    # Step 3: Shared baseline resources (always needed)
    _add_resource(resources, "app_insights", 1, "Monitoring (baseline)")
    _add_resource(resources, "key_vault", 1, "Secrets management (baseline)")
    _add_resource(resources, "load_balancer", 1, "Traffic distribution (baseline)")

    # Step 3.5: Detect Azure services mentioned in work item reasons (PRD-driven)
    all_reasons = " ".join(item.reason.lower() for item in work_items)
    prd_azure_hints = {
        "service bus": ("service_bus_standard", "Service Bus (mentioned in PRD)"),
        "cosmos": ("cosmos_db", "Cosmos DB (mentioned in PRD)"),
        "redis": ("redis_cache_c1", "Redis Cache (mentioned in PRD)"),
        "blob storage": ("blob_storage_hot", "Blob Storage (mentioned in PRD)"),
        "iot hub": ("iot_hub_s1", "IoT Hub (mentioned in PRD)"),
        "cdn": ("cdn_standard", "CDN (mentioned in PRD)"),
        "api management": ("api_management_basic", "API Management (mentioned in PRD)"),
        "apim": ("api_management_basic", "APIM (mentioned in PRD)"),
        "signalr": ("signalr_standard", "SignalR (mentioned in PRD)"),
        "notification hub": ("notification_hub", "Notification Hub (mentioned in PRD)"),
        "function app": ("function_app", "Function App (mentioned in PRD)"),
        "azure function": ("function_app", "Azure Function (mentioned in PRD)"),
    }
    for keyword, (resource_type, reason) in prd_azure_hints.items():
        if keyword in all_reasons:
            _add_resource(resources, resource_type, 1, reason)

    # Step 4: Deployment multiplier
    deploy_mult = 1.0
    for system in target_systems:
        sys_info = systems_info.get(system, {})
        deploy_model = sys_info.get("deploymentModel", "").lower()
        if "ib" in deploy_model and "country" in deploy_model:
            deploy_mult = max(deploy_mult, DEPLOYMENT_MULTIPLIERS["ib_countrywise"])
        elif "ib" in deploy_model and "region" in deploy_model:
            deploy_mult = max(deploy_mult, DEPLOYMENT_MULTIPLIERS["ib_regionwise"])
        elif "multi" in deploy_model:
            deploy_mult = max(deploy_mult, DEPLOYMENT_MULTIPLIERS["multi_region"])

    # Step 5: Calculate costs
    breakdown = []
    monthly_total = 0.0

    for resource_type, info in sorted(resources.items(), key=lambda x: -AZURE_RESOURCE_COSTS.get(x[0], 0) * x[1]["qty"]):
        unit_cost = AZURE_RESOURCE_COSTS.get(resource_type, 0)
        qty = info["qty"]
        line_cost = unit_cost * qty * deploy_mult
        monthly_total += line_cost

        breakdown.append({
            "resource": resource_type.replace("_", " ").title(),
            "quantity": qty,
            "unitCost": unit_cost,
            "monthlyCost": round(line_cost),
            "reason": "; ".join(info["reasons"][:2]),  # First 2 reasons
        })

    # Add environment multiplier (Dev + UAT + Prod = ~2.5x of single prod)
    # But we report just prod cost, with a note about non-prod
    non_prod_cost = round(monthly_total * 0.6)  # Dev+UAT typically 60% of prod

    result = {
        "monthlyTotal": round(monthly_total),
        "monthlyTotalWithNonProd": round(monthly_total + non_prod_cost),
        "breakdown": breakdown,
        "deploymentMultiplier": deploy_mult,
        "notes": [],
    }

    if deploy_mult > 1.0:
        result["notes"].append(
            f"Multi-region deployment detected (×{deploy_mult:.1f}). "
            f"Costs reflect all regions."
        )
    result["notes"].append(
        f"Non-prod environments (Dev+UAT) estimated at ₹{non_prod_cost:,}/mo additional."
    )
    result["notes"].append(
        "Costs are estimates based on Azure India (Central India) Pay-As-You-Go pricing. "
        "Actual costs may vary with Reserved Instances or Enterprise Agreement discounts."
    )

    logger.info(
        f"Cloud cost estimate: ₹{monthly_total:,.0f}/mo (prod), "
        f"₹{monthly_total + non_prod_cost:,.0f}/mo (all envs), "
        f"{len(breakdown)} resources, deploy_mult={deploy_mult}"
    )

    return result


def _add_resource(resources: dict, resource_type: str, qty: int, reason: str):
    """Add or merge a resource into the resources dict."""
    if resource_type in resources:
        resources[resource_type]["qty"] = max(resources[resource_type]["qty"], qty)
        if reason not in resources[resource_type]["reasons"]:
            resources[resource_type]["reasons"].append(reason)
    else:
        resources[resource_type] = {"qty": qty, "reasons": [reason]}
