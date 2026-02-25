from __future__ import annotations

"""Deterministic scoring engine for training exercises."""

from datetime import datetime, timezone
from uuid import UUID

from app.models import ExerciseScore, ObjectiveStatus, ObjectiveType


def calculate_exercise_score(
    exercise_id: UUID,
    objectives: list[dict],
    injects: list[dict] | None = None,
) -> ExerciseScore:
    """
    Compute an ExerciseScore from a list of scored objectives (dicts with keys:
    objective_type, status, score, weight) and optionally a list of injects
    (dicts with keys: trigger_type, injected_at, acknowledged_at).
    """
    injects = injects or []

    met = 0
    partial = 0
    not_met = 0
    skipped = 0
    total = len(objectives)

    weighted_sum = 0.0
    total_weight = 0.0

    # Per-type accumulators for sub-scores
    comm_scores: list[float] = []

    for obj in objectives:
        obj_status = obj.get("status", ObjectiveStatus.PENDING)
        obj_score = obj.get("score")
        weight = float(obj.get("weight", 1.0))
        obj_type = obj.get("objective_type", "")

        if obj_status in (ObjectiveStatus.PENDING, ObjectiveStatus.SKIPPED, "PENDING", "SKIPPED"):
            skipped += 1
            continue

        # Derive a numeric score if not explicitly provided
        if obj_score is None:
            if obj_status in (ObjectiveStatus.MET, "MET"):
                obj_score = 100.0
            elif obj_status in (ObjectiveStatus.PARTIALLY_MET, "PARTIALLY_MET"):
                obj_score = 50.0
            else:
                obj_score = 0.0

        obj_score = float(obj_score)

        if obj_status in (ObjectiveStatus.MET, "MET"):
            met += 1
        elif obj_status in (ObjectiveStatus.PARTIALLY_MET, "PARTIALLY_MET"):
            partial += 1
        else:
            not_met += 1

        weighted_sum += obj_score * weight
        total_weight += weight

        if obj_type in (ObjectiveType.COMMUNICATION, "COMMUNICATION"):
            comm_scores.append(obj_score)

    # Total score: weighted average of scored objectives
    scored_count = met + partial + not_met
    if total_weight > 0:
        total_score = weighted_sum / total_weight
    else:
        total_score = 0.0

    # Completion percentage (non-skipped / total)
    completion_pct = (scored_count / total * 100.0) if total > 0 else 0.0

    # Accuracy score: ratio of MET objectives among non-skipped
    if scored_count > 0:
        accuracy_score = ((met + 0.5 * partial) / scored_count) * 100.0
    else:
        accuracy_score = 0.0

    # Communication score
    communication_score = (sum(comm_scores) / len(comm_scores)) if comm_scores else accuracy_score

    # Timeliness score: ratio of TIME_BASED injects acknowledged within 5 minutes
    time_based = [
        inj for inj in injects
        if inj.get("trigger_type") in ("TIME_BASED", "TIME_BASED")
        and inj.get("injected_at") is not None
        and inj.get("acknowledged_at") is not None
    ]
    if time_based:
        timely = 0
        for inj in time_based:
            injected = inj["injected_at"]
            acked = inj["acknowledged_at"]
            if isinstance(injected, str):
                injected = datetime.fromisoformat(injected)
            if isinstance(acked, str):
                acked = datetime.fromisoformat(acked)
            delta_minutes = (acked - injected).total_seconds() / 60.0
            if delta_minutes <= 5.0:
                timely += 1
        timeliness_score = (timely / len(time_based)) * 100.0
    else:
        timeliness_score = 100.0  # No timed injects — full marks by default

    # Grade thresholds
    if total_score >= 90:
        grade = "A"
    elif total_score >= 80:
        grade = "B"
    elif total_score >= 70:
        grade = "C"
    elif total_score >= 60:
        grade = "D"
    else:
        grade = "F"

    return ExerciseScore(
        exercise_id=exercise_id,
        total_score=round(total_score, 2),
        objectives_met=met,
        objectives_partial=partial,
        objectives_not_met=not_met,
        objectives_total=total,
        completion_pct=round(completion_pct, 2),
        timeliness_score=round(timeliness_score, 2),
        accuracy_score=round(accuracy_score, 2),
        communication_score=round(communication_score, 2),
        grade=grade,
        scored_at=datetime.now(tz=timezone.utc),
    )
