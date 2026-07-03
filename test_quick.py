"""快速测试脚本"""
import traceback
try:
    import akshare as ak
    print("akshare 导入成功")
    
    import yaml
    print("yaml 导入成功")
    
    import pandas as pd
    print("pandas 导入成功")
    
    # 测试获取 A 股数据
    print("\n正在获取 A 股实时数据...")
    df = ak.stock_zh_a_spot_em()
    print(f"获取到 {len(df)} 条数据")
    print(f"列名: {list(df.columns)}")
    
    # 查找平安银行
    row = df[df["代码"] == "000001"]
    if not row.empty:
        print(f"\n平安银行: 最新价={row.iloc[0]['最新价']}, 涨跌幅={row.iloc[0]['涨跌幅']}%")
    
    # 测试港股
    print("\n正在获取港股实时数据...")
    hk_df = ak.stock_hk_spot_em()
    print(f"获取到 {len(hk_df)} 条数据")
    print(f"列名: {list(hk_df.columns)}")
    
    row = hk_df[hk_df["代码"] == "00700"]
    if not row.empty:
        print(f"\n腾讯控股: 最新价={row.iloc[0]['最新价']}, 涨跌幅={row.iloc[0]['涨跌幅']}%")
    
    print("\n✅ 所有测试通过！")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    traceback.print_exc()
