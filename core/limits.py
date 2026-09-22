from sqlalchemy.ext.asyncio import AsyncSession

from models import SystemLimit


async def get_limits(db: AsyncSession) -> SystemLimit:
    limits = await db.get(SystemLimit, 1)
    if limits is None:
        limits = SystemLimit(id=1)
        db.add(limits)
        await db.commit()
        await db.refresh(limits)
    return limits
