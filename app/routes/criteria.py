from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.criteria import Criteria as CriteriaSchema
from app.schemas.criteria import CriteriaCreate
from app.services.criteria import (TEST_USER_ID, get_or_create_user_criteria,
                                   update_user_criteria)

router = APIRouter(prefix="/criteria", tags=["criteria"])


@router.get("/user/{user_id}", response_model=CriteriaSchema)
def read_user_criteria(user_id: int, db: Session = Depends(get_db)):
    """Retrieve the active criteria set for a specific user (creates default if none)."""
    # TODO: Later, protect this and get user_id from authenticated user
    try:
        criteria = get_or_create_user_criteria(db=db, user_id=user_id)
        return criteria
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving criteria",
        )


@router.post("/user/{user_id}", response_model=CriteriaSchema)
def save_user_criteria(
    user_id: int, criteria_in: CriteriaCreate, db: Session = Depends(get_db)
):
    """Create or update the active criteria set for a specific user."""
    # TODO: Later, protect this and get user_id from authenticated user
    try:
        updated_criteria = update_user_criteria(
            db=db, user_id=user_id, criteria_in=criteria_in
        )
        return updated_criteria
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving criteria",
        )


@router.get("/test-user", response_model=CriteriaSchema)
def read_test_user_criteria(db: Session = Depends(get_db)):
    return read_user_criteria(user_id=TEST_USER_ID, db=db)


@router.post("/test-user", response_model=CriteriaSchema)
def save_test_user_criteria(criteria_in: CriteriaCreate, db: Session = Depends(get_db)):
    return save_user_criteria(user_id=TEST_USER_ID, criteria_in=criteria_in, db=db)
