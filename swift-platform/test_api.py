"""SwiftPlatform API 功能测试脚本 - 根据 httpx 官方文档正确用法"""

import asyncio
import httpx

BASE_URL = "http://localhost:8090/api"


class APITester:
    def __init__(self):
        # 创建 AsyncClient，设置 base_url
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30)
        self.results = []

    def _log(self, name: str, ok: bool, detail: str = ""):
        tag = "✅" if ok else "❌"
        self.results.append((name, ok, detail))
        print(f"  {tag} {name}" + (f" — {detail}" if detail else ""))

    # ==================== 认证模块 ====================

    async def test_login(self) -> bool:
        """登录并更新 client.headers"""
        try:
            # 登录请求（不需要 token）
            resp = await self.client.post("/auth/login", json={
                "username": "admin", "password": "admin123"
            })
            data = resp.json()
            
            if resp.status_code == 200 and data.get("code") == 200:
                token = data["data"]["access_token"]
                # 关键：登录成功后，直接更新 client.headers
                # 根据 httpx 文档，这样所有后续请求都会自动带上这个 header
                self.client.headers["Authorization"] = f"Bearer {token}"
                self._log("登录", True, f"token={token[:20]}...")
                return True
            else:
                self._log("登录", False, f"code={data.get('code')}, msg={data.get('message')}")
                return False
        except Exception as e:
            self._log("登录", False, str(e))
            return False

    async def test_user_info(self):
        """后续请求自动带上 Authorization header"""
        try:
            resp = await self.client.get("/auth/user-info")
            data = resp.json()
            if resp.status_code == 200 and data.get("code") == 200:
                user = data.get("data", {}).get("user", {})
                self._log("获取用户信息", user.get("username") == "admin", f"username={user.get('username')}")
            else:
                self._log("获取用户信息", False, f"HTTP {resp.status_code}, code={data.get('code')}, msg={data.get('message')}")
        except Exception as e:
            self._log("获取用户信息", False, str(e))

    async def test_change_password(self):
        try:
            resp = await self.client.put("/auth/password", json={
                "old_password": "admin123", "new_password": "admin123"
            })
            data = resp.json()
            self._log("修改密码", data.get("code") == 200, str(data) if data.get("code") != 200 else "")
        except Exception as e:
            self._log("修改密码", False, str(e))

    # ==================== 用户管理 ====================

    async def test_user_list(self):
        try:
            resp = await self.client.get("/system/user?page=1&page_size=10")
            data = resp.json()
            if data.get("code") == 200:
                items = data.get("data", [])
                self._log("用户列表", True, f"count={len(items)}, total={data.get('total')}")
            else:
                self._log("用户列表", False, f"code={data.get('code')}, msg={data.get('message')}")
        except Exception as e:
            self._log("用户列表", False, str(e))

    async def test_user_create_and_delete(self):
        try:
            # 先尝试删除可能残留的测试用户
            resp0 = await self.client.get("/system/user?page=1&page_size=100&username=test_api_user")
            data0 = resp0.json()
            if data0.get("code") == 200:
                for u in data0.get("data", []):
                    if u.get("username") == "test_api_user":
                        await self.client.delete(f"/system/user/{u['id']}")

            # 创建
            resp = await self.client.post("/system/user", json={
                "username": "test_api_user", "password": "Test@12345",
                "nickname": "API测试用户", "status": 1
            })
            data = resp.json()
            if data.get("code") != 200:
                self._log("用户创建", False, data.get("message", ""))
                return
            self._log("用户创建", True)

            # 查找
            resp2 = await self.client.get("/system/user?page=1&page_size=100&username=test_api_user")
            data2 = resp2.json()
            items = data2.get("data", []) if data2.get("code") == 200 else []
            user_id = None
            for u in items:
                if u.get("username") == "test_api_user":
                    user_id = u.get("id")
                    break

            if not user_id:
                self._log("用户删除", False, "未找到用户ID")
                return

            # 删除
            resp3 = await self.client.delete(f"/system/user/{user_id}")
            data3 = resp3.json()
            self._log("用户删除", data3.get("code") == 200, data3.get("message", "") if data3.get("code") != 200 else "")
        except Exception as e:
            self._log("用户创建/删除", False, str(e))

    # ==================== 角色管理 ====================

    async def test_role_list(self):
        try:
            resp = await self.client.get("/system/role?page=1&page_size=10")
            data = resp.json()
            self._log("角色列表", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("角色列表", False, str(e))

    async def test_role_detail(self):
        try:
            resp = await self.client.get("/system/role/1")
            data = resp.json()
            role = data.get("data", {})
            self._log("角色详情", data.get("code") == 200 and "menu_ids" in role, f"role_name={role.get('role_name')}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("角色详情", False, str(e))

    # ==================== 菜单管理 ====================

    async def test_menu_tree(self):
        try:
            resp = await self.client.get("/system/menu/tree")
            data = resp.json()
            self._log("菜单树", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("菜单树", False, str(e))

    # ==================== 部门管理 ====================

    async def test_dept_list(self):
        try:
            resp = await self.client.get("/system/dept/list")
            data = resp.json()
            self._log("部门列表", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("部门列表", False, str(e))

    # ==================== 岗位管理 ====================

    async def test_post_list(self):
        try:
            resp = await self.client.get("/system/post/list?page=1&page_size=10")
            data = resp.json()
            self._log("岗位列表", data.get("code") == 200, f"count={len(data.get('data', {}).get('items', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("岗位列表", False, str(e))

    # ==================== 字典管理 ====================

    async def test_dict_type_list(self):
        try:
            resp = await self.client.get("/system/dict/type/list?page=1&page_size=10")
            data = resp.json()
            self._log("字典类型列表", data.get("code") == 200, "" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("字典类型列表", False, str(e))

    async def test_dict_data_list(self):
        try:
            resp = await self.client.get("/system/dict/data/list")
            data = resp.json()
            self._log("字典数据列表", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("字典数据列表", False, str(e))

    # ==================== 操作日志 ====================

    async def test_log_list(self):
        try:
            resp = await self.client.get("/system/log/list?page=1&page_size=10")
            data = resp.json()
            self._log("操作日志列表", data.get("code") == 200, "" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("操作日志列表", False, str(e))

    # ==================== 系统配置 ====================

    async def test_config_list(self):
        try:
            resp = await self.client.get("/system/config/list?page=1&page_size=10")
            data = resp.json()
            self._log("系统配置列表", data.get("code") == 200, "" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("系统配置列表", False, str(e))

    # ==================== 流程引擎 ====================

    async def test_workflow_definition_list(self):
        try:
            resp = await self.client.get("/workflow/definition?page=1&page_size=10")
            data = resp.json()
            self._log("流程定义列表", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("流程定义列表", False, str(e))

    async def test_workflow_instance_list(self):
        try:
            resp = await self.client.get("/workflow/instance?page=1&page_size=10")
            data = resp.json()
            self._log("流程实例列表", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("流程实例列表", False, str(e))

    async def test_workflow_todo_list(self):
        try:
            resp = await self.client.get("/workflow/task/todo?page=1&page_size=10")
            data = resp.json()
            self._log("我的待办", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("我的待办", False, str(e))

    async def test_workflow_done_list(self):
        try:
            resp = await self.client.get("/workflow/task/done?page=1&page_size=10")
            data = resp.json()
            self._log("我的已办", data.get("code") == 200, f"count={len(data.get('data', []))}" if data.get("code") == 200 else f"code={data.get('code')}")
        except Exception as e:
            self._log("我的已办", False, str(e))

    # ==================== 运行 ====================

    async def run_all(self):
        print("=" * 60)
        print("  SwiftPlatform API 功能测试")
        print(f"  目标: {BASE_URL}")
        print("=" * 60)

        print("\n📌 认证模块")
        if not await self.test_login():
            print("\n⚠️  登录失败，无法继续测试")
            await self.client.aclose()
            self._print_summary()
            return

        await self.test_user_info()
        await self.test_change_password()

        print("\n📌 系统管理模块")
        await self.test_user_list()
        await self.test_user_create_and_delete()
        await self.test_role_list()
        await self.test_role_detail()
        await self.test_menu_tree()
        await self.test_dept_list()
        await self.test_post_list()

        print("\n📌 字典与配置模块")
        await self.test_dict_type_list()
        await self.test_dict_data_list()
        await self.test_config_list()

        print("\n📌 日志模块")
        await self.test_log_list()

        print("\n📌 流程引擎模块")
        await self.test_workflow_definition_list()
        await self.test_workflow_instance_list()
        await self.test_workflow_todo_list()
        await self.test_workflow_done_list()

        await self.client.aclose()
        self._print_summary()

    def _print_summary(self):
        print("\n" + "=" * 60)
        print("  测试结果汇总")
        print("=" * 60)
        passed = sum(1 for _, ok, _ in self.results if ok)
        failed = sum(1 for _, ok, _ in self.results if not ok)
        for name, ok, detail in self.results:
            tag = "✅" if ok else "❌"
            line = f"  {tag} {name}"
            if detail and not ok:
                line += f"  ← {detail}"
            print(line)
        print("=" * 60)
        print(f"  总计: {len(self.results)} 项  |  ✅ 通过: {passed}  |  ❌ 失败: {failed}")
        if failed == 0:
            print("\n  🎉 全部测试通过！")
        else:
            print(f"\n  ⚠️  有 {failed} 项测试失败")
        print("=" * 60)


if __name__ == "__main__":
    tester = APITester()
    asyncio.run(tester.run_all())