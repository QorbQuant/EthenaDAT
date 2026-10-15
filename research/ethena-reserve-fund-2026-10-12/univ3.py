"""Uniswap V3 position math in exact integers, as the core and periphery contracts compute it.

get_sqrt_ratio_at_tick follows TickMath.getSqrtRatioAtTick. amounts_for_liquidity follows
LiquidityAmounts.getAmountsForLiquidity, which rounds down. fees_owed follows Tick.getFeeGrowthInside and
Position.update, with uint256 wraparound.
"""

MAX_TICK = 887272
Q96 = 1 << 96
Q128 = 1 << 128
U256 = 1 << 256

_STEPS = [
    (0x2, 0xfff97272373d413259a46990580e213a),
    (0x4, 0xfff2e50f5f656932ef12357cf3c7fdcc),
    (0x8, 0xffe5caca7e10e4e61c3624eaa0941cd0),
    (0x10, 0xffcb9843d60f6159c9db58835c926644),
    (0x20, 0xff973b41fa98c081472e6896dfb254c0),
    (0x40, 0xff2ea16466c96a3843ec78b326b52861),
    (0x80, 0xfe5dee046a99a2a811c461f1969c3053),
    (0x100, 0xfcbe86c7900a88aedcffc83b479aa3a4),
    (0x200, 0xf987a7253ac413176f2b074cf7815e54),
    (0x400, 0xf3392b0822b70005940c7a398e4b70f3),
    (0x800, 0xe7159475a2c29b7443b29c7fa6e889d9),
    (0x1000, 0xd097f3bdfd2022b8845ad8f792aa5825),
    (0x2000, 0xa9f746462d870fdf8a65dc1f90e061e5),
    (0x4000, 0x70d869a156d2a1b890bb3df62baf32f7),
    (0x8000, 0x31be135f97d08fd981231505542fcfa6),
    (0x10000, 0x9aa508b5b7a84e1c677de54f3e99bc9),
    (0x20000, 0x5d6af8dedb81196699c329225ee604),
    (0x40000, 0x2216e584f5fa1ea926041bedfe98),
    (0x80000, 0x48a170391f7dc42444e8fa2),
]


def get_sqrt_ratio_at_tick(tick):
    abs_tick = -tick if tick < 0 else tick
    if abs_tick > MAX_TICK:
        raise ValueError("tick out of range")
    ratio = 0xfffcb933bd6fad37aa2d162d1a594001 if abs_tick & 0x1 else 0x100000000000000000000000000000000
    for bit, mul in _STEPS:
        if abs_tick & bit:
            ratio = (ratio * mul) >> 128
    if tick > 0:
        ratio = (U256 - 1) // ratio
    return (ratio >> 32) + (0 if ratio % (1 << 32) == 0 else 1)


def amount0_for_liquidity(sa, sb, liquidity):
    if sa > sb:
        sa, sb = sb, sa
    return ((liquidity << 96) * (sb - sa) // sb) // sa


def amount1_for_liquidity(sa, sb, liquidity):
    if sa > sb:
        sa, sb = sb, sa
    return liquidity * (sb - sa) // Q96


def amounts_for_liquidity(sqrt_price, sa, sb, liquidity):
    if sa > sb:
        sa, sb = sb, sa
    if sqrt_price <= sa:
        return amount0_for_liquidity(sa, sb, liquidity), 0
    if sqrt_price < sb:
        return amount0_for_liquidity(sqrt_price, sb, liquidity), amount1_for_liquidity(sa, sqrt_price, liquidity)
    return 0, amount1_for_liquidity(sa, sb, liquidity)


def fee_growth_inside(tick_current, tick_lower, tick_upper, lower_outside, upper_outside, global_growth):
    below = lower_outside if tick_current >= tick_lower else (global_growth - lower_outside) % U256
    above = upper_outside if tick_current < tick_upper else (global_growth - upper_outside) % U256
    return (global_growth - below - above) % U256


def fees_owed(liquidity, inside_now, inside_last, tokens_owed):
    return tokens_owed + (((inside_now - inside_last) % U256) * liquidity) // Q128


if __name__ == "__main__":
    assert get_sqrt_ratio_at_tick(0) == Q96
    assert get_sqrt_ratio_at_tick(-887272) == 4295128739
    assert get_sqrt_ratio_at_tick(887272) == 1461446703485210103287273052203988822378723970342
    assert get_sqrt_ratio_at_tick(1) == 79232123823359799118286999568
    assert get_sqrt_ratio_at_tick(-1) == 79224201403219477170569942574
    print("tick math ok")
