"""Budget Service for the MPCP Project Tracker - Ledger-based."""
import uuid
import logging
from datetime import date
from typing import List
from app.models.mpcp_schemas import (
    BudgetData, BudgetTransaction, BudgetTransactionCreateRequest,
    BudgetTransactionType, BudgetUpdateRequest, RAGStatus,
)

logger = logging.getLogger(__name__)


def create_default_budget(project_id: str) -> BudgetData:
    return BudgetData(project_id=project_id)


def update_budget_metadata(budget: BudgetData, request: BudgetUpdateRequest) -> BudgetData:
    if request.approved_budget is not None:
        budget.approved_budget = request.approved_budget
    if request.internal_estimate is not None:
        budget.internal_estimate = request.internal_estimate
    if request.quarterly_plan is not None:
        budget.quarterly_plan = request.quarterly_plan
    if request.remarks is not None:
        budget.remarks = request.remarks
    _recompute(budget)
    return budget


def add_transaction(budget: BudgetData, request: BudgetTransactionCreateRequest) -> BudgetTransaction:
    txn = BudgetTransaction(
        id=str(uuid.uuid4()),
        transaction_type=request.transaction_type,
        po_number=request.po_number,
        vendor=request.vendor,
        amount=request.amount,
        date=request.date,
        quarter=request.quarter,
        remarks=request.remarks,
    )
    budget.transactions.append(txn)
    _recompute(budget)
    return txn


def remove_transaction(budget: BudgetData, txn_id: str) -> None:
    budget.transactions = [t for t in budget.transactions if t.id != txn_id]
    _recompute(budget)


def _recompute(budget: BudgetData) -> None:
    budget.total_committed = sum(
        t.amount for t in budget.transactions
        if t.transaction_type in (BudgetTransactionType.PO_ISSUED, BudgetTransactionType.CHANGE_REQUEST)
    )
    budget.total_spent = sum(
        t.amount for t in budget.transactions
        if t.transaction_type == BudgetTransactionType.SPEND
    ) - sum(
        t.amount for t in budget.transactions
        if t.transaction_type == BudgetTransactionType.REFUND
    )
    budget.remaining = budget.approved_budget - budget.total_committed


def get_budget_rag(budget: BudgetData) -> RAGStatus:
    if budget.approved_budget <= 0:
        return RAGStatus.GREEN
    if budget.total_spent > budget.approved_budget:
        return RAGStatus.RED
    if budget.total_spent > 0.8 * budget.approved_budget:
        return RAGStatus.YELLOW
    return RAGStatus.GREEN


def is_over_budget(budget: BudgetData) -> bool:
    return budget.approved_budget > 0 and budget.total_spent > budget.approved_budget


def get_budget_utilization_pct(budget: BudgetData) -> float:
    if budget.approved_budget <= 0:
        return 0.0
    return (budget.total_spent / budget.approved_budget) * 100.0
