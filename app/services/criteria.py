import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.criteria import Criteria
from app.models.user import User
from app.schemas.criteria import CriteriaCreate
from app.services.neighborhoods import normalize_neighborhood_list

logger = logging.getLogger(__name__)

TEST_USER_ID = 1


def _select_criteria(db: Session, user_id: int) -> Optional[Criteria]:
    return (
        db.execute(
            select(Criteria)
            .where(Criteria.user_id == user_id)
            .order_by(Criteria.is_active.desc(), Criteria.id.desc())
        )
        .scalars()
        .first()
    )


def get_or_create_user_criteria(
    db: Session, user_id: int, commit_changes: bool = True
) -> Criteria:
    """Retrieve active criteria or prepare a default one.

    This helper is used by read-heavy endpoints (matches, criteria GET).
    If we create or mutate rows, we should commit by default to avoid:
    - Rolling back newly created criteria on request teardown.
    - Holding an open write transaction while doing long-running work (e.g., OpenAI calls),
      which can lock SQLite for ingestion writes.
    """
    criteria = _select_criteria(db, user_id)
    changed = False

    if not criteria:
        user = db.get(User, user_id)
        if not user:
            raise ValueError(
                f"User with id {user_id} not found. Cannot create criteria."
            )
        default_schema = CriteriaCreate(name="Default Criteria")
        criteria = Criteria(**default_schema.model_dump(), user_id=user_id)
        db.add(criteria)
        db.flush()
        changed = True

    if criteria and not criteria.is_active:
        criteria.is_active = True
        changed = True

    if commit_changes and changed:
        try:
            db.commit()
            db.refresh(criteria)
        except SQLAlchemyError as exc:
            logger.error(
                "Database error committing criteria for user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            db.rollback()
            raise
        except Exception as exc:
            logger.error(
                "Unexpected error committing criteria for user %s: %s",
                user_id,
                exc,
                exc_info=True,
            )
            db.rollback()
            raise

    return criteria


def update_user_criteria(
    db: Session, user_id: int, criteria_in: CriteriaCreate
) -> Criteria:
    """Update user's criteria and commit if changes occur."""
    try:
        db_criteria = get_or_create_user_criteria(
            db=db, user_id=user_id, commit_changes=False
        )
        update_data = criteria_in.model_dump(exclude_unset=True)
        needs_update = False
        if "preferred_neighborhoods" in update_data:
            update_data["preferred_neighborhoods"] = normalize_neighborhood_list(
                update_data.get("preferred_neighborhoods")
            )
        if "avoid_neighborhoods" in update_data:
            update_data["avoid_neighborhoods"] = normalize_neighborhood_list(
                update_data.get("avoid_neighborhoods")
            )
        if "price_soft_max" in update_data and "price_max" in update_data:
            soft_cap = update_data.get("price_soft_max")
            hard_cap = update_data.get("price_max")
            if soft_cap and hard_cap and soft_cap > hard_cap:
                update_data["price_soft_max"] = hard_cap
        if "neighborhood_mode" in update_data:
            mode = update_data.get("neighborhood_mode")
            if mode not in {"strict", "boost", None}:
                update_data["neighborhood_mode"] = None
        if "recency_mode" in update_data:
            mode = update_data.get("recency_mode")
            if mode not in {"fresh", "balanced", "hidden_gems", None}:
                update_data["recency_mode"] = None
        for key, value in update_data.items():
            if getattr(db_criteria, key) != value:
                setattr(db_criteria, key, value)
                needs_update = True

        if not db_criteria.is_active:
            db_criteria.is_active = True
            needs_update = True

        if needs_update or db_criteria in db.new:
            db.commit()
            db.refresh(db_criteria)

        return db_criteria
    except SQLAlchemyError as exc:
        logger.error(
            "Database error updating criteria for user %s: %s",
            user_id,
            exc,
            exc_info=True,
        )
        db.rollback()
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error updating criteria for user %s: %s",
            user_id,
            exc,
            exc_info=True,
        )
        db.rollback()
        raise
