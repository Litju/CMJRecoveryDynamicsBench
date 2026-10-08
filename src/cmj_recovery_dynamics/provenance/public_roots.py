"""Preserved public RNG root identities, separate from clean-room seeds."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from cmj_recovery_dynamics.reproduction.contracts import ReproductionStatus


@dataclass(frozen=True, slots=True)
class PublicRootAuthority:
    benchmark: str
    status: ReproductionStatus
    shared_root: str | None = None
    training_root: str | None = None
    validation_root: str | None = None

    def __post_init__(self) -> None:
        split_roots = (self.training_root, self.validation_root)
        if not self.benchmark or any(
            root is not None and not root
            for root in (self.shared_root, self.training_root, self.validation_root)
        ):
            raise ValueError("public root authority needs a benchmark identity")
        if self.status is ReproductionStatus.EXACT:
            shared = self.shared_root is not None and all(root is None for root in split_roots)
            split_specific = self.shared_root is None and all(
                root is not None for root in split_roots
            )
            if not (shared or split_specific):
                raise ValueError("exact public roots need one shared root or both split roots")
        elif self.shared_root is not None or any(root is not None for root in split_roots):
            raise ValueError("unknown public roots cannot include seed values")


PUBLIC_ROOT_AUTHORITIES: Mapping[str, PublicRootAuthority] = MappingProxyType(
    {
        "initial_preseason_camp_recovery": PublicRootAuthority(
            "initial_preseason_camp_recovery", ReproductionStatus.UNKNOWN
        ),
        "canonical_preseason_camp_recovery": PublicRootAuthority(
            "canonical_preseason_camp_recovery", ReproductionStatus.UNKNOWN
        ),
        "rich_history_camp_recovery": PublicRootAuthority(
            "rich_history_camp_recovery",
            ReproductionStatus.EXACT,
            training_root="l05-public-train-v3",
            validation_root="l05-public-validation-v3",
        ),
        "preliminary_post_exposure_recovery": PublicRootAuthority(
            "preliminary_post_exposure_recovery",
            ReproductionStatus.EXACT,
            shared_root="ALI-494-LCMJ-V2-PUBLIC-001",
        ),
        "phase_consistent_post_exposure_recovery": PublicRootAuthority(
            "phase_consistent_post_exposure_recovery",
            ReproductionStatus.EXACT,
            shared_root="ALI-494-LCMJ-V2-PUBLIC-001",
        ),
        "correlated_exposure_recovery": PublicRootAuthority(
            "correlated_exposure_recovery",
            ReproductionStatus.EXACT,
            shared_root="ALI-494-LCMJ-V2-PUBLIC-001",
        ),
        "threshold_response_recovery": PublicRootAuthority(
            "threshold_response_recovery",
            ReproductionStatus.EXACT,
            shared_root="LCMJ-C1-PUBLIC-003-e88b767181cf4e1c",
        ),
        "fixed_mode_discrepancy_recovery": PublicRootAuthority(
            "fixed_mode_discrepancy_recovery",
            ReproductionStatus.EXACT,
            shared_root="ALI-517-CANDIDATE-H-PUBLIC-001",
        ),
    }
)


def get_public_root_authority(benchmark: str) -> PublicRootAuthority:
    """Return the public root record, including explicit unknown authorities."""
    return PUBLIC_ROOT_AUTHORITIES[benchmark]
