
@router.post("/reset-scans-temp")
async def reset_scans_temp(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    current_user.scan_count_today = 0
    await db.commit()
    return {"status": "reset", "user": current_user.email}
