"""Dynamic skill selection based on user query."""

from typing import List, Optional, Set

from src.config.logging import get_logger
from src.llm import LLMClient, LLMMessage
from src.models.llm_config import LLMConfig
from src.skills.models import Skill

logger = get_logger(__name__)


class SkillSelector:
    """
    Selects relevant skills for a user query using LLM.

    Instead of injecting all skills into the system prompt (which wastes tokens
    and dilutes focus), this selector picks only the most relevant skills
    for each specific query.
    """

    def __init__(self, llm_config: LLMConfig):
        """
        Initialize SkillSelector.

        Args:
            llm_config: LLM configuration for making selection calls
        """
        self._provider = LLMClient.get_provider(llm_config)

    async def select(
        self,
        query: str,
        available_skills: List[Skill],
        max_skills: int = 2,
        user_id: Optional[str] = None,
    ) -> List[Skill]:
        """
        Select the most relevant skills for the given query.

        Args:
            query: The user's input/question
            available_skills: List of all enabled skills to choose from
            max_skills: Maximum number of skills to select (default: 2)
            user_id: Optional user ID for LLM call tracking

        Returns:
            List of selected skills, ordered by relevance
        """
        # No selection needed if few skills
        if len(available_skills) <= max_skills:
            logger.debug(
                "skill_selection_skipped",
                reason="few_skills",
                skill_count=len(available_skills),
            )
            return available_skills

        # Build selection prompt
        skill_descriptions = self._format_skill_options(available_skills)
        skill_ids = [s.id for s in available_skills]

        system_prompt = """You are a skill selector. Your job is to pick the most relevant skill(s) for a user query.

Rules:
- Select skills that directly help answer the query
- Prefer skills whose domain matches the query topic
- If no skills are relevant, respond with "none"
- Return ONLY skill IDs, one per line, nothing else"""

        user_prompt = f"""USER QUERY: {query}

AVAILABLE SKILLS:
{skill_descriptions}

Select up to {max_skills} most relevant skill ID(s). Return ONLY the ID(s), one per line."""

        try:
            response = await self._provider.complete(
                [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_prompt),
                ],
                user_id=user_id or "system",
                agent_id="skill-selector",
            )

            selected_ids = self._parse_response(response.content, skill_ids)

            # Filter to only valid selected skills, maintaining order
            selected_skills = [s for s in available_skills if s.id in selected_ids]

            logger.info(
                "skills_selected",
                query_preview=query[:50],
                available_count=len(available_skills),
                selected_count=len(selected_skills),
                selected_ids=[s.id for s in selected_skills],
            )

            # If no valid skills selected, return all (fallback)
            if not selected_skills:
                logger.warning(
                    "skill_selection_fallback",
                    reason="no_valid_selection",
                    raw_response=response.content[:100],
                )
                return available_skills

            return selected_skills

        except Exception as e:
            # On any error, fall back to using all skills
            logger.error(
                "skill_selection_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return available_skills

    def _format_skill_options(self, skills: List[Skill]) -> str:
        """Format skills for the selection prompt."""
        lines = []
        for skill in skills:
            lines.append(f"ID: {skill.id}")
            lines.append(f"  Name: {skill.name}")
            lines.append(f"  Domain: {skill.definition.capability.expertise.domain}")
            lines.append(f"  Description: {skill.description}")
            if skill.tags:
                lines.append(f"  Tags: {', '.join(skill.tags)}")
            lines.append("")
        return "\n".join(lines)

    def _parse_response(self, content: str, valid_ids: List[str]) -> Set[str]:
        """
        Parse skill IDs from LLM response.

        Args:
            content: Raw LLM response
            valid_ids: List of valid skill IDs to match against

        Returns:
            Set of valid skill IDs found in response
        """
        if not content:
            return set()

        content_lower = content.lower().strip()

        # Check for explicit "none" response
        if content_lower == "none" or content_lower == "none.":
            return set()

        # Extract IDs from response
        selected = set()

        # Try line-by-line parsing
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check if this line matches any valid ID
            for valid_id in valid_ids:
                if valid_id in line or valid_id.lower() in line.lower():
                    selected.add(valid_id)
                    break

        return selected
