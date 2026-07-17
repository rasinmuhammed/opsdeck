import asyncio
import time
from opsdeck.core.rate_limiter import RateLimiter
from opsdeck.auth.models import AdminUserMixin


async def test_rate_limiter():
    print("🚦 Testing Rate Limiter...")
    limiter = RateLimiter(rate=2, per=5)  # 2 tokens per 5 seconds

    # Fill bucket
    res1 = limiter.consume("ip-1")
    print(f"Request 1: {'Allowed' if res1 else 'Blocked'} (Expected: Allowed)")
    assert res1 is True

    res2 = limiter.consume("ip-1")
    print(f"Request 2: {'Allowed' if res2 else 'Blocked'} (Expected: Allowed)")
    assert res2 is True

    res3 = limiter.consume("ip-1")
    print(f"Request 3: {'Allowed' if res3 else 'Blocked'} (Expected: Blocked)")
    assert res3 is False  # Bucket empty

    print("⏳ Waiting 3 seconds for refill...")
    time.sleep(3)

    res4 = limiter.consume("ip-1")
    print(f"Request 4: {'Allowed' if res4 else 'Blocked'} (Expected: Allowed)")
    assert res4 is True
    print("✅ Rate Limiter Passed\n")


async def test_argon2_hashing():
    print("🔐 Testing Argon2 Hashing...")
    from opsdeck.auth.models import pwd_context

    password = "secret-matrix-admin"

    # Hash
    start = time.time()
    hashed = AdminUserMixin.hash_password(password)
    duration = time.time() - start
    print(f"Hashing Time: {duration:.4f}s (Should be > 0.01s for security)")
    assert duration > 0.01  # Ensure it's not instant (hashing should take some time)
    assert hashed != password
    assert "argon2" in hashed or "$" in hashed

    # Verify using pwd_context directly
    valid = pwd_context.verify(password, hashed)
    print(f"Password Verify: {'Valid' if valid else 'Invalid'} (Expected: Valid)")
    assert valid is True

    invalid = pwd_context.verify("wrong-password", hashed)
    print(f"Wrong Password: {'Valid' if invalid else 'Invalid'} (Expected: Invalid)")
    assert invalid is False
    print("✅ Argon2 Hashing Passed\n")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_rate_limiter())
    loop.run_until_complete(test_argon2_hashing())
