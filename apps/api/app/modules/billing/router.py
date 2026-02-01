from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.billing.schemas import (
    BillingStatusOut,
    BillingVersionRequest,
    InvoiceOut,
    InvoicePayRequest,
    PaymentMethodCreate,
    PaymentMethodOut,
    PaymentOut,
)
from app.modules.billing.models import PaymentMethod
from app.modules.billing.service import (
    add_payment_method,
    change_tenant_version,
    generate_invoice_pdf,
    get_billing_status,
    get_invoice,
    list_invoices,
    list_payment_methods,
    process_payment,
    remove_payment_method,
    set_default_payment_method,
)
from app.modules.rbac.deps import require_permissions
from app.modules.tenants.models import Tenant

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/status", response_model=BillingStatusOut)
async def status(
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return await get_billing_status(db, tenant)


@router.post("/version", response_model=BillingStatusOut)
async def change_version(
    payload: BillingVersionRequest,
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    try:
        await change_tenant_version(db, tenant, payload.version, current_user.id, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return await get_billing_status(db, tenant)


@router.get("/invoices", response_model=list[InvoiceOut])
async def invoices(
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_invoices(db, current_user.tenant_id)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def invoice_detail(
    invoice_id: UUID,
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    invoice = await get_invoice(db, current_user.tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/invoices/{invoice_id}/pdf")
async def invoice_pdf(
    invoice_id: UUID,
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    invoice = await get_invoice(db, current_user.tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    pdf_bytes = generate_invoice_pdf(invoice)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice.year_month}.pdf"},
    )


@router.post("/invoices/{invoice_id}/pay", response_model=PaymentOut)
async def pay_invoice(
    invoice_id: UUID,
    payload: InvoicePayRequest,
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    invoice = await get_invoice(db, current_user.tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    tenant = await db.get(Tenant, current_user.tenant_id)
    try:
        payment = await process_payment(db, tenant, invoice, payload.method, payload.payment_method_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return payment


@router.get("/payment-methods", response_model=list[PaymentMethodOut])
async def payment_methods(
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_payment_methods(db, current_user.tenant_id)


@router.post("/payment-methods", response_model=PaymentMethodOut, status_code=201)
async def add_method(
    payload: PaymentMethodCreate,
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    method = await add_payment_method(db, current_user.tenant_id, payload)
    await db.commit()
    return method


@router.delete("/payment-methods/{method_id}", status_code=204)
async def delete_method(
    method_id: UUID,
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    method = await db.get(PaymentMethod, method_id)
    if not method or method.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Payment method not found")
    await remove_payment_method(db, method)
    await db.commit()
    return Response(status_code=204)


@router.post("/payment-methods/{method_id}/set-default", response_model=PaymentMethodOut)
async def set_default(
    method_id: UUID,
    current_user=Depends(require_permissions(["billing:manage"])),
    db: AsyncSession = Depends(get_db),
):
    method = await db.get(PaymentMethod, method_id)
    if not method or method.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Payment method not found")
    method = await set_default_payment_method(db, method)
    await db.commit()
    return method
