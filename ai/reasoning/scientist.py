"""LLM-based scientist for autonomous research reasoning."""

from typing import Dict, List, Optional


class Scientist:
    def __init__(self, llm_client=None, model: str = "claude-opus"):
        """Initialize autonomous scientist."""
        self.llm_client = llm_client
        self.model = model
        self.science_context = ""
        self.analysis_history = []

    def analyze_sample(self, sample_data: Dict) -> Dict:
        """Analyze a rock sample and generate scientific assessment."""
        analysis = {
            "sample_id": sample_data.get("id"),
            "rock_type": sample_data.get("type", "unknown"),
            "composition": sample_data.get("composition", {}),
            "visual_confidence": sample_data.get("visual_confidence", 0.5),
            "spectral_confidence": sample_data.get("spectral_confidence", 0.5),
        }

        # Generate scientific explanation using LLM
        if self.llm_client:
            explanation = self._generate_explanation(analysis)
            analysis["explanation"] = explanation
        else:
            # Fallback to rule-based explanation
            analysis["explanation"] = self._generate_heuristic_explanation(analysis)

        analysis["scientific_value"] = self._score_scientific_value(analysis)
        self.analysis_history.append(analysis)
        return analysis

    def _generate_explanation(self, analysis: Dict) -> str:
        """Generate scientific explanation using LLM."""
        prompt = f"""
As a lunar geologist analyzing a rock sample, provide a concise scientific assessment:

Rock Type: {analysis["rock_type"]}
Composition: {analysis["composition"]}
Confidence: {analysis["visual_confidence"]:.1%}

What is scientifically significant about this sample? (2-3 sentences)
"""
        try:
            response = self.llm_client.messages.create(
                model=self.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            return f"Analysis pending: {str(e)}"

    def _generate_heuristic_explanation(self, analysis: Dict) -> str:
        """Generate explanation without LLM."""
        rock_type = analysis["rock_type"]
        significance = {
            "basalt": "Volcanic rock indicating past lava flows and geological activity",
            "olivine": "Mantle material; reveals subsurface composition and thermal history",
            "anorthosite": "Ancient lunar highlands; records early lunar differentiation",
            "regolith": "Space weathering and impact processes; useful for dating",
        }
        return significance.get(rock_type, "Rock of interest for further analysis")

    def _score_scientific_value(self, analysis: Dict) -> float:
        """Score the scientific value of a sample (0-1)."""
        base_score = (
            analysis["visual_confidence"] + analysis["spectral_confidence"]
        ) / 2
        rock_value = {
            "anorthosite": 0.95,
            "olivine": 0.85,
            "basalt": 0.75,
            "regolith": 0.6,
            "unknown": 0.3,
        }
        type_bonus = rock_value.get(analysis["rock_type"], 0.3)
        return min(1.0, (base_score * 0.5) + (type_bonus * 0.5))

    def rank_samples(self, samples: List[Dict]) -> List[Dict]:
        """Rank samples by scientific value."""
        ranked = []
        for sample in samples:
            analysis = self.analyze_sample(sample)
            ranked.append(analysis)
        ranked.sort(key=lambda x: x["scientific_value"], reverse=True)
        return ranked

    def get_analysis_summary(self) -> str:
        """Get summary of analyses performed."""
        if not self.analysis_history:
            return "No analyses performed yet."

        top_samples = sorted(
            self.analysis_history, key=lambda x: x["scientific_value"], reverse=True
        )[:5]

        summary = "Top 5 Scientifically Valuable Samples:\n"
        for i, sample in enumerate(top_samples, 1):
            summary += f"{i}. Sample #{sample['sample_id']} ({sample['rock_type']}) - "
            summary += f"Value: {sample['scientific_value']:.2f}\n"

        return summary
