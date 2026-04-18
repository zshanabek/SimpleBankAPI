from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transfer import TransferRequest, TransferResponse
from app.services.transfer import transfer_funds

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferResponse)
def transfer(
    data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transfer_funds(data, current_user, db)
