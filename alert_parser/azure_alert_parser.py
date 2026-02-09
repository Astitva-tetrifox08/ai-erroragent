def parse_azure_alert(payload: dict) -> dict:
    essentials = payload.get("data", {}).get("essentials", {})

    return {
        "is_error": True,
        "alert_name": essentials.get("alertRule"),
        "severity": essentials.get("severity"),
        "resource": essentials.get("targetResourceName"),
        "resource_type": essentials.get("targetResourceType"),
        "subscription": essentials.get("subscriptionId"),
        "fired_time": essentials.get("firedDateTime"),
        "service": "azure_monitor"
    }
