"""菜单服务：树结构构建 + 拖拽排序"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sys_menu import SysMenu
from app.models.relations import sys_role_menu, sys_user_role


class MenuService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_full_menu_tree(self) -> list:
        """获取完整菜单树（仅 M/C）"""
        result = await self.db.execute(
            select(SysMenu)
            .where(SysMenu.status == 1, SysMenu.menu_type.in_(["M", "C"]))
            .order_by(SysMenu.sort_order)
        )
        menus = result.scalars().all()
        return self._build_tree(menus, parent_id=0)

    async def get_user_menu_tree(self, user_id: int, is_super_admin: bool) -> list:
        """获取用户的菜单树（仅 M/C）"""
        if is_super_admin:
            return await self.get_full_menu_tree()

        result = await self.db.execute(
            select(SysMenu)
            .join(sys_role_menu, sys_role_menu.c.menu_id == SysMenu.id)
            .join(sys_user_role, sys_user_role.c.role_id == sys_role_menu.c.role_id)
            .where(
                sys_user_role.c.user_id == user_id,
                SysMenu.status == 1,
                SysMenu.menu_type.in_(["M", "C"]),
            )
            .order_by(SysMenu.sort_order)
            .distinct()
        )
        menus = result.scalars().all()
        return self._build_tree(menus, parent_id=0)

    async def batch_update_sort(self, items: list):
        """批量更新菜单的 parent_id 和 sort_order（拖拽排序）"""
        for item in items:
            menu = await self.db.get(SysMenu, item.id)
            if menu:
                menu.parent_id = item.parent_id
                menu.sort_order = item.sort_order
        await self.db.commit()

    def _build_tree(self, menus: list[SysMenu], parent_id: int = 0) -> list:
        """递归构建树结构（返回给前端的菜单数据结构）"""
        tree: list[dict] = []
        for menu in menus:
            if menu.parent_id == parent_id:
                tree.append(
                    {
                        "id": menu.id,
                        "menu_name": menu.menu_name,
                        "menu_type": menu.menu_type,
                        "path": menu.path,
                        "component": menu.component,
                        "perms": menu.perms,
                        "icon": menu.icon,
                        "sort_order": menu.sort_order,
                        "visible": menu.visible,
                        "children": self._build_tree(menus, menu.id),
                    }
                )
        return tree
