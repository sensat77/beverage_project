# === 最终版，请用这份代码完整替换 parser_service.py 的所有内容 ===
from collections import defaultdict
import re
from app.models.product import Product

def parse_order_text(text_content: str) -> dict:
    # 修复：初始化 parsed_data 时包含 total_gifting_cost
    parsed_data = { "customer_name": "", "order_items": [], "display_fee": 0.0, "old_goods_disposal_fee": 0.0, "total_gifting_cost": 0.0, "messages": [] }
    lines = [line.strip() for line in text_content.strip().split('\n') if line.strip()]
    if not lines: return parsed_data
    
    all_products = Product.query.all()
    product_line_pattern = re.compile(r'(.+?)\s*(\d+)\s*(?:件|箱|瓶|支|盒)\s*(?:(\d+\.?\d*))?')

    alias_map = {
        "大橙汁": "2L鲜橙多",
        "大啊萨姆": "1.5L阿萨姆奶茶",
        "大阿萨姆": "1.5L阿萨姆奶茶",
        "啊萨姆": "阿萨姆", # 错别字纠正
        "一升": "1L",
        "1升" : "1L",
        "1.5升": "1.5L",
        "1升春拂绿茶": "900/1L春拂绿茶",
        "小茗同学": "450ml小茗同学",
        "900春拂绿茶": "900/1L春拂绿茶",
        "1升海之言柠檬": "1L海之言柠檬",
        "1升海之言西柚": "1L海之言西柚",
        "1升水晶葡萄": "1L水晶葡萄", 
        "1升金桔": "1L金桔柠檬", 
        "大红袍牛乳茶":"希蒂大红袍",
        "金桔": "金桔柠檬",
        "雪梨": "冰糖雪梨",
        "冰糖雪梨": "冰糖雪梨",
        "1升绿茶": "1L绿茶",
        "费用": "陈列费" # 费用关键词别名
    }

    # 定义用于识别“减返”或“搭赠”的正则表达式
    gifting_deduction_pattern = re.compile(r'(?:减返|搭赠|搭增)\s*(\d+(?:\.\d+)?)\s*元?')


    temp_items_list = []
    unrecognized_parts = []

    for line in lines:
        parts = re.split(r'[，、；,;]', line)
        
        for part in parts:
            part = part.strip()
            if not part or part.startswith('共'): continue

            is_processed = False
            
            # --- 1. 费用判断 (新逻辑：智能提取最后一个数字) ---
            if '陈列费' in part or '陈列' in part or '费用' in part:
                numbers = re.findall(r'\d+\.?\d+', part)
                if numbers: parsed_data['display_fee'] += float(numbers[-1])
                is_processed = True
            elif '扣旧货' in part or '旧货' in part:
                numbers = re.findall(r'\d+\.?\d+', part)
                if numbers: parsed_data['old_goods_disposal_fee'] += float(numbers[-1])
                is_processed = True
            # 识别“减返”或“搭赠”，并将其金额加入总搭赠费用
            elif gifting_deduction_pattern.search(part):
                match = gifting_deduction_pattern.search(part)
                if match:
                    parsed_data['total_gifting_cost'] += float(match.group(1)) # 直接累加到已初始化的 total_gifting_cost
                is_processed = True

            if is_processed: continue

            # --- 2. 产品判断 ---
            product_line_match = product_line_pattern.search(part)
            if product_line_match:
                product_name_str, quantity_str, price_str = product_line_match.groups()
                product_name_str = product_name_str.strip()
                if not product_name_str: continue
                
                quantity = int(quantity_str)
                processed_name = product_name_str
                for alias, standard in alias_map.items():
                    if alias in processed_name: processed_name = processed_name.replace(alias, standard)
                
                normalized_input = processed_name.replace('升', 'L')
                input_keywords = set(re.findall(r'[a-zA-Z]+|\d+\.\d*|\d+|[\u4e00-\u9fa5]+', normalized_input))
                if not input_keywords: continue
                
                best_match_product, highest_score = None, 0
                for db_product in all_products:
                    db_product_name_lower = db_product.name.lower()
                    score = sum(1 for keyword in input_keywords if keyword.lower() in db_product_name_lower)
                    if score > highest_score:
                        highest_score, best_match_product = score, db_product
                    elif score == highest_score and score > 0:
                        if len(db_product.name) < len(best_match_product.name):
                            best_match_product = db_product
                
                if best_match_product and highest_score / len(input_keywords) >= 0.5:
                    # 关键修复点：如果 price_str 为 None，则使用数据库原价
                    actual_price = float(price_str) if price_str else float(best_match_product.unit_price) 
                    
                    item_gifting_cost = max(0, float(best_match_product.unit_price) - actual_price) * quantity 
                    
                    temp_items_list.append({ "product_name": best_match_product.name, "unit_price": best_match_product.unit_price, "quantity": quantity, "actual_unit_price": actual_price, 'item_gifting_cost': item_gifting_cost })
                else:
                    unrecognized_parts.append(part)
            else:
                unrecognized_parts.append(part)
    
    # --- 3. 客户名最终决策 ---
    if unrecognized_parts:
        parsed_data['customer_name'] = max(unrecognized_parts, key=len)
    elif lines and not temp_items_list: # 如果一行都识别不出来，第一行就是客户
        parsed_data['customer_name'] = lines[0]

    # --- 4. 合并与总计 ---
    consolidated_items = defaultdict(lambda: {'quantity': 0, 'total_amount': 0, 'total_gifting': 0, 'unit_price': 0})
    for item in temp_items_list:
        name = item['product_name']
        consolidated_items[name]['quantity'] += item['quantity']
        consolidated_items[name]['total_amount'] += item['quantity'] * float(item['actual_unit_price'])
        # item['item_gifting_cost'] 已经包含了这个产品本身的搭赠
        consolidated_items[name]['total_gifting'] += item['item_gifting_cost'] 
        consolidated_items[name]['unit_price'] = item['unit_price']
        
    for name, data in consolidated_items.items():
        avg_price = data['total_amount'] / data['quantity'] if data['quantity'] else 0
        parsed_data['order_items'].append({ 'product_name': name, 'quantity': data['quantity'], 'actual_unit_price': round(avg_price, 2), 'item_amount': data['total_amount'], 'item_gifting_cost': data['total_gifting'] })
        
    parsed_data['total_item_count'] = sum(item['quantity'] for item in parsed_data['order_items'])
    
    # 修复：将产品项的搭赠成本累加到总搭赠费用中
    # parsed_data['total_gifting_cost'] 已经包含了额外识别的“减返/搭赠”金额
    # 这里再累加产品项的搭赠成本。
    parsed_data['total_gifting_cost'] += sum(item['item_gifting_cost'] for item in parsed_data['order_items'])

    total_commission = 0
    for item in parsed_data['order_items']:
        product = Product.query.filter_by(name=item['product_name']).first()
        if product:
            total_commission += float(product.commission_per_item) * item['quantity']
    parsed_data['total_commission'] = total_commission
    
    return parsed_data