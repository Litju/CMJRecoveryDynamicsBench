"""Optional mappings from scientific benchmark names to preserved historical identities."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class HistoricalAlias:
    specimen_label: str
    world_label: str
    observation_label: str
    dataset_label: str
    task_label: str
    historical_labels: tuple[str, ...]
    preserved_commit_reference: str
    preserved_tree_reference: str


HISTORICAL_ALIASES: Mapping[str, HistoricalAlias] = MappingProxyType(
    {
        "initial_preseason_camp_recovery": HistoricalAlias(
            specimen_label="SP01",
            world_label="W01",
            observation_label="O01",
            dataset_label="D02",
            task_label="T01",
            historical_labels=("Gate3/L05", "historical V1", "Gate5 public fixture"),
            preserved_commit_reference="21066991371a58c3ae309c9f33e2dbba699a1cd0",
            preserved_tree_reference="037fd0510dec208d20d9af5eb10f4812ee423abf",
        ),
        "canonical_preseason_camp_recovery": HistoricalAlias(
            specimen_label="SP02",
            world_label="W01",
            observation_label="O01",
            dataset_label="D03",
            task_label="T01",
            historical_labels=(
                "CYCLE3",
                "early V2",
                "Gate6 canonical surface",
                "LCMJ-V2-CANONICAL-HORIZON-ROW-1.0",
            ),
            preserved_commit_reference="6261c409ee522dd3e074cc5f5cbfc3cba471fae1",
            preserved_tree_reference="c3cd13ea8328c3a877d7845b51fed86853b70f2f",
        ),
        "rich_history_camp_recovery": HistoricalAlias(
            specimen_label="SP03",
            world_label="W02",
            observation_label="O02",
            dataset_label="D04",
            task_label="T01",
            historical_labels=("LCMJ-V3", "V3", "LCMJ-V3-CANONICAL-HORIZON-ROW-1.1"),
            preserved_commit_reference="ad5e48a1dc9c1fd1e27ecd314940a9be1b4fd50a",
            preserved_tree_reference="e2871ccac43e4e6b7dfaa0c7cc2eec9d05b03e0b",
        ),
        "preliminary_post_exposure_recovery": HistoricalAlias(
            specimen_label="SP04",
            world_label="W03",
            observation_label="O03",
            dataset_label="D05",
            task_label="T02",
            historical_labels=("LCMJ-V2", "ALI-494 1.0", "82-field episode task"),
            preserved_commit_reference="da3fa115838b177f5ba2bd055a5c3465654c4e22",
            preserved_tree_reference="e11c1140b362c52d40942463bb0714171ae165f8",
        ),
        "phase_consistent_post_exposure_recovery": HistoricalAlias(
            specimen_label="SP05",
            world_label="W03",
            observation_label="O04",
            dataset_label="D06",
            task_label="T02",
            historical_labels=("LCMJ-V2", "ALI-494 1.1", "phase-mechanics repair"),
            preserved_commit_reference="04e9db465a481a88f18e8fc062e317269204dce8",
            preserved_tree_reference="5ef8ad267d3e57f8fa73dd3b82967937291b20ca",
        ),
        "correlated_exposure_recovery": HistoricalAlias(
            specimen_label="SP06",
            world_label="W04",
            observation_label="O04",
            dataset_label="D07",
            task_label="T02",
            historical_labels=(
                "LCMJ-V2",
                "ALI-506 1.2",
                "four-factor/four-archetype exposure redesign",
            ),
            preserved_commit_reference="144d283f7b43e6c1a2972b8b58cfc3e4e05b384a",
            preserved_tree_reference="7dbd339858555e11065f9a022820708d8c012f96",
        ),
        "threshold_response_recovery": HistoricalAlias(
            specimen_label="SP07",
            world_label="W05",
            observation_label="O04",
            dataset_label="D08",
            task_label="T02",
            historical_labels=(
                "C1",
                "C1 2.1",
                "LCMJ-V2-PARAMETERS-C1-2.1.0",
                "LCMJ-C1-PUBLIC-003-e88b767181cf4e1c",
                "LCMJ-V2-PUBLIC-MANIFEST-2.0.0",
            ),
            preserved_commit_reference="059f42ebc7396662dba04f0b0021d834e4e1aa79",
            preserved_tree_reference="d6758ab6f75262121bc6b6df1eb995cb32567386",
        ),
        "fixed_mode_discrepancy_recovery": HistoricalAlias(
            specimen_label="SP08",
            world_label="W06",
            observation_label="O04",
            dataset_label="D09",
            task_label="T02",
            historical_labels=(
                "Candidate H",
                "ALI-517",
                "LCMJ-CANDIDATE-H-PARAMETERS-ALI-517-1.0.0",
                "current V2 task state",
                "ALI-517-CANDIDATE-H-PUBLIC-001",
            ),
            preserved_commit_reference="984a9c740f7fab11d5ae10c5eee3c99f53f43537",
            preserved_tree_reference="96dd5450512aca55d42c90c7c1a845ebbb2887bd",
        ),
    }
)
