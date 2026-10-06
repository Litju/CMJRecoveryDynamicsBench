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


HISTORICAL_ALIASES: Mapping[str, HistoricalAlias] = MappingProxyType(
    {
        "initial_preseason_camp_recovery": HistoricalAlias(
            specimen_label="SP01",
            world_label="W01",
            observation_label="O01",
            dataset_label="D02",
            task_label="T01",
            historical_labels=("Gate3/L05", "historical V1", "Gate5 public fixture"),
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
        ),
        "rich_history_camp_recovery": HistoricalAlias(
            specimen_label="SP03",
            world_label="W02",
            observation_label="O02",
            dataset_label="D04",
            task_label="T01",
            historical_labels=("LCMJ-V3", "V3", "LCMJ-V3-CANONICAL-HORIZON-ROW-1.1"),
        ),
        "preliminary_post_exposure_recovery": HistoricalAlias(
            specimen_label="SP04",
            world_label="W03",
            observation_label="O03",
            dataset_label="D05",
            task_label="T02",
            historical_labels=("LCMJ-V2", "ALI-494 1.0", "82-field episode task"),
        ),
        "phase_consistent_post_exposure_recovery": HistoricalAlias(
            specimen_label="SP05",
            world_label="W03",
            observation_label="O04",
            dataset_label="D06",
            task_label="T02",
            historical_labels=("LCMJ-V2", "ALI-494 1.1", "phase-mechanics repair"),
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
        ),
        "threshold_response_recovery": HistoricalAlias(
            specimen_label="SP07",
            world_label="W05",
            observation_label="O04",
            dataset_label="D08",
            task_label="T02",
            historical_labels=("C1", "C1 2.1", "LCMJ-V2-PUBLIC-MANIFEST-2.0.0"),
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
            ),
        ),
    }
)
