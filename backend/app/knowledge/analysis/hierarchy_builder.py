"""Hierarchy Builder for constructing parent-child document trees."""

from typing import Dict, List
from app.knowledge.exceptions import HierarchyBuilderError
from app.knowledge.models.section import Section
from app.utils.logging import logger


class HierarchyBuilder:
    """Builds hierarchical parent-child relationships across document Section objects."""

    @classmethod
    def build_hierarchy(cls, sections: List[Section]) -> List[Section]:
        """Constructs parent-child hierarchy tree from a flat list of Section objects in reading order.

        Updates parent_id and children_ids attributes across section objects.

        Args:
            sections (List[Section]): Flat ordered list of Section objects.

        Returns:
            List[Section]: List of top-level root Section objects with children_ids populated.

        Raises:
            HierarchyBuilderError: If hierarchy construction fails.
        """
        if not sections:
            return []

        logger.info(f"Building document hierarchy tree across {len(sections)} sections...")

        try:
            # Map of section ID to Section object for fast lookup & mutation
            section_map: Dict[str, Section] = {sec.id: sec for sec in sections}

            # Level stack maintaining active parent for each level (level 1 to 6)
            # Level 1 is top-level H1/Section, Level 2 is H2/Subsection, etc.
            stack: Dict[int, Section] = {}

            root_sections: List[Section] = []

            for sec in sections:
                current_level = sec.level

                # Find nearest parent in stack with level < current_level
                parent: Section | None = None
                for lvl in range(current_level - 1, 0, -1):
                    if lvl in stack:
                        parent = stack[lvl]
                        break

                if parent:
                    sec.parent_id = parent.id
                    if sec.id not in parent.children_ids:
                        parent.children_ids.append(sec.id)
                else:
                    sec.parent_id = None
                    root_sections.append(sec)

                # Set current section as the active stack parent for current_level
                stack[current_level] = sec

                # Clear lower level stack entries (since siblings/children reset below current level)
                keys_to_clear = [lvl for lvl in stack if lvl > current_level]
                for lvl in keys_to_clear:
                    del stack[lvl]

            logger.info(
                f"Successfully built document hierarchy. "
                f"Top-level root sections: {len(root_sections)}, Total sections linked: {len(sections)}."
            )
            return root_sections

        except Exception as e:
            logger.error(f"Hierarchy construction failed: {e}")
            raise HierarchyBuilderError(f"Failed to build section hierarchy: {str(e)}") from e
