import logging # Add logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError

from app.models.criteria import Criteria
from app.models.user import User # Need user model for relationship
from app.schemas.criteria import CriteriaCreate # Only import CriteriaCreate

logger = logging.getLogger(__name__) # Setup logger

# For now, we assume a fixed test user ID
TEST_USER_ID = 1

def get_or_create_user_criteria(db: Session, user_id: int, commit_changes: bool = False) -> Criteria:
    """Retrieves the active OR first criteria for a user, OR prepares a new default one.
       Does NOT commit unless commit_changes is True (used carefully)."""
    logger.debug(f"Getting/creating criteria for user_id: {user_id}")
    criteria = db.query(Criteria).filter(Criteria.user_id == user_id, Criteria.is_active == True).first()
    
    should_commit_later = False # Flag if changes were made that need committing by caller

    if not criteria:
        criteria = db.query(Criteria).filter(Criteria.user_id == user_id).first()
        
    if not criteria:
        logger.debug(f"No criteria found for user {user_id}, preparing new default.")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found in DB.")
            raise ValueError(f"User with id {user_id} not found. Cannot create criteria.")
        
        default_schema = CriteriaCreate(name="Default Criteria") 
        db_criteria = Criteria(**default_schema.model_dump(), user_id=user_id)
        logger.debug(f"Prepared default criteria object: {db_criteria.name}, is_active={db_criteria.is_active}")
        db.add(db_criteria)
        db.flush() # Flush to get ID assigned, but don't commit yet
        logger.info(f"Prepared default criteria for user {user_id} (needs commit).")
        criteria = db_criteria # <--- Assign newly created object back to criteria
        should_commit_later = True # The add needs a commit
        # Do NOT return here, fall through to check/set is_active if needed (though it is already True)
            
    # If found existing criteria, check if it needs activation
    if not criteria.is_active:
        logger.warning(f"Found existing criteria for user {user_id} but it was inactive. Marking active.")
        criteria.is_active = True
        should_commit_later = True # The activation needs a commit
        # Do NOT commit here

    # Optional: Commit here only if explicitly told AND changes were made
    if commit_changes and should_commit_later:
        logger.debug(f"Committing changes within get_or_create for user {user_id}")
        try:
            db.commit()
            db.refresh(criteria)
        except SQLAlchemyError as e:
            logger.error(f"Database error committing within get_or_create for user {user_id}: {e}", exc_info=True)
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error committing within get_or_create for user {user_id}: {e}", exc_info=True)
            db.rollback()
            raise
        
    return criteria

def update_user_criteria(db: Session, user_id: int, criteria_in: CriteriaCreate) -> Criteria:
    """Updates the user's active criteria set (or prepares a new one), then commits."""
    logger.debug(f"Updating criteria for user_id: {user_id}")
    try:
        # Get or prepare the criteria object. This adds/flushes/marks active if needed, but doesn't commit.
        db_criteria = get_or_create_user_criteria(db=db, user_id=user_id, commit_changes=False) 
        
        update_data = criteria_in.model_dump(exclude_unset=True)
        logger.debug(f"Applying update data: {update_data}")
        needs_update = False
        for key, value in update_data.items():
            if getattr(db_criteria, key) != value:
                 setattr(db_criteria, key, value)
                 needs_update = True
        
        # Ensure it's marked active (might have been done by get_or_create)
        if not db_criteria.is_active:
             db_criteria.is_active = True 
             needs_update = True
        
        # Only commit if there were changes
        if needs_update or db.new or db.dirty:
            logger.info(f"Committing updated criteria for user {user_id}")
            db.commit()
            db.refresh(db_criteria)
        else:
            logger.info(f"No changes detected for criteria of user {user_id}. Skipping commit.")
            
        return db_criteria
    except SQLAlchemyError as e:
        logger.error(f"Database error updating criteria for user {user_id}: {e}", exc_info=True)
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating criteria for user {user_id}: {e}", exc_info=True)
        db.rollback()
        raise 