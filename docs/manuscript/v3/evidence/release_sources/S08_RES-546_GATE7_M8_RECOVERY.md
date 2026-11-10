# RES-546: original Gate7 M8 recovery

This is the trained Gate7 M8 candidate, distinct from the earlier M8 release and reference-study milestones. Its complete final-repeat set is M8-r0 and M8-r1. The original model has 10,796 parameters: a 39→64→64 raw backbone, a one-layer 4→32 GRU with mean/latest pooling, a 2×8 horizon embedding, a 5→16 basis projection, a 152→2 residual head and a bias-free 5→2 basis head. Both basis paths consume all five standardized basis values.

Authenticated original configurations, checkpoints, source and validation identities were checked privately. Original fitted preprocessing and all four forward-input tensors were compared for the 24-row synthetic fixture and 512-row historical validation split. For each repeat, recovered inference matched original CPU source exactly and was deterministic. Input tensor and private prediction identities are retained in the private receipt; no trained weights or restricted observations are distributed.

CPU-to-saved-CUDA comparisons use the original rule `abs(replayed-saved) <= 1e-5 + 1e-4*abs(saved)`. Both failed: r0 maximum absolute difference 0.00022125244140625 with 98 of 1,024 elements outside tolerance; r1 maximum 0.00030422210693359375 with 145 outside tolerance. Historical CUDA compatibility is not established. The fixed CPU TF32 approximation had zero tolerance failures for both repeats; it is an explanatory diagnostic, not an authentic CUDA replay. Historical runtime attribution remains unresolved.

CPU source parity does not establish predictive accuracy, generalization, robustness, clinical applicability, production readiness or checkpoint redistribution rights. The existing rights and release decisions remain unchanged.
