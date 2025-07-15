import json
import akshare as ak

# 加载 JSON 文件
with open("akshare_interfaces.json", "r", encoding="utf-8") as f:
    config = json.load(f)

errors = []

# 通用调用函数
def call_interface(name, params):
    func = getattr(ak, name, None)
    if func is None:
        raise AttributeError(f"AKShare 中未找到接口：{name}")
    try:
        return func(**params)
    except Exception as e:
        raise RuntimeError(f"{name} 调用失败：{e}")

# 遍历所有接口
for category in config["categories"]:
    for iface in category["interfaces"]:
        name = iface["name"]
        params = iface.get("example_params", {})
        print(f"调用接口 {name}，参数 {params} ...", end=" ")
        try:
            df = call_interface(name, params)
            # 检查返回是否非空
            if df is None or (hasattr(df, "empty") and df.empty):
                print("⚠️ 返回为空")
                errors.append((name, "空数据"))
            else:
                print("✅ 成功")
        except Exception as e:
            print("❌ 失败")
            errors.append((name, str(e)))

# 总结结果
print("\n测试结束。")
if errors:
    print("以下接口有问题：")
    for name, errmsg in errors:
        print(f"- {name}：{errmsg}")
else:
    print("所有接口均成功返回数据。")
