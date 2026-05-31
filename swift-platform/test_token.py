"""简化测试 - 验证 token 传递"""

import httpx
import asyncio

BASE_URL = "http://localhost:8090/api"

async def test():
    print("=" * 50)
    print("  Token 传递验证测试")
    print("=" * 50)
    
    # 使用独立的 client，不设置 base_url
    client = httpx.AsyncClient(timeout=30)
    
    # 1. 登录
    print("\n1. 登录...")
    resp = await client.post(f"{BASE_URL}/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    print(f"   状态码: {resp.status_code}")
    data = resp.json()
    print(f"   响应: code={data.get('code')}, msg={data.get('message')}")
    
    if data.get('code') != 200:
        print("   ❌ 登录失败")
        return
    
    token = data['data']['access_token']
    print(f"   ✅ Token 获取成功: {token[:30]}...")
    
    # 2. 测试 user-info - 方式1: 直接在请求中设置 headers
    print("\n2. 获取用户信息 (方式1: 直接设置 headers)...")
    headers = {"Authorization": f"Bearer {token}"}
    resp2 = await client.get(f"{BASE_URL}/auth/user-info", headers=headers)
    print(f"   状态码: {resp2.status_code}")
    print(f"   响应: {resp2.text[:200]}")
    
    # 3. 测试 user-info - 方式2: 更新 client 的默认 headers
    print("\n3. 获取用户信息 (方式2: 更新 client.headers)...")
    client.headers["Authorization"] = f"Bearer {token}"
    resp3 = await client.get(f"{BASE_URL}/auth/user-info")
    print(f"   状态码: {resp3.status_code}")
    print(f"   响应: {resp3.text[:200]}")
    
    await client.aclose()
    print("\n" + "=" * 50)

asyncio.run(test())