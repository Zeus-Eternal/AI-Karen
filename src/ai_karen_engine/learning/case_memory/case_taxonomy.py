"""
Case Taxonomy and Clustering - Intelligent Organization

This module provides advanced case organization through:
- Automatic clustering and categorization
- Hierarchical taxonomy construction
- Skill discovery and mapping
- Pattern mining and relationship detection
- Knowledge graph construction
- Dynamic taxonomy evolution
"""

from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime
from .case_types import Case

logger = logging.getLogger(__name__)


@dataclass
class ClusterInfo:
    """Information about a case cluster"""
    cluster_id: str
    name: str
    description: str
    centroid: Optional[List[float]]
    case_ids: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    avg_reward: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    parent_cluster: Optional[str] = None
    child_clusters: Set[str] = field(default_factory=set)


@dataclass
class SkillPattern:
    """Discovered skill pattern"""
    skill_id: str
    name: str
    description: str
    tool_sequence: List[str]
    success_rate: float
    use_count: int
    example_cases: List[str]
    prerequisites: Set[str] = field(default_factory=set)
    outcomes: Set[str] = field(default_factory=set)


@dataclass
class TaxonomyNode:
    """Node in the taxonomy tree"""
    node_id: str
    name: str
    level: int  # 0=root, 1=domain, 2=category, 3=subcategory
    description: str
    parent: Optional[str] = None
    children: Set[str] = field(default_factory=set)
    case_ids: Set[str] = field(default_factory=set)
    keywords: Set[str] = field(default_factory=set)
    cluster_ids: Set[str] = field(default_factory=set)


class CaseTaxonomyEngine:
    """
    Intelligent case taxonomy and clustering engine

    Features:
    - Automatic hierarchical clustering
    - Dynamic taxonomy construction
    - Skill pattern discovery
    - Relationship mining
    - Knowledge graph building
    - Taxonomy evolution tracking
    """

    def __init__(
        self,
        max_clusters: int = 50,
        min_cluster_size: int = 3,
        similarity_threshold: float = 0.75
    ):
        self.max_clusters = max_clusters
        self.min_cluster_size = min_cluster_size
        self.similarity_threshold = similarity_threshold

        # Storage
        self.clusters: Dict[str, ClusterInfo] = {}
        self.taxonomy: Dict[str, TaxonomyNode] = {}
        self.skills: Dict[str, SkillPattern] = {}
        self.case_cluster_map: Dict[str, str] = {}  # case_id -> cluster_id
        self.knowledge_graph: Dict[str, Set[str]] = defaultdict(set)

        # Initialize root taxonomy node
        self._initialize_taxonomy()

    def _initialize_taxonomy(self) -> None:
        """Initialize root taxonomy structure"""
        root = TaxonomyNode(
            node_id="root",
            name="All Cases",
            level=0,
            description="Root node containing all case categories"
        )
        self.taxonomy["root"] = root

    def cluster_cases(self, cases: List[Case], method: str = "hierarchical") -> Dict[str, ClusterInfo]:
        """
        Cluster cases using specified method

        Args:
            cases: List of cases to cluster
            method: Clustering method ('hierarchical', 'kmeans', 'dbscan')

        Returns:
            Dictionary of cluster_id to ClusterInfo
        """
        if not cases:
            return {}

        # Extract embeddings
        embeddings = []
        case_ids = []
        for case in cases:
            if case.embeddings and case.embeddings.get('task'):
                embeddings.append(case.embeddings['task'])
                case_ids.append(case.case_id)

        if not embeddings:
            logger.warning("No embeddings available for clustering")
            return {}

        embeddings_array = np.array(embeddings)

        # Perform clustering based on method
        if method == "hierarchical":
            labels = self._hierarchical_clustering(embeddings_array)
        elif method == "kmeans":
            labels = self._kmeans_clustering(embeddings_array)
        elif method == "dbscan":
            labels = self._dbscan_clustering(embeddings_array)
        else:
            raise ValueError(f"Unknown clustering method: {method}")

        # Create cluster objects
        clusters = self._create_clusters(cases, case_ids, labels, embeddings_array)

        # Update internal state
        self.clusters.update(clusters)
        for case_id, cluster_id in zip(case_ids, labels):
            if cluster_id >= 0:  # DBSCAN can return -1 for noise
                self.case_cluster_map[case_id] = f"cluster_{cluster_id}"

        return clusters

    def _hierarchical_clustering(self, embeddings: np.ndarray) -> List[int]:
        """Perform hierarchical clustering"""
        from scipy.cluster.hierarchy import linkage, fcluster
        from scipy.spatial.distance import pdist

        # Calculate linkage
        distances = pdist(embeddings, metric='cosine')
        Z = linkage(distances, method='ward')

        # Form flat clusters
        labels = fcluster(Z, t=1-self.similarity_threshold, criterion='distance')
        return labels - 1  # Convert to 0-indexed

    def _kmeans_clustering(self, embeddings: np.ndarray) -> List[int]:
        """Perform K-means clustering"""
        from sklearn.cluster import KMeans

        # Determine optimal k
        n_samples = len(embeddings)
        k = min(int(np.sqrt(n_samples / 2)), self.max_clusters)
        k = max(k, 2)

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        return labels.tolist()

    def _dbscan_clustering(self, embeddings: np.ndarray) -> List[int]:
        """Perform DBSCAN clustering"""
        from sklearn.cluster import DBSCAN

        dbscan = DBSCAN(
            eps=1-self.similarity_threshold,
            min_samples=self.min_cluster_size,
            metric='cosine'
        )
        labels = dbscan.fit_predict(embeddings)
        return labels.tolist()

    def _create_clusters(
        self,
        cases: List[Case],
        case_ids: List[str],
        labels: List[int],
        embeddings: np.ndarray
    ) -> Dict[str, ClusterInfo]:
        """Create cluster info objects from clustering results"""
        clusters = {}
        case_map = {c.case_id: c for c in cases}

        # Group by cluster label
        cluster_groups = defaultdict(list)
        for idx, (case_id, label) in enumerate(zip(case_ids, labels)):
            if label >= 0:  # Skip noise points
                cluster_groups[label].append((case_id, idx))

        # Create cluster info for each group
        for label, group in cluster_groups.items():
            if len(group) < self.min_cluster_size:
                continue

            cluster_id = f"cluster_{label}"
            member_case_ids = [cid for cid, _ in group]
            member_indices = [idx for _, idx in group]

            # Calculate centroid
            centroid = np.mean(embeddings[member_indices], axis=0).tolist()

            # Collect tags and calculate avg reward
            all_tags = set()
            total_reward = 0.0
            for cid in member_case_ids:
                case = case_map[cid]
                all_tags.update(case.tags)
                total_reward += case.reward.score

            avg_reward = total_reward / len(member_case_ids)

            # Generate cluster name and description
            name, description = self._generate_cluster_metadata(
                member_case_ids, case_map, all_tags
            )

            cluster = ClusterInfo(
                cluster_id=cluster_id,
                name=name,
                description=description,
                centroid=centroid,
                case_ids=set(member_case_ids),
                tags=all_tags,
                avg_reward=avg_reward
            )

            clusters[cluster_id] = cluster

        return clusters

    def _generate_cluster_metadata(
        self,
        case_ids: List[str],
        case_map: Dict[str, Case],
        tags: Set[str]
    ) -> Tuple[str, str]:
        """Generate name and description for cluster"""
        # Use most common tags
        if tags:
            most_common = Counter(tags).most_common(3)
            name = " / ".join([tag for tag, _ in most_common])
        else:
            name = f"Cluster {len(self.clusters) + 1}"

        # Generate description from case patterns
        case_sample = [case_map[cid] for cid in case_ids[:5]]
        tool_usage = Counter()
        for case in case_sample:
            for step in case.steps:
                if step.tool_io:
                    tool_usage[step.tool_io.tool_name] += 1

        common_tools = [tool for tool, _ in tool_usage.most_common(3)]

        description = f"Cases involving {', '.join(common_tools) if common_tools else 'various operations'}"
        description += f" ({len(case_ids)} cases, avg reward: {sum(case_map[cid].reward.score for cid in case_ids) / len(case_ids):.2f})"

        return name, description

    def build_taxonomy(self, cases: List[Case]) -> Dict[str, TaxonomyNode]:
        """
        Build hierarchical taxonomy from cases

        Creates a multi-level taxonomy:
        Level 0: Root
        Level 1: Domains (broad categories)
        Level 2: Categories
        Level 3: Subcategories
        """
        # First cluster cases
        if not self.clusters:
            self.cluster_cases(cases)

        # Build domain level (level 1) from clusters
        domain_map = self._create_domains_from_clusters()

        # Build category level (level 2) from tags
        category_map = self._create_categories_from_tags(cases)

        # Link domains and categories
        self._link_taxonomy_levels(domain_map, category_map)

        # Update internal taxonomy
        self.taxonomy.update(domain_map)
        self.taxonomy.update(category_map)

        return self.taxonomy

    def _create_domains_from_clusters(self) -> Dict[str, TaxonomyNode]:
        """Create domain-level taxonomy nodes from clusters"""
        domains = {}

        # Group similar clusters into domains
        cluster_list = list(self.clusters.values())
        if not cluster_list:
            return domains

        # Simple approach: create domains from top-level clusters
        for idx, cluster in enumerate(cluster_list):
            domain_id = f"domain_{idx}"
            domain = TaxonomyNode(
                node_id=domain_id,
                name=cluster.name,
                level=1,
                description=cluster.description,
                parent="root",
                case_ids=cluster.case_ids.copy(),
                keywords=cluster.tags.copy(),
                cluster_ids={cluster.cluster_id}
            )

            domains[domain_id] = domain
            self.taxonomy["root"].children.add(domain_id)

        return domains

    def _create_categories_from_tags(self, cases: List[Case]) -> Dict[str, TaxonomyNode]:
        """Create category-level taxonomy nodes from case tags"""
        categories = {}

        # Collect tag frequencies
        tag_cases = defaultdict(set)
        for case in cases:
            for tag in case.tags:
                tag_cases[tag].add(case.case_id)

        # Create category for each significant tag
        for idx, (tag, case_ids) in enumerate(tag_cases.items()):
            if len(case_ids) >= self.min_cluster_size:
                category_id = f"category_{tag.replace(' ', '_')}"
                category = TaxonomyNode(
                    node_id=category_id,
                    name=tag.title(),
                    level=2,
                    description=f"Cases tagged with '{tag}'",
                    case_ids=case_ids,
                    keywords={tag}
                )
                categories[category_id] = category

        return categories

    def _link_taxonomy_levels(
        self,
        domains: Dict[str, TaxonomyNode],
        categories: Dict[str, TaxonomyNode]
    ) -> None:
        """Link taxonomy levels based on case overlap"""
        for cat_id, category in categories.items():
            best_domain = None
            max_overlap = 0

            # Find domain with most case overlap
            for dom_id, domain in domains.items():
                overlap = len(category.case_ids & domain.case_ids)
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_domain = dom_id

            # Link category to best matching domain
            if best_domain and max_overlap >= self.min_cluster_size:
                category.parent = best_domain
                domains[best_domain].children.add(cat_id)

    def discover_skills(self, cases: List[Case]) -> Dict[str, SkillPattern]:
        """
        Discover skill patterns from case execution traces

        Identifies common tool sequences and operation patterns
        """
        # Extract tool sequences from cases
        tool_sequences = defaultdict(list)  # sequence -> [case_ids]

        for case in cases:
            if not case.steps:
                continue

            # Extract tool sequence
            sequence = tuple(
                step.tool_io.tool_name
                for step in case.steps
                if step.tool_io
            )

            if len(sequence) >= 2:  # Minimum sequence length
                tool_sequences[sequence].append(case.case_id)

        # Create skill patterns from frequent sequences
        skills = {}
        for idx, (sequence, case_ids) in enumerate(tool_sequences.items()):
            if len(case_ids) >= self.min_cluster_size:
                # Calculate success rate
                cases_dict = {c.case_id: c for c in cases}
                success_count = sum(
                    1 for cid in case_ids
                    if cases_dict[cid].reward.score >= 0.6
                )
                success_rate = success_count / len(case_ids)

                skill_id = f"skill_{idx}"
                skill = SkillPattern(
                    skill_id=skill_id,
                    name=self._generate_skill_name(sequence),
                    description=f"Pattern using {' -> '.join(sequence)}",
                    tool_sequence=list(sequence),
                    success_rate=success_rate,
                    use_count=len(case_ids),
                    example_cases=case_ids[:5]
                )

                skills[skill_id] = skill

        self.skills.update(skills)
        return skills

    def _generate_skill_name(self, sequence: Tuple[str, ...]) -> str:
        """Generate a readable name for a skill pattern"""
        if len(sequence) <= 3:
            return " + ".join(sequence)
        else:
            return f"{sequence[0]} ... {sequence[-1]} ({len(sequence)} steps)"

    def build_knowledge_graph(self, cases: List[Case]) -> Dict[str, Set[str]]:
        """
        Build knowledge graph connecting related cases, clusters, and skills

        Graph structure:
        - case -> cluster
        - case -> skill
        - cluster -> domain
        - skill -> skill (prerequisites)
        """
        graph = defaultdict(set)

        # Link cases to clusters
        for case_id, cluster_id in self.case_cluster_map.items():
            graph[case_id].add(cluster_id)
            graph[cluster_id].add(case_id)

        # Link cases to skills
        for skill_id, skill in self.skills.items():
            for case_id in skill.example_cases:
                graph[case_id].add(skill_id)
                graph[skill_id].add(case_id)

        # Link clusters to domains
        for domain_id, domain in self.taxonomy.items():
            if domain.level == 1:
                for cluster_id in domain.cluster_ids:
                    graph[cluster_id].add(domain_id)
                    graph[domain_id].add(cluster_id)

        # Detect skill prerequisites based on co-occurrence
        self._detect_skill_relationships(cases, graph)

        self.knowledge_graph = graph
        return dict(graph)

    def _detect_skill_relationships(self, cases: List[Case], graph: Dict[str, Set[str]]) -> None:
        """Detect prerequisite relationships between skills"""
        # Build skill co-occurrence matrix
        skill_cooccurrence = defaultdict(Counter)

        case_skills = defaultdict(set)
        for skill_id, skill in self.skills.items():
            for case_id in skill.example_cases:
                case_skills[case_id].add(skill_id)

        # Count co-occurrences
        for case_id, skills in case_skills.items():
            for skill1 in skills:
                for skill2 in skills:
                    if skill1 != skill2:
                        skill_cooccurrence[skill1][skill2] += 1

        # Establish prerequisite relationships
        for skill1_id, cooccur in skill_cooccurrence.items():
            for skill2_id, count in cooccur.items():
                # If skill2 frequently occurs with skill1, it might be a prerequisite
                if count >= self.min_cluster_size:
                    self.skills[skill1_id].prerequisites.add(skill2_id)
                    graph[skill1_id].add(skill2_id)

    def get_recommendations(
        self,
        case: Case,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations for related cases, skills, and clusters

        Args:
            case: Case to find recommendations for
            top_k: Number of recommendations to return

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Find similar clusters
        if case.embeddings and case.embeddings.get('task'):
            similar_clusters = self._find_similar_clusters(
                case.embeddings['task'],
                top_k
            )
            recommendations.extend([
                {
                    'type': 'cluster',
                    'id': cluster_id,
                    'name': self.clusters[cluster_id].name,
                    'similarity': sim,
                    'avg_reward': self.clusters[cluster_id].avg_reward
                }
                for cluster_id, sim in similar_clusters
            ])

        # Find relevant skills
        case_tools = {
            step.tool_io.tool_name
            for step in case.steps
            if step.tool_io
        }
        relevant_skills = [
            skill for skill in self.skills.values()
            if any(tool in case_tools for tool in skill.tool_sequence)
        ]
        recommendations.extend([
            {
                'type': 'skill',
                'id': skill.skill_id,
                'name': skill.name,
                'success_rate': skill.success_rate,
                'use_count': skill.use_count
            }
            for skill in sorted(relevant_skills, key=lambda s: s.success_rate, reverse=True)[:top_k]
        ])

        return recommendations[:top_k]

    def _find_similar_clusters(
        self,
        embedding: List[float],
        top_k: int
    ) -> List[Tuple[str, float]]:
        """Find clusters most similar to given embedding"""
        similarities = []

        for cluster_id, cluster in self.clusters.items():
            if cluster.centroid:
                sim = self._cosine_similarity(embedding, cluster.centroid)
                similarities.append((cluster_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot / (norm1 * norm2))


# Global taxonomy engine instance
_global_taxonomy: Optional[CaseTaxonomyEngine] = None

def get_taxonomy_engine() -> CaseTaxonomyEngine:
    """Get global taxonomy engine instance"""
    global _global_taxonomy
    if _global_taxonomy is None:
        _global_taxonomy = CaseTaxonomyEngine()
    return _global_taxonomy
