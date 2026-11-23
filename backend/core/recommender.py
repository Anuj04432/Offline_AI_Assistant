"""Hardware-aware local model recommender and catalog."""

from typing import List, Dict, Any


MODEL_CATALOG = [
    {
        "id": "llama3.2:1b",
        "name": "Llama 3.2 (1B)",
        "parameter_size": "1B",
        "download_size": "1.3 GB",
        "min_ram_gb": 4.0,
        "recommended_ram_gb": 6.0,
        "tag": "Light",
        "category": "Ultra-Lightweight & Fast",
        "description": "Meta's smallest Llama model. Extremely fast on any modern CPU with minimal memory footprint.",
        "pull_command": "ollama run llama3.2:1b",
    },
    {
        "id": "llama3.2:3b",
        "name": "Llama 3.2 (3B)",
        "parameter_size": "3B",
        "download_size": "2.0 GB",
        "min_ram_gb": 6.0,
        "recommended_ram_gb": 8.0,
        "tag": "Light",
        "category": "Smart & Balanced",
        "description": "High intelligence per parameter. Perfect everyday assistant for general reasoning and summaries on laptops.",
        "pull_command": "ollama run llama3.2:3b",
    },
    {
        "id": "qwen2.5:3b",
        "name": "Qwen 2.5 (3B)",
        "parameter_size": "3B",
        "download_size": "1.9 GB",
        "min_ram_gb": 6.0,
        "recommended_ram_gb": 8.0,
        "tag": "Fast",
        "category": "Multilingual & Quick",
        "description": "Very fast inference, strong multilingual skills, and structured reasoning with low resource usage.",
        "pull_command": "ollama run qwen2.5:3b",
    },
    {
        "id": "phi3:mini",
        "name": "Phi-3 Mini (3.8B)",
        "parameter_size": "3.8B",
        "download_size": "2.3 GB",
        "min_ram_gb": 6.0,
        "recommended_ram_gb": 8.0,
        "tag": "Reason",
        "category": "Logic & Math",
        "description": "Microsoft's compact powerhouse trained heavily on synthetic reasoning data.",
        "pull_command": "ollama run phi3:mini",
    },
    {
        "id": "qwen2.5-coder:7b",
        "name": "Qwen 2.5 Coder (7B)",
        "parameter_size": "7B",
        "download_size": "4.7 GB",
        "min_ram_gb": 8.0,
        "recommended_ram_gb": 12.0,
        "tag": "Code",
        "category": "Coding & Development",
        "description": "Top-tier code generation, debugging, and explanation. The gold standard for local programming assistance.",
        "pull_command": "ollama run qwen2.5-coder:7b",
    },
    {
        "id": "llama3.1:8b",
        "name": "Llama 3.1 (8B)",
        "parameter_size": "8B",
        "download_size": "4.7 GB",
        "min_ram_gb": 8.0,
        "recommended_ram_gb": 12.0,
        "tag": "Smart",
        "category": "General Intelligence",
        "description": "State-of-the-art open weights model from Meta. Outstanding conversation, writing, and logic.",
        "pull_command": "ollama run llama3.1:8b",
    },
    {
        "id": "mistral:7b",
        "name": "Mistral (7B)",
        "parameter_size": "7B",
        "download_size": "4.1 GB",
        "min_ram_gb": 8.0,
        "recommended_ram_gb": 12.0,
        "tag": "Fast",
        "category": "Speed & Fluency",
        "description": "Classic and reliable. Known for snappy response times and crisp writing style.",
        "pull_command": "ollama run mistral:7b",
    },
    {
        "id": "gemma2:9b",
        "name": "Gemma 2 (9B)",
        "parameter_size": "9B",
        "download_size": "5.5 GB",
        "min_ram_gb": 10.0,
        "recommended_ram_gb": 16.0,
        "tag": "Smart",
        "category": "Deep Reasoning",
        "description": "Google's high-precision open model with class-leading factual accuracy.",
        "pull_command": "ollama run gemma2:9b",
    },
    {
        "id": "qwen2.5-coder:14b",
        "name": "Qwen 2.5 Coder (14B)",
        "parameter_size": "14B",
        "download_size": "9.0 GB",
        "min_ram_gb": 16.0,
        "recommended_ram_gb": 24.0,
        "tag": "Power",
        "category": "Advanced Coding",
        "description": "Heavyweight coding model for multi-file architectures and complex refactoring. Requires 16GB+ RAM.",
        "pull_command": "ollama run qwen2.5-coder:14b",
    },
]


def get_recommendations(system_hardware: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate catalog models against the user's hardware.
    Returns:
    - user_summary: string summarizing capacity
    - recommended_models: list of models with suitability ('optimal', 'compatible', 'heavy')
    """
    ram_total = system_hardware.get("ram_total_gb", 8.0)
    tier = system_hardware.get("hardware_tier", "MEDIUM")

    evaluated = []
    for model in MODEL_CATALOG:
        m = dict(model)
        min_ram = m["min_ram_gb"]
        rec_ram = m["recommended_ram_gb"]

        if ram_total >= rec_ram:
            suitability = "optimal"
            badge_color = "green"
            badge_label = "Optimal"
        elif ram_total >= min_ram:
            suitability = "compatible"
            badge_color = "yellow"
            badge_label = "Compatible"
        else:
            suitability = "heavy"
            badge_color = "red"
            badge_label = "High RAM Demand"

        m["suitability"] = suitability
        m["badge_color"] = badge_color
        m["badge_label"] = badge_label
        evaluated.append(m)

    # Sort so optimal comes first, then compatible, then heavy
    order = {"optimal": 0, "compatible": 1, "heavy": 2}
    evaluated.sort(key=lambda x: (order.get(x["suitability"], 9), x["min_ram_gb"]))

    if tier == "LIGHT":
        summary = f"Your system has {ram_total:.1f} GB RAM. Lightweight 1B–3B models are strongly recommended for smooth offline performance."
    elif tier == "MEDIUM":
        summary = f"Your system has {ram_total:.1f} GB RAM. You can comfortably run 7B–8B models like Qwen 2.5 Coder and Llama 3.1, or ultra-fast 3B models."
    else:
        summary = f"Your system has {ram_total:.1f} GB RAM. High-capacity hardware detected! You can run full 7B–14B models with ease."

    return {
        "tier": tier,
        "summary": summary,
        "models": evaluated,
    }
